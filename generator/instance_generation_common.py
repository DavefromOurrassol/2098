#!/usr/bin/env python3
"""
instance_generation_common.py — Ourrassol 2098
=================================================

Module partagé factorisant la logique de génération d'instances, jusqu'ici
dupliquée entre `generate_instances.py` (backfill d'instances pour des
entités déjà créées) et `create_entities_and_instances.py` (création
d'entité + instances en un seul run) — deux scripts actifs et
complémentaires, PAS un cas legacy/remplacé (vérifié le 9 août 2026 via
`scripts_config.json` : les deux ont une entrée GUI distincte, avec une
description qui les différencie explicitement).

Créé le 9 août 2026, en préalable au chantier de fusion `trajectoire`
(etat_temporel + age_historique → axe unique), pour éviter d'avoir à
répercuter cette fusion — et toute modification future de ce genre — dans
deux fichiers séparés au risque de les faire diverger. Diagnostic ayant
motivé ce chantier : `generate_instances.py` et `create_entities_and_
instances.py` contenaient ~20 fonctions dupliquées, dont plusieurs avaient
déjà divergé silencieusement :
  - `call_claude_json()` : le correctif du 11 juillet 2026 (extraction
    JSON de secours, détection de troncature) n'existait que côté
    `create_entities_and_instances.py`, jamais porté dans
    `generate_instances.py`.
  - `validate_instance()` : le contrôle de plage [0-5] sur impact_local/
    impact_systemique_global n'existait que côté `create_entities_and_
    instances.py`.
  - `MAX_TOKENS` : `generate_instances.py` était resté à 2000 (jugé
    insuffisant, commentaire historique dans create_entities_and_
    instances.py), qui l'avait déjà relevé à 4000.
Ce module reprend systématiquement la version la plus robuste des deux
pour chaque fonction divergente.

Les deux scripts appelants gardent leur logique propre (argparse, boucle
principale, mode interactif de création d'entité côté
create_entities_and_instances.py) — seule la mécanique partagée de
génération d'UNE instance (prompt, appel LLM, validation, écriture
fichier) vit ici.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from llm_client import call_llm  # tier structured_strict — canonique/référencé

# ---------------------------------------------------------------------------
# Configuration partagée
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent  # Ourrassol2098/
GENERATOR_DIR = Path(__file__).resolve().parent
VARIABLES_DIR = VAULT_ROOT / "variables"
SCENARIOS_DIR = VAULT_ROOT / "scenarios"
ENTITES_DIR = VAULT_ROOT / "entites"
INSTANCES_DIR = VAULT_ROOT / "instances"
REGISTRE_PATH = GENERATOR_DIR / "registre_evenements.md"
ETAT_MONDE_PATH = GENERATOR_DIR / "etat_du_monde_reel.md"

# Valeur canonique : create_entities_and_instances.py l'avait déjà relevée
# de 2000 à 4000 (cf. TODO historique — 2000 jugé trop juste). Reprise ici
# comme seule valeur, plus de divergence possible entre les deux scripts.
INSTANCE_MAX_TOKENS = 4000

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

# TODO (chantier trajectoire, à venir) : VALID_ETATS sera remplacé par
# VALID_TRAJECTOIRE (11 valeurs) — voir SPEC_CHANTIER_TRAJECTOIRE.md §3.2.
VALID_ETATS = ["actif", "disparu", "transformé", "clandestin", "historique", "mythifié"]

SLUG_PATTERN = re.compile(r"^[a-z0-9_]+$")

_registre_cache = None
_timeline_cache = {}
_etat_monde_cache = None


# ---------------------------------------------------------------------------
# Lecture de fichiers / parsing générique
# ---------------------------------------------------------------------------

def parse_md(filepath):
    """Parse un fichier .md avec frontmatter YAML. Retourne (frontmatter
    dict, body str). Étape importante : les wikilinks [[...]] du
    frontmatter sont dépouillés de leurs crochets AVANT le parsing YAML
    (sinon `[[slug]]` serait interprété comme une liste imbriquée par
    yaml.safe_load, pas comme la chaîne "slug") — ne pas simplifier cette
    étape."""
    if not filepath.exists():
        return {}, ""
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not m:
        return {}, raw
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        import yaml
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2).strip()


def _est_ligne_separateur(ligne: str) -> bool:
    """Portée depuis inject_custom_signals.py (26 juillet 2026) — détecte
    `|---|---|` et les variantes espacées/alignées `| --------- |`."""
    contenu = ligne.strip()
    if not contenu.startswith("|"):
        return False
    interieur = contenu.replace("|", "")
    return bool(interieur.strip()) and all(c in "-: \t" for c in interieur)


def _read_registre_text():
    global _registre_cache
    if _registre_cache is not None:
        return _registre_cache
    if not REGISTRE_PATH.exists():
        _registre_cache = ""
        return _registre_cache
    _registre_cache = REGISTRE_PATH.read_text(encoding="utf-8")
    return _registre_cache


def _parse_registre_table(scen_body):
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


def load_etat_monde_reel():
    """
    Charge etat_du_monde_reel.md (ajouté le 7 août 2026, audit point 1.2) —
    instantané factuel du monde réel rédigé manuellement par David, distinct
    de registre_evenements.md (qui décrit la chronologie FICTIONNELLE interne
    au scénario). Sert à éviter qu'une entité datée proche d'aujourd'hui soit
    inventée sans lien avec ce qui existe réellement. Mis en cache pour la
    durée du run — fichier lu une seule fois, pas par instance générée.
    Absence tolérée (retombe sur un message explicite plutôt que de faire
    échouer la génération) : ce fichier est un ajout, pas un prérequis
    bloquant tant que David ne l'a pas rempli.
    """
    global _etat_monde_cache
    if _etat_monde_cache is not None:
        return _etat_monde_cache
    if not ETAT_MONDE_PATH.exists():
        _etat_monde_cache = "(etat_du_monde_reel.md absent — aucun ancrage réel disponible, se fier uniquement au profil narratif choisi)"
        return _etat_monde_cache
    text = ETAT_MONDE_PATH.read_text(encoding="utf-8").strip()
    _etat_monde_cache = text if text else "(etat_du_monde_reel.md présent mais vide — pas encore rempli)"
    return _etat_monde_cache


def load_scenario_timeline_summary(scenario_slug):
    """Résumé des jalons datés (événements custom + signaux pilotes) du
    scénario, extraits de registre_evenements.md. Mis en cache par
    scénario pour la durée du run."""
    if scenario_slug in _timeline_cache:
        return _timeline_cache[scenario_slug]

    registre_text = _read_registre_text()
    if not registre_text:
        _timeline_cache[scenario_slug] = "(registre_evenements.md introuvable ou vide)"
        return _timeline_cache[scenario_slug]

    parts = re.split(r"\n## (" + "|".join(SCENARIOS) + r")\n", registre_text)
    body = None
    for i in range(1, len(parts), 2):
        if parts[i] == scenario_slug:
            body = parts[i + 1]
            break

    if body is None:
        _timeline_cache[scenario_slug] = f"(aucune section '## {scenario_slug}' trouvée dans le registre)"
        return _timeline_cache[scenario_slug]

    lines = []
    for cols in _parse_registre_table(body):
        if len(cols) < 6:
            continue
        type_, date, source, variables, pilote, evenement_cle = cols[:6]
        if type_ == "evenement" or pilote.strip().lower() == "oui":
            lines.append(f"- [{type_}] {date} : {evenement_cle}")

    summary = "\n".join(lines[:40]) if lines else "(aucun jalon trouvé pour ce scénario)"
    _timeline_cache[scenario_slug] = summary
    return summary


def load_scenario_context(scenario):
    fm, body = parse_md(SCENARIOS_DIR / f"{scenario}.md")
    summary = ""
    m = re.search(r"\*\*Résumé\*\*\s*\n(.+?)(?=\n\*\*|\n##|\Z)", body, re.DOTALL)
    if m:
        summary = m.group(1).strip()[:300]
    return {
        "state_of_system": fm.get("state_of_system", ""),
        "trajectory": fm.get("trajectory", ""),
        "tension_level": fm.get("tension_level", ""),
        "political_regime": fm.get("political_regime", ""),
        "transformation_speed": fm.get("transformation_speed", ""),
        "dominant_variables": fm.get("dominant_variables", []) or [],
        "summary": summary,
    }


def load_variables_states(scenario):
    states = {}
    for var in VALID_VARS:
        fm, _ = parse_md(VARIABLES_DIR / f"{var}.md")
        var_states = fm.get("states", {}) or {}
        if scenario in var_states and isinstance(var_states[scenario], dict):
            states[var] = str(var_states[scenario].get("state_logic", ""))[:150]
    return states


def instance_exists(slug_entite, scenario):
    return (INSTANCES_DIR / f"{slug_entite}_{scenario}.md").exists()


def load_instances_in_scenario(scenario, exclude_slug=None):
    """
    Charge {slug_instance: nom} pour toutes les instances déjà existantes
    dans CE scénario — utilisé pour proposer des alliances/oppositions
    réelles (slugs valides) plutôt que du texte libre inventé. On ne
    référence que le même scénario : une alliance n'a de sens que dans
    le même monde.
    """
    result = {}
    if not INSTANCES_DIR.exists():
        return result
    for path in sorted(INSTANCES_DIR.glob(f"*_{scenario}.md")):
        if path.stem == exclude_slug:
            continue
        fm, _ = parse_md(path)
        if fm.get("type") != "instance":
            continue
        result[fm.get("slug", path.stem)] = fm.get("name", path.stem)
    return result


# ---------------------------------------------------------------------------
# Appel LLM
# ---------------------------------------------------------------------------

def get_client():
    """Vestige d'API — call_llm() (llm_client.py) ne nécessite plus de
    client explicite, conservé pour compatibilité de signature avec les
    appelants existants."""
    return None


def call_claude_json(client, system, user_content, max_tokens=INSTANCE_MAX_TOKENS):
    """Version canonique — reprise de create_entities_and_instances.py,
    la plus robuste des deux versions historiques (celle de
    generate_instances.py n'avait ni le filet de sécurité d'extraction
    JSON, ni la détection de troncature, ni le correctif du 11 juillet
    2026 sur le NameError `resp` — jamais porté avant ce chantier)."""
    text = call_llm(
        system_prompt=system,
        user_prompt=user_content,
        max_tokens=max_tokens,
        temperature=0.0,
        task_tier="structured_strict",
    ).strip()

    if not text:
        raise RuntimeError("Réponse LLM vide.")

    candidate = re.sub(r"^```(?:json)?\s*", "", text)
    candidate = re.sub(r"\s*```$", "", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Filet de sécurité : le modèle raisonne parfois en texte libre avant
    # de donner le JSON final malgré la consigne — on cherche le dernier
    # bloc {...} complet plutôt que d'exiger une réponse 100% JSON pure.
    matches = re.findall(r"\{(?:[^{}]|\{[^{}]*\})*\}", text)
    if matches:
        try:
            return json.loads(matches[-1])
        except json.JSONDecodeError:
            pass

    likely_truncated = len(text) >= max_tokens * 3  # ~3-4 car/token en français
    if likely_truncated:
        raise RuntimeError(
            f"Réponse LLM probablement tronquée (max_tokens={max_tokens}, "
            f"{len(text)} caractères reçus, aucun JSON complet trouvé) — "
            f"texte reçu: {text[:200]!r}"
        )
    raise RuntimeError(f"Aucun JSON exploitable trouvé dans la réponse : {text[:200]!r}")


# ---------------------------------------------------------------------------
# Construction du prompt
# ---------------------------------------------------------------------------

def build_instance_prompt(entity_fm, scenario, hard_constraint=None, exclude_slug=None,
                           zone_hint=None, ancrage_temporel="libre"):
    """hard_constraint, si fourni : {"role": ..., "etat": ...} — contrainte
    dure pour le scénario de référence d'une entité custom.

    zone_hint (fonctionnalité create_entities_and_instances.py, absente
    historiquement de generate_instances.py — désormais disponible aux
    deux appelants) : ancrage géographique suggéré par l'utilisateur.

    ancrage_temporel (ajouté le 8 août 2026, suite au constat que la
    "PRIORITÉ ABSOLUE" aux jalons de la chronologie du scénario l'emporte
    quasi systématiquement sur l'ÉTAT DU MONDE RÉEL dès qu'une origine de
    crise/rupture est évoquée dans la fiche — ce qui est le cas pour la
    quasi-totalité des entités du vault par style d'écriture) :
      - "libre" (par défaut) : comportement inchangé, priorité aux jalons
        du scénario si un jalon correspond clairement au profil.
      - "recent" : inverse la priorité pour CE run — force une origine
        dans les 1-3 prochaines années, ancrée dans l'ÉTAT DU MONDE RÉEL
        plutôt que dans un jalon lointain du scénario. À utiliser quand on
        veut délibérément des entités qui émergent "maintenant".
    """
    sc_ctx = load_scenario_context(scenario)
    var_states = load_variables_states(scenario)
    available_instances = load_instances_in_scenario(scenario, exclude_slug=exclude_slug)

    vars_context = ""
    for var in entity_fm.get("variables_potentielles", []) or []:
        if var in var_states:
            vars_context += f"\n- **{var}** dans {scenario} : {var_states[var]}"

    if available_instances:
        instances_list = "\n".join(
            f"- {slug} — {nom}" for slug, nom in sorted(available_instances.items())
        )
    else:
        instances_list = "(aucune autre instance encore créée dans ce scénario)"

    zone_hint_block = ""
    if zone_hint:
        zone_hint_block = f"""
## ANCRAGE GÉOGRAPHIQUE (hint utilisateur)
L'utilisateur souhaite ancrer cette entité dans la zone : **{zone_hint}**
Tiens-en compte pour la localisation, les responsabilités et le contexte
narratif — mais reste cohérent avec la logique du scénario.
"""

    constraint_block = ""
    role_etat_instruction = ""
    if hard_constraint:
        constraint_block = f"""
## CONTRAINTES DURES POUR CE SCÉNARIO (ne pas reformuler, ne pas contredire)
- Rôle dans ce scénario : {hard_constraint['role']}
- État temporel dans ce scénario : {hard_constraint['etat']}

Ces deux éléments sont déjà fixés par l'utilisateur. Construis le reste
de l'instance (description journalistique, responsabilités, relations,
tensions...) en cohérence stricte avec eux — ne les modifie pas, ne les
édulcore pas, ne les contredis pas.
"""
        role_etat_instruction = f"""
Réponds en JSON, avec "role_dans_scenario" reprenant le rôle ci-dessus
(tu peux le développer en 3-5 lignes mais sans en changer le sens) et
"etat_temporel" devant valoir exactement "{hard_constraint['etat']}".
"""

    if ancrage_temporel == "recent":
        chronologie_block = """CONSIGNE CHRONOLOGIE — ANCRAGE RÉCENT FORCÉ (mode "recent", 8 août 2026) :
Cette instance DOIT émerger dans les 1 à 3 prochaines années (annee_debut
entre 2026 et 2029) — age_historique DOIT être "émergent" et generation
DOIT être "transition". N'utilise PAS la CHRONOLOGIE RÉELLE DU SCÉNARIO
ci-dessus pour choisir annee_debut, même si un jalon semble correspondre —
ignore délibérément cette source pour cette instance précise. À la place,
l'origine de cette instance DOIT être un prolongement direct et plausible
de la section ÉTAT DU MONDE RÉEL ci-dessus : son role_dans_scenario et sa
description doivent se lire comme émergeant de la situation réelle
d'aujourd'hui, pas d'une rupture ou crise future du scénario. N'invente
aucun événement fondateur lointain, aucune rupture historique différée —
si tu ressens le besoin d'écrire "fondée dans le sillage de..." ou "née de
la crise de...", assure-toi que cette crise est déjà engagée ou clairement
amorcée dans l'ÉTAT DU MONDE RÉEL, pas une projection future du scénario.
CONTRAINTE DE MATURITÉ (ajoutée le 8 août 2026, suite à un test réel où le
texte décrivait une institution déjà pleinement consolidée malgré une
origine forcée à 2027) : role_dans_scenario ET description_journalistique
DOIVENT rester cohérents avec une origine récente et un statut "émergent" —
même décrite depuis 2098, cette instance doit se lire comme une réponse
encore en cours de structuration, pas comme un appareil institutionnel
déjà abouti. Évite : un réseau d'alliances déjà large et bien établi, une
symbolique/emblème historique daté ("depuis 20XX"), des systèmes internes
sophistiqués déjà généralisés (badges, scores calculés, protocoles
formalisés), ou une portée géographique disproportionnée (plusieurs
continents/corridors simultanément). Privilégie une portée plus modeste,
un fonctionnement encore expérimental ou local, une légitimité disputée
plutôt qu'acquise — la maturité, si elle existe, doit être racontée comme
récente et fragile, pas comme un acquis ancien.
Renseigne également le champ "ancrage_reel" (obligatoire dans ce mode) :
une phrase courte et concrète nommant explicitement l'organisme/mouvement/
tendance réel(le) de l'ÉTAT DU MONDE RÉEL ci-dessus dont cette instance
descend ou s'inspire directement.
annee_fin reste null sauf raison narrative explicite."""
    else:
        chronologie_block = """CONSIGNE CHRONOLOGIE (ajoutée le 7 août 2026 — audit point 1.2 du backlog) :
annee_debut DOIT être une année cohérente avec age_historique et generation
que tu choisis toi-même ci-dessous, PAS une valeur par défaut. Une entité
"émergente"/"transition" peut légitimement démarrer proche de 2026 ; une
entité "résiduelle"/"post-effondrement" ou "mythifiée" doit avoir un
annee_debut nettement antérieur à 2098 (reflétant son ancienneté narrative,
typiquement des décennies plus tôt) ; une entité "ascendante"/"dominante"
se situe généralement entre les deux.
ATTENTION — CONFUSION À ÉVITER (ajoutée le 8 août 2026, après un échec réel
sur une fiche existante proposée à annee_debut=2002) : annee_debut décrit
TOUJOURS quand LA VERSION FICTIVE de cette instance, telle que décrite ici,
est née dans le scénario — jamais la date de fondation d'une organisation
RÉELLE du monde d'aujourd'hui dont le nom ou le rôle pourrait s'en
inspirer. Si le nom de l'instance rappelle une organisation réelle
existante, ignore complètement sa date de fondation réelle — seule compte
la date où LA FICTION a commencé, obligatoirement entre 2026 et 2098.
PRIORITÉ ABSOLUE : si un jalon de la
CHRONOLOGIE RÉELLE ci-dessus correspond clairement à la naissance/l'origine
de cette instance (rupture, crise, bascule cohérente avec le rôle que tu lui
donnes), utilise l'année de CE jalon plutôt qu'une estimation libre — c'est
la source la plus fiable disponible. Sinon, choisis une année précise entre
2026 et 2098 qui raconte une histoire cohérente avec l'âge que tu attribues
à l'entité. annee_fin reste null sauf si tu as une raison narrative explicite
de dater la fin de cette relation/existence.
CONSIGNE ANCRAGE RÉEL (resserrée le 8 août 2026 après test réel — la bande
graduée jusqu'à 50 ans exigeait un ancrage réel même pour des dates déjà
bien justifiées par un jalon de scénario construit sérieusement, ce qui
créait une friction inutile sans gain de qualité réel) :
  - 2026-2036 (0-10 ans) : DOIT être un prolongement direct et nommé d'un
    organisme, mouvement, technologie ou tendance CITÉ EXPLICITEMENT dans
    l'ÉTAT DU MONDE RÉEL ci-dessus — ancrage_reel OBLIGATOIRE.
  - 2036-2098 (10 ans et plus) : l'ÉTAT DU MONDE RÉEL sert de toile de
    fond, pas de contrainte directe — ancrage_reel OPTIONNEL. Si tu
    identifies un lien plausible même lointain, mentionne-le ; sinon,
    laisse le champ à null plutôt que d'en inventer un.

Renseigne le champ "ancrage_reel" : une phrase courte et concrète nommant
explicitement l'organisme/mouvement/tendance réel(le) de l'ÉTAT DU MONDE
RÉEL dont cette instance descend ou s'inspire directement (ex. "évolution
du mouvement Gen Z 2025-2026 documenté dans valeurs_culture_tempo_
sociale"). CE CHAMP EST OBLIGATOIRE si annee_debut < 2036 — laisse-le à
null si annee_debut >= 2036 et qu'aucun lien réel pertinent ne te vient
naturellement.
ATTENTION — CONFUSION FRÉQUENTE À ÉVITER : "ancrage_reel" doit citer un
élément de la section ÉTAT DU MONDE RÉEL (des faits du monde d'aujourd'hui,
2026, obtenus par recherche web) — JAMAIS un jalon de la CHRONOLOGIE RÉELLE
DU SCÉNARIO (qui, malgré son nom, est un événement FICTIF propre à ce
scénario, pas un fait du monde réel). Si tu utilises un jalon du scénario
pour choisir annee_debut, ne le recopie pas dans ancrage_reel — cherche
plutôt, dans l'ÉTAT DU MONDE RÉEL, un fait authentique de 2026 en lien avec
le rôle de cette instance."""

    prompt = f"""Tu es un expert en worldbuilding pour Ourrassol 2098.

Génère l'instance de l'entité "{entity_fm['name']}" dans le scénario "{scenario}".

## ENTITÉ ARCHÉTYPE
- Nom : {entity_fm['name']}
- Catégorie : {entity_fm.get('category', '')}
- Description : {entity_fm.get('description', '')}
- Tension fondamentale : {entity_fm.get('tension_fondamentale', '')}
{constraint_block}
## SCÉNARIO {scenario.upper()}
- État : {sc_ctx['state_of_system']} | Tension : {sc_ctx['tension_level']}/5 | Trajectoire : {sc_ctx['trajectory']}
- Régime : {sc_ctx['political_regime']} | Vitesse : {sc_ctx['transformation_speed']}
- Variables dominantes : {', '.join(sc_ctx['dominant_variables'])}
{f"- Contexte : {sc_ctx['summary']}" if sc_ctx['summary'] else ""}

{zone_hint_block}## ÉTAT DES VARIABLES INFLUENCÉES DANS CE SCÉNARIO
{vars_context if vars_context else "Non défini"}

## INSTANCES DÉJÀ EXISTANTES DANS CE SCÉNARIO (pour alliances/oppositions)
{instances_list}

## CHRONOLOGIE RÉELLE DU SCÉNARIO {scenario} (jalons datés majeurs/structurants)
{load_scenario_timeline_summary(scenario)}

## ÉTAT DU MONDE RÉEL (référence factuelle, PAS de la fiction)
{load_etat_monde_reel()}

## CONSIGNE

Génère une instance cohérente avec ce scénario. L'instance DOIT refléter
l'état du monde — si le scénario est chaotique, l'institution est
fragmentée ou disparue. Si le scénario est stable, elle peut être
dominante ou mature.

Le nom de l'instance peut être identique à l'entité, une variante, ou
radicalement différent selon le monde — mais il doit rester évocateur
du nom de l'entité archétype.

RÈGLE STRICTE pour "alliances" et "oppositions" : ces champs ne doivent
contenir QUE des slugs exacts pris dans la liste "INSTANCES DÉJÀ
EXISTANTES" ci-dessus (copie le slug tel quel, jamais le nom). N'invente
JAMAIS de nom d'organisation en texte libre. Si aucune instance existante
de la liste ne convient comme allié ou opposant plausible, laisse le
champ en liste vide plutôt que d'inventer un acteur non référencé.

RÈGLE STRICTE pour "impact_local" et "impact_systemique_global" : entiers
sur une échelle de 0 à 5 UNIQUEMENT (0 = négligeable, 5 = maximal/dominant).
Jamais une autre échelle (pas de note sur 10, pas de pourcentage sur 100).
{role_etat_instruction}
{chronologie_block}
Réponds en JSON uniquement :
{{
  "nom": "Nom de l'instance dans ce scénario",
  "type_dans_scenario": "IA|organisation|entreprise|institution|infrastructure|réseau|humain|système|hybride|autre",
  "role_dans_scenario": "Rôle narratif et systémique détaillé (3-5 lignes)",
  "responsabilites": "Actions concrètes exercées dans ce monde (2-3 lignes)",
  "impact_local": 0,
  "impact_systemique_global": 0,
  "variables_influencees": ["variable_1", "variable_2"],
  "zone_geographique": ["locale|urbaine|nationale|régionale|continentale|globale|orbital"],
  "zone_systemique": ["énergie|IA|gouvernance|économie|information|sécurité|infrastructure|société|cyberspace|orbital"],
  "alliances": [],
  "oppositions": [],
  "type_relation_dominante": "coopération|alliance stratégique|dépendance|neutralité|rivalité|conflit|infiltration|symbiose",
  "annee_debut": "<année entre 2026 et 2098, cohérente avec age_historique/generation choisis ci-dessous — voir CONSIGNE CHRONOLOGIE>",
  "ancrage_reel": "<phrase courte nommant l'élément réel dont cette instance descend, OBLIGATOIRE si annee_debut < 2036, sinon null/optionnel>",
  "annee_fin": null,
  "etat_temporel": "actif|disparu|transformé|clandestin|historique|mythifié",
  "age_historique": "émergent|marginal|ascendant|dominant|mature|déclinant|résiduel|mythifié",
  "generation": "pré-crise|transition|post-effondrement|IA-native|forteresse|reconstruction|ère cognitive",
  "description_journalistique": "Comment un journaliste de 2098 décrirait cette entité (4-6 lignes vivantes et concrètes)",
  "signes_distinctifs": "Éléments visuels, symboliques, stylistiques (2-3 lignes)",
  "tensions_narratives": "Conflits, enjeux, trajectoires possibles pour les articles (3-4 lignes)"
}}"""
    return prompt


def _normalize_for_matching(text):
    """Normalise un texte pour la comparaison n-gram : minuscules, retire
    la ponctuation, espace unique entre mots."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_registre_leakage(ancrage_reel_text, min_shingle=6):
    """
    Détecte si ancrage_reel recopie (même reformulé légèrement) un jalon de
    la CHRONOLOGIE RÉELLE DU SCÉNARIO (fictive, malgré son nom) plutôt que
    de citer un fait authentique de l'ÉTAT DU MONDE RÉEL. Ajouté le 8 août
    2026 : la consigne en prose seule ne suffisait pas — testé en
    conditions réelles par David (fix_annee_debut_placeholder.py, fiche
    AMMC), le LLM continuait de recycler le nom du jalon fictif malgré un
    avertissement explicite. Garde-fou mécanique : recherche de séquences
    de 6 mots consécutifs identiques entre ancrage_reel et le registre
    complet — un tel chevauchement est hautement improbable par hasard. Seuil
    relevé de 4 à 6 mots le 8 août 2026 après un faux positif réel : "de
    l'agence internationale" (4 mots) matchait à la fois la vraie AIE (Agence
    Internationale de l'Énergie, citée légitimement depuis l'ÉTAT DU MONDE
    RÉEL) et un jalon fictif totalement différent ("Agence Internationale
    de la Fusion", 2045, registre new_sustainability) — 6 mots réduit ce
    risque de collision sur des tournures administratives génériques.

    min_shingle fixé en dur à 6 mots dans le code (cf. backlog 8 août §4 —
    pourrait devenir un paramètre CLI si un nouveau faux positif/négatif
    apparaît en usage réel, pas nécessaire tant que ça ne se manifeste pas).

    Renvoie la séquence détectée, ou None si aucun chevauchement suspect.
    """
    # Comparaison par TUPLES DE MOTS (pas de sous-chaîne de caractères) —
    # correctif du 8 août 2026 : la version précédente (recherche de
    # sous-chaîne sur texte joint par espaces) produisait un faux positif
    # sur la vraie AIE ("...internationale de l'Énergie") à cause d'un
    # chevauchement de CARACTÈRES avec un jalon fictif sans rapport
    # ("...internationale de la Fusion") — "de l" est un préfixe littéral
    # de "de la", donc matchait à tort même si "l" et "la" sont deux mots
    # différents. La comparaison par tuples élimine structurellement ce
    # type de faux positif : deux séquences ne matchent que si TOUS leurs
    # mots sont identiques un par un, jamais par chevauchement partiel.
    registre_words = _normalize_for_matching(_read_registre_text()).split()
    registre_shingles = set()
    for i in range(len(registre_words) - min_shingle + 1):
        registre_shingles.add(tuple(registre_words[i:i + min_shingle]))

    ancrage_words = _normalize_for_matching(ancrage_reel_text).split()
    for i in range(len(ancrage_words) - min_shingle + 1):
        shingle = tuple(ancrage_words[i:i + min_shingle])
        if shingle in registre_shingles:
            return " ".join(shingle)
    return None


# ---------------------------------------------------------------------------
# Validation mécanique
# ---------------------------------------------------------------------------

def validate_instance(data, hard_constraint=None):
    """Version canonique — reprise de create_entities_and_instances.py,
    qui incluait le contrôle de plage [0-5] sur impact_local/impact_
    systemique_global, absent de la version historique de generate_
    instances.py (bug de divergence corrigé par cette factorisation)."""
    issues = []
    required = ["nom", "role_dans_scenario", "description_journalistique"]
    for field in required:
        if not data.get(field):
            issues.append(f"Champ requis manquant ou vide : '{field}'")

    etat = data.get("etat_temporel", "")
    if etat and etat not in VALID_ETATS:
        issues.append(f"etat_temporel invalide : {etat!r}")

    variables = data.get("variables_influencees") or []
    for v in variables:
        if v not in VALID_VARS:
            issues.append(f"Variable inconnue dans variables_influencees : {v!r}")

    for field in ("impact_local", "impact_systemique_global"):
        val = data.get(field)
        try:
            v = int(val)
            if not (0 <= v <= 5):
                issues.append(f"{field} hors plage [0-5] : {val!r} "
                               f"(échelle attendue 0-5, pas 0-10 ni 0-100)")
        except (TypeError, ValueError):
            issues.append(f"{field} invalide (doit être un entier 0-5) : {val!r}")

    # Plage annee_debut (ajoutée le 8 août 2026, après un cas réel dans
    # fix_annee_debut_placeholder.py où le LLM a confondu la date de
    # fondation RÉELLE d'une organisation existante avec l'origine de sa
    # VERSION FICTIVE dans le scénario).
    try:
        annee_debut_val = int(data.get("annee_debut"))
    except (TypeError, ValueError):
        annee_debut_val = None
    if annee_debut_val is not None and not (2026 <= annee_debut_val <= 2098):
        if annee_debut_val < 2026:
            issues.append(
                f"annee_debut hors plage [2026-2098] : {annee_debut_val!r} — "
                f"probable confusion avec la date de fondation réelle d'une "
                f"organisation existante dont cette instance s'inspire ; "
                f"annee_debut doit décrire l'origine de LA VERSION FICTIVE "
                f"de ce scénario, jamais de l'organisation réelle"
            )
        else:
            issues.append(f"annee_debut hors plage [2026-2098] : {annee_debut_val!r}")

    # Traçabilité graduée (ajoutée le 8 août 2026) : en dessous de 10 ans
    # (annee_debut < 2036, resserré en fin de session le 8 août — était
    # 2076 dans une version antérieure), une justification explicite de
    # continuité avec l'ÉTAT DU MONDE RÉEL est obligatoire.
    try:
        annee_debut_val = int(data.get("annee_debut"))
    except (TypeError, ValueError):
        annee_debut_val = None
    if annee_debut_val is not None:
        ancrage = (data.get("ancrage_reel") or "").strip()
        if annee_debut_val < 2036 and not ancrage:
            issues.append(
                f"ancrage_reel manquant ou vide alors que annee_debut "
                f"({annee_debut_val}) < 2036 — traçabilité avec l'état du "
                f"monde réel requise dans les 10 prochaines années"
            )
        elif ancrage:
            leaked = detect_registre_leakage(ancrage)
            if leaked:
                issues.append(
                    f"ancrage_reel semble recopier un jalon fictif du "
                    f"registre du scénario plutôt qu'un fait authentique "
                    f"de l'état du monde réel (séquence détectée : "
                    f"{leaked!r}) — cite un élément vérifiable de 2026, "
                    f"pas un événement fictif du scénario"
                )

    if hard_constraint:
        if data.get("etat_temporel") != hard_constraint["etat"]:
            issues.append(
                f"etat_temporel ({data.get('etat_temporel')!r}) ne respecte pas "
                f"la contrainte dure ({hard_constraint['etat']!r})"
            )

    return issues


def clean_relations(data, available_instances):
    """Filtre silencieusement les entrées alliances/oppositions qui ne
    sont pas des slugs valides référençant une instance existante du
    même scénario, plutôt que de rejeter toute la fiche. Retourne
    (data nettoyé, liste des entrées filtrées pour log)."""
    dropped = []
    for field in ("alliances", "oppositions"):
        items = data.get(field) or []
        kept = []
        for item in items:
            item_clean = str(item).strip()
            if SLUG_PATTERN.match(item_clean) and item_clean in available_instances:
                kept.append(item_clean)
            else:
                dropped.append((field, item_clean))
        data[field] = kept
    return data, dropped


# ---------------------------------------------------------------------------
# Écriture de la fiche instance
# ---------------------------------------------------------------------------

def write_instance_file(entity_fm, scenario, instance_data):
    """NOTE (chantier trajectoire, à venir) : c'est CETTE fonction — un
    seul endroit désormais grâce à la factorisation — que la fusion
    etat_temporel+age_historique → trajectoire modifiera. Voir
    SPEC_CHANTIER_TRAJECTOIRE.md §3.4."""
    INSTANCES_DIR.mkdir(parents=True, exist_ok=True)

    slug_entite = entity_fm["slug"]
    slug_instance = f"{slug_entite}_{scenario}"
    filepath = INSTANCES_DIR / f"{slug_instance}.md"

    def yaml_list(lst, indent=2):
        if not lst:
            return ""
        pad = "  " * indent
        return "\n" + "\n".join(f"{pad}- {i}" for i in lst)

    vars_yaml = yaml_list(instance_data.get("variables_influencees", []))
    zones_geo = yaml_list(instance_data.get("zone_geographique", []))
    zones_sys = yaml_list(instance_data.get("zone_systemique", []))
    alliances = yaml_list(instance_data.get("alliances", []))
    oppositions = yaml_list(instance_data.get("oppositions", []))
    annee_fin_str = instance_data.get("annee_fin")
    annee_fin_str = "" if annee_fin_str is None else str(annee_fin_str)

    # Sécurise annee_debut (ajouté le 7 août 2026, audit point 1.2) : le
    # prompt demande désormais au LLM de choisir l'année plutôt que de
    # recopier un exemple fixe -- si la réponse n'est malgré tout pas un
    # entier exploitable dans la plage 2026-2098, retombe sur 2026 comme
    # avant plutôt que d'écrire une valeur invalide dans le frontmatter.
    try:
        annee_debut_val = int(instance_data.get("annee_debut", 2026))
        if not (2026 <= annee_debut_val <= 2098):
            annee_debut_val = 2026
    except (TypeError, ValueError):
        annee_debut_val = 2026

    content = """---
name: {nom}
type: instance
slug: {slug_instance}
entite: {slug_entite}
scenario: {scenario}

type_dans_scenario: {type_dans_scenario}

role_dans_scenario: >
  {role_dans_scenario}

responsabilites: >
  {responsabilites}

impact_local: {impact_local}
impact_systemique_global: {impact_systemique_global}

variables_influencees:{vars_yaml}

zone_geographique:{zones_geo}

zone_systemique:{zones_sys}

alliances:{alliances}

oppositions:{oppositions}

type_relation_dominante: {type_relation_dominante}

annee_debut: {annee_debut}
annee_fin: {annee_fin}

etat_temporel: {etat_temporel}
age_historique: {age_historique}
generation: {generation}

injection:
  type: canonique
  annee_injection:
  contexte_injection:
  impact_sur_variables:
  propagation:
    via_matrice: false

description_journalistique: >
  {description_journalistique}

signes_distinctifs: >
  {signes_distinctifs}

tensions_narratives: >
  {tensions_narratives}

date_creation: {date_creation}
---

# {nom}

## Rôle dans [[{scenario}]]
{role_dans_scenario}

## Responsabilités
{responsabilites}

## Variables influencées
{vars_md}

## Relations
**Alliés** : {alliances_md}
**Opposants** : {oppositions_md}

## Description journalistique
{description_journalistique}

## Tensions narratives
{tensions_narratives}
""".format(
        nom=instance_data.get("nom", entity_fm["name"]),
        slug_instance=slug_instance,
        slug_entite=slug_entite,
        scenario=scenario,
        type_dans_scenario=instance_data.get("type_dans_scenario", ""),
        role_dans_scenario=instance_data.get("role_dans_scenario", "").replace("\n", " "),
        responsabilites=instance_data.get("responsabilites", "").replace("\n", " "),
        impact_local=instance_data.get("impact_local", 0),
        impact_systemique_global=instance_data.get("impact_systemique_global", 0),
        vars_yaml=vars_yaml,
        zones_geo=zones_geo,
        zones_sys=zones_sys,
        alliances=alliances,
        oppositions=oppositions,
        type_relation_dominante=instance_data.get("type_relation_dominante", "neutralité"),
        annee_debut=annee_debut_val,
        annee_fin=annee_fin_str,
        etat_temporel=instance_data.get("etat_temporel", "actif"),
        age_historique=instance_data.get("age_historique", "mature"),
        generation=instance_data.get("generation", "transition"),
        description_journalistique=instance_data.get("description_journalistique", "").replace("\n", " "),
        signes_distinctifs=instance_data.get("signes_distinctifs", "").replace("\n", " "),
        tensions_narratives=instance_data.get("tensions_narratives", "").replace("\n", " "),
        date_creation=datetime.now().strftime("%Y-%m-%d"),
        vars_md="\n".join(f"- [[{v}]]" for v in instance_data.get("variables_influencees", [])) or "_aucune_",
        alliances_md=", ".join(f"[[{a}]]" for a in instance_data.get("alliances", [])) or "_aucun défini_",
        oppositions_md=", ".join(f"[[{o}]]" for o in instance_data.get("oppositions", [])) or "_aucun défini_",
    )

    filepath.write_text(content, encoding="utf-8")
    return filepath


# ---------------------------------------------------------------------------
# Pipeline : une entité × un scénario
# ---------------------------------------------------------------------------

def process_entity_scenario(client, entity_fm, scenario, force=False, dry_run=False,
                             ancrage_temporel="libre", log_prefix="  →"):
    """Génère UNE instance pour UNE entité dans UN scénario. Retourne un
    statut sans jamais lever d'exception non gérée — les échecs sont
    capturés ici pour ne pas interrompre la chaîne (résilience voulue).

    zone_hint n'est PAS un paramètre — comme dans le code d'origine
    (create_entities_and_instances.py), il est lu directement depuis
    entity_fm.get("zone_hint") : présent en mémoire juste après une
    création en mode custom (jamais persisté sur disque par write_entity_
    file), donc naturellement absent — et sans effet, pas une régression —
    quand cette fonction est appelée depuis generate_instances.py sur une
    entité relue du disque.

    log_prefix : les deux scripts appelants avaient un formatage de log
    légèrement différent (generate_instances.py affichait le slug entité
    dans la ligne, create_entities_and_instances.py l'affichait une fois
    au niveau de l'entité parente et indentait juste le scénario ici) —
    paramétré plutôt que figé, chaque appelant garde son style d'affichage
    sans dupliquer la fonction.
    """
    slug_entite = entity_fm["slug"]

    if instance_exists(slug_entite, scenario) and not force:
        print(f"{log_prefix} {scenario}... (déjà existant)")
        return {"status": "skipped"}

    hard_constraint = None
    if entity_fm.get("scenario_ref") == scenario:
        hard_constraint = {
            "role": entity_fm.get("role_ref", ""),
            "etat": entity_fm.get("etat_ref", ""),
            # est_clandestin optionnel (None/True/False) — ajouté au
            # schéma le 9 août 2026 en préparation du chantier trajectoire
            # (voir SPEC_CHANTIER_TRAJECTOIRE.md §Question 1) ; mécanisme
            # jamais exercé en pratique à ce jour (0 fiche entité avec
            # scenario_ref/etat_ref renseigné sur le vault actuel), posé
            # par anticipation plutôt que par besoin observé.
            "est_clandestin": entity_fm.get("est_clandestin_ref"),
        }

    print(f"{log_prefix} {scenario}"
          f"{' [CONTRAINTE DURE]' if hard_constraint else ''}"
          f"{' [ANCRAGE RÉCENT]' if ancrage_temporel == 'recent' else ''}...",
          end=" ", flush=True)

    prompt = build_instance_prompt(
        entity_fm, scenario, hard_constraint=hard_constraint,
        exclude_slug=f"{slug_entite}_{scenario}",
        zone_hint=entity_fm.get("zone_hint"),
        ancrage_temporel=ancrage_temporel,
    )
    try:
        instance_data = call_claude_json(
            client, "Tu es un expert en worldbuilding.", prompt,
            max_tokens=INSTANCE_MAX_TOKENS,
        )
    except Exception as e:
        print(f"✗ ({e})")
        return {"status": "error", "error": str(e)}

    issues = validate_instance(instance_data, hard_constraint=hard_constraint)
    if issues:
        print("✗")
        for i in issues:
            print(f"     - {i}")
        return {"status": "needs_review", "issues": issues, "instance_data": instance_data}

    available_instances = load_instances_in_scenario(
        scenario, exclude_slug=f"{slug_entite}_{scenario}"
    )
    instance_data, dropped_relations = clean_relations(instance_data, available_instances)
    if dropped_relations:
        for field, value in dropped_relations:
            print(f"\n     ⚠ {field} filtrée (pas un slug d'instance valide) : "
                  f"'{value}'", end="")
        print()

    if not dry_run:
        write_instance_file(entity_fm, scenario, instance_data)
    print("✓")
    if dry_run:
        print(json.dumps(instance_data, ensure_ascii=False, indent=2))
    return {"status": "created", "instance_data": instance_data}
