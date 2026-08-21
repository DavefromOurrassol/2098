#!/usr/bin/env python3
"""
promote_ville.py — Ourrassol 2098
====================================

Injection CIBLÉE d'une ville dans la géographie du vault, sur un ou
plusieurs scénarios — complément d'enrich_geographie_recursive.py
(étape 2), qui procède par scan complet du corpus et n'est jamais
garanti de retenir un lieu précis (arbitrage LLM en une seule passe sur
tout un scénario, non déterministe — voir cas Istanbul du 18 août 2026,
oublié malgré sa présence en lieu_emblematique lors d'un run réel).

Ici, une seule ville, un traitement dédié, avec un rattachement au
parent le plus précis possible et une détection multi-forme AVANT toute
création.

PRINCIPE
--------
Pour chaque scénario ciblé :
1. Résout le pays réel 2026 de la ville (fourni en argument, ou en
   secours un appel LLM léger avec confirmation avant toute écriture).
2. Cherche si la ville existe déjà, sous une forme ou une autre :
     a. slug exact (slugify_fixed) déjà présent dans `zones`
     b. `nom` de zone correspondant
     c. entrée `lieux_emblematiques.nom` sur une zone existante
     d. simple mention narrative dans le corpus (instances/événements),
        sans aucune structure
   Ces 4 cas ne sont PAS équivalents du point de vue de l'exploitabilité
   (voir doctrine ci-dessous).
3. Selon le cas trouvé, demande confirmation puis agit :
     - cas (a) zone déjà exploitable : rien à faire par défaut, sauf
       refus explicite (ex. deux villes homonymes réellement distinctes).
     - cas (b)/(c) : PROMOTION FORCÉE par défaut, même si l'utilisateur
       confirme que "c'est déjà le bon endroit conceptuellement" — un
       lieu_emblematique ou une mention narrative n'est PAS un slug de
       zone valide pour `localisation.zone` (validate.py ne connaît que
       les slugs du champ `zones`). Ne jamais laisser croire qu'un trou
       est comblé alors qu'il ne l'est pas structurellement.
     - cas (d)/rien trouvé : création directe.
4. Pour toute création, résout le parent le plus précis possible via
   zones_pays.json (point de départ déterministe : pays -> zone niveau 1
   du scénario), PUIS interroge le LLM avec la liste complète des
   sous-zones déjà existantes sous cette zone-pays pour choisir un
   parent plus profond si pertinent, plutôt que de rattacher
   systématiquement au niveau 1.
5. Génère la fiche complète de la nouvelle zone (LLM, corpus réduit aux
   instances/événements mentionnant déjà la ville), valide mécaniquement
   avec les MÊMES fonctions qu'enrich_geographie_recursive.py (import
   direct, aucune duplication de logique), écrit avec backup .bak.

DOCTRINE — pourquoi la distinction des 4 cas est stricte
-----------------------------------------------------------
Rappel (validate.py, load_valid_zone_slugs) : la seule source de vérité
pour un slug de zone valide est le champ `zones[].slug` de
geographie/{scenario}.md. Un `lieu_emblematique` ou une simple mention
narrative n'y figurent jamais. Répondre "oui, ça répond au besoin" sur un
cas (b)/(c) sans promouvoir recrée exactement le bug d'origine
(gelecek_meclisi_policy_reform / istanbul, 17-18 août 2026) : un article
peut se localiser dessus, la validation échoue, personne ne le sait tant
que review_localisation.py ne tombe pas dessus par hasard.

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...  (ou clé du provider configuré)

USAGE
-----
    python3 promote_ville.py --ville Istanbul --dry-run
    python3 promote_ville.py --ville Istanbul --pays Turquie
    python3 promote_ville.py --ville Istanbul --pays Turquie \
        --scenarios policy_reform,reference
    python3 promote_ville.py --ville Istanbul --pays Turquie --all
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

import yaml

from llm_client import call_llm, resolve_for_tier

# Réutilisation intégrale — aucune logique dupliquée depuis l'étape 2.
from enrich_geographie_recursive import (
    parse_md,
    load_existing_geographie,
    gather_instance_texts,
    gather_event_texts,
    validate_zone,
    resolve_parents_and_levels,
    clean_sources,
    clean_zone_relations,
    dedupe_promoted_lieux,
    build_geographie_md,
    write_geographie_file,
    ZONE_TYPES,
    ZONE_STATUTS,
    TYPE_ENTITE_REELLE,
)

TASK_TIER_LEGER = "strict"            # résolution pays, arbitrage parent
TASK_TIER_REDACTION = "structured_strict"  # rédaction de la fiche zone

QUIET = False  # positionné depuis main() via --quiet


def _call_llm(**kwargs):
    """Wrapper autour de call_llm : en mode --quiet, masque le print
    '[llm] Provider (model) — entrée : X | sortie : Y' émis par
    llm_client.py (fichier partagé, volontairement non modifié pour ne
    pas affecter les autres scripts du pipeline)."""
    if not QUIET:
        return call_llm(**kwargs)
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = call_llm(**kwargs)
    return result

VAULT_ROOT = Path(__file__).resolve().parent.parent
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"
GUI_DIR = VAULT_ROOT / "gui"
ZONES_PAYS_PATH = GUI_DIR / "zones_pays.json"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]


# ---------------------------------------------------------------------------
# Slugify (même convention que audit_broken_slugs.py, corrigée 14 août 2026)
# ---------------------------------------------------------------------------

def slugify_fixed(text):
    import unicodedata
    s = unicodedata.normalize("NFD", text or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


# ---------------------------------------------------------------------------
# Étape 1 — résolution ville -> pays réel (si non fourni)
# ---------------------------------------------------------------------------

RESOLVE_PAYS_SYSTEM = """Tu réponds à une question factuelle simple et précise sur \
le monde réel de 2026. On te donne un nom de ville. Réponds UNIQUEMENT avec un objet \
JSON, sans aucun texte autour :
{"pays": "Nom du pays réel en français, tel qu'il apparaîtrait dans une liste de pays \
(ex: 'Turquie', 'États-Unis', 'Corée du Sud')", "confiance": "haute|moyenne|basse", \
"note": "1 courte phrase si ambiguïté (plusieurs villes homonymes dans des pays \
différents), sinon chaîne vide"}"""


def resolve_pays_via_llm(ville):
    text = _call_llm(
        system_prompt=RESOLVE_PAYS_SYSTEM,
        user_prompt=f"Ville : {ville}",
        max_tokens=300,
        temperature=0.0,
        task_tier=TASK_TIER_LEGER,
    ).strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", text)
    candidate = re.sub(r"\s*```$", "", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        raise RuntimeError(f"Réponse LLM non exploitable pour la résolution pays : {text[:200]!r}")


def confirm(question):
    reponse = input(f"{question} [o/N] : ").strip().lower()
    return reponse in ("o", "oui", "y", "yes")


# ---------------------------------------------------------------------------
# Étape 2 — détection multi-forme, par scénario
# ---------------------------------------------------------------------------

def detect_existing(ville, zones, corpus_text):
    """Retourne un dict décrivant le meilleur match trouvé, ou None.
    {"cas": "a"|"b"|"c"|"d", "slug": ..., "detail": ...}
    Cas a = zone existante (slug ou nom) -> exploitable tel quel.
    Cas b = lieu_emblematique -> PAS exploitable, promotion nécessaire.
    Cas c = alias identique au cas b, conservé séparé pour le message.
    Cas d = mention narrative libre seulement, ou rien -> création directe.
    """
    ville_slug = slugify_fixed(ville)
    ville_norm = ville.strip().lower()

    # cas (a) — slug exact
    for zone in zones:
        if zone.get("slug") == ville_slug:
            return {"cas": "a", "slug": zone["slug"],
                    "detail": f"zone existante (slug exact '{zone['slug']}')"}

    # cas (a) — nom exact ou très proche
    for zone in zones:
        nom = str(zone.get("nom", "")).strip().lower()
        if nom == ville_norm or difflib.SequenceMatcher(None, nom, ville_norm).ratio() > 0.92:
            return {"cas": "a", "slug": zone.get("slug"),
                    "detail": f"zone existante (nom proche : '{zone.get('nom')}')"}

    # cas (b) — lieu_emblematique sur une zone existante
    for zone in zones:
        for lieu in (zone.get("lieux_emblematiques") or []):
            nom = (lieu.get("nom", "") if isinstance(lieu, dict) else str(lieu)).strip()
            if nom.lower().startswith(ville_norm) or ville_norm in nom.lower():
                return {"cas": "b", "slug": zone.get("slug"), "lieu_nom": nom,
                        "detail": f"trouvé comme lieu_emblematique '{nom}' "
                                  f"sur la zone '{zone.get('slug')}'"}

    # cas (d) — mention narrative libre uniquement
    if ville_norm in corpus_text.lower():
        return {"cas": "d", "slug": None,
                "detail": "mention narrative trouvée dans le corpus, "
                          "aucune structure de zone"}

    return None


# ---------------------------------------------------------------------------
# Étape 3 — résolution du parent le plus précis (zones_pays.json + LLM)
# ---------------------------------------------------------------------------

def load_zones_pays():
    if not ZONES_PAYS_PATH.exists():
        return {}
    return json.loads(ZONES_PAYS_PATH.read_text(encoding="utf-8"))


CHOOSE_PARENT_SYSTEM = """Tu travailles sur Ourrassol 2098, simulateur de presse \
fictive en 2098. On te donne une ville réelle à rattacher géographiquement dans un \
scénario précis, la zone-pays de niveau 1 à laquelle son pays réel est normalement \
rattaché (point de départ déterministe), et la liste complète des sous-zones déjà \
existantes sous cette zone-pays (si il y en a). Choisis le parent le PLUS PRÉCIS et \
narrativement cohérent pour cette ville : une sous-zone existante si l'une d'elles \
correspond clairement à la région où se trouve la ville, SINON la zone-pays de niveau \
1 elle-même. Ne propose jamais un slug qui n'est pas dans la liste fournie.

Réponds UNIQUEMENT avec un objet JSON : {"parent_slug": "slug_exact_de_la_liste", \
"raison": "1 courte phrase"}"""


def choose_parent(ville, scenario, zone_pays_slug, all_zones):
    sous_zones = [z for z in all_zones if z.get("parent") == zone_pays_slug]
    if not sous_zones:
        return zone_pays_slug, "aucune sous-zone existante sous la zone-pays — rattachement direct"

    liste_txt = "\n".join(
        f"  - {z['slug']} — {z.get('nom', z['slug'])} ({z.get('type', '?')})"
        for z in sous_zones
    )
    user_content = (
        f"Scénario : {scenario}\nVille à rattacher : {ville}\n"
        f"Zone-pays de niveau 1 (point de départ) : {zone_pays_slug}\n\n"
        f"Sous-zones déjà existantes sous {zone_pays_slug} :\n{liste_txt}"
    )
    text = _call_llm(
        system_prompt=CHOOSE_PARENT_SYSTEM,
        user_prompt=user_content,
        max_tokens=300,
        temperature=0.0,
        task_tier=TASK_TIER_LEGER,
    ).strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", text)
    candidate = re.sub(r"\s*```$", "", candidate)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return zone_pays_slug, "échec de parsing LLM — repli sur la zone-pays niveau 1"

    valid_slugs = {zone_pays_slug} | {z["slug"] for z in sous_zones}
    parent_slug = parsed.get("parent_slug")
    if parent_slug not in valid_slugs:
        return zone_pays_slug, f"parent LLM invalide ('{parent_slug}') — repli sur la zone-pays niveau 1"
    return parent_slug, parsed.get("raison", "")


# ---------------------------------------------------------------------------
# Étape 4 — génération de la fiche de la nouvelle zone
# ---------------------------------------------------------------------------

CREATE_ZONE_SYSTEM = """Tu travailles sur Ourrassol 2098, simulateur de presse \
fictive en 2098. Rédige la fiche complète d'UNE SEULE zone géographique — une ville \
promue en sous-zone à part entière dans le scénario donné, sous le parent déjà \
déterminé (fourni ci-dessous, ne le remets pas en question). Appuie-toi sur le corpus \
narratif fourni s'il existe (mentions déjà présentes de cette ville) ; s'il est vide, \
imagine un rôle plausible et cohérent avec la description de la zone parente et le ton \
général du scénario.

RÈGLES :
- "origine_reelle" : TOUJOURS renseigné, la ville réelle de 2026 elle-même. \
IMPORTANT : "type_entite" n'accepte QUE ces valeurs exactes : "pays", "etat_federe", \
"province", "region_administrative", "autre" — il n'existe PAS de catégorie "ville". \
Puisque l'entité listée est la ville elle-même (pas un pays), utilise TOUJOURS \
"type_entite": "autre" dans ce cas précis.
- "sources_attestees" : slugs [INSTANCE: ...] ou [EVENEMENT: ...] réellement présents \
dans le corpus fourni ci-dessous qui mentionnent cette ville — n'invente aucune source, \
liste vide si aucune.
- "relations" (allies/rivaux) : uniquement des slugs de zones qui existent réellement \
dans la liste fournie en contexte (zone parente incluse) — laisse vide si aucune \
relation propre n'a de sens à cette échelle.
- Ne remplis PAS "parent" ni "niveau" ni "promu_depuis" toi-même, ils sont déjà fixés \
par le pipeline.

Réponds UNIQUEMENT avec un objet JSON :
{
  "slug": "slug_snake_case",
  "nom": "Nom canonique de la zone",
  "type": "une valeur parmi: bloc_continental, union_regionale, territoire_autonome, territoire_herite, region, ville, infrastructure, site_strategique, zone_sinistree, autre",
  "origine_reelle": [{"entite": "Nom réel", "type_entite": "pays|etat_federe|province|region_administrative|autre", "portion": null}],
  "description": "2-3 lignes sur ce qu'est cette zone DANS ce scénario précis",
  "statut": "une valeur parmi: dominant, stable, fragmenté, en_declin, disparu, emergent",
  "tensions_internes": "1-2 lignes, ou chaîne vide",
  "periode_transition": "période approximative, ex: 2031-2045",
  "evenement_transition": null,
  "lieux_emblematiques": [{"nom": "...", "type": "ville|region|infrastructure|site_strategique", "notes": "..."}],
  "relations": {"allies": [], "rivaux": []},
  "sources_attestees": []
}"""


def generate_zone_fiche(ville, scenario, forced_slug, corpus_extrait, valid_sources, contexte_zones):
    zones_txt = "\n".join(
        f"  - {z['slug']} — {z.get('nom', z['slug'])}" for z in contexte_zones
    )
    user_content = (
        f"Scénario : {scenario}\nVille à rédiger : {ville}\n"
        f"Slug imposé : {forced_slug}\n\n"
        f"Zones du contexte (parent + zones sœurs, pour cohérence des relations) :\n{zones_txt}\n\n"
        f"Corpus narratif mentionnant déjà cette ville "
        f"({len(corpus_extrait)} caractères, vide si aucune mention) :\n{corpus_extrait}"
    )
    text = _call_llm(
        system_prompt=CREATE_ZONE_SYSTEM,
        user_prompt=user_content,
        max_tokens=2000,
        temperature=0.2,
        task_tier=TASK_TIER_REDACTION,
    ).strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", text)
    candidate = re.sub(r"\s*```$", "", candidate)
    zone = json.loads(candidate)
    zone["slug"] = forced_slug  # le slug est TOUJOURS imposé, jamais laissé au LLM
    zone["sources_attestees"] = [s for s in zone.get("sources_attestees", []) if s in valid_sources]

    # Filet de sécurité mécanique (indépendant de la discipline du prompt) :
    # normalise tout type_entite hors de TYPE_ENTITE_REELLE vers "autre" plutôt
    # que de laisser validate_zone rejeter toute la fiche pour ce seul champ.
    for entite in zone.get("origine_reelle", []) or []:
        if isinstance(entite, dict) and entite.get("type_entite") not in TYPE_ENTITE_REELLE:
            entite["type_entite"] = "autre"

    return zone


# ---------------------------------------------------------------------------
# Orchestration par scénario
# ---------------------------------------------------------------------------

def process_scenario(scenario, ville, pays, forced_slug, dry_run):
    print(f"\n=== {scenario} ===")
    zones, vue_ensemble = load_existing_geographie(scenario)
    if zones is None:
        print(f"  ✗ geographie/{scenario}.md n'existe pas — ignoré.")
        return

    instance_blocks = gather_instance_texts(scenario)
    event_blocks = gather_event_texts(scenario)
    corpus_text = "\n\n".join(instance_blocks + event_blocks)
    valid_sources = set()
    for block in instance_blocks + event_blocks:
        m = re.match(r"\[(?:INSTANCE|EVENEMENT): ([a-z0-9_]+)\]", block)
        if m:
            valid_sources.add(m.group(1))

    match = detect_existing(ville, zones, corpus_text)

    if match and match["cas"] == "a":
        print(f"  → {match['detail']}")
        if not confirm("  Ce slug répond-il déjà au besoin (rien à créer) ?"):
            print("  → refus noté, poursuite vers une création malgré le match (cas homonyme).")
        else:
            print("  ✓ Rien à faire sur ce scénario.")
            return

    elif match and match["cas"] == "b":
        print(f"  → {match['detail']}")
        print("  ⚠ Un lieu_emblematique n'est PAS un slug de zone valide pour "
              "localisation.zone — promotion nécessaire pour être réellement exploitable.")
        if not confirm("  Promouvoir cette entrée en zone à part entière ?"):
            print("  → refus explicite : trou laissé tel quel, non exploitable, "
                  "signalé mais aucune action.")
            return
        # on retient le slug de la zone parente pour dedupe_promoted_lieux
        parent_hint = match["slug"]

    elif match and match["cas"] == "d":
        print(f"  → {match['detail']}")
        if not confirm("  Créer une zone structurée pour cette ville ?"):
            print("  → refus explicite, rien créé.")
            return

    else:
        print("  → aucune trace trouvée, création directe.")

    # -- résolution parent --
    zones_pays = load_zones_pays()
    scenario_map = zones_pays.get(scenario, {})
    zone_pays_slug = scenario_map.get(pays)
    if not zone_pays_slug:
        print(f"  ✗ pays '{pays}' non rattaché à une zone dans zones_pays.json "
              f"pour ce scénario — impossible de poursuivre sans intervention manuelle.")
        return

    parent_slug, raison = choose_parent(ville, scenario, zone_pays_slug, zones)
    print(f"  → parent retenu : {parent_slug} ({raison})")

    # -- génération de la fiche --
    contexte_zones = [z for z in zones if z.get("slug") in {parent_slug, zone_pays_slug}]
    corpus_extrait = "\n\n".join(
        b for b in (instance_blocks + event_blocks) if ville.lower() in b.lower()
    )
    slug_final = forced_slug or slugify_fixed(ville)
    try:
        zone = generate_zone_fiche(ville, scenario, slug_final, corpus_extrait,
                                    valid_sources, contexte_zones)
    except Exception as e:
        print(f"  ✗ Erreur génération : {e}")
        return

    zone["parent"] = parent_slug
    zone["promu_depuis"] = match.get("lieu_nom") if match and match["cas"] == "b" else None

    issues = validate_zone(zone)
    if issues:
        print(f"  ✗ Zone rejetée après génération : {', '.join(issues)}")
        return

    new_zones, rejected = resolve_parents_and_levels(zones, [zone])
    for slug, reason in rejected:
        print(f"  ✗ Zone rejetée ('{slug}') : {reason}")
    if not new_zones:
        return

    new_zones = clean_sources(new_zones, valid_sources)
    all_slugs = {z["slug"] for z in zones if z.get("slug")} | {z["slug"] for z in new_zones}
    new_zones, dropped = clean_zone_relations(all_slugs, new_zones)
    for zslug, field, value in dropped:
        print(f"  ⚠ {field} filtrée sur '{zslug}' (pas une zone connue) : '{value}'")

    zones, dedupe_log = dedupe_promoted_lieux(zones, new_zones)
    for zslug, parent_slug_log, nom, action in dedupe_log:
        print(f"  → lieu_emblematique '{nom}' {action} sur '{parent_slug_log}' "
              f"(promu en zone '{zslug}')")

    all_zones = zones + new_zones
    print(f"  → zone créée : [{new_zones[0]['niveau']}] {new_zones[0]['nom']} "
          f"(slug: {new_zones[0]['slug']}, sous {new_zones[0]['parent']})")

    if dry_run:
        print(f"  (dry-run : fichier non affiché en entier — {len(all_zones)} zones "
              f"au total après ajout, résumé de la nouvelle zone ci-dessus)")
        return

    result_path = write_geographie_file(scenario, all_zones, vue_ensemble,
                                         len(new_zones), dry_run)
    if result_path:
        print(f"  ✓ Écrit : {result_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Injection ciblée d'une ville dans la géographie du vault, "
                     "sur un ou plusieurs scénarios."
    )
    parser.add_argument("--ville", required=True, help="Nom de la ville à promouvoir")
    parser.add_argument("--pays", help="Pays réel 2026 (sinon résolu par LLM avec confirmation)")
    parser.add_argument("--slug", help="Force un slug précis (sinon slugify_fixed(ville))")
    parser.add_argument("--scenarios", help="Liste de scénarios séparés par des virgules")
    parser.add_argument("--all", action="store_true", help="Traiter les 6 scénarios (défaut)")
    parser.add_argument("--dry-run", action="store_true",
                         help="Affiche le résultat sans rien écrire sur disque")
    parser.add_argument("--quiet", action="store_true",
                         help="Log minimal : détection, confirmations, parent, résultat final "
                              "seulement (masque les lignes [llm] et de détail intermédiaire)")
    args = parser.parse_args()

    if args.quiet:
        global QUIET
        QUIET = True

    if args.scenarios:
        targets = [s.strip() for s in args.scenarios.split(",") if s.strip()]
        invalid = [s for s in targets if s not in SCENARIOS]
        if invalid:
            sys.exit(f"Scénario(s) inconnu(s) : {invalid}")
    else:
        targets = SCENARIOS  # --all par défaut

    pays = args.pays
    if not pays:
        print(f"Résolution du pays réel pour '{args.ville}' via LLM...")
        result = resolve_pays_via_llm(args.ville)
        print(f"  → Pays proposé : {result.get('pays')} "
              f"(confiance : {result.get('confiance')})")
        if result.get("note"):
            print(f"  Note : {result['note']}")
        if not confirm("  Confirmer ce pays ?"):
            sys.exit("Abandon — relance avec --pays pour préciser toi-même.")
        pays = result["pays"]

    print("=" * 60)
    print(f"OURRASSOL 2098 — promote_ville.py : {args.ville} ({pays})")
    print(f"Scénarios ciblés : {', '.join(targets)}")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit, mais de vrais appels API sont faits)")

    for scenario in targets:
        process_scenario(scenario, args.ville, pays, args.slug, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("Terminé.")
    print("=" * 60)


if __name__ == "__main__":
    main()
