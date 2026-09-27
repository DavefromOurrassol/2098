#!/usr/bin/env python3
"""
inject_custom_signals.py — Ourrassol 2098
==========================================

Injecte des "signaux faibles custom" (idées fournies par l'utilisateur,
souvent inspirées de l'actualité) dans les fiches variables du vault,
en suivant le même format que les signaux développés lors du chantier
"section 7 -> section 12" (voir brief_section7_vers_12.md).

PRINCIPE
--------
1. Tu remplis `signaux_custom/queue.yaml` avec une liste d'idées en
   langage naturel (voir exemple plus bas / README).
2. Tu lances :  python3 inject_custom_signals.py
3. Pour chaque idée, le script :
     - appelle le LLM (étape 1) pour choisir la/les variable(s) cible(s),
       la catégorie, et un slug snake_case pour le signal
     - appelle le LLM (étape 2) pour rédiger le bloc YAML signal_to_state
       (6 scénarios) + l'annotation section 7, en s'appuyant sur le
       state_logic de la fiche variable et le registre des événements
     - valide mécaniquement le résultat (comptage de mots, fenêtres de
       dates, collisions) — purement Python, aucun appel API
     - si la validation échoue, rappelle le LLM (étape 3, correction
       ciblée) jusqu'à 2 fois
     - injecte le bloc validé dans variables/{slug}.md (sections 7 et 12)
     - régénère registre_evenements.md
     - écrit une fiche d'audit dans signaux_custom/{signal_slug}.md
     - déplace l'idée de queue.yaml vers processed.yaml
       (ou needs_review.yaml si la validation échoue malgré les retries)

PRÉREQUIS
---------
    pip install anthropic pyyaml --break-system-packages
    export ANTHROPIC_API_KEY=sk-ant-...

USAGE
-----
    python3 inject_custom_signals.py            # traite toute la queue
    python3 inject_custom_signals.py --dry-run  # appelle le LLM, valide,
                                                  # affiche le résultat,
                                                  # mais n'écrit rien sur disque
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from llm_client import call_llm  # tier structured_strict — canonique/référencé
from echelles import CONVENTION_NIVEAUX, CONSIGNE_IMPACT, texte_echelle, verifier_impact
import dynamique as dyn  # niveaux de persistance (module pur, aucune lecture de fichier)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
VARIABLES_DIR = VAULT_ROOT / "variables"
REGISTRE_PATH = Path(__file__).resolve().parent / "registre_evenements.md"
SIGNAUX_CUSTOM_DIR = VAULT_ROOT / "signaux_custom"
QUEUE_PATH = SIGNAUX_CUSTOM_DIR / "queue.yaml"
PROCESSED_PATH = SIGNAUX_CUSTOM_DIR / "processed.yaml"
NEEDS_REVIEW_PATH = SIGNAUX_CUSTOM_DIR / "needs_review.yaml"


MAX_FIX_ATTEMPTS = 2

# Chantier injection matricielle des signaux faibles (16 août 2026) :
# plafond volontairement fixe et bas (pas dérivé d'un score comme pour les
# instances, qui n'ont pas d'équivalent ici) — un signal "faible" doit
# rester un effet mineur sur le monde, jamais comparable à un événement ou
# une entité custom. Décidé avec David (via_matrice à false par défaut,
# même session).
MAX_DELTA_SIGNAL = 10

# Bornes du champ optionnel `annee_apparition` (27 septembre 2026) : un
# signal apparaît au plus tôt en 2025 (début de la fiction) et au plus tard
# en 2097 (il faut au moins un an de fenêtre avant 2098).
ANNEE_APPARITION_MIN = 2025
ANNEE_APPARITION_MAX = 2097

SCENARIOS = [
    "breakdown",
    "fortress_world",
    "new_sustainability",
    "eco_communalism",
    "policy_reform",
    "reference",
]

VALID_VARS = [
    "systeme_economique_redistribution",
    "gouvernance_institutions",
    "geopolitique_conflits",
    "valeurs_culture_tempo_sociale",
    "organisation_territoires",
    "sante_biotechnologies",
    "frontieres_du_systeme",
    "technologie_information",
    "climat_environnement_global",
    "energie_ressources_critiques",
    "demographie_mobilite_humaine",
    "systemes_productifs_travail",
]

PILOTS = [
    "geopolitique_conflits",
    "energie_ressources_critiques",
    "organisation_territoires",
    "climat_environnement_global",
    "systemes_productifs_travail",
]


# ---------------------------------------------------------------------------
# Lecture des fiches variables
# ---------------------------------------------------------------------------

def read_variable_file(slug):
    path = VARIABLES_DIR / f"{slug}.md"
    return path.read_text(encoding="utf-8")


def split_frontmatter(content):
    """Retourne (frontmatter_dict, body_str).

    Les fiches utilisent la syntaxe Obsidian [[lien]] dans le frontmatter
    (ex: coupling_intensity: { [[geopolitique_conflits]]: 90 }), ce qui
    n'est pas du YAML valide tel quel -> on retire les doubles crochets
    avant le parsing.
    """
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    raw_fm = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    fm = yaml.safe_load(raw_fm) or {}
    return fm, m.group(2)


def extract_section(content, number, next_number=None):
    """Extrait le texte de la section '## {number}. ...' jusqu'à la
    section suivante ('## {next_number}.' ou EOF si non fourni)."""
    start_pat = re.compile(rf"^##\s*{number}\.\s.*$", re.MULTILINE)
    m_start = start_pat.search(content)
    if not m_start:
        return ""
    start = m_start.end()
    if next_number is not None:
        end_pat = re.compile(rf"^##\s*{next_number}\.\s", re.MULTILINE)
        m_end = end_pat.search(content, start)
        end = m_end.start() if m_end else len(content)
    else:
        end = len(content)
    return content[start:end].strip()


def build_variables_summary():
    """Construit un résumé condensé des 12 variables (pour l'étape 1) :
    name, variable_type, domain, sub_variables, state_logic par scénario."""
    chunks = []
    for slug in VALID_VARS:
        content = read_variable_file(slug)
        fm, _ = split_frontmatter(content)
        domain = ", ".join(fm.get("domain", []))
        sub_vars = fm.get("sub_variables", []) or []
        sub_vars_str = "; ".join(
            f"{sv.get('name')} ({sv.get('role', '')})" for sv in sub_vars
        )
        states = fm.get("states", {}) or {}
        state_logics = []
        for scen in SCENARIOS:
            sl = (states.get(scen, {}) or {}).get("state_logic", "").strip()
            sl = re.sub(r"\s+", " ", sl)
            if sl:
                state_logics.append(f"    - {scen}: {sl}")
        chunk = (
            f"### {slug}\n"
            f"  type: {fm.get('variable_type', '')}\n"
            f"  domain: {domain}\n"
            f"  sub_variables: {sub_vars_str}\n"
            f"  state_logic:\n" + "\n".join(state_logics)
        )
        chunks.append(chunk)
    return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Registre des événements
# ---------------------------------------------------------------------------

def read_registre_text():
    if not REGISTRE_PATH.exists():
        return ""
    return REGISTRE_PATH.read_text(encoding="utf-8")


def _est_ligne_separateur(ligne: str) -> bool:
    """
    Détecte une ligne séparatrice de tableau markdown (`|---|---|` ou une
    variante espacée/alignée comme `| --------- | --------- |`, produite
    par certains éditeurs -- Obsidian notamment -- qui réalignent les
    colonnes automatiquement). Corrige un bug trouvé le 26 juillet 2026 :
    `line.startswith("|---")` ne matchait QUE le format compact -- une
    section de registre_evenements.md reformatée avec des espaces (ex.
    ## breakdown) faisait planter regenerate_registre() sur `table_start +
    1` (table_start resté None), et faisait aussi silencieusement échouer
    la détection de collision de fenêtre temporelle dans
    parse_registre_table() pour cette même section (aucune erreur levée,
    mais la vérification "fenêtre déjà utilisée" ne pouvait jamais se
    déclencher pour cette section précise).
    """
    contenu = ligne.strip()
    if not contenu.startswith("|"):
        return False
    interieur = contenu.replace("|", "")
    return bool(interieur.strip()) and all(c in "-: \t" for c in interieur)


def parse_registre_table(scen_body):
    """Parse les lignes '| type | date | source | variable(s) | pilote | evenement_cle |'
    (nouveau format 6 colonnes) d'une section de scénario, retourne une
    liste de listes de colonnes."""
    rows = []
    table_started = False
    for line in scen_body.split("\n"):
        if _est_ligne_separateur(line):
            table_started = True
            continue
        if table_started and line.startswith("|"):
            cols = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cols)
        elif table_started and not line.startswith("|"):
            break
    return rows


def get_existing_windows_for_variable(registre_text, variable_slug):
    """Retourne {scenario: set(date)} pour les signaux/événements déjà
    présents pour cette variable dans le registre.

    Pour les événements (type=evenement), "variable(s)" peut contenir
    plusieurs slugs séparés par ", " — on matche si variable_slug en
    fait partie.
    """
    result = {scen: set() for scen in SCENARIOS}
    parts = re.split(
        r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text
    )
    for i in range(1, len(parts), 2):
        scen = parts[i]
        body = parts[i + 1]
        for cols in parse_registre_table(body):
            if len(cols) < 6:
                continue
            row_vars = [v.strip() for v in cols[3].split(",")]
            if variable_slug in row_vars:
                result[scen].add(cols[1])
    return result


def get_all_evenements(registre_text):
    """Retourne l'ensemble (lowercase) de tous les evenement_cle du
    registre (signaux ET événements custom confondus)."""
    events = set()
    parts = re.split(
        r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text
    )
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        for cols in parse_registre_table(body):
            if len(cols) >= 6:
                events.add(cols[5].strip().lower())
    return events


# ---------------------------------------------------------------------------
# Appels LLM
# ---------------------------------------------------------------------------

def get_client():
    """Conservé pour compatibilité — retourne None, call_claude_json n'en a plus besoin."""
    return None


def call_claude_json(client, system, user_content, max_tokens=3000):
    """Appelle le LLM, exige une réponse JSON pure, la parse et la retourne."""
    text = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
        task_tier="structured_strict",
    ).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


FORMAT_RULES = """\
RÈGLES DE FORMAT (calibrées sur le chantier section 7 -> section 12) :
- `evolution` et `evenement_cle` : ~7 mots en moyenne, MINIMUM 4 mots,
  MAXIMUM 11 mots. Phrases courtes et percutantes, pas de longues
  descriptions.
- `evenement_cle` : inclut une année précise, de préférence à la fin (ex: "... 2051"),
  SAUF pour les scénarios eco_communalism où l'absence d'année est
  acceptée (mouvements/chartes/réseaux sans date précise), en cohérence
  avec le style déjà présent dans la fiche.
- `date_bascule` : fenêtre temporelle "AAAA-AAAA", l'année de
  `evenement_cle` doit être DANS cette fenêtre.
- Les `evolution` doivent être cohérentes avec le `state_logic` de la
  section 8 du scénario correspondant (ex: si breakdown dit
  "effondrement des systèmes de santé", l'évolution d'un nouveau signal
  santé doit aller dans ce sens).
- Réutiliser intelligemment la géographie/factions déjà établies dans le
  registre (Detroit-Sud, Lagos-Est, Lagos-Mumbai-Jakarta, Carthage-Nord,
  Bloc Atlantique, Bloc Sibérien, Bloc Eurasiatique, Alliance Pacifique,
  Réseau des Assemblées Bioterritoriales...) quand c'est pertinent, sans
  forcer.
- Pas de nom d'`evenement_cle` identique ou quasi-identique à un
  événement déjà présent dans le registre fourni.
- Pas de fenêtre `date_bascule` strictement identique, pour le même
  scénario, à une fenêtre déjà utilisée par une AUTRE variable/signal —
  privilégier une fenêtre voisine mais distincte.
- Le champ `scenarios` doit contenir EXACTEMENT ces 6 clés, jamais une
  de plus : breakdown, fortress_world, new_sustainability,
  eco_communalism, policy_reform, reference. Aucune autre clé n'est
  valide -- en particulier, n'ajoute JAMAIS le nom de la variable cible
  elle-même comme clé de `scenarios` (ce n'est pas un scénario).
"""


def step1_select_variable(client, idea_text, variable_hint=None, variable_hint_count=None):
    summary = build_variables_summary()

    # variable_hint accepte : None, une chaîne unique, ou une liste de slugs.
    if variable_hint is None:
        hints = []
    elif isinstance(variable_hint, str):
        hints = [variable_hint]
    else:
        hints = list(variable_hint)
    hints = [h for h in hints if h in VALID_VARS]

    max_vars = variable_hint_count if variable_hint_count else 2
    max_vars = max(1, min(4, max_vars))

    if hints:
        hint_txt = (
            f"\nL'utilisateur impose déjà {'la variable' if len(hints) == 1 else 'les variables'} "
            f"suivante{'s' if len(hints) > 1 else ''} comme cible{'s' if len(hints) > 1 else ''} : "
            f"{', '.join(hints)}.\n"
            f"Tu DOIS les inclure dans ta réponse. Tu peux en ajouter d'autres si "
            f"pertinent, dans la limite du plafond ci-dessous.\n"
        )
    else:
        hint_txt = ""

    user_content = f"""Voici une idée de "signal faible" (observation de l'actualité
réelle) à intégrer dans le simulateur de presse fictive Ourrassol 2098 :

IDÉE :
{idea_text}
{hint_txt}
Voici un résumé condensé des 12 variables systémiques du système
(domain, sous-variables, state_logic par scénario) :

{summary}

TÂCHE :
1. Choisis entre 1 et {max_vars} variable{'s' if max_vars > 1 else ''} cible{'s' if max_vars > 1 else ''}
   parmi les 12 — privilégie 2 par défaut (un signal touche presque toujours
   plusieurs systèmes), monte au-delà de 2 (jusqu'à {max_vars}) seulement si
   l'idée est clairement structurante (ex: une crise qui percute climat +
   énergie + géopolitique simultanément), et descends à 1 seulement si
   l'idée est vraiment locale à un seul domaine.
   {"Les variables imposées listées ci-dessus comptent dans ce plafond." if hints else ""}
2. Détermine la catégorie : technological | geopolitical | social |
   environmental | cognitive_cultural.
3. Propose un identifiant `signal_slug` en snake_case, sans accents,
   court (3-5 mots), qui décrit le signal (ex: chatbots_therapeutes_remboursement).

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact :
{{"variables": ["slug1"], "categorie": "social", "signal_slug": "..."}}
"""
    result = call_claude_json(client, "Tu es un assistant de world-building.", user_content)

    # Fait respecter max_vars mécaniquement -- trouvé le 26 juillet 2026 :
    # le LLM a retourné 3 variables alors que le plafond par défaut est 2,
    # rien ne vérifiait la consigne du prompt après coup. Les variables
    # imposées (hints) sont toujours conservées en premier, complétées par
    # les suivantes proposées par le LLM dans l'ordre, jusqu'à max_vars.
    variables = result.get("variables") or []
    if len(variables) > max_vars:
        ordonnees = [v for v in hints if v in variables] + [v for v in variables if v not in hints]
        result["variables"] = ordonnees[:max_vars]

    return result


MOTS_VIDES_FR = {
    "dans", "pour", "avec", "sans", "cette", "cette", "leurs", "leur",
    "plus", "gros", "vers", "sont", "être", "avoir", "fait", "faits",
    "tout", "tous", "toute", "toutes", "comme", "entre", "sous", "chez",
    "depuis", "pendant", "après", "avant", "encore", "ainsi", "alors",
    "donc", "mais", "aussi", "très", "peut", "peuvent", "doit", "doivent",
    "cette", "cette", "monde", "mondial", "mondiale", "devient", "devenir",
}


def _mots_cles(texte: str) -> set:
    """Extrait des mots-clés approximatifs d'un texte (mots de 5+ lettres,
    hors mots vides courants) -- pas de la vraie recherche sémantique
    (aucune infra d'embeddings ici), juste un repérage lexical grossier
    pour retrouver des signaux existants qui parlent probablement du même
    sujet."""
    mots = re.findall(r"[a-zàâäéèêëïîôöùûüç]{5,}", texte.lower())
    return {m for m in mots if m not in MOTS_VIDES_FR}


def _signaux_thematiquement_proches(idea_text: str, section12: str, signal_slug: str = None) -> list:
    """
    Repère, par recours lexical (mots-clés partagés, pas de sémantique
    réelle), les signaux DÉJÀ existants dans la section 12 qui parlent
    probablement du même sujet que la nouvelle idée -- ex. une nouvelle
    idée sur les "terres rares" en Norvège doit voir qu'un signal
    "tensions_sur_terres_rares" existe déjà, pour que le LLM se positionne
    explicitement par rapport à lui (cohérent, complémentaire, ou
    contradiction à assumer) plutôt que de l'ignorer silencieusement --
    jusqu'ici la section 12 n'était montrée que "pour le style", sans
    consigne de cohérence thématique. Ajouté le 26 juillet 2026 suite à
    une question de David sur le signal norvege_terres_rares_geopolitique
    vs. tensions_sur_terres_rares (variable geopolitique_conflits).

    `signal_slug` : exclut le signal en cours de génération de ses propres
    résultats -- il partage toujours des mots-clés avec l'idée dont il est
    issu, et ses éventuelles entrées sœurs (autres variables, même idée)
    sont déjà couvertes séparément par `sibling_block`.

    Retourne une liste de blocs texte "  - signal: xxx\\n    ..." bruts,
    tels qu'ils apparaissent dans la section 12 -- pas reparsés en YAML,
    pour rester robuste même si le YAML de la section a un souci de
    formatage ponctuel (voir bug du 26 juillet sur les séparateurs de
    tableau -- même prudence ici : mieux vaut afficher un extrait brut
    que planter sur un YAML légèrement irrégulier).
    """
    mots_idee = _mots_cles(idea_text)
    if not mots_idee:
        return []

    # Découpe grossière par entrée "  - signal: ..." (2 espaces d'indentation,
    # cohérent avec le format écrit par ce même script -- voir FORMAT_RULES).
    blocs = re.split(r"(?=^  - signal: )", section12, flags=re.M)
    proches = []
    for bloc in blocs:
        if not bloc.strip().startswith("- signal:"):
            continue
        if signal_slug and bloc.strip() == f"- signal: {signal_slug}" or \
           (signal_slug and bloc.strip().startswith(f"- signal: {signal_slug}\n")):
            continue
        mots_bloc = _mots_cles(bloc)
        if mots_idee & mots_bloc:
            proches.append(bloc.strip())
    return proches


def step2_develop(client, idea_text, source, variable_slug, signal_slug, categorie,
                   registre_text, previous=None, issues=None, sibling_events=None,
                   zone_hint=None, annee_apparition=None):
    content = read_variable_file(variable_slug)
    section7 = extract_section(content, 7, 8)
    section8 = extract_section(content, 8, 9)
    section12 = extract_section(content, 12, None)

    # Ancrage géographique optionnel -- ajouté le 26 juillet 2026, RECONÇU
    # le même jour suite à un échange avec David : la première version
    # utilisait un slug de zone 2098 (widget `zones_hier`, même que
    # inject_custom_events.py), mais une zone 2098 est par nature propre à
    # UN SEUL scénario (nom narratif, découpage différent d'un scénario à
    # l'autre) -- aucune garantie de correspondance dans les 5 autres, et
    # le sélecteur GUI ne pouvait de toute façon afficher que les zones du
    # scénario par défaut de la Config, pas un choix pertinent pour un
    # signal qui couvre toujours les 6 scénarios en un seul appel.
    #
    # Reconçu en champ TEXTE LIBRE pour un lieu réel de 2026 (pays, région,
    # ville) plutôt qu'un slug de zone 2098 : contrairement à une zone
    # narrative, un pays réel existe à l'identique dans les 6 scénarios --
    # seule son appartenance à tel ou tel bloc/zone change. Le LLM voit déjà
    # la section 8 (state_logic par scénario) dans le prompt : avec un lieu
    # réel plutôt qu'un slug figé, il peut raisonner lui-même à quelle
    # zone/bloc ce lieu correspond dans CHAQUE scénario, au lieu de devoir
    # deviner ce que représente un slug hors-contexte.
    zone_hint_txt = ""
    if zone_hint:
        zone_hint_txt = (
            f"\nAncrage géographique souhaité par l'utilisateur : **{zone_hint}** "
            f"(lieu réel de 2026 -- pays, région ou ville, PAS un slug de zone "
            f"2098). Pour chacun des 6 scénarios, identifie toi-même à quelle "
            f"zone/bloc ce lieu correspond aujourd'hui dans ce scénario précis "
            f"(section 8 ci-dessous) et utilise cette zone comme contexte "
            f"géographique principal des `evenement_cle` -- la correspondance "
            f"peut légitimement différer d'un scénario à l'autre (un même pays "
            f"n'appartient pas forcément au même bloc partout).\n"
            f"\n⚠️ VÉRIFICATION DE COHÉRENCE OBLIGATOIRE avant de rédiger : "
            f"compare cet ancrage à l'idée source ci-dessus -- si l'idée "
            f"mentionne elle-même un lieu différent de '{zone_hint}', les deux "
            f"ne peuvent pas être vrais en même temps. Dans ce cas, privilégie "
            f"le lieu mentionné explicitement dans l'idée source (c'est "
            f"l'intention la plus sûre de l'utilisateur) et ignore '{zone_hint}' "
            f"plutôt que d'essayer de concilier les deux artificiellement.\n"
        )

    # Année d'apparition imposée (27 septembre 2026) : le signal ÉMERGE à
    # cette date, la même dans les 6 scénarios -- il ne peut donc basculer
    # nulle part avant. Contrainte vérifiée mécaniquement ensuite par
    # validate_signal_block().
    apparition_txt = ""
    if annee_apparition:
        apparition_txt = (
            f"\n⚠️ ANNÉE D'APPARITION IMPOSÉE : ce signal apparaît en {annee_apparition}, "
            f"dans les 6 scénarios. Aucune fenêtre `date_bascule` ne peut commencer avant "
            f"{annee_apparition}, et l'année de chaque `evenement_cle` doit être "
            f"{annee_apparition} ou plus tard. La bascule elle-même peut venir plus tard, "
            f"et à des dates différentes selon les scénarios.\n"
        )

    proches = _signaux_thematiquement_proches(idea_text, section12, signal_slug)
    proches_block = ""
    if proches:
        proches_txt = "\n\n".join(proches[:3])  # 3 max -- pas noyer le prompt
        proches_block = f"""
--- ⚠️ SIGNAUX EXISTANTS PROBABLEMENT SUR LE MÊME SUJET (repérage par mots-clés, à vérifier toi-même) ---
{proches_txt}

Positionne explicitement ton nouveau signal par rapport à ceux-ci :
- s'ils décrivent le même phénomène à un autre endroit/échelle, assume-le
  comme complémentaire (ex: deux foyers de tension distincts d'une même
  dynamique mondiale) plutôt que de l'ignorer,
- si ton idée modifie la logique de fond de ces signaux existants (ex: un
  acteur devient dominant, réduisant l'enjeu ailleurs), reflète cette
  tension ou ce changement dans `evolution` plutôt que de raconter une
  histoire parallèle qui les contredit silencieusement.
"""

    if previous is None:
        task = f"""TÂCHE : rédige le bloc YAML `signal_to_state` pour ce signal,
pour les 6 scénarios ({", ".join(SCENARIOS)}), au format calibré ci-dessous,
ainsi qu'une ligne d'annotation pour la section 7 (catégorie {categorie}).
"""
    else:
        issues_txt = "\n".join(f"- {i}" for i in issues)
        task = f"""Le bloc YAML précédent a échoué la validation mécanique :
{issues_txt}

Voici le bloc précédent :
{previous}

TÂCHE : corrige UNIQUEMENT les points listés ci-dessus, en gardant le
reste identique autant que possible.
- Si un point concerne un `evenement_cle` "déjà présent dans le registre",
  n'essaie PAS de le reformuler légèrement (changer un mot) : invente un
  événement RÉELLEMENT différent (autre lieu, autre acteur, autre nature
  de fait) pour ce scénario, tout en restant cohérent avec le
  `state_logic` de la section 8.
- Si un point concerne un nombre de mots hors de la fourchette 4-11,
  ne te contente pas de retirer un mot : reformule la phrase en gardant
  seulement le fait central (acteur + action + lieu/cible + année) et
  en supprimant les qualificatifs, compléments de manière ou noms
  d'institution à rallonge. Un evenement_cle court et concret ("Oslo
  bloque l'accès au port de Narvik 2049") vaut mieux qu'une version
  complète mais verbeuse ("Oslo impose un blocus stratégique sur les
  exportations minières via le port de Narvik 2049").
- Si un point concerne un "Scénario inconnu", supprime purement et
  simplement cette clé en trop -- `scenarios` ne doit contenir QUE les
  6 clés valides (breakdown, fortress_world, new_sustainability,
  eco_communalism, policy_reform, reference), rien d'autre. Vérifie en
  particulier que tu n'as pas ajouté le nom de la variable cible
  elle-même comme clé.
- Si un point concerne l'année d'apparition, décale la fenêtre `date_bascule`
  et l'`evenement_cle` du scénario concerné APRÈS cette année, sans changer
  le fond de l'évolution.
- Si un point concerne "polarite" ou "delta_level", corrige ces champs
  JSON (pas le YAML) : "polarite" est un dictionnaire des 6 scénarios à
  +1/-1, déduit de l'`evolution` de chaque scénario ; "delta_level" est un
  entier entre 1 et {MAX_DELTA_SIGNAL}.
"""

    sibling_block = ""
    if sibling_events:
        sibling_lines = "\n".join(
            f"  - [{scen}] {ev}" for scen, ev in sibling_events.items()
        )
        sibling_block = f"""
--- ⚠️ ÉVÉNEMENTS DÉJÀ ÉCRITS POUR CE MÊME SIGNAL DANS UNE AUTRE VARIABLE ---
Ce signal ({signal_slug}) est aussi développé pour {("d'autres variables" if len(sibling_events) else "une autre variable")}
dans cette même session. Les `evenement_cle` suivants viennent d'être
injectés dans le registre — ils sont INTERDITS pour cette variable :
{sibling_lines}

Écris des `evenement_cle` DIFFÉRENTS pour chaque scénario concerné :
même thème de fond (c'est le même signal réel), mais un fait daté distinct
— un autre lieu, un autre acteur institutionnel, une autre conséquence
concrète — plutôt qu'une reformulation du même événement.
"""

    user_content = f"""Idée source (signal d'actualité, source : {source}) :
{idea_text}

Variable cible : {variable_slug}
Catégorie : {categorie}
Identifiant du signal : {signal_slug}
{zone_hint_txt}{apparition_txt}
{FORMAT_RULES}

--- SECTION 7 actuelle (signaux faibles existants) ---
{section7}

--- SECTION 8 actuelle (state_logic par scénario) ---
{section8}

--- SECTION 12 actuelle (signal_to_state existants, pour le style) ---
{section12}

--- EXTRAIT DU REGISTRE DES ÉVÉNEMENTS (anti-collision) ---
{registre_text}
{proches_block}
{sibling_block}
{task}

Réponds UNIQUEMENT en JSON, sans aucun texte autour, format exact
(le champ "signal_to_state_yaml" doit être une chaîne YAML valide,
indentée comme les entrées existantes de la section 12, commençant par
"  - signal: {signal_slug}") :
{{
  "signal_to_state_yaml": "  - signal: {signal_slug}\\n    scenarios:\\n      breakdown:\\n        evolution: ...\\n        date_bascule: AAAA-AAAA\\n        evenement_cle: ... AAAA\\n      ...",
  "section7_annotation": "- description courte du signal (→ signal_custom: {signal_slug}, source: {source})",
  "signaux_existants_consideres": "Explique en 1-3 phrases si un signal déjà présent en section 12 traite d'un sujet proche, et comment tu t'es positionné par rapport à lui (complémentaire / conséquence / tension assumée). Si aucun signal existant proche n'a été identifié, dis-le explicitement (ex: 'Aucun signal existant sur un sujet proche identifié.') -- ce champ est obligatoire même en l'absence de recoupement, pour que le choix (ou l'absence de choix à faire) reste vérifiable a posteriori plutôt que silencieux.",
  "delta_level": 5,
  "polarite": {{"breakdown": "<+1 ou -1>", "fortress_world": "<+1 ou -1>", "new_sustainability": "<+1 ou -1>", "eco_communalism": "<+1 ou -1>", "policy_reform": "<+1 ou -1>", "reference": "<+1 ou -1>"}},
  "propagation_via_matrice": false,
  "contexte_injection": "phrase courte expliquant l'impact chiffré ci-dessous"
}}

IMPORTANT sur "section7_annotation" : le texte "signal_custom: " (avec les
deux-points) doit apparaître MOT POUR MOT juste avant "{signal_slug}" --
n'écris jamais juste "(→ {signal_slug}, source: ...)" en sautant ce
préfixe, même si ça semble redondant. C'est ce texte exact qui permet de
retrouver et retirer cette ligne proprement si le signal est annulé plus
tard.

IMPORTANT sur "delta_level"/"polarite"/"propagation_via_matrice" (chantier
injection matricielle, 16 août 2026) : ce signal doit pouvoir influencer
RÉELLEMENT le niveau de la variable {variable_slug}, pas seulement la
mentionner narrativement.
PLAFOND STRICT : |delta_level| ne doit JAMAIS dépasser {MAX_DELTA_SIGNAL}
— un signal reste par nature un effet MINEUR, très inférieur à un
événement ou une entité custom (qui peuvent aller jusqu'à 25). Si l'idée
source te semble mériter un impact plus fort que {MAX_DELTA_SIGNAL},
c'est probablement le signe que ce n'est pas un "signal faible" mais un
véritable événement — choisis quand même une valeur dans la plage
autorisée, ne la dépasse pas.
{CONVENTION_NIVEAUX}
Échelle de {variable_slug} : {texte_echelle(variable_slug) or "non définie"}.
{CONSIGNE_IMPACT}
"delta_level" : UNE SEULE valeur entière entre 1 et {MAX_DELTA_SIGNAL} (jamais 0 :
un signal sans effet chiffré n'a pas lieu d'être injecté ; les valeurs de
l'exemple JSON ci-dessus sont illustratives, ne les recopie pas). C'est la
FORCE du signal, appliquée UNE FOIS PAR SCÉNARIO avec une année d'injection
et une durée d'effet dérivées automatiquement de "date_bascule" (pas besoin
de les répéter ici) — choisis une valeur cohérente avec l'ensemble des 6
scénarios, pas seulement celui qui te semble le plus marquant.
"polarite" : UN DICTIONNAIRE avec EXACTEMENT les 6 clés de scénario
({", ".join(SCENARIOS)}), chacune valant +1 ou -1 (jamais 0). C'est le SENS
de l'effet DANS CE SCÉNARIO PRÉCIS : +1 si l'`evolution` que tu as écrite
pour ce scénario aggrave la crise de {variable_slug} (niveau qui monte),
-1 si elle l'apaise (niveau qui baisse). Déduis chaque polarité de
l'`evolution` du scénario correspondant, pas d'une impression globale :
un même signal peut légitimement aggraver la crise dans un scénario et
l'apaiser dans un autre.
"propagation_via_matrice" : false SAUF SI ce signal touche une dynamique
véritablement structurelle et durable (rare pour un signal faible) — en
cas de doute, false.
"""
    return call_claude_json(client, "Tu es un assistant de world-building.", user_content, max_tokens=4000)


# ---------------------------------------------------------------------------
# Validation mécanique
# ---------------------------------------------------------------------------

def normaliser_polarites(polarite):
    """
    Convertit le champ "polarite" renvoyé par le LLM en {scénario: +1/-1}
    et liste les problèmes (27 septembre 2026).

    Jusqu'ici le LLM renvoyait UNE polarité recopiée dans les 6 scénarios,
    alors que la trajectoire narrative diverge (un même signal peut aggraver
    la crise dans breakdown et l'apaiser dans new_sustainability) -- seul
    reevaluer_polarites.py corrigeait après coup. Désormais une polarité par
    scénario est exigée : un entier unique est refusé (et non recopié), une
    valeur 0 aussi (l'ancien `polarite or 1` la transformait en +1 sans
    prévenir).

    Retourne (polarites_valides, issues) : polarites_valides ne contient que
    les scénarios dont la valeur est correcte.
    """
    if not isinstance(polarite, dict):
        return {}, [
            f"polarite doit être un dictionnaire avec les 6 scénarios "
            f"({', '.join(SCENARIOS)}), chacun à +1 ou -1 -- reçu : {polarite!r}"
        ]
    valides, issues = {}, []
    manquants = [s for s in SCENARIOS if s not in polarite]
    if manquants:
        issues.append(f"polarite : scénarios manquants {manquants}")
    inconnus = [s for s in polarite if s not in SCENARIOS]
    if inconnus:
        issues.append(f"polarite : clés inconnues {inconnus} (seules les 6 clés de scénario sont valides)")
    for scen in SCENARIOS:
        if scen not in polarite:
            continue
        try:
            val = int(polarite[scen])
        except (TypeError, ValueError):
            issues.append(f"polarite[{scen}] non numérique : {polarite[scen]!r}")
            continue
        if val not in (1, -1):
            issues.append(f"polarite[{scen}]={val} : doit valoir +1 ou -1")
            continue
        valides[scen] = val
    return valides, issues


def validate_signal_block(yaml_text, signal_slug, variable_slug, registre_text,
                           delta_level=None, propagation_via_matrice=None, polarite=None,
                           annee_apparition=None):
    """Retourne une liste de problèmes (vide si tout est OK).

    delta_level/propagation_via_matrice (16 août 2026, chantier injection
    matricielle) : validés ici en plus du bloc YAML narratif, pour
    centraliser tous les contrôles de ce (signal, variable) en un seul
    passage — cohérent avec le fait que les deux sont produits par le
    même appel LLM (step2_develop) et corrigés ensemble en cas d'échec."""
    issues = []

    if delta_level is not None:
        try:
            delta_val = float(delta_level)
        except (TypeError, ValueError):
            issues.append(f"delta_level non numérique : {delta_level!r}")
            delta_val = None
        if delta_val is not None and abs(delta_val) > MAX_DELTA_SIGNAL:
            issues.append(
                f"delta_level={delta_val} dépasse le plafond {MAX_DELTA_SIGNAL} "
                f"(un signal faible ne peut pas avoir un impact aussi fort)"
            )
        # 27 septembre 2026 : un delta nul passait la validation puis était
        # écarté en silence par dynamique.chocs_depuis_donnees() -- le signal
        # n'avait alors aucun effet chiffré, sans aucun message.
        if delta_val is not None and abs(delta_val) < 1:
            issues.append(
                f"delta_level={delta_val} : doit être au moins 1 "
                f"(un signal sans effet chiffré ne doit pas être injecté)"
            )
    if polarite is not None or delta_level is not None:
        # Polarité PAR SCÉNARIO (27 septembre 2026) -- voir normaliser_polarites().
        # Vérifiée aussi quand le LLM l'a omise (None) alors qu'il a fourni un
        # delta_level : l'absence est alors signalée au lieu d'être remplacée
        # par +1 en silence.
        polarites, issues_pol = normaliser_polarites(polarite)
        issues.extend(issues_pol)
    else:
        polarites = {}
    if delta_level is not None:
        # Convention de signe (27 septembre 2026, echelles.py), vérifiée pour
        # chaque polarité distincte -- dédoublonnée pour ne pas répéter 6 fois
        # le même message.
        for pol in sorted(set(polarites.values())) or [1]:
            for issue in verifier_impact(delta_level, pol):
                if issue not in issues:
                    issues.append(issue)
    if propagation_via_matrice is not None and not isinstance(propagation_via_matrice, bool):
        issues.append(f"propagation_via_matrice doit être un booléen : {propagation_via_matrice!r}")

    try:
        parsed = yaml.safe_load("signal_to_state:\n" + yaml_text)
    except yaml.YAMLError as e:
        return [f"YAML invalide : {e}"]

    entries = (parsed or {}).get("signal_to_state") or []
    if not entries:
        return ["Bloc YAML vide ou mal formé (pas d'entrée 'signal_to_state')."]
    entry = entries[0]

    if entry.get("signal") != signal_slug:
        issues.append(
            f"Le champ 'signal' ({entry.get('signal')!r}) ne correspond pas "
            f"au signal_slug attendu ({signal_slug!r})."
        )

    scenarios = entry.get("scenarios") or {}
    missing = set(SCENARIOS) - set(scenarios.keys())
    if missing:
        issues.append(f"Scénarios manquants : {sorted(missing)}")

    existing_windows = get_existing_windows_for_variable(registre_text, variable_slug)
    all_events = get_all_evenements(registre_text)
    new_windows_by_scen = {}

    for scen, data in scenarios.items():
        if scen not in SCENARIOS:
            issues.append(f"Scénario inconnu : {scen}")
            continue

        evolution = (data or {}).get("evolution", "")
        evenement = (data or {}).get("evenement_cle", "")
        date_bascule = (data or {}).get("date_bascule", "")

        for field_name, value in (("evolution", evolution), ("evenement_cle", evenement)):
            wc = len(value.split())
            if wc < 4 or wc > 11:
                issues.append(
                    f"[{scen}] '{field_name}' a {wc} mots "
                    f"(attendu 4-11) : {value!r}"
                )

        m = re.match(r"^(\d{4})-(\d{4})$", date_bascule)
        if not m:
            issues.append(f"[{scen}] date_bascule invalide : {date_bascule!r}")
        else:
            start, end = int(m.group(1)), int(m.group(2))
            if annee_apparition and start < annee_apparition:
                issues.append(
                    f"[{scen}] date_bascule {date_bascule} commence avant l'année "
                    f"d'apparition imposée ({annee_apparition})"
                )
            # Année acceptée n'importe où dans la phrase (27 septembre 2026,
            # même correctif que inject_custom_events.py le 13 août) -- la
            # DERNIÈRE année citée fait foi ("révision en 2045 du traité de
            # 2041" -> 2045). L'ancienne regex exigeait l'année en toute fin
            # de phrase et consommait des relances pour une simple question
            # de format.
            annees_evt = re.findall(r"\b(\d{4})\b", evenement)
            year_match = re.match(r"(\d{4})", annees_evt[-1]) if annees_evt else None
            if annee_apparition and year_match and int(year_match.group(1)) < annee_apparition:
                issues.append(
                    f"[{scen}] année {year_match.group(1)} de evenement_cle antérieure "
                    f"à l'année d'apparition imposée ({annee_apparition})"
                )
            if year_match:
                year = int(year_match.group(1))
                if not (start <= year <= end):
                    issues.append(
                        f"[{scen}] année {year} dans evenement_cle hors de "
                        f"date_bascule {date_bascule}"
                    )
            elif scen != "eco_communalism":
                issues.append(
                    f"[{scen}] evenement_cle sans année "
                    f"(attendue sauf pour eco_communalism) : {evenement!r}"
                )

        if date_bascule in existing_windows.get(scen, set()):
            # Volontairement un AVERTISSEMENT, pas un blocage (changé le 26
            # juillet 2026, à la demande de David) : le registre existe pour
            # "éviter les collisions de noms/dates/lieux" (doublons
            # accidentels), pas pour interdire à deux signaux réellement
            # indépendants de coexister sur la même fenêtre -- rien
            # n'empêche narrativement deux causes distinctes de coïncider
            # dans le temps pour la même variable. Reste visible dans le
            # rapport pour vérification humaine si besoin, mais ne consomme
            # plus un essai de correction pour rien.
            print(f"  ⚠ [avertissement, non bloquant] [{scen}] fenêtre {date_bascule} "
                  f"déjà utilisée par un autre signal de {variable_slug} dans le registre.")
        new_windows_by_scen.setdefault(date_bascule, []).append(scen)

        if evenement.strip().lower() in all_events:
            issues.append(
                f"[{scen}] evenement_cle déjà présent dans le registre : "
                f"{evenement!r}"
            )

    for window, scens in new_windows_by_scen.items():
        if len(scens) > 1:
            issues.append(
                f"Fenêtre {window} dupliquée entre plusieurs scénarios "
                f"du même nouveau signal : {scens}"
            )

    return issues


# ---------------------------------------------------------------------------
# Injection dans les fiches variables
# ---------------------------------------------------------------------------

def _signal_deja_injecte(variable_slug, signal_slug):
    """True si la section 12 de la fiche variable contient déjà une entrée
    `- signal: {signal_slug}` (27 septembre 2026, garde-fou anti-doublon)."""
    try:
        section12 = extract_section(read_variable_file(variable_slug), 12, None)
    except OSError:
        return False
    return re.search(rf"^\s*-\s*signal:\s*{re.escape(signal_slug)}\s*$",
                     section12, re.MULTILINE) is not None


def inject_signal_to_state(variable_slug, yaml_text):
    path = VARIABLES_DIR / f"{variable_slug}.md"
    content = path.read_text(encoding="utf-8")

    # Le bloc section 12 est le DERNIER bloc ```yaml ... ``` du fichier.
    matches = list(re.finditer(r"```yaml\n(.*?)\n```", content, re.DOTALL))
    if not matches:
        raise RuntimeError(f"Aucun bloc ```yaml trouvé dans {variable_slug}.md")
    last = matches[-1]
    block_content = last.group(1)

    if not yaml_text.endswith("\n"):
        yaml_text += "\n"
    new_block_content = block_content.rstrip("\n") + "\n\n" + yaml_text.rstrip("\n")

    new_content = (
        content[: last.start(1)] + new_block_content + content[last.end(1):]
    )
    path.write_text(new_content, encoding="utf-8")


def inject_section7_annotation(variable_slug, annotation_line, signal_slug):
    path = VARIABLES_DIR / f"{variable_slug}.md"
    content = path.read_text(encoding="utf-8")

    section7 = extract_section(content, 7, 8)
    marker = "**custom (signaux d'actualité)**"

    if marker in section7:
        new_section7 = section7.rstrip() + f"\n{annotation_line}"
    else:
        new_section7 = section7.rstrip() + f"\n\n{marker}\n{annotation_line}"

    # Remplace l'ancienne section 7 par la nouvelle, en conservant les
    # titres "## 7." et "## 8." intacts.
    start_pat = re.compile(r"^##\s*7\.\s.*$", re.MULTILINE)
    end_pat = re.compile(r"^##\s*8\.\s", re.MULTILINE)
    m_start = start_pat.search(content)
    m_end = end_pat.search(content, m_start.end())

    new_content = (
        content[: m_start.end()]
        + "\n"
        + new_section7
        + "\n\n"
        + content[m_end.start():]
    )
    path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Régénération du registre
# ---------------------------------------------------------------------------

def _all_rows(registre_text):
    """Retourne toutes les lignes (listes de colonnes) du registre,
    tous scénarios confondus — utilisé pour recompter les totaux par type."""
    rows = []
    parts = re.split(r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text)
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        rows.extend(parse_registre_table(body))
    return rows


def regenerate_registre(variable_slug, signal_slug, entry, pilote):
    registre_text = read_registre_text()
    parts = re.split(r"(\n## (?:" + "|".join(SCENARIOS) + r")\n)", registre_text)
    output = [parts[0]]
    pilote_str = "oui" if pilote else "non"
    total_rows = 0

    for i in range(1, len(parts), 2):
        header = parts[i]
        body = parts[i + 1]
        scen = header.strip().replace("## ", "")

        lines = body.split("\n")
        table_start = None
        for idx, l in enumerate(lines):
            if _est_ligne_separateur(l):
                table_start = idx
                break

        # Filet de sécurité : si aucune ligne séparatrice n'est trouvée
        # malgré la détection robuste ci-dessus (section vraiment sans
        # tableau, cas jamais rencontré jusqu'ici mais pas impossible),
        # on ne plante plus avec `None + 1` -- on signale clairement le
        # scénario fautif plutôt que de laisser une TypeError opaque
        # remonter jusqu'à needs_review.yaml sans dire où chercher.
        if table_start is None:
            raise ValueError(
                f"regenerate_registre : aucune ligne séparatrice de tableau "
                f"trouvée dans la section '## {scen}' de {REGISTRE_PATH.name} -- "
                f"vérifier manuellement le format de cette section."
            )

        rows = []
        end_idx = len(lines)
        for idx in range(table_start + 1, len(lines)):
            l = lines[idx]
            if not l.startswith("|"):
                end_idx = idx
                break
            cols = [c.strip() for c in l.strip("|").split("|")]
            rows.append(cols)

        scen_data = entry["scenarios"][scen]
        rows.append([
            "signal", scen_data["date_bascule"], signal_slug, variable_slug,
            pilote_str, scen_data["evenement_cle"],
        ])

        def date_debut(row):
            try:
                return int(row[1].split("-")[0])
            except Exception:
                return 9999

        rows.sort(key=date_debut)
        total_rows += len(rows)

        new_table_lines = ["| " + " | ".join(r) + " |" for r in rows]
        new_body_lines = lines[: table_start + 1] + new_table_lines + lines[end_idx:]
        output.append(header)
        output.append("\n".join(new_body_lines))

    new_content = "".join(output)
    signal_rows = sum(
        1 for r in _all_rows(new_content) if len(r) >= 1 and r[0] == "signal"
    )
    evenement_rows = sum(
        1 for r in _all_rows(new_content) if len(r) >= 1 and r[0] == "evenement"
    )
    unique_signals = signal_rows // len(SCENARIOS)
    new_content = re.sub(
        r"Total : \d+ entrées \(\d+ signaux uniques × 6 scénarios( \+ \d+ entrées d'événements custom)?\)\.",
        "Total : {} entrées ({} signaux uniques × 6 scénarios + {} entrées d'événements custom).".format(
            signal_rows + evenement_rows, unique_signals, evenement_rows
        ),
        new_content,
    )
    REGISTRE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if REGISTRE_PATH.exists():
        # Sauvegarde manquante jusqu'ici -- ajoutée le 26 juillet 2026,
        # même convention que le reste du pipeline (check_zones_coherence.py,
        # generer_zones_topdown.py, etc.) : jamais écraser un fichier du
        # vault sans un .bak avant, même pour une écriture "de confiance".
        bak = REGISTRE_PATH.with_suffix(REGISTRE_PATH.suffix + ".bak")
        bak.write_text(REGISTRE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    REGISTRE_PATH.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Fiche d'audit signaux_custom/
# ---------------------------------------------------------------------------

def write_custom_fiche(signal_slug, idea_text, source, variables, categorie, yaml_text,
                        notes_coherence=None, impacts=None, annee_apparition=None,
                        completer=False):
    SIGNAUX_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    path = SIGNAUX_CUSTOM_DIR / f"{signal_slug}.md"

    # Reprise d'une injection partielle (27 septembre 2026) : la fiche
    # existante est COMPLÉTÉE (variables, trajectoires, cohérence, impacts)
    # au lieu d'être écrasée par les seules variables de cette reprise.
    coherence_existante, impacts_existants = "", ""
    if completer and path.exists():
        ancien = path.read_text(encoding="utf-8")
        fm, _ = split_frontmatter(ancien)
        variables = list(dict.fromkeys(list(fm.get("variables_cibles") or []) + list(variables)))
        m = re.search(r"## Trajectoire injectée\n\n```yaml\nsignal_to_state:\n(.*?)\n```", ancien, re.S)
        if m:
            yaml_text = m.group(1).rstrip() + "\n" + yaml_text
        m = re.search(r"## Cohérence avec les signaux existants\n\n(.*?)\n\n## ", ancien, re.S)
        if m:
            coherence_existante = m.group(1).rstrip() + "\n"
        m = re.search(r"```yaml\nimpact_sur_variables:\n(.*?)\n```", ancien, re.S)
        if m:
            impacts_existants = m.group(1).rstrip() + "\n"
        bak = path.with_suffix(".md.bak")
        bak.write_text(ancien, encoding="utf-8")

    # Section "cohérence" -- ajoutée le 26 juillet 2026 (option B) : rend
    # vérifiable a posteriori si le LLM a repéré un signal existant sur le
    # même sujet et comment il s'est positionné, au lieu de rester une
    # étape silencieuse du prompt. Une note par variable, puisque la
    # section 12 diffère d'une fiche variable à l'autre.
    coherence_block = ""
    if notes_coherence:
        lignes = coherence_existante + "\n".join(
            f"- **{var}** : {note}" for var, note in notes_coherence.items() if note
        )
        if lignes.strip():
            coherence_block = f"\n## Cohérence avec les signaux existants\n\n{lignes.strip()}\n"

    # Bloc impact chiffré (16 août 2026, chantier injection matricielle) --
    # DÉLIBÉRÉMENT séparé du bloc `signal_to_state` narratif ci-dessous, et
    # DÉLIBÉRÉMENT écrit avec `>` pour contexte_injection (pas un scalaire
    # brut sur une ligne) -- leçon tirée du bug YAML du 16 août 2026 sur le
    # chantier instances (un ' : ' dans le texte cassait tout le parsing
    # de la fiche). Consommé par apply_custom_signals() dans snapshot.py.
    impact_block = ""
    if impacts:
        entries_yaml = []
        for imp in impacts:
            scen_lines = "\n".join(
                "      {}:\n        annee_injection: {}\n        duree: {}\n"
                "        delta_level: {}\n        polarite: {}".format(
                    scen, d["annee_injection"], d["duree"],
                    d["delta_level"], d["polarite"],
                )
                for scen, d in imp["scenarios"].items()
            )
            contexte = (imp.get("contexte_injection") or "").strip().replace("\n", " ")
            entries_yaml.append(
                "  - variable: {}\n"
                "    propagation_via_matrice: {}\n"
                "    persistance: {}\n"
                "    contexte_injection: >\n      {}\n"
                "    scenarios:\n{}".format(
                    imp["variable"],
                    str(bool(imp.get("propagation_via_matrice", False))).lower(),
                    imp.get("persistance") or dyn.PERSISTANCE_DEFAUT,
                    contexte,
                    scen_lines,
                )
            )
        impact_block = "\n## Impact chiffré\n\n```yaml\nimpact_sur_variables:\n{}{}\n```\n".format(
            impacts_existants, "\n".join(entries_yaml)
        )

    content = f"""---
slug: {signal_slug}
source: {source}
categorie: {categorie}
variables_cibles: {variables}
{"annee_apparition: " + str(annee_apparition) + chr(10) if annee_apparition else ""}statut: injected
---

## Idée source

{idea_text.strip()}
{coherence_block}
## Trajectoire injectée

```yaml
signal_to_state:
{yaml_text.rstrip()}
```
{impact_block}"""
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Gestion de la queue
# ---------------------------------------------------------------------------

def load_yaml_list(path, key="queue"):
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get(key, []) or []


def save_yaml_list(path, items, key="queue"):
    SIGNAUX_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump({key: items}, allow_unicode=True, sort_keys=False),
                     encoding="utf-8")


def append_yaml_list(path, item, key="processed"):
    items = load_yaml_list(path, key=key)
    items.append(item)
    save_yaml_list(path, items, key=key)


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

def process_idea(client, idea, dry_run=False):
    idea_id = idea.get("id", "sans_id")
    idea_text = idea["description"]
    source = idea.get("source", "actualite")
    variable_hint = idea.get("variable_hint")
    variable_hint_count = idea.get("variable_hint_count")
    zone_hint = idea.get("zone_hint") or None

    # Persistance du choc chiffré (27 septembre 2026) -- vérifiée AVANT tout
    # appel LLM : une faute de frappe ne doit pas coûter un développement
    # complet pour finir en needs_review.
    persistance = dyn.normaliser_persistance(idea.get("persistance")) or dyn.PERSISTANCE_DEFAUT
    if persistance not in dyn.PERSISTANCE:
        return {"status": "needs_review", "idea": idea,
                "reason": "persistance {!r} inconnue (valeurs : {})".format(
                    idea.get("persistance"), ", ".join(dyn.PERSISTANCE))}

    # Année d'apparition (27 septembre 2026), optionnelle -- vérifiée avant
    # tout appel LLM, même logique que la persistance.
    annee_apparition = idea.get("annee_apparition")
    if annee_apparition not in (None, ""):
        try:
            annee_apparition = int(annee_apparition)
        except (TypeError, ValueError):
            annee_apparition = -1
        if not ANNEE_APPARITION_MIN <= annee_apparition <= ANNEE_APPARITION_MAX:
            return {"status": "needs_review", "idea": idea,
                    "reason": "annee_apparition {!r} invalide (entier entre {} et {})".format(
                        idea.get("annee_apparition"), ANNEE_APPARITION_MIN, ANNEE_APPARITION_MAX)}
    else:
        annee_apparition = None

    print(f"\n=== {idea_id} ===  (persistance : {persistance}"
          + (f", apparition : {annee_apparition}" if annee_apparition else "") + ")")
    # Reprise d'une injection PARTIELLE (27 septembre 2026) : une idée dont
    # certaines variables ont échoué est renvoyée en needs_review avec une
    # entrée "idee_a_remettre_en_queue" qui porte un bloc `reprise` (slug et
    # catégorie du signal déjà créé) et seulement les variables restantes.
    # Remise en queue telle quelle, elle complète le MÊME signal au lieu d'en
    # créer un second -- auparavant, l'idée entière repartait en needs_review
    # et sa remise en queue réinjectait en double les variables déjà passées.
    reprise = idea.get("reprise") or None
    if reprise:
        hints = variable_hint if isinstance(variable_hint, list) else [variable_hint]
        variables = [v for v in hints if v in VALID_VARS]
        categorie = reprise.get("categorie", "")
        signal_slug = reprise.get("signal_slug", "")
        selection = {"variables": variables, "categorie": categorie,
                     "signal_slug": signal_slug, "reprise": True}
        print(f"[1/4] Reprise du signal {signal_slug} -> variables restantes={variables}")
        if not signal_slug:
            return {"status": "needs_review", "idea": idea,
                    "reason": "bloc reprise sans signal_slug"}
    else:
        print("[1/4] Sélection de variable(s)...")
        selection = step1_select_variable(client, idea_text, variable_hint, variable_hint_count)
        variables = [v for v in selection["variables"] if v in VALID_VARS]
        categorie = selection["categorie"]
        signal_slug = selection["signal_slug"]
        # Slug déjà pris par un AUTRE signal (fiche d'audit existante) : la
        # fiche aurait été écrasée sans prévenir -- on suffixe à la place.
        base, n = signal_slug, 2
        while (SIGNAUX_CUSTOM_DIR / f"{signal_slug}.md").exists():
            signal_slug = f"{base}_{n}"
            n += 1
        if signal_slug != base:
            print(f"  ⚠ slug {base!r} déjà utilisé par un autre signal -> {signal_slug!r}")
            selection["signal_slug"] = signal_slug
        print(f"  -> variables={variables} categorie={categorie} signal_slug={signal_slug}")

    if not variables:
        return {"status": "needs_review", "reason": "aucune variable valide proposée",
                "idea": idea, "selection": selection}

    registre_text = read_registre_text()
    results = []
    sibling_events = {}  # {scenario: evenement_cle} déjà validés pour CE signal dans ce run

    for variable_slug in variables:
        # Garde-fou anti-doublon (27 septembre 2026) : ce signal est déjà
        # dans la section 12 de cette variable (reprise, ou idée remise en
        # queue à la main) -> on ne la redéveloppe pas, sans appel LLM.
        if _signal_deja_injecte(variable_slug, signal_slug):
            print(f"[2/4] {variable_slug} : signal {signal_slug} déjà injecté -> ignorée")
            results.append({"variable": variable_slug, "status": "deja_present"})
            continue
        print(f"[2/4] Développement pour {variable_slug}...")
        previous, issues = None, None
        develop = step2_develop(
            client, idea_text, source, variable_slug, signal_slug, categorie,
            registre_text, sibling_events=sibling_events, zone_hint=zone_hint,
            annee_apparition=annee_apparition,
        )

        for attempt in range(MAX_FIX_ATTEMPTS + 1):
            yaml_text = develop["signal_to_state_yaml"]
            print(f"[3/4] Validation (essai {attempt + 1})...")
            issues = validate_signal_block(
                yaml_text, signal_slug, variable_slug, registre_text,
                delta_level=develop.get("delta_level"),
                propagation_via_matrice=develop.get("propagation_via_matrice"),
                polarite=develop.get("polarite"),
                annee_apparition=annee_apparition,
            )
            if not issues:
                break
            print("  -> problèmes :")
            for i in issues:
                print(f"     - {i}")
            if attempt < MAX_FIX_ATTEMPTS:
                develop = step2_develop(
                    client, idea_text, source, variable_slug, signal_slug, categorie,
                    registre_text, previous=yaml_text, issues=issues,
                    sibling_events=sibling_events, zone_hint=zone_hint,
                    annee_apparition=annee_apparition,
                )

        if issues:
            results.append({
                "variable": variable_slug, "status": "needs_review",
                "issues": issues, "yaml_text": yaml_text,
                "annotation": develop["section7_annotation"],
                "signaux_existants_consideres": develop.get("signaux_existants_consideres", ""),
            })
            continue

        print("[4/4] Injection...")
        if not dry_run:
            inject_signal_to_state(variable_slug, yaml_text)
            inject_section7_annotation(variable_slug, develop["section7_annotation"], signal_slug)
            entry = yaml.safe_load("signal_to_state:\n" + yaml_text)["signal_to_state"][0]
            regenerate_registre(variable_slug, signal_slug, entry,
                                 pilote=variable_slug in PILOTS)
            # le registre vient de changer, on relit pour le prochain variable_slug
            registre_text = read_registre_text()
        else:
            print(yaml_text)
            print(develop["section7_annotation"])

        # On retient les evenement_cle de cette variable pour que la/les
        # variable(s) suivante(s) de CE MÊME signal (dans cette boucle) ne
        # les réutilisent pas, même en --dry-run où le registre n'est pas
        # encore mis à jour sur disque.
        entry_for_siblings = yaml.safe_load("signal_to_state:\n" + yaml_text)["signal_to_state"][0]
        for scen, data in entry_for_siblings["scenarios"].items():
            sibling_events[scen] = data["evenement_cle"]

        # Bloc d'impact chiffré par scénario (16 août 2026, chantier
        # injection matricielle) : annee_injection/duree dérivés de la
        # fenêtre date_bascule déjà écrite pour ce scénario, pas redemandés
        # au LLM -- garantit la cohérence entre narratif et numérique sans
        # risque de désynchronisation entre les deux.
        # Polarité propre à chaque scénario (27 septembre 2026) -- déjà
        # validée par validate_signal_block(), aucun repli silencieux ici.
        polarites, _ = normaliser_polarites(develop.get("polarite"))
        impact_scenarios = {}
        for scen, data in entry_for_siblings["scenarios"].items():
            m = re.match(r"^(\d{4})-(\d{4})$", data.get("date_bascule", ""))
            if not m:
                continue  # date_bascule déjà validée plus haut, filet de sécurité seulement
            start, end = int(m.group(1)), int(m.group(2))
            impact_scenarios[scen] = {
                "annee_injection": start,
                "duree": max(end - start, 1),
                "delta_level": develop["delta_level"],
                "polarite": polarites[scen],
            }

        results.append({"variable": variable_slug, "status": "injected",
                         "yaml_text": yaml_text,
                         "signaux_existants_consideres": develop.get("signaux_existants_consideres", ""),
                         "impact": {
                             "variable": variable_slug,
                             "propagation_via_matrice": bool(develop.get("propagation_via_matrice", False)),
                             "persistance": persistance,
                             "contexte_injection": develop.get("contexte_injection", ""),
                             "scenarios": impact_scenarios,
                         }})

    injectees = [r["variable"] for r in results if r["status"] == "injected"]
    echouees = [r["variable"] for r in results if r["status"] == "needs_review"]

    if not dry_run:
        injected_yaml = "\n".join(
            r["yaml_text"] for r in results if r["status"] == "injected"
        )
        if injected_yaml:
            notes_coherence = {
                r["variable"]: r.get("signaux_existants_consideres", "")
                for r in results if r["status"] == "injected"
            }
            impacts = [r["impact"] for r in results if r["status"] == "injected"]
            # variables_cibles = variables RÉELLEMENT injectées (27 septembre
            # 2026) -- listait auparavant aussi celles qui avaient échoué.
            write_custom_fiche(signal_slug, idea_text, source, injectees, categorie,
                                injected_yaml, notes_coherence, impacts=impacts,
                                annee_apparition=annee_apparition,
                                completer=bool(reprise))

    overall = "needs_review" if echouees else "injected"
    outcome = {"status": overall, "idea": idea, "selection": selection, "results": results}

    # Injection partielle : entrée prête à remettre en queue, limitée aux
    # variables en échec et rattachée au signal déjà créé (voir `reprise`).
    if echouees and not dry_run and (injectees or reprise):
        a_remettre = {k: v for k, v in idea.items() if k != "reprise"}
        a_remettre.update({
            "variable_hint": echouees,
            "variable_hint_count": len(echouees),
            "reprise": {"signal_slug": signal_slug, "categorie": categorie},
        })
        outcome["idee_a_remettre_en_queue"] = a_remettre
        print(f"  ⚠ Injection partielle : {injectees or 'aucune nouvelle'} injectée(s), "
              f"{echouees} en échec. Pour compléter ce signal, copie "
              f"'idee_a_remettre_en_queue' de needs_review.yaml dans queue.yaml.")
    return outcome


QUEUE_TEMPLATE = """\
# signaux_custom/queue.yaml
#
# Ajoute ici tes idées de signaux faibles "custom" (observations de l'actualité,
# lectures, intuitions...). Lance ensuite :
#
#   python3 generator/inject_custom_signals.py            ← injection réelle
#   python3 generator/inject_custom_signals.py --dry-run  ← test sans écriture
#
# CHAMPS :
#   id                  : identifiant court lisible (lettres, chiffres, underscores)
#   description         : l'observation en langage naturel, quelques phrases suffisent
#   source              : libre — date, lien d'article, nom d'un livre...
#   variable_hint       : optionnel. Met null si tu ne sais pas — le LLM choisit
#                         automatiquement. Sinon, une variable unique (chaîne) ou
#                         plusieurs (liste) que tu IMPOSES comme cibles ; le LLM
#                         peut en ajouter d'autres si pertinent, dans la limite
#                         de variable_hint_count.
#                         Variables disponibles :
#                           systeme_economique_redistribution | gouvernance_institutions
#                           geopolitique_conflits | valeurs_culture_tempo_sociale
#                           organisation_territoires | sante_biotechnologies
#                           frontieres_du_systeme | technologie_information
#                           climat_environnement_global | energie_ressources_critiques
#                           demographie_mobilite_humaine | systemes_productifs_travail
#   variable_hint_count : optionnel, entier 1-4. Plafond du nombre total de
#                         variables que le LLM peut retourner (hint(s) inclus).
#                         Par défaut : 2. Monte à 3-4 si tu penses que le signal
#                         est vraiment structurant entre plusieurs domaines.
#   zone_hint           : optionnel. Un LIEU RÉEL de 2026 (pays, région, ville --
#                         ex: "Norvège"), PAS un slug de zone 2098. Le LLM
#                         retrouve lui-même à quelle zone/bloc ce lieu
#                         correspond dans chacun des 6 scénarios (la
#                         correspondance peut différer d'un scénario à
#                         l'autre). Influence la rédaction des
#                         evenement_cle/evolution -- si l'idée source
#                         mentionne elle-même un lieu différent, celui-ci
#                         est prioritaire sur zone_hint.
#   annee_apparition    : optionnel. Année (2025-2097) où le signal APPARAÎT,
#                         la même dans les 6 scénarios. Aucune fenêtre de
#                         bascule ne pourra commencer avant (vérifié
#                         mécaniquement) ; la bascule peut venir plus tard,
#                         à une date différente selon le scénario. Absent =
#                         le LLM choisit librement les fenêtres.
#   reprise             : NE PAS REMPLIR À LA MAIN. Présent dans l'entrée
#                         'idee_a_remettre_en_queue' de needs_review.yaml
#                         après une injection PARTIELLE : recopier cette
#                         entrée telle quelle ici complète le signal déjà
#                         créé (mêmes slug/catégorie, variables restantes
#                         seulement) au lieu d'en créer un second.
#   persistance         : optionnel. Combien de temps l'effet CHIFFRÉ du
#                         signal dure après sa fenêtre de bascule :
#                           ephemere   -> s'estompe vite (demi-vie 10 ans)
#                           normale    -> défaut (demi-vie du type signal)
#                           durable    -> s'estompe lentement (demi-vie 40 ans)
#                           permanente -> ne s'estompe jamais
#                         Valeurs réglables dans dynamique.py (PERSISTANCE).
#                         Absent = normale. Modifiable après coup dans la
#                         fiche d'audit (bloc "Impact chiffré"), sans
#                         réinjecter.
#
# EXEMPLES :
#   - id: mon_signal_2026
#     description: >
#       Plusieurs pays testent des chatbots thérapeutes remboursés par la
#       sécurité sociale, avec débat sur la responsabilité médicale en cas
#       d'erreur de l'IA.
#     source: actualite_2026-06
#     variable_hint: sante_biotechnologies
#     variable_hint_count: null   # garde le défaut (2)
#
#   - id: crise_structurante_2026
#     description: >
#       Une vague de ruptures d'approvisionnement en terres rares déclenche
#       à la fois des tensions diplomatiques et une accélération forcée des
#       politiques de relocalisation industrielle.
#     source: actualite_2026-06
#     variable_hint: [energie_ressources_critiques, geopolitique_conflits]
#     variable_hint_count: 4   # le LLM peut ajouter jusqu'à 2 variables de plus
#
# Les idées traitées sont déplacées vers processed.yaml (succès) ou
# needs_review.yaml (échec après corrections automatiques).
# ──────────────────────────────────────────────────────────────────────────────

queue:
"""


def save_queue_with_template(remaining):
    """Réécrit queue.yaml avec l'en-tête template + les idées restantes.
    Si la queue est vide, le fichier reste prêt à l'emploi avec le template."""
    SIGNAUX_CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    if remaining:
        items_yaml = yaml.dump(remaining, allow_unicode=True,
                               sort_keys=False, default_flow_style=False)
        # yaml.dump génère "- id: ...\n  description: ...\n" — on indente de 2
        indented = "\n".join("  " + line for line in items_yaml.splitlines())
        content = QUEUE_TEMPLATE + indented + "\n"
    else:
        content = QUEUE_TEMPLATE + "  [] # ← remplace [] par tes idées\n"
    QUEUE_PATH.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Appelle le LLM et valide, mais n'écrit rien sur disque.")
    args = parser.parse_args()

    queue = load_yaml_list(QUEUE_PATH, key="queue")
    if not queue:
        print(f"Queue vide ({QUEUE_PATH}). Rien à faire.")
        return

    client = get_client()
    remaining = []

    for idea in queue:
        try:
            outcome = process_idea(client, idea, dry_run=args.dry_run)
        except Exception as e:
            outcome = {"status": "needs_review", "idea": idea, "error": str(e)}

        if args.dry_run:
            print(json.dumps(outcome, ensure_ascii=False, indent=2, default=str))
            remaining.append(idea)
            continue

        if outcome["status"] == "injected":
            append_yaml_list(PROCESSED_PATH, outcome, key="processed")
        else:
            append_yaml_list(NEEDS_REVIEW_PATH, outcome, key="needs_review")

    if not args.dry_run:
        save_queue_with_template(remaining)
        print(f"\nTerminé. Voir {PROCESSED_PATH} et {NEEDS_REVIEW_PATH}.")


if __name__ == "__main__":
    main()
