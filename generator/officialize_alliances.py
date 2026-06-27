#!/usr/bin/env python3
"""
officialize_alliances.py — Ourrassol 2098
============================================

Phase 1 du chantier "alliances/oppositions" (voir HANDOFF du 20 juin).

PROBLÈME TRAITÉ
----------------
Les champs `alliances`/`oppositions` des fiches instances/{slug}.md
contiennent très majoritairement du texte libre ("Consortium
Technocratique de Régulation Globale", "Mouvements souverainistes
territoriaux de deuxième génération"...) plutôt que des slugs réels.
prompt_builder.py n'exploite jamais ces champs aujourd'hui, donc cela
n'a aucun impact sur les articles générés — mais empêche toute
exploitation future et laisse le vault dans un état hétérogène.

CE QUE FAIT CE SCRIPT (one-shot, à lancer UNE fois)
-----------------------------------------------------
1. Scanne toutes les instances/*.md, extrait toutes les mentions
   alliances/oppositions en texte libre (ignore les slugs déjà valides
   — référence à une instance existante).
2. Envoie le lot complet à Claude pour déduplication sémantique : les
   mentions qui désignent manifestement le même acteur sous des
   formulations différentes (ex: "Souverainistes du Bloc Eurasien" vs
   "Blocs régionaux souverainistes (Ligue Eurasiatique...)") sont
   fusionnées sous UN nom canonique. Fusion appliquée automatiquement,
   sans validation humaine intermédiaire (décision explicite de
   l'utilisateur). Les 1-2 mentions trop vagues pour avoir un nom
   propre clair ("Quelques cités-États côtières désespérées") se voient
   attribuer un nom propre inventé par Claude dans la même passe.
3. Pour chaque nom canonique retenu :
   - crée une fiche entité MINIMALE (entites/{slug}.md) avec
     `statut: officialise_minimal` dans le frontmatter — champs
     structurels remplis a minima (assez pour valider proprement dans
     validate.py), PAS de description longue ni de tension fondamentale
     travaillée. Ces fiches sont des candidates pour un enrichissement
     ultérieur en phase 2 (par lots, en différé — voir HANDOFF), repris
     manuellement via create_entity.py/generate_instances.py sur la
     base de ce statut.
   - crée l'instance MINIMALE correspondante (instances/{slug}_{scenario}.md)
     dans le SEUL scénario où elle a été mentionnée à l'origine (déduit
     de la fiche source qui la citait) — pas dans les 6 scénarios.
   - met à jour entites/_entities_list.json (registre anti-doublon
     permanent).
4. Réécrit les fiches instances/*.md sources : chaque mention texte
   libre est remplacée par le slug du nom canonique correspondant dans
   les champs `alliances`/`oppositions`.

RÈGLE POUR LA SUITE (pas appliquée par ce script, à respecter à la main)
--------------------------------------------------------------------------
À partir de maintenant, toute nouvelle alliance/opposition ajoutée à
une fiche doit référencer un slug déjà officialisé (de cette liste ou
créé via create_entity.py), plus jamais de texte libre.

SÉCURITÉ / IDEMPOTENCE
------------------------
- Une sauvegarde de instances/ est créée avant toute réécriture
  (instances_backup_<timestamp>/), au cas où.
- Le script est conçu pour tourner UNE fois. Le relancer après un
  premier passage réussi ne devrait plus rien trouver à officialiser
  (toutes les mentions texte libre auront été remplacées par des
  slugs), donc c'est sans danger mais inutile.
- --dry-run affiche le plan complet (clusters, nouvelles fiches,
  réécritures prévues) sans rien écrire sur disque.

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...

USAGE
-----
    python3 officialize_alliances.py --dry-run   # plan complet, rien écrit
    python3 officialize_alliances.py              # exécution réelle
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

try:
    import anthropic
except ImportError:
    anthropic = None


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_DIR = VAULT_ROOT / "instances"
ENTITES_DIR = VAULT_ROOT / "entites"
ENTITES_LIST_PATH = ENTITES_DIR / "_entities_list.json"

MODEL = "claude-sonnet-4-6"
CLUSTER_BATCH_SIZE = 80  # mentions par appel de déduplication (réduit pour éviter
                          # toute troncature du JSON de sortie — voir incident du
                          # 2026-06-20 : un lot de 150 mentions a généré une sortie
                          # JSON tronquée à max_tokens=8000)

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

VALID_VARS = [
    "systeme_economique_redistribution", "gouvernance_institutions",
    "geopolitique_conflits", "valeurs_culture_tempo_sociale",
    "organisation_territoires", "sante_biotechnologies",
    "frontieres_du_systeme", "technologie_information",
    "climat_environnement_global", "energie_ressources_critiques",
    "demographie_mobilite_humaine", "systemes_productifs_travail",
]

VALID_CATEGORIES = [
    "IA", "organisation", "entreprise", "institution", "infrastructure",
    "réseau", "humain", "système", "hybride", "autre",
]


# ---------------------------------------------------------------------------
# Utilitaires partagés (mêmes conventions que create_entity.py / generate_instances.py)
# ---------------------------------------------------------------------------

def slugify(text):
    s = text.lower()
    for fr, en in [("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"),
                   ("à", "a"), ("â", "a"), ("ä", "a"), ("ù", "u"),
                   ("û", "u"), ("ü", "u"), ("î", "i"), ("ï", "i"),
                   ("ô", "o"), ("ö", "o"), ("ç", "c")]:
        s = s.replace(fr, en)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def parse_md(filepath):
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not m:
        return {}, raw, raw
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError as e:
        print(f"  ⚠ YAML cassé dans {filepath.name} : {e}")
        fm = {}
    return fm, m.group(2).strip(), raw


def load_entities_list():
    if not ENTITES_LIST_PATH.exists():
        return []
    try:
        return json.loads(ENTITES_LIST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_entities_list(entities):
    ENTITES_DIR.mkdir(parents=True, exist_ok=True)
    ENTITES_LIST_PATH.write_text(
        json.dumps(entities, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_client():
    if anthropic is None:
        sys.exit("Le package 'anthropic' n'est pas installé. "
                  "pip install anthropic --break-system-packages")
    return anthropic.Anthropic()


def call_claude_json(client, system, user_content, max_tokens=4000):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    text = resp.content[0].text.strip()
    # tolère un éventuel fencing ```json ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        if resp.stop_reason == "max_tokens":
            raise RuntimeError(
                f"Réponse Claude tronquée (max_tokens={max_tokens} atteint, "
                f"{resp.usage.output_tokens} tokens générés) — le JSON de sortie "
                f"est incomplet. Augmente max_tokens ou réduis la taille du lot."
            ) from e
        raise


# ---------------------------------------------------------------------------
# Étape 1 — Extraction des mentions texte libre
# ---------------------------------------------------------------------------

def is_slug_like(item):
    return bool(re.fullmatch(r"[a-z0-9_]+", item))


def extract_mentions():
    """
    Parcourt toutes les instances et collecte les mentions alliances/
    oppositions en texte libre, avec leur(s) source(s) (fichier +
    champ + scénario), pour pouvoir les réécrire ensuite.

    Retourne :
      mentions_index : dict {texte_mention: [(fname, field, scenario), ...]}
      instance_slugs : set des slugs d'instance valides (pour ignorer
                       les références déjà correctes)
    """
    instance_files = sorted(
        f for f in INSTANCES_DIR.glob("*.md") if f.name != "instance_template.md"
    )
    instance_slugs = {f.stem for f in instance_files}

    mentions_index = {}
    skipped_broken_yaml = []

    for f in instance_files:
        fm, _, _ = parse_md(f)
        if not fm:
            skipped_broken_yaml.append(f.name)
            continue
        scenario = fm.get("scenario", "")
        for field in ("alliances", "oppositions"):
            items = fm.get(field) or []
            if isinstance(items, str):
                items = [items]
            for item in items:
                item = str(item).strip()
                if not item or is_slug_like(item):
                    continue
                mentions_index.setdefault(item, []).append((f.name, field, scenario))

    if skipped_broken_yaml:
        print(f"  ⚠ {len(skipped_broken_yaml)} fichier(s) ignoré(s) (YAML cassé) : "
              f"{', '.join(skipped_broken_yaml)}")

    return mentions_index, instance_slugs


# ---------------------------------------------------------------------------
# Étape 2 — Déduplication sémantique via Claude
# ---------------------------------------------------------------------------

DEDUP_SYSTEM = """Tu travailles sur Ourrassol 2098, un simulateur de presse fictive \
située en 2098. Tu reçois une liste de mentions d'organisations/groupes/mouvements \
fictifs, extraites en texte libre de fiches "instances" du worldbuilding. Beaucoup de \
ces mentions désignent en réalité le même acteur narratif, simplement décrit avec des \
formulations différentes selon la fiche qui le mentionne.

Ta tâche : regrouper ces mentions en clusters. Un cluster ne contient plusieurs mentions \
QUE si elles désignent de façon non ambiguë le même acteur (même fonction, même camp \
politique/idéologique, même échelle d'action) — pas seulement un thème vaguement \
similaire. Dans le doute, NE PAS fusionner : un cluster à 1 seule mention est la norme, \
pas l'exception.

Pour chaque cluster, choisis ou invente un NOM CANONIQUE : un nom propre concis et \
plausible dans l'univers de 2098 (cohérent avec le registre des autres mentions du lot — \
mélange d'institutions, de consortiums, de mouvements, de réseaux informels...). Si une \
mention du cluster est déjà un bon nom propre clair, réutilise-la telle quelle comme nom \
canonique plutôt que d'en inventer un nouveau.

Certaines mentions sont trop vagues pour être un nom propre (ex: "Quelques cités-États \
côtières désespérées", "Certains groupes de hackers..."). Pour celles-ci, invente un nom \
propre plausible qui capture la même idée (ex: "Ligue des Cités Littorales en Sursis").

Réponds UNIQUEMENT avec un objet JSON de cette forme, sans aucun texte avant/après :
{
  "clusters": [
    {
      "nom_canonique": "Nom propre choisi ou inventé",
      "categorie": "une seule valeur parmi: IA, organisation, entreprise, institution, infrastructure, réseau, humain, système, hybride, autre",
      "mentions_originales": ["texte exact mention 1", "texte exact mention 2", ...]
    },
    ...
  ]
}

Chaque mention originale du lot fourni doit apparaître dans EXACTEMENT un cluster — \
aucune omise, aucune dupliquée entre clusters."""


CHECKPOINT_PATH = Path(__file__).resolve().parent / "officialize_checkpoint.json"


def load_checkpoint():
    if CHECKPOINT_PATH.exists():
        try:
            return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def save_checkpoint(clusters, batches_done, total_batches):
    CHECKPOINT_PATH.write_text(
        json.dumps({
            "clusters": clusters,
            "batches_done": batches_done,
            "total_batches": total_batches,
            "saved_at": datetime.now().isoformat(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_checkpoint():
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()


def deduplicate_mentions(client, mentions, dry_run, resume=False):
    """
    mentions : liste de chaînes (textes uniques à traiter)
    Retourne : liste de clusters {nom_canonique, categorie, mentions_originales}

    Sauvegarde un checkpoint après chaque lot réussi (officialize_checkpoint.json)
    pour pouvoir reprendre sans tout refaire si le script s'interrompt (ex:
    réponse Claude tronquée sur un lot, coupure réseau...).
    """
    batches = [mentions[i:i + CLUSTER_BATCH_SIZE]
               for i in range(0, len(mentions), CLUSTER_BATCH_SIZE)]

    all_clusters = []
    start_batch = 0
    if resume:
        checkpoint = load_checkpoint()
        if checkpoint:
            all_clusters = checkpoint["clusters"]
            start_batch = checkpoint["batches_done"]
            print(f"  [dédup] Reprise depuis checkpoint : {start_batch}/{len(batches)} "
                  f"lot(s) déjà traité(s), {len(all_clusters)} cluster(s) déjà formé(s)")

    for i, batch in enumerate(batches, 1):
        if i <= start_batch:
            continue
        print(f"  [dédup] Lot {i}/{len(batches)} ({len(batch)} mentions)...")
        user_content = "Mentions à regrouper :\n" + "\n".join(f"- {m}" for m in batch)
        result = call_claude_json(client, DEDUP_SYSTEM, user_content, max_tokens=16000)
        clusters = result.get("clusters", [])

        # Validation mécanique : chaque mention du batch doit apparaître
        # exactement une fois dans les clusters retournés.
        seen = []
        for c in clusters:
            seen.extend(c.get("mentions_originales", []))
        missing = set(batch) - set(seen)
        extra = set(seen) - set(batch)
        if missing:
            print(f"    ⚠ {len(missing)} mention(s) non reprise(s) par Claude — "
                  f"ajout en clusters singletons : {list(missing)[:3]}...")
            for m in missing:
                clusters.append({
                    "nom_canonique": m, "categorie": "autre",
                    "mentions_originales": [m],
                })
        if extra:
            print(f"    ⚠ {len(extra)} mention(s) halluc inée(s) hors du lot fourni, ignorée(s)")
            for c in clusters:
                c["mentions_originales"] = [
                    m for m in c.get("mentions_originales", []) if m in batch
                ]
            clusters = [c for c in clusters if c["mentions_originales"]]

        all_clusters.extend(clusters)
        print(f"    → {len(clusters)} cluster(s) pour ce lot")

        if not dry_run:
            save_checkpoint(all_clusters, i, len(batches))

    return all_clusters


FINAL_DEDUP_SYSTEM = """Tu travailles sur Ourrassol 2098, simulateur de presse fictive \
située en 2098. On te donne une liste de noms canoniques d'organisations/groupes/ \
mouvements fictifs, déjà nettoyés une première fois — mais issus de lots traités \
séparément, donc certains peuvent en réalité désigner le même acteur sous deux noms \
légèrement différents (ex: "Souverainistes du Bloc Eurasien" et "Bloc Souverainiste \
Eurasien").

Repère UNIQUEMENT les doublons évidents — même fonction, même camp, même échelle. Dans \
le doute, NE PAS fusionner. La grande majorité des noms n'ont pas de doublon : c'est \
attendu, ne force rien.

Réponds UNIQUEMENT avec un objet JSON :
{
  "doublons": [
    {"garder": "nom canonique à conserver", "fusionner": ["autre nom 1", "autre nom 2"]}
  ]
}
Si aucun doublon n'est trouvé, réponds {"doublons": []}."""


def final_dedup_pass(client, clusters, dry_run):
    """
    Passe de sécurité inter-lots : repère les noms canoniques quasi-
    identiques produits par des lots différents et les fusionne.
    Coût marginal (1 appel sur les noms déjà condensés, pas sur les
    mentions brutes).
    """
    if len(clusters) < 2:
        return clusters

    noms = [c["nom_canonique"] for c in clusters]
    print(f"  [dédup finale] Vérification inter-lots sur {len(noms)} noms canoniques...")
    user_content = "Noms canoniques à vérifier :\n" + "\n".join(f"- {n}" for n in noms)
    result = call_claude_json(client, FINAL_DEDUP_SYSTEM, user_content, max_tokens=4000)
    doublons = result.get("doublons", [])

    if not doublons:
        print("    → aucun doublon inter-lots détecté")
        return clusters

    by_nom = {c["nom_canonique"]: c for c in clusters}
    merged_away = set()

    for d in doublons:
        garder = d.get("garder")
        fusionner = d.get("fusionner", [])
        if garder not in by_nom:
            continue
        for autre_nom in fusionner:
            if autre_nom not in by_nom or autre_nom == garder or autre_nom in merged_away:
                continue
            print(f"    → fusion inter-lots : '{autre_nom}' → '{garder}'")
            by_nom[garder]["mentions_originales"].extend(
                by_nom[autre_nom]["mentions_originales"]
            )
            merged_away.add(autre_nom)

    final_clusters = [c for c in clusters if c["nom_canonique"] not in merged_away]
    if merged_away:
        print(f"    → {len(merged_away)} cluster(s) fusionné(s) en plus")
    return final_clusters


# ---------------------------------------------------------------------------
# Étape 3 — Création des fiches minimales (entité + instance)
# ---------------------------------------------------------------------------

ENRICH_SYSTEM = """Tu travailles sur Ourrassol 2098, simulateur de presse fictive \
située en 2098. On te donne le nom d'une organisation/groupe/mouvement fictif déjà \
choisi, ainsi que le contexte (scénario systémique, et la phrase qui le mentionnait \
à l'origine comme allié ou opposant d'une autre entité). Tu dois produire le minimum \
structurel pour en faire une fiche valide dans le vault — PAS de développement \
narratif poussé, ce travail sera fait plus tard.

Réponds UNIQUEMENT avec un objet JSON de cette forme :
{
  "description_courte": "1-2 phrases, ce que cette entité représente fondamentalement",
  "role_court": "1-2 phrases, son rôle dans ce scénario précis",
  "variables_potentielles": ["1 à 3 slugs parmi la liste fournie"],
  "type_dans_scenario": "une valeur parmi: IA, organisation, entreprise, institution, infrastructure, réseau, humain, système, hybride, autre"
}"""


def enrich_minimal(client, nom_canonique, categorie, scenario, contexte_mention, dry_run):
    if dry_run:
        return {
            "description_courte": f"[dry-run] {nom_canonique} — à enrichir en phase 2.",
            "role_court": f"[dry-run] rôle dans {scenario} — à enrichir en phase 2.",
            "variables_potentielles": [VALID_VARS[0]],
            "type_dans_scenario": categorie if categorie in (
                "IA", "organisation", "entreprise", "institution", "infrastructure",
                "réseau", "humain", "système", "hybride", "autre") else "autre",
        }
    user_content = f"""Nom : {nom_canonique}
Catégorie pressentie : {categorie}
Scénario : {scenario}
Contexte d'origine (phrase qui la mentionnait) : {contexte_mention}

Variables systémiques valides (choisis parmi celles-ci uniquement) :
{chr(10).join('- ' + v for v in VALID_VARS)}"""
    return call_claude_json(client, ENRICH_SYSTEM, user_content, max_tokens=600)


def write_minimal_entity_file(slug, nom, categorie, description_courte,
                               variables, scenario):
    vars_yaml = "\n".join(f"  - {v}" for v in variables) if variables else f"  - {VALID_VARS[0]}"
    content = f"""---
name: {nom}
type: entity
slug: {slug}
category: {categorie}
statut: officialise_minimal
description: >
  {description_courte.strip()}
tension_fondamentale: >
  (à développer en phase 2 — fiche créée par officialisation automatique)
variables_potentielles:
{vars_yaml}
scenarios_instances:
  - {scenario}
date_creation: {datetime.now().strftime("%Y-%m-%d")}
---

# {nom}

## Description archétypale
{description_courte.strip()}

## Tension fondamentale
(à développer en phase 2)

## Instances par scénario
| Scénario | Instance | État | Rôle |
|---|---|---|---|
| [[{scenario}]] | [[{slug}_{scenario}]] | | |
"""
    path = ENTITES_DIR / f"{slug}.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_minimal_instance_file(slug_entite, scenario, nom, role_court,
                                 type_dans_scenario, variables):
    vars_yaml = "\n".join(f"  - {v}" for v in variables) if variables else f"  - {VALID_VARS[0]}"
    slug_instance = f"{slug_entite}_{scenario}"
    content = f"""---
name: {nom}
type: instance
slug: {slug_instance}
entite: {slug_entite}
scenario: {scenario}
statut: officialise_minimal

type_dans_scenario: {type_dans_scenario}

role_dans_scenario: >
  {role_court.strip()}

responsabilites: >
  (à développer en phase 2 — fiche créée par officialisation automatique)

impact_local: 1
impact_systemique_global: 1

variables_influencees:
{vars_yaml}

zone_geographique:
  - régionale

zone_systemique:
  - société

alliances: []

oppositions: []

type_relation_dominante: neutralité

annee_debut: 2026
annee_fin:

etat_temporel: actif
age_historique: émergent
generation: transition

injection:
  type: canonique
  annee_injection:
  contexte_injection:
  impact_sur_variables:
  propagation:
    via_matrice: false

description_journalistique: >
  (à développer en phase 2)

signes_distinctifs: >
  (à développer en phase 2)

tensions_narratives: >
  (à développer en phase 2)

date_creation: {datetime.now().strftime("%Y-%m-%d")}
---

# {nom}

## Rôle dans [[{scenario}]]
{role_court.strip()}

## Variables influencées
{chr(10).join('- [[' + v + ']]' for v in variables) if variables else ''}

## Notes
Fiche créée par officialisation automatique (officialize_alliances.py) à partir \
d'une mention en texte libre. À enrichir en phase 2.
"""
    path = INSTANCES_DIR / f"{slug_instance}.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Étape 4 — Réécriture des fiches sources
# ---------------------------------------------------------------------------

def rewrite_source_files(mention_to_slug, mentions_index, dry_run):
    """
    Pour chaque fichier source, remplace les mentions texte libre par
    leur slug officialisé dans les champs alliances/oppositions —
    remplacement structurel via le frontmatter parsé puis réécrit
    (pas un simple find&replace texte, pour éviter de casser le YAML
    si une mention apparaît aussi ailleurs dans le corps du fichier).
    """
    affected_files = set()
    for mention, refs in mentions_index.items():
        for fname, field, scenario in refs:
            affected_files.add(fname)

    rewritten = []
    for fname in sorted(affected_files):
        path = INSTANCES_DIR / fname
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)", raw, re.DOTALL)
        if not m:
            continue
        fm_str = m.group(2)
        lines = fm_str.split("\n")
        new_lines = []
        in_field = None
        changed = False
        for line in lines:
            field_match = re.match(r"^(alliances|oppositions):\s*$", line)
            if field_match:
                in_field = field_match.group(1)
                new_lines.append(line)
                continue
            item_match = re.match(r"^(\s*-\s*)(.+)$", line) if in_field else None
            if item_match:
                prefix, value = item_match.groups()
                value_clean = value.strip()
                if value_clean in mention_to_slug:
                    new_lines.append(f"{prefix}{mention_to_slug[value_clean]}")
                    changed = True
                else:
                    new_lines.append(line)
                continue
            # toute autre ligne de premier niveau ferme le champ courant
            if in_field and line and not line.startswith((" ", "-")):
                in_field = None
            new_lines.append(line)

        if changed:
            new_fm = "\n".join(new_lines)
            new_raw = m.group(1) + new_fm + m.group(3) + m.group(4)
            if not dry_run:
                path.write_text(new_raw, encoding="utf-8")
            rewritten.append(fname)

    return rewritten


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def backup_instances():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = VAULT_ROOT / f"instances_backup_{timestamp}"
    shutil.copytree(INSTANCES_DIR, backup_dir)
    return backup_dir


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1 — officialise les mentions alliances/oppositions en texte libre"
    )
    parser.add_argument("--dry-run", action="store_true",
                         help="Affiche le plan complet sans rien écrire sur disque")
    parser.add_argument("--limit", type=int, default=None,
                         help="Ne traite que les N premières mentions uniques "
                              "(tri alphabétique) — utile pour tester rapidement "
                              "avant un run complet")
    parser.add_argument("--resume", action="store_true",
                         help="Reprend la déduplication depuis le dernier checkpoint "
                              "(officialize_checkpoint.json) après une interruption, "
                              "au lieu de tout recommencer depuis le premier lot")
    args = parser.parse_args()
    dry_run = args.dry_run

    if args.resume and args.limit:
        sys.exit("--resume et --limit ne sont pas compatibles ensemble : le "
                  "checkpoint a été construit sur un ensemble de mentions "
                  "différent. Termine le run --limit en cours, ou repars sans "
                  "--limit pour le run complet.")

    print("=" * 60)
    print("OURRASSOL 2098 — Officialisation alliances/oppositions")
    print("=" * 60)
    if dry_run:
        print("(mode --dry-run : rien ne sera écrit)\n")

    # --- Étape 1 : extraction ---
    print("\n[1/4] Extraction des mentions texte libre...")
    mentions_index, instance_slugs = extract_mentions()
    unique_mentions = sorted(mentions_index.keys())
    print(f"  → {sum(len(v) for v in mentions_index.values())} mentions au total, "
          f"{len(unique_mentions)} unique(s)")

    if not unique_mentions:
        print("\nRien à officialiser. Vault déjà propre.")
        return

    if args.limit:
        unique_mentions = unique_mentions[:args.limit]
        mentions_index = {m: mentions_index[m] for m in unique_mentions}
        print(f"  → --limit {args.limit} : traitement restreint à {len(unique_mentions)} mention(s)")

    # --- Étape 2 : déduplication sémantique ---
    print(f"\n[2/4] Déduplication sémantique ({len(unique_mentions)} mentions)...")
    client = get_client()
    clusters = deduplicate_mentions(client, unique_mentions, dry_run, resume=args.resume)
    print(f"  → {len(clusters)} entité(s) canonique(s) après fusion par lots "
          f"(réduction de {len(unique_mentions)} à {len(clusters)})")
    if not dry_run:
        clear_checkpoint()  # déduplication par lots terminée avec succès

    clusters = final_dedup_pass(client, clusters, dry_run)
    print(f"  → {len(clusters)} entité(s) canonique(s) après vérification inter-lots")

    # --- Étape 3 : création des fiches minimales ---
    print(f"\n[3/4] Création des fiches minimales...")
    existing_entities = load_entities_list()
    existing_slugs = {e["slug"] for e in existing_entities}
    mention_to_slug = {}
    created = []

    for i, cluster in enumerate(clusters, 1):
        nom = cluster["nom_canonique"]
        categorie = cluster.get("categorie", "autre")
        mentions_orig = cluster["mentions_originales"]
        slug = slugify(nom)

        # anti-collision basique avec le registre existant
        if slug in existing_slugs:
            slug = f"{slug}_{i}"

        # scénario(s) d'origine : on prend le premier scénario rencontré
        # parmi les mentions du cluster (une mention = 1 scénario source)
        first_mention = mentions_orig[0]
        refs = mentions_index.get(first_mention, [])
        scenario = refs[0][2] if refs else "reference"
        contexte = f"Mentionnée dans une fiche du scénario {scenario} : « {first_mention} »"

        print(f"  [{i}/{len(clusters)}] {nom} (slug: {slug}, scénario: {scenario})"
              + (f" — fusion de {len(mentions_orig)} mentions" if len(mentions_orig) > 1 else ""))

        enrichment = enrich_minimal(client, nom, categorie, scenario, contexte, dry_run)
        variables = [v for v in enrichment.get("variables_potentielles", []) if v in VALID_VARS]
        type_scenario = enrichment.get("type_dans_scenario", categorie)

        if not dry_run:
            write_minimal_entity_file(
                slug, nom, categorie, enrichment["description_courte"],
                variables, scenario,
            )
            write_minimal_instance_file(
                slug, scenario, nom, enrichment["role_court"],
                type_scenario, variables,
            )
            existing_entities.append({
                "nom": nom, "slug": slug, "categorie": categorie,
                "description": enrichment["description_courte"],
                "tension_fondamentale": "(à développer en phase 2)",
                "variables_potentielles": variables,
                "scenarios": [scenario],
                "statut": "officialise_minimal",
            })

        instance_slug = f"{slug}_{scenario}"
        for mention in mentions_orig:
            mention_to_slug[mention] = instance_slug
        created.append((nom, slug, scenario, len(mentions_orig)))

    if not dry_run:
        save_entities_list(existing_entities)

    # --- Étape 4 : réécriture des fiches sources ---
    print(f"\n[4/4] Réécriture des fiches sources...")
    if not dry_run:
        backup_dir = backup_instances()
        print(f"  → Sauvegarde créée : {backup_dir.name}")
    rewritten = rewrite_source_files(mention_to_slug, mentions_index, dry_run)
    print(f"  → {len(rewritten)} fichier(s) réécrit(s)")

    # --- Résumé ---
    print("\n" + "=" * 60)
    print(f"✓ {len(created)} entité(s)/instance(s) {'à créer' if dry_run else 'créées'}")
    print(f"✓ {len(rewritten)} fichier(s) source {'à réécrire' if dry_run else 'réécrits'}")
    fusions = [c for c in created if c[3] > 1]
    if fusions:
        print(f"\nFusions réalisées ({len(fusions)}) :")
        for nom, slug, scenario, n in fusions:
            print(f"  - {nom} ({n} mentions fusionnées)")
    if dry_run:
        print("\n(mode --dry-run : rien n'a été écrit sur disque)")
    print("=" * 60)


if __name__ == "__main__":
    main()
