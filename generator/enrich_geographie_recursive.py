#!/usr/bin/env python3
"""
enrich_geographie_recursive.py — Ourrassol 2098
==================================================

Étape 2 du chantier géographie : enrichit les bibles monde déjà
produites par build_geographie_monde.py (étape 1, schéma plat) en y
ajoutant un maillage hiérarchique récursif — sous-zones (territoires,
régions, villes, infrastructures...) reliées aux zones de niveau 1
via `parent`, à une profondeur libre (pas de niveaux fixes imposés).

PRINCIPE CENTRAL : ADDITIF, JAMAIS DESTRUCTEUR
------------------------------------------------
Contrairement à build_geographie_monde.py --force (qui régénère tout
le fichier), ce script ne touche JAMAIS aux zones déjà présentes dans
geographie/{scenario}.md : elles sont relues comme contexte FIXE et
recopiées telles quelles dans le fichier final. Le script ajoute
uniquement de nouvelles zones au tableau `zones` :
  - des sous-zones, à n'importe quelle profondeur, sous une zone
    existante (ou sous une autre zone nouvellement créée dans la même
    passe) ;
  - éventuellement, une nouvelle zone de niveau 1 si le corpus
    justifie clairement qu'une zone majeure manque (rare — la plupart
    du temps l'étape 1 les a déjà toutes trouvées).

Toute édition manuelle que tu as faite dans Obsidian sur les zones
existantes (description, statut, relations...) est donc préservée à
l'identique, À UNE EXCEPTION CIBLÉE PRÈS : si une nouvelle sous-zone
correspond à un `lieu_emblematique` déjà listé sur sa zone parente
(promotion explicite, tracée via le champ `promu_depuis`), cette
entrée est retirée de `lieux_emblematiques` du parent pour éviter la
duplication — c'est le SEUL champ d'une zone existante qui peut être
modifié par ce script, jamais la description/statut/relations/etc.
Chaque retrait est loggé en console. Seul le corps markdown sous le
frontmatter (vue d'ensemble, notes) est régénéré pour refléter les
nouvelles zones — une sauvegarde .bak est créée avant toute écriture,
par précaution, même si aucune zone existante n'est modifiée.

CE QUE FAIT CE SCRIPT (one-shot par scénario, ré-exécutable)
---------------------------------------------------------------
Pour chaque scénario :
1. Relit geographie/{scenario}.md existant (refuse de continuer s'il
   n'existe pas encore — lance d'abord build_geographie_monde.py).
2. Rassemble le même corpus narratif brut que l'étape 1 (instances +
   event_instances du scénario) — Claude replonge dans le texte
   original, pas seulement dans la synthèse déjà faite, pour pouvoir
   repérer des lieux/sous-zones mentionnés mais pas remontés en
   zone de niveau 1.
3. Envoie corpus + zones existantes (figées, comme contexte) à Claude,
   avec consigne de proposer un maillage en sous-zones à profondeur
   libre (et, marginalement, d'éventuelles nouvelles zones de
   niveau 1) — un seul appel par scénario.
4. Valide mécaniquement chaque nouvelle zone (mêmes garde-fous que
   l'étape 1, plus vérification de `parent` et détection de cycles),
   fusionne avec les zones existantes inchangées, réécrit le fichier.

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...
    geographie/{scenario}.md doit déjà exister (étape 1 faite)

USAGE
-----
    python3 enrich_geographie_recursive.py --scenario breakdown --dry-run
    python3 enrich_geographie_recursive.py --scenario breakdown
    python3 enrich_geographie_recursive.py --all                # les 6 scénarios
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
# Configuration (alignée sur build_geographie_monde.py)
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_DIR = VAULT_ROOT / "instances"
EVENT_INSTANCES_DIR = VAULT_ROOT / "event_instances"
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"

MODEL = "claude-sonnet-4-6"
ENRICH_MAX_TOKENS = 24000  # doublé suite à troncature réelle observée à 12000 sur le
                             # scénario 'reference' (9 zones niveau 1, gros corpus) —
                             # voir historique : 12000/12000 consommés sans même finir
                             # une première vague de sous-zones

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]

ZONE_TYPES = ["bloc_continental", "union_regionale", "territoire_autonome",
              "territoire_herite", "region", "ville", "infrastructure",
              "site_strategique", "zone_sinistree", "autre"]
ZONE_STATUTS = ["dominant", "stable", "fragmenté", "en_declin", "disparu", "emergent"]
LIEU_TYPES = ["ville", "region", "infrastructure", "site_strategique"]
TYPE_ENTITE_REELLE = ["pays", "etat_federe", "province", "region_administrative", "autre"]


# ---------------------------------------------------------------------------
# Lecture du vault
# ---------------------------------------------------------------------------

def parse_md(filepath):
    if not filepath.exists():
        return {}, ""
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not m:
        return {}, raw
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2).strip()


def load_existing_geographie(scenario):
    """Charge geographie/{scenario}.md existant. Retourne (zones, vue_ensemble)
    ou (None, None) si le fichier n'existe pas encore."""
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    if not path.exists():
        return None, None
    fm, body = parse_md(path)
    zones = fm.get("zones") or []
    m = re.search(r"## Vue d'ensemble\s*\n(.*?)(?:\n## |\Z)", body, re.DOTALL)
    vue_ensemble = m.group(1).strip() if m else ""
    return zones, vue_ensemble


def gather_instance_texts(scenario):
    blocks = []
    if not INSTANCES_DIR.exists():
        return blocks
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, _ = parse_md(path)
        if fm.get("type") != "instance" or fm.get("scenario") != scenario:
            continue
        slug = fm.get("slug", path.stem)
        parts = [
            fm.get("description_journalistique", ""),
            fm.get("role_dans_scenario", ""),
            fm.get("tensions_narratives", ""),
        ]
        text = " ".join(str(p).strip() for p in parts if p)
        if text:
            blocks.append(f"[INSTANCE: {slug}]\n{text}")
    return blocks


def gather_event_texts(scenario):
    blocks = []
    if not EVENT_INSTANCES_DIR.exists():
        return blocks
    for path in sorted(EVENT_INSTANCES_DIR.glob(f"*_{scenario}.md")):
        fm, _ = parse_md(path)
        if fm.get("scenario") != scenario:
            continue
        slug = fm.get("slug", path.stem)
        parts = [
            fm.get("description", ""),
            fm.get("consequences", ""),
            fm.get("realisation", ""),
        ]
        text = " ".join(str(p).strip() for p in parts if p)
        if text:
            blocks.append(f"[EVENEMENT: {slug}]\n{text}")
    return blocks


# ---------------------------------------------------------------------------
# Appel Claude
# ---------------------------------------------------------------------------

def get_client():
    if anthropic is None:
        sys.exit("Le package 'anthropic' n'est pas installé. "
                  "pip install anthropic --break-system-packages")
    return anthropic.Anthropic()


def call_claude_json(client, system, user_content, max_tokens=ENRICH_MAX_TOKENS):
    # Mode streaming requis : avec max_tokens=24000 sur un gros corpus, le SDK
    # anticipe une génération potentiellement >10min et refuse l'appel synchrone
    # classique (client.messages.create) — voir
    # https://github.com/anthropics/anthropic-sdk-python#long-requests
    with client.messages.stream(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        resp = stream.get_final_message()

    text = "".join(
        block.text for block in resp.content if getattr(block, "type", "") == "text"
    ).strip()

    print(f"    [diagnostic appel API] stop_reason={resp.stop_reason}, "
          f"tokens_entree={resp.usage.input_tokens}, "
          f"tokens_sortie={resp.usage.output_tokens}/{max_tokens}, "
          f"longueur_texte={len(text)} caractères")

    if resp.stop_reason == "max_tokens":
        print(f"    ⚠ ATTENTION : la réponse a été TRONQUÉE par la limite max_tokens "
              f"({max_tokens}) — même si un JSON exploitable est trouvé ci-dessous, "
              f"il peut être incomplet (zones manquantes en fin de réponse).")

    if not text:
        raise RuntimeError(
            f"Réponse Claude vide (stop_reason={resp.stop_reason}, "
            f"{resp.usage.output_tokens} tokens générés)."
        )

    candidate = re.sub(r"^```(?:json)?\s*", "", text)
    candidate = re.sub(r"\s*```$", "", candidate)
    try:
        parsed = json.loads(candidate)
        print(f"    [diagnostic] JSON parsé directement, clé 'nouvelles_zones' : "
              f"{len(parsed.get('nouvelles_zones', [])) if isinstance(parsed, dict) else 'N/A (pas un objet)'} entrée(s)")
        return parsed
    except json.JSONDecodeError as e:
        print(f"    [diagnostic] échec du parsing JSON direct ({e}), "
              f"tentative d'extraction du dernier bloc {{...}} dans le texte...")

    matches = re.findall(r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}", text)
    print(f"    [diagnostic] {len(matches)} bloc(s) {{...}} candidat(s) trouvé(s) par regex")
    if matches:
        try:
            parsed = json.loads(matches[-1])
            print(f"    [diagnostic] dernier bloc parsé avec succès en JSON valide "
                  f"(probablement incomplet si stop_reason=max_tokens ci-dessus)")
            return parsed
        except json.JSONDecodeError:
            print(f"    [diagnostic] le dernier bloc {{...}} trouvé n'est PAS un JSON valide "
                  f"(confirme une troncature en plein milieu d'un objet)")

    if resp.stop_reason == "max_tokens":
        raise RuntimeError(
            f"Réponse Claude tronquée (max_tokens={max_tokens} atteint, "
            f"aucun JSON complet trouvé) — texte reçu: {text[:300]!r}"
        )
    raise RuntimeError(f"Aucun JSON exploitable trouvé : {text[:300]!r}")


ENRICH_SYSTEM = """Tu travailles sur Ourrassol 2098, simulateur de presse fictive située \
en 2098. Un premier passage a déjà identifié les zones géopolitiques MAJEURES (niveau 1 \
— blocs continentaux, unions régionales...) d'UN scénario précis, à partir du corpus \
narratif existant. On te les donne ci-dessous, TELLES QUELLES, comme contexte FIXE : tu \
ne dois RIEN modifier dessus (ni description, ni statut, ni relations, ni aucun autre \
champ) — elles sont peut-être déjà éditées à la main dans Obsidian. SEULE exception, gérée \
mécaniquement après ta réponse (tu n'as rien à faire toi-même pour ça, juste remplir \
honnêtement le champ "promu_depuis" décrit au point 10) : si tu promeus un lieu déjà \
listé dans `lieux_emblematiques` d'une zone en vraie sous-zone, ce lieu sera retiré de la \
liste de son ancien parent pour éviter la duplication.

TA TÂCHE : enrichir cette géographie en profondeur, en proposant des SOUS-ZONES sous ces \
zones de niveau 1 — territoires, régions, villes, infrastructures, sites stratégiques, \
zones sinistrées... tout ce qui a du sens narrativement, à une profondeur LIBRE (une \
sous-zone peut elle-même avoir des sous-zones, etc. — pas de nombre de niveaux imposé).

1. Cherche en priorité dans les `lieux_emblematiques` DÉJÀ LISTÉS sur chaque zone de \
niveau 1 ci-dessous : ce sont des candidats NATURELS et IMMÉDIATS à la promotion en \
vraies sous-zones — ils ont déjà un nom, un type (ville/region/infrastructure/\
site_strategique) et une note de contexte, c'est exactement la matière première attendue \
ici. Un lieu emblématique qui a un rôle narratif notable (siège d'une institution, lieu \
d'un événement, foyer d'une dynamique propre à ce lieu) mérite normalement de devenir une \
zone à part entière avec sa propre fiche, reliée par `parent` à la zone qui le contenait. \
Ne te limite pas à eux : relis aussi le corpus narratif brut fourni (les mêmes textes qui \
ont servi à la première passe) pour repérer d'autres lieux PLUS PRÉCIS que les zones \
niveau 1 actuelles ne capturent pas et qui ne sont pas encore dans `lieux_emblematiques` : \
villes nommées, infrastructures, sites stratégiques, sous-régions, enclaves, zones \
sinistrées locales, etc.

2. Le nombre de sous-zones par zone de niveau 1 n'est pas fixé à l'avance et peut varier \
fortement d'une zone à l'autre selon ce que le corpus offre réellement — une zone peut \
légitimement n'avoir aucune sous-zone si elle n'a ni lieu emblématique exploitable ni \
mention précise dans le corpus, mais ne traite pas la prudence comme une raison de t'abstenir \
quand la matière est déjà là (notamment dans `lieux_emblematiques`, voir point 1). \
N'invente jamais un lieu qui n'a aucune trace dans le corpus ou la liste fournie.

3. Chaque sous-zone DOIT avoir un champ "parent" qui est le slug exact d'UNE AUTRE zone \
de l'ensemble complet (une zone de niveau 1 fournie ci-dessous, OU une autre zone que TU \
proposes dans cette même réponse). Jamais un slug inventé, jamais null pour une sous-zone \
(seules les zones de niveau 1 — fournies ou nouvellement proposées — ont parent=null).

4. "niveau" : 1 pour une zone sans parent, 2 pour une zone dont le parent est niveau 1, \
3 pour une zone dont le parent est niveau 2, etc. — calcule-le correctement selon la \
chaîne de parenté que tu construis.

5. Marginalement, si le corpus révèle clairement une zone géopolitique MAJEURE (niveau 1, \
parent=null) que la première passe a manquée, tu peux la proposer — mais c'est rare : ne \
le fais que si c'est manifeste dans le texte, pas par défaut.

6. RÈGLE STRICTE pour "relations" (allies/rivaux) : uniquement des slugs d'AUTRES zones \
de l'ensemble complet (niveau 1 fournies + nouvelles zones que tu proposes) — jamais un \
slug d'instance, jamais un concept inventé. Une sous-zone peut très bien avoir pour \
allié/rival une zone de niveau 1, une zone sœur, ou une zone d'une autre branche — reste \
réaliste sur ce qui a un sens narratif à cette échelle locale (beaucoup de sous-zones \
n'ont logiquement aucune relation propre, c'est normal, laisse vide dans ce cas).

7. "origine_reelle" : comme à l'étape 1, TOUJOURS renseigné — pays/subdivision réelle de \
2026 dont hérite la zone, à l'échelle appropriée (un quartier ou une ville réelle precise \
sont valides ici, plus seulement des pays entiers).

8. "sources_attestees" : slugs [INSTANCE: ...] ou [EVENEMENT: ...] réellement présents \
dans le corpus qui justifient cette sous-zone — n'invente aucune source.

9. "evenement_transition" : si un événement du corpus documente explicitement la \
transition de cette sous-zone, indique son slug ; sinon null.

10. "promu_depuis" : si cette sous-zone correspond à un `lieu_emblematique` déjà listé \
sur SA zone parente (cas du point 1), indique ICI le nom exact de ce lieu tel qu'il \
apparaît dans le champ `lieux_emblematiques` du parent (pour qu'il puisse en être retiré \
mécaniquement et éviter la duplication) ; sinon null. Ne remplis ce champ QUE si le lieu \
était déjà littéralement présent dans `lieux_emblematiques` du parent fourni — jamais \
pour un lieu que tu identifies uniquement dans le corpus brut.

Réponds UNIQUEMENT avec un objet JSON, sans aucun texte autour :
{
  "nouvelles_zones": [
    {
      "slug": "slug_snake_case",
      "nom": "Nom canonique de la zone",
      "niveau": 2,
      "type": "une valeur parmi: bloc_continental, union_regionale, territoire_autonome, territoire_herite, region, ville, infrastructure, site_strategique, zone_sinistree, autre",
      "parent": "slug_de_la_zone_parente",
      "origine_reelle": [
        {"entite": "Nom du pays/subdivision/ville réelle", "type_entite": "pays|etat_federe|province|region_administrative|autre", "portion": null}
      ],
      "description": "2-3 lignes sur ce qu'est cette zone DANS ce scénario précis",
      "statut": "une valeur parmi: dominant, stable, fragmenté, en_declin, disparu, emergent",
      "tensions_internes": "1-2 lignes, ou chaîne vide si non pertinent",
      "periode_transition": "période approximative, ex: 2031-2045",
      "evenement_transition": null,
      "lieux_emblematiques": [
        {"nom": "Nom du lieu", "type": "ville|region|infrastructure|site_strategique", "notes": "courte note"}
      ],
      "relations": {"allies": [], "rivaux": []},
      "sources_attestees": [],
      "promu_depuis": null
    }
  ]
}"""


def enrich_geographie(client, scenario, corpus_text, existing_zones):
    zones_context = yaml.dump(existing_zones, allow_unicode=True, sort_keys=False,
                               default_flow_style=False, width=100)
    user_content = f"""Scénario : {scenario}

Zones de niveau 1 déjà établies (CONTEXTE FIXE — ne pas modifier) :

{zones_context}

Corpus narratif brut ({len(corpus_text)} caractères) :

{corpus_text}"""
    return call_claude_json(client, ENRICH_SYSTEM, user_content)


# ---------------------------------------------------------------------------
# Validation et fusion
# ---------------------------------------------------------------------------

def validate_zone(zone):
    issues = []
    if not zone.get("slug") or not re.fullmatch(r"[a-z0-9_]+", zone["slug"]):
        issues.append(f"slug invalide : {zone.get('slug')!r}")
    if not zone.get("nom"):
        issues.append("nom manquant")
    if zone.get("type") not in ZONE_TYPES:
        issues.append(f"type invalide : {zone.get('type')!r}")
    if zone.get("statut") not in ZONE_STATUTS:
        issues.append(f"statut invalide : {zone.get('statut')!r}")
    origine = zone.get("origine_reelle") or []
    if not origine:
        issues.append("origine_reelle manquante (toujours requise, voir consigne)")
    else:
        for o in origine:
            if not o.get("entite"):
                issues.append("origine_reelle : 'entite' manquante sur une entrée")
            if o.get("type_entite") not in TYPE_ENTITE_REELLE:
                issues.append(f"origine_reelle : type_entite invalide : {o.get('type_entite')!r}")
    return issues


def resolve_parents_and_levels(existing_zones, new_zones):
    """Valide les `parent` des nouvelles zones contre l'ensemble existant+nouveau,
    calcule `niveau` à partir de la chaîne de parenté réelle (ignore ce que Claude
    a pu renvoyer dans ce champ), et détecte les cycles. Retourne
    (nouvelles_zones_valides, zones_rejetees_avec_raison)."""
    existing_slugs = {z["slug"] for z in existing_zones if z.get("slug")}
    existing_levels = {z["slug"]: z.get("niveau", 1) for z in existing_zones if z.get("slug")}

    by_slug = {z["slug"]: z for z in new_zones if z.get("slug")}
    rejected = []

    # Dédoublonnage de slug : un nouveau slug ne doit collisionner ni avec
    # l'existant ni avec un autre nouveau slug du même batch.
    seen = set(existing_slugs)
    deduped = []
    for z in new_zones:
        slug = z.get("slug")
        if not slug:
            rejected.append((z.get("nom", "?"), "slug manquant"))
            continue
        if slug in seen:
            rejected.append((z.get("nom", "?"),
                              f"slug en collision avec une zone déjà existante ou un autre "
                              f"doublon du batch : '{slug}' — si une autre zone de ce batch "
                              f"déclare '{slug}' comme parent, elle pointera vers la zone "
                              f"EXISTANTE de ce nom, pas vers celle-ci"))
            continue
        seen.add(slug)
        deduped.append(z)
    new_zones = deduped
    by_slug = {z["slug"]: z for z in new_zones}

    def compute_level(slug, trail):
        """Remonte la chaîne de parenté pour calculer le niveau réel.
        `trail` détecte les cycles."""
        if slug in existing_levels:
            return existing_levels[slug]
        if slug in trail:
            return None  # cycle détecté
        zone = by_slug.get(slug)
        if zone is None:
            return None  # parent inconnu
        parent = zone.get("parent")
        if parent is None:
            return 1
        parent_level = compute_level(parent, trail | {slug})
        if parent_level is None:
            return None
        return parent_level + 1

    valid = []
    for zone in new_zones:
        parent = zone.get("parent")
        if parent is not None:
            if parent not in existing_slugs and parent not in by_slug:
                rejected.append((zone["slug"],
                                  f"parent inconnu : '{parent}' (ni zone existante, "
                                  f"ni nouvelle zone de ce batch)"))
                continue
            level = compute_level(zone["slug"], set())
            if level is None:
                rejected.append((zone["slug"], "cycle de parenté détecté ou parent invalide"))
                continue
            zone["niveau"] = level
        else:
            zone["niveau"] = 1
        valid.append(zone)

    return valid, rejected


def clean_zone_relations(all_zones_by_slug, new_zones):
    """Filtre allies/rivaux des nouvelles zones : ne garde que des slugs
    présents dans l'ensemble complet (existant + nouveau), jamais soi-même."""
    dropped = []
    for zone in new_zones:
        own_slug = zone.get("slug")
        rel = zone.get("relations") or {}
        for field in ("allies", "rivaux"):
            items = rel.get(field) or []
            kept = []
            for item in items:
                item_clean = str(item).strip()
                if item_clean in all_zones_by_slug and item_clean != own_slug:
                    kept.append(item_clean)
                else:
                    dropped.append((own_slug, field, item_clean))
            rel[field] = kept
        zone["relations"] = rel
    return new_zones, dropped


def clean_sources(new_zones, valid_sources):
    for zone in new_zones:
        sources = [s for s in zone.get("sources_attestees", []) if s in valid_sources]
        zone["sources_attestees"] = sources
        evt = zone.get("evenement_transition")
        if evt and evt not in valid_sources:
            zone["evenement_transition"] = None
    return new_zones


def dedupe_promoted_lieux(existing_zones, new_zones):
    """SEULE exception à la règle 'zones existantes jamais modifiées' : retire de
    `lieux_emblematiques` d'une zone existante l'entrée correspondant à un lieu
    explicitement promu en vraie sous-zone (champ `promu_depuis` rempli par Claude
    et confirmé ici par correspondance exacte de nom). Aucun autre champ d'une zone
    existante n'est touché.

    Retire le lieu PARTOUT où il apparaît dans les zones existantes, pas seulement
    sur le parent désigné par Claude — un même lieu emblématique peut avoir été
    listé sur plusieurs zones niveau 1 dès l'étape 1 (ex: une ville-siège mentionnée
    à la fois comme lieu notable de sa zone d'appartenance ET de la grande région qui
    l'englobe). Sans cette extension, seul le retrait sur le parent désigné aurait
    lieu et un résidu identique resterait visible ailleurs.

    Retourne (existing_zones modifiées en place, liste des dédoublonnages effectués
    pour log)."""
    existing_by_slug = {z["slug"]: z for z in existing_zones if z.get("slug")}
    dedupe_log = []

    for zone in new_zones:
        promu_depuis = zone.get("promu_depuis")
        if not promu_depuis:
            continue
        promu_depuis_clean = str(promu_depuis).strip()
        parent_slug = zone.get("parent")

        any_match = False
        for existing_zone in existing_zones:
            lieux = existing_zone.get("lieux_emblematiques") or []
            match_idx = next(
                (i for i, lieu in enumerate(lieux)
                 if str(lieu.get("nom", "")).strip() == promu_depuis_clean),
                None,
            )
            if match_idx is None:
                continue
            any_match = True
            removed = lieux.pop(match_idx)
            existing_zone["lieux_emblematiques"] = lieux
            dedupe_log.append((zone.get("slug", "?"), existing_zone["slug"],
                                removed.get("nom", "?"), "retiré"))

        if not any_match:
            # promu_depuis ne correspond à AUCUN lieu réel d'aucune zone existante —
            # Claude a halluciné ou mal recopié le nom : on ignore silencieusement
            # plutôt que de risquer de retirer le mauvais lieu.
            dedupe_log.append((zone.get("slug", "?"), parent_slug, promu_depuis,
                                "ignoré (aucun lieu_emblematique correspondant trouvé "
                                "sur aucune zone existante)"))

    return existing_zones, dedupe_log


# ---------------------------------------------------------------------------
# Écriture du fichier
# ---------------------------------------------------------------------------

def build_geographie_md(scenario, all_zones, vue_ensemble, nb_nouvelles):
    """Reconstruit le fichier complet à partir de TOUTES les zones
    (existantes inchangées + nouvelles), triées par niveau puis par slug
    pour une lecture stable (zones niveau 1 en tête)."""
    sorted_zones = sorted(all_zones, key=lambda z: (z.get("niveau", 1), z.get("slug", "")))

    zones_yaml = yaml.dump(sorted_zones, allow_unicode=True, sort_keys=False,
                            default_flow_style=False, width=100)
    zones_yaml_indented = "\n".join(
        ("  " + line if line.strip() else line) for line in zones_yaml.splitlines()
    )

    zones_md = ""
    for zone in sorted_zones:
        heading = "#" * min(2 + zone.get("niveau", 1), 6)
        parent_txt = f" — sous [[{zone['parent']}]]" if zone.get("parent") else ""
        zones_md += f"\n{heading} {zone['nom']}{parent_txt}\n\n"
        zones_md += f"*{zone['type']} — niveau {zone.get('niveau', 1)} — statut : {zone['statut']}*\n\n"
        origine = zone.get("origine_reelle") or []
        if origine:
            parts = []
            for o in origine:
                p = o.get("entite", "?")
                if o.get("portion"):
                    p += f" ({o['portion']})"
                parts.append(p)
            zones_md += f"**Origine réelle (2026)** : {', '.join(parts)}\n\n"
        if zone.get("periode_transition"):
            evt = zone.get("evenement_transition")
            evt_txt = f" — voir [[{evt}]]" if evt else ""
            zones_md += f"**Transition** : {zone['periode_transition']}{evt_txt}\n\n"
        zones_md += f"{zone.get('description', '')}\n\n"
        if zone.get("tensions_internes"):
            zones_md += f"**Tensions internes** : {zone['tensions_internes']}\n\n"
        lieux = zone.get("lieux_emblematiques", [])
        if lieux:
            zones_md += "**Lieux emblématiques** :\n"
            for lieu in lieux:
                note = f" — {lieu.get('notes', '')}" if lieu.get("notes") else ""
                zones_md += f"- {lieu.get('nom', '?')} ({lieu.get('type', '')}){note}\n"
            zones_md += "\n"
        rel = zone.get("relations", {}) or {}
        if rel.get("allies"):
            zones_md += f"**Alliés** : {', '.join(rel['allies'])}\n\n"
        if rel.get("rivaux"):
            zones_md += f"**Rivaux** : {', '.join(rel['rivaux'])}\n\n"
        if zone.get("sources_attestees"):
            zones_md += f"*Sources attestées : {', '.join(zone['sources_attestees'])}*\n"

    enrich_note = (f"\n_Maillage récursif enrichi le {datetime.now().strftime('%Y-%m-%d')} "
                    f"({nb_nouvelles} nouvelle(s) zone(s) ajoutée(s) sous les zones "
                    f"existantes)._\n" if nb_nouvelles else "")

    content = f"""---
scenario: {scenario}
type: geographie_monde
date_creation: {datetime.now().strftime("%Y-%m-%d")}
date_derniere_maj: {datetime.now().strftime("%Y-%m-%d")}
zones:
{zones_yaml_indented.rstrip()}
---

# Géographie — {scenario}

## Vue d'ensemble
{vue_ensemble}
{enrich_note}
## Zones
{zones_md if zones_md else "_Aucune zone identifiée — à enrichir manuellement._"}

## Notes / zones à enrichir
_Espace libre, jamais lu par les scripts — ajoute ici tes idées, brouillons, zones à
créer manuellement._
"""
    return content


def write_geographie_file(scenario, all_zones, vue_ensemble, nb_nouvelles, dry_run):
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    content = build_geographie_md(scenario, all_zones, vue_ensemble, nb_nouvelles)

    if dry_run:
        print(content)
        return None

    if path.exists():
        backup_path = path.with_suffix(".md.bak")
        shutil.copy(path, backup_path)
        print(f"  → Sauvegarde créée : {backup_path.name}")

    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def process_scenario(client, scenario, dry_run):
    print(f"\n=== {scenario} ===")

    existing_zones, vue_ensemble = load_existing_geographie(scenario)
    if existing_zones is None:
        print(f"  ✗ geographie/{scenario}.md n'existe pas — lance d'abord "
              f"build_geographie_monde.py --scenario {scenario}")
        return
    print(f"  Zones existantes (niveau 1, contexte fixe) : {len(existing_zones)}")

    instance_blocks = gather_instance_texts(scenario)
    event_blocks = gather_event_texts(scenario)
    all_blocks = instance_blocks + event_blocks

    valid_sources = set()
    for block in all_blocks:
        m = re.match(r"\[(?:INSTANCE|EVENEMENT): ([a-z0-9_]+)\]", block)
        if m:
            valid_sources.add(m.group(1))

    corpus_text = "\n\n".join(all_blocks)
    print(f"  Corpus : {len(instance_blocks)} instance(s), {len(event_blocks)} "
          f"événement(s), ~{len(corpus_text)} caractères")

    if not corpus_text.strip():
        print("  Corpus vide — rien à enrichir.")
        return

    print("  Enrichissement en cours...")
    try:
        result = enrich_geographie(client, scenario, corpus_text, existing_zones)
    except Exception as e:
        print(f"  ✗ Erreur : {e}")
        return

    new_zones = result.get("nouvelles_zones", [])
    print(f"  → {len(new_zones)} nouvelle(s) zone(s) proposée(s) par Claude")

    # 1. Validation mécanique de base (slug/nom/type/statut/origine_reelle)
    structurally_valid = []
    for zone in new_zones:
        issues = validate_zone(zone)
        if issues:
            print(f"  ⚠ Zone rejetée ({zone.get('nom', '?')}) : {', '.join(issues)}")
            continue
        structurally_valid.append(zone)

    # 2. Résolution des parents + calcul de niveau réel + détection de cycles
    new_zones, rejected_parents = resolve_parents_and_levels(existing_zones, structurally_valid)
    for slug, reason in rejected_parents:
        print(f"  ⚠ Zone rejetée ('{slug}') : {reason}")

    # 3. Sources et evenement_transition anti-hallucination
    new_zones = clean_sources(new_zones, valid_sources)

    # 4. Relations (allies/rivaux) contre l'ensemble complet existant+nouveau
    all_slugs = {z["slug"] for z in existing_zones if z.get("slug")} | \
                {z["slug"] for z in new_zones if z.get("slug")}
    new_zones, dropped_relations = clean_zone_relations(all_slugs, new_zones)
    for zslug, field, value in dropped_relations:
        print(f"  ⚠ {field} filtrée sur '{zslug}' (pas une zone connue) : '{value}'")

    print(f"  → {len(new_zones)} nouvelle(s) zone(s) retenue(s) après validation")
    if new_zones:
        for z in sorted(new_zones, key=lambda z: z.get("niveau", 1)):
            parent_txt = f" (sous {z['parent']})" if z.get("parent") else " (niveau 1)"
            print(f"     - [{z['niveau']}] {z['nom']}{parent_txt}")

    # 5. Déduplication : un lieu_emblematique promu en vraie zone est retiré de
    # la liste lieux_emblematiques de son ancien parent (SEULE exception à la
    # règle "zones existantes jamais modifiées" — voir dedupe_promoted_lieux).
    existing_zones, dedupe_log = dedupe_promoted_lieux(existing_zones, new_zones)
    for zslug, parent_slug, nom, action in dedupe_log:
        print(f"  → lieu_emblematique '{nom}' {action} sur '{parent_slug}' "
              f"(promu en zone '{zslug}')")

    all_zones = existing_zones + new_zones
    result_path = write_geographie_file(scenario, all_zones, vue_ensemble,
                                         len(new_zones), dry_run)
    if result_path:
        print(f"  ✓ Écrit : {result_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Enrichit récursivement les bibles géographiques en sous-zones "
                     "(étape 2, additif — ne modifie jamais les zones existantes)"
    )
    parser.add_argument("--scenario", choices=SCENARIOS,
                         help="Un seul scénario à traiter")
    parser.add_argument("--all", action="store_true",
                         help="Traiter les 6 scénarios")
    parser.add_argument("--dry-run", action="store_true",
                         help="Affiche le résultat sans rien écrire sur disque "
                              "(fait un vrai appel API)")
    args = parser.parse_args()

    if not args.scenario and not args.all:
        sys.exit("Précise --scenario {nom} ou --all.")

    print("=" * 60)
    print("OURRASSOL 2098 — Enrichissement récursif géographie (étape 2)")
    print("=" * 60)
    if args.dry_run:
        print("(mode --dry-run : rien ne sera écrit, mais un vrai appel API est fait)")

    client = get_client()
    targets = SCENARIOS if args.all else [args.scenario]

    for scenario in targets:
        process_scenario(client, scenario, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("Terminé.")
    print("=" * 60)


if __name__ == "__main__":
    main()
