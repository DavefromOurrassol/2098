#!/usr/bin/env python3
"""
trace_injection.py — Ourrassol 2098
=====================================

Outil de traçabilité : pour une instance, un événement ou un signal
donné (identifié par son slug), reconstitue et assemble en une seule
vue tout ce que le pipeline sait de son parcours — origine, propagation
dans l'espace (scénarios/zones), dans le temps (fictif et réel), et
dans le réseau causal/relationnel (variables influencées, acteurs,
alliances/oppositions) — plus, en aval, les articles qui le mentionnent
une fois publié.

PROBLÈME TRAITÉ
----------------
Chaque script du pipeline écrit sa propre trace dans son coin
(processed.yaml par pipeline custom, "## Notes" seulement pour
enrich_minimal, rien pour la propagation narrative ou l'usage aval en
article). Aucune vue transversale par slug n'existait avant ce script.

Diagnostic pur, lecture seule — aucune écriture, aucun appel LLM.
Type auto-détecté depuis le slug fourni (cherche dans entites/,
evenements/, signaux_custom/ dans cet ordre) ; peut être forcé avec
--type si un slug existe dans plusieurs catégories par coïncidence.

USAGE
-----
    python3 trace_injection.py --slug <slug>
    python3 trace_injection.py --slug <slug> --type instance|evenement|signal
    python3 trace_injection.py --slug <slug> --json                # stdout JSON seul
    python3 trace_injection.py --slug <slug> --report               # écrit aussi un .md
    python3 trace_injection.py --slug <slug> --skip-articles         # saute le scan aval (plus rapide)
    python3 trace_injection.py --list                                # liste les slugs disponibles
    python3 trace_injection.py --list --type evenement                # ... filtrés par type
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent

ENTITES_DIR          = VAULT_ROOT / "entites"
INSTANCES_DIR        = VAULT_ROOT / "instances"
EVENEMENTS_DIR        = VAULT_ROOT / "evenements"
EVENT_INSTANCES_DIR  = VAULT_ROOT / "event_instances"
SIGNAUX_CUSTOM_DIR   = VAULT_ROOT / "signaux_custom"
ARTICLES_DIR         = VAULT_ROOT / "articles"
VARIABLES_DIR        = VAULT_ROOT / "variables"
GEO_DIR              = VAULT_ROOT / "geographie"

ENTITES_CUSTOM_DIR    = VAULT_ROOT / "entites_custom"
EVENEMENTS_CUSTOM_DIR = VAULT_ROOT / "evenements_custom"

SCENARIOS = [
    "breakdown", "fortress_world", "new_sustainability",
    "eco_communalism", "policy_reform", "reference",
]


def _lister_slugs(type_filtre: str = None) -> dict:
    """Liste les slugs disponibles par type -- pour --list en CLI, et pour
    garder une seule source de vérité avec les fonctions de scan côté GUI
    (app.py duplique volontairement cette logique en Python pur, sans
    import croisé generator/ <-> gui/, même principe que le reste du
    pipeline)."""
    resultat = {}
    if not type_filtre or type_filtre == "instance":
        resultat["instance"] = sorted(p.stem for p in ENTITES_DIR.glob("*.md")) if ENTITES_DIR.exists() else []
    if not type_filtre or type_filtre == "evenement":
        resultat["evenement"] = sorted(p.stem for p in EVENEMENTS_DIR.glob("*.md")) if EVENEMENTS_DIR.exists() else []
    if not type_filtre or type_filtre == "signal":
        resultat["signal"] = sorted(p.stem for p in SIGNAUX_CUSTOM_DIR.glob("*.md")) if SIGNAUX_CUSTOM_DIR.exists() else []
    return resultat


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _read_frontmatter(path: Path) -> tuple:
    """Retourne (frontmatter dict, body str). Tolérant : ne lève jamais,
    retourne ({}, '') si le fichier est illisible ou mal formé -- un
    outil de traçabilité ne doit jamais planter sur une fiche abîmée,
    juste signaler un trou dans la trace."""
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception:
        return {}, ""
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, parts[2]


def _load_yaml_list(path: Path, key: str) -> list:
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    return data.get(key) or []


def _resoudre_slug_entite(slug: str) -> str:
    """
    Tolère qu'on lui passe un slug d'INSTANCE (entité + suffixe scénario,
    ex. 'xxx_reference') plutôt qu'un slug d'ENTITÉ -- cas réel rencontré
    le 2 août 2026 : le menu déroulant du GUI peut retomber sur son
    fallback instances/*.md (si _entities_list.json est introuvable côté
    _scan_entity_slugs() dans app.py), qui liste des slugs d'instances,
    pas d'entités.

    Retourne le vrai slug d'entité si résolu, sinon le slug donné tel
    quel (laisse _detecter_type()/tracer_instance() échouer normalement
    si ce n'est vraiment pas trouvable).
    """
    if (ENTITES_DIR / f"{slug}.md").exists():
        return slug  # déjà un slug d'entité correct

    # Le slug donné est peut-être directement un fichier instance --
    # on lit son champ `entite:` plutôt que de deviner en tronquant le
    # suffixe scénario (plus fiable : le nom de l'entité peut lui-même
    # contenir un underscore suivi d'un mot qui ressemble à un scénario).
    # On fait confiance à ce champ directement (pas de re-vérification de
    # l'existence d'entites/{entite}.md) : le champ `entite:` de la fiche
    # instance fait foi, même si le dossier entites/ n'est pas accessible
    # dans l'environnement où tourne ce diagnostic.
    if (INSTANCES_DIR / f"{slug}.md").exists():
        fm, _ = _read_frontmatter(INSTANCES_DIR / f"{slug}.md")
        entite = fm.get("entite")
        if entite:
            return entite

    # Dernier recours : essayer de tronquer un suffixe _{scenario} connu.
    for sc in SCENARIOS:
        suffixe = f"_{sc}"
        if slug.endswith(suffixe):
            candidat = slug[: -len(suffixe)]
            if (ENTITES_DIR / f"{candidat}.md").exists():
                return candidat

    return slug


def _resoudre_slug_evenement(slug: str) -> str:
    """Même principe que _resoudre_slug_entite() ci-dessus, pour le cas où
    un slug d'event_instance (archétype + suffixe scénario) serait passé
    à la place du slug d'archétype attendu."""
    if (EVENEMENTS_DIR / f"{slug}.md").exists():
        return slug

    if (EVENT_INSTANCES_DIR / f"{slug}.md").exists():
        fm, _ = _read_frontmatter(EVENT_INSTANCES_DIR / f"{slug}.md")
        archetype = fm.get("archetype")
        if archetype:
            return archetype

    for sc in SCENARIOS:
        suffixe = f"_{sc}"
        if slug.endswith(suffixe):
            candidat = slug[: -len(suffixe)]
            if (EVENEMENTS_DIR / f"{candidat}.md").exists():
                return candidat

    return slug


_CACHE_ZONES_PAR_SCENARIO = {}   # scenario -> {zone_slug: {nom, niveau, ...}}
_CACHE_LABELS_VARIABLES = {}     # variable_slug -> label ou None


def _lire_zones_scenario(scenario: str) -> dict:
    """Lit geographie/{scenario}.md une seule fois par scénario (mis en
    cache), indexe les zones par slug. Ajouté le 2 août 2026 -- avant ça,
    trace_injection.py n'ouvrait jamais geographie/, se contentant du
    slug brut déjà présent dans localisation.zone des fiches."""
    if scenario in _CACHE_ZONES_PAR_SCENARIO:
        return _CACHE_ZONES_PAR_SCENARIO[scenario]
    index = {}
    geo_file = GEO_DIR / f"{scenario}.md"
    if geo_file.exists():
        fm, _ = _read_frontmatter(geo_file)
        for z in (fm.get("zones") or []):
            if isinstance(z, dict) and z.get("slug"):
                index[z["slug"]] = z
    _CACHE_ZONES_PAR_SCENARIO[scenario] = index
    return index


def _decrire_zone(scenario: str, zone_slug: str) -> str:
    """Retourne 'nom (niveau N)' si la zone est trouvée dans
    geographie/{scenario}.md, sinon le slug brut suivi d'un avertissement
    -- un slug de zone qui ne résout à rien est un signal utile (zone
    supprimée/renommée depuis, ou fiche jamais passée par
    extract_localisation.py correctement)."""
    if not zone_slug:
        return "—"
    zones = _lire_zones_scenario(scenario)
    z = zones.get(zone_slug)
    if not z:
        return f"{zone_slug} (⚠ introuvable dans geographie/{scenario}.md)"
    nom = z.get("nom") or zone_slug
    niveau = z.get("niveau")
    return f"{nom} (niveau {niveau})" if niveau is not None else nom


def _label_variable(slug: str) -> str:
    """Retourne le nom lisible d'une variable si trouvé en frontmatter de
    variables/{slug}.md (champ 'name' ou 'nom'), sinon le slug tel quel."""
    if slug in _CACHE_LABELS_VARIABLES:
        label = _CACHE_LABELS_VARIABLES[slug]
        return label or slug
    var_path = VARIABLES_DIR / f"{slug}.md"
    label = None
    if var_path.exists():
        fm, _ = _read_frontmatter(var_path)
        label = fm.get("name") or fm.get("nom")
    _CACHE_LABELS_VARIABLES[slug] = label
    return label or slug


def _detecter_type(slug: str) -> str:
    """Auto-détection : cherche le slug dans entites/, evenements/,
    signaux_custom/ dans cet ordre. Un signal se reconnaît à
    signaux_custom/{slug}.md (fiche d'audit) ; un événement à
    evenements/{slug}.md (archétype, avant déclinaison par scénario) ;
    une entité à entites/{slug}.md."""
    if (ENTITES_DIR / f"{slug}.md").exists():
        return "instance"
    if (EVENEMENTS_DIR / f"{slug}.md").exists():
        return "evenement"
    if (SIGNAUX_CUSTOM_DIR / f"{slug}.md").exists():
        return "signal"
    return None


# ---------------------------------------------------------------------------
# Origine (commun aux 3 types -- cherche dans processed.yaml/needs_review.yaml
# du pipeline custom concerné)
# ---------------------------------------------------------------------------

def _chercher_origine(slug: str, pipeline_dir: Path) -> dict:
    """Cherche l'entrée d'origine (idée source) dans processed.yaml puis
    needs_review.yaml du pipeline concerné. Le slug recherché dans
    processed.yaml peut être celui de l'idée elle-même ou dérivé --
    matching best-effort sur toute occurrence du slug dans l'entrée
    sérialisée (robuste aux variations de schéma entre pipelines)."""
    for fname, statut in (("processed.yaml", "traité"), ("needs_review.yaml", "en échec")):
        entries = _load_yaml_list(pipeline_dir / fname, fname.split(".")[0])
        for e in entries:
            if not isinstance(e, dict):
                continue
            blob = json.dumps(e, ensure_ascii=False, default=str)
            if slug in blob:
                return {"statut_injection": statut, "entree_brute": e, "fichier_source": str(pipeline_dir / fname)}
    return {"statut_injection": "origine introuvable (idée non trouvée dans processed/needs_review.yaml)", "entree_brute": None, "fichier_source": None}


# ---------------------------------------------------------------------------
# Type INSTANCE (entité + ses instances par scénario)
# ---------------------------------------------------------------------------

def tracer_instance(slug: str) -> dict:
    entite_fm, entite_body = _read_frontmatter(ENTITES_DIR / f"{slug}.md")
    origine = _chercher_origine(slug, ENTITES_CUSTOM_DIR)

    instances = []
    for sc in SCENARIOS:
        path = INSTANCES_DIR / f"{slug}_{sc}.md"
        if not path.exists():
            continue
        fm, body = _read_frontmatter(path)
        marqueur_enrichi = None
        m = re.search(r"Fiche enrichie depuis officialise_minimal le (\d{4}-\d{2}-\d{2})", body)
        if m:
            marqueur_enrichi = m.group(1)
        instances.append({
            "scenario": sc,
            "fichier": str(path),
            "statut": fm.get("statut"),
            "date_enrichissement": marqueur_enrichi,
            "localisation": fm.get("localisation"),
            "role_dans_scenario": fm.get("role_dans_scenario"),
            "description_journalistique": fm.get("description_journalistique"),
            "impact_local": fm.get("impact_local"),
            "impact_systemique_global": fm.get("impact_systemique_global"),
            "variables_influencees": fm.get("variables_influencees") or [],
            "alliances": fm.get("alliances") or [],
            "oppositions": fm.get("oppositions") or [],
        })

    return {
        "slug": slug,
        "type": "instance",
        "nom": entite_fm.get("name") or entite_fm.get("nom"),
        "description": entite_fm.get("description"),
        "origine": origine,
        "entite_scenario_ref": entite_fm.get("scenario_ref"),
        "zone_hint_origine": entite_fm.get("zone_hint"),
        "date_creation_entite": entite_fm.get("date_creation"),
        "scenarios_presents": [i["scenario"] for i in instances],
        "instances": instances,
    }


# ---------------------------------------------------------------------------
# Type EVENEMENT (archétype + instances par scénario)
# ---------------------------------------------------------------------------

def tracer_evenement(slug: str) -> dict:
    archetype_fm, _ = _read_frontmatter(EVENEMENTS_DIR / f"{slug}.md")
    origine = _chercher_origine(slug, EVENEMENTS_CUSTOM_DIR)

    instances = []
    for sc in SCENARIOS:
        path = EVENT_INSTANCES_DIR / f"{slug}_{sc}.md"
        if not path.exists():
            continue
        fm, _ = _read_frontmatter(path)
        instances.append({
            "scenario": sc,
            "fichier": str(path),
            "date_fictive": fm.get("date"),
            "date_creation_reelle": fm.get("date_creation"),
            "impossible_dans_scenario": fm.get("impossible"),
            "localisation": fm.get("localisation"),
            "realisation": fm.get("realisation"),
            "description_journalistique": fm.get("description"),
            "consequences": fm.get("consequences"),
            "impact_sur_variables": fm.get("impact_sur_variables") or [],
            "propagation_via_matrice": (fm.get("propagation") or {}).get("via_matrice"),
            "acteurs_impliques": fm.get("acteurs_impliques") or [],
        })

    return {
        "slug": slug,
        "type": "evenement",
        "nom": archetype_fm.get("name"),
        "description": archetype_fm.get("description"),
        "origine": origine,
        "date_approximative_archetype": archetype_fm.get("date_approximative"),
        "portee": archetype_fm.get("portee"),
        "intensite": archetype_fm.get("intensite"),
        "date_creation_archetype": archetype_fm.get("date_creation"),
        "scenarios_injectes": [i["scenario"] for i in instances],
        "instances": instances,
    }


# ---------------------------------------------------------------------------
# Type SIGNAL (fiche d'audit signaux_custom/ + trace dans variables/)
# ---------------------------------------------------------------------------

def _extraire_section(body: str, titre: str) -> str:
    """Extrait le texte d'une section '## {titre}' jusqu'au prochain '##'
    (ou fin de fichier). Tolérant : retourne '' si la section est absente."""
    m = re.search(rf"##\s*{re.escape(titre)}\s*\n(.*?)(?=\n##\s|\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else ""


def tracer_signal(slug: str) -> dict:
    audit_fm, audit_body = _read_frontmatter(SIGNAUX_CUSTOM_DIR / f"{slug}.md")
    origine = _chercher_origine(slug, SIGNAUX_CUSTOM_DIR)

    # Schéma réel (inject_custom_signals.py::write_custom_fiche) : frontmatter
    # `variables_cibles` (liste, pas un champ singulier), body avec sections
    # "## Idée source" (description d'origine) et "## Trajectoire injectée"
    # (bloc ```yaml signal_to_state``` -- l'évolution par scénario).
    variables_cibles = audit_fm.get("variables_cibles") or []
    if isinstance(variables_cibles, str):
        variables_cibles = [v.strip() for v in variables_cibles.strip("[]").split(",") if v.strip()]

    description = _extraire_section(audit_body, "Idée source")

    # Parsing du bloc signal_to_state -- best-effort, ne doit jamais faire
    # planter le diagnostic si le YAML est légèrement irrégulier.
    evolution_par_scenario = {}
    m_yaml = re.search(r"```yaml\s*\nsignal_to_state:\s*\n(.*?)```", audit_body, re.DOTALL)
    if m_yaml:
        try:
            parsed = yaml.safe_load("signal_to_state:\n" + m_yaml.group(1))
            entries = (parsed or {}).get("signal_to_state") or []
            if entries and isinstance(entries[0], dict):
                evolution_par_scenario = entries[0].get("scenarios") or {}
        except yaml.YAMLError:
            pass

    trace_par_variable = []
    for var in variables_cibles:
        var_path = VARIABLES_DIR / f"{var}.md"
        if not var_path.exists():
            trace_par_variable.append({"variable": var, "fichier": None, "trouve": False})
            continue
        var_txt = var_path.read_text(encoding="utf-8", errors="ignore")
        section_12 = var_txt.split("## 12")[1] if "## 12" in var_txt else ""
        trace_par_variable.append({
            "variable": var,
            "fichier": str(var_path),
            "trouve": True,
            "present_section_12": slug in section_12,
        })

    registre_mention = None
    registre_path = SCRIPT_DIR / "registre_evenements.md"
    if registre_path.exists():
        registre_txt = registre_path.read_text(encoding="utf-8", errors="ignore")
        registre_mention = slug in registre_txt

    return {
        "slug": slug,
        "type": "signal",
        "description": description,
        "variables_cibles": variables_cibles,
        "categorie": audit_fm.get("categorie"),
        "source": audit_fm.get("source"),
        "origine": origine,
        "date_creation": audit_fm.get("date_creation") or audit_fm.get("date"),
        "evolution_par_scenario": evolution_par_scenario,
        "scenarios_presents": sorted(evolution_par_scenario.keys()),
        "trace_par_variable": trace_par_variable,
        "mentionne_dans_registre_evenements": registre_mention,
        "audit_fichier": str(SIGNAUX_CUSTOM_DIR / f"{slug}.md"),
    }


# ---------------------------------------------------------------------------
# Aval : usage réel dans les articles publiés
# ---------------------------------------------------------------------------

def _scan_articles(slug: str, nom: str = None) -> list:
    """Cherche toute mention du slug (wikilink [[slug]] ou texte brut) dans
    articles/*.md. Best-effort -- un faux négatif est possible si le nom
    a été reformulé par le LLM sans garder le slug/nom exact, ce que ce
    scan ne peut pas détecter (pas d'appel LLM ici, diagnostic pur)."""
    if not ARTICLES_DIR.exists():
        return []
    hits = []
    motifs = [slug]
    if nom:
        motifs.append(nom)
    # Récursif depuis le 10 août 2026 (fix save_article dans api.py) : les
    # articles générés en série/manuel sont désormais réellement rangés
    # dans articles/{scenario}/, plus seulement à la racine -- un scan
    # non récursif les aurait rendus invisibles à ce diagnostic.
    for path in sorted(ARTICLES_DIR.glob("**/*.md")):
        try:
            txt = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if any(m and m in txt for m in motifs):
            fm, _ = _read_frontmatter(path)
            hits.append({
                "fichier": str(path),
                "scenario": fm.get("scenario"),
                "date_publication": fm.get("date_publication") or fm.get("date"),
                "titre": fm.get("titre") or fm.get("name"),
            })
    return hits


# ---------------------------------------------------------------------------
# Rendu markdown
# ---------------------------------------------------------------------------

def _textes_proches(a: str, b: str, seuil: float = 0.6) -> bool:
    """Détecte une redondance entre deux textes sans exiger l'identité
    stricte -- le descriptif final reformule/étoffe presque toujours
    l'idée d'origine, ils ne sont jamais mot pour mot identiques. On
    compare sur un préfixe commun (150 premiers caractères de chaque,
    la partie la plus susceptible de se recouper) avec SequenceMatcher,
    tolérant aux différences de ponctuation/accents introduites par le
    LLM lors de la génération de l'archétype."""
    if not a or not b:
        return False
    from difflib import SequenceMatcher
    a_, b_ = a[:150].lower(), b[:150].lower()
    return SequenceMatcher(None, a_, b_).ratio() >= seuil


def _formater_liste_slugs(slugs: list, scenario: str = None, max_n: int = 5) -> str:
    """Rend une liste de slugs lisible : retire le suffixe _{scenario} de
    chaque slug (fourni explicitement, ou détecté automatiquement si TOUS
    les slugs de la liste partagent le même suffixe parmi SCENARIOS --
    cas d'une entité présente dans un seul scénario, ex. alliances/
    oppositions agrégées "tous scénarios confondus" qui n'en couvrent en
    réalité qu'un seul), puis remplace les underscores par des espaces et
    met en majuscule chaque mot pour un rendu lisible plutôt que du
    snake_case brut. Tronque au-delà de max_n avec un compteur plutôt que
    de tout aligner sur une seule ligne illisible.

    Corrigé le 11 août 2026 (retour de David sur un exemple réel où une
    liste de 20+ slugs bruts, tous suffixés "_eco_communalism" à
    l'identique et sans aucune mise en forme, était quasiment illisible).
    """
    if not slugs:
        return "—"
    suffixe = scenario
    if suffixe is None:
        # Détection auto : un seul suffixe scénario partagé par tous ?
        for sc in SCENARIOS:
            if all(s.endswith(f"_{sc}") for s in slugs):
                suffixe = sc
                break
    nettoyes = []
    for s in slugs:
        if suffixe and s.endswith(f"_{suffixe}"):
            s = s[: -(len(suffixe) + 1)]
        nettoyes.append(s.replace("_", " ").strip().capitalize())
    if len(nettoyes) <= max_n:
        return ", ".join(nettoyes)
    reste = len(nettoyes) - max_n
    return ", ".join(nettoyes[:max_n]) + f", et {reste} autre(s)"


def _rendre_markdown(trace: dict) -> str:
    # Libellés lisibles pour le type technique (instance/evenement/signal),
    # utilisés uniquement pour l'affichage -- corrigé le 11 août 2026 suite
    # à un retour de David sur la clarté générale de cette sortie.
    TYPE_LABELS = {"instance": "entité", "evenement": "événement", "signal": "signal"}
    type_label = TYPE_LABELS.get(trace["type"], trace["type"])
    lines = [
        f"# Traçabilité — `{trace['slug']}` ({type_label})",
        "",
        f"*Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## 1. Origine",
        "",
    ]
    origine = trace.get("origine") or {}
    # Reformulation en langage clair du statut brut de _chercher_origine()
    # (valeur JSON/API inchangée pour ne rien casser en aval -- seule cette
    # phrase d'affichage change).
    statut_brut = origine.get("statut_injection") or ""
    if statut_brut == "traité":
        lines.append("- **Origine** : l'idée de départ à l'origine de cette fiche a été retrouvée.")
    elif statut_brut == "en échec":
        lines.append("- **Origine** : l'idée de départ a été retrouvée, mais sa création avait initialement échoué avant d'être reprise.")
    else:
        lines.append("- **Origine** : non retrouvée — l'idée qui a mené à la création de cette fiche n'a pas pu être identifiée (probablement une fiche ancienne, créée avant la mise en place du suivi).")
    if origine.get("fichier_source"):
        lines.append(f"- **Détail technique** : `{origine['fichier_source']}`")
    entree = origine.get("entree_brute")
    description_origine = None
    if entree:
        idea = entree.get("idea") if isinstance(entree, dict) else None
        if isinstance(idea, dict):
            lines.append(f"- **Source de l'idée** : {idea.get('source', '?')}")
            description_origine = idea.get("description")
            description_finale = trace.get("description") or ""
            if description_origine and not _textes_proches(description_origine, description_finale):
                # Affichée seulement si elle apporte quelque chose de différent
                # du §2 -- sinon redondant, l'idée d'origine et le descriptif
                # final se recoupent presque toujours mot pour mot.
                lines.append(f"- **Description d'origine** : {description_origine.strip()}")
            elif description_origine:
                lines.append("- **Description d'origine** : _quasi identique au Descriptif ci-dessous (§2), non répétée._")

    # --- Section 2 : Descriptif -------------------------------------------------
    lines += ["", "## 2. Descriptif", ""]
    nom = trace.get("nom")
    if nom:
        lines.append(f"**{nom}**")
        lines.append("")
    description = trace.get("description")
    if description:
        lines.append(description)
    else:
        lines.append("_Pas de description archétypale trouvée (fiche minimale, jamais enrichie ?)._")

    # --- Section 3 : Évolution dans le temps et l'espace -------------------------
    lines += ["", "## 3. Évolution dans le temps et l'espace", ""]

    if trace["type"] == "instance":
        if trace.get("entite_scenario_ref"):
            lines.append(f"- **Créée en mode custom, contrainte au scénario** : {trace['entite_scenario_ref']}")
        if trace.get("zone_hint_origine"):
            lines.append(f"- **Ancrage géographique souhaité à la création** : {trace['zone_hint_origine']}")
        lines.append(f"- **Présente dans {len(trace['instances'])}/6 scénarios** : {', '.join(trace['scenarios_presents']) or '(aucun)'}")
        lines.append("")
        for i in trace["instances"]:
            loc = (i.get("localisation") or {}).get("zone") if i.get("localisation") else None
            zone_desc = _decrire_zone(i["scenario"], loc) if loc else "—"
            lines.append(f"### {i['scenario']}")
            impact_l = i.get("impact_local")
            impact_g = i.get("impact_systemique_global")
            impact_l_str = f"{impact_l}/5" if impact_l is not None else "—"
            impact_g_str = f"{impact_g}/5" if impact_g is not None else "—"
            lines.append(f"- Zone : {zone_desc} · Impact local : {impact_l_str} · Impact global : {impact_g_str} · Détails complétés par l'IA le : {i.get('date_enrichissement') or '—'}")
            if i.get("role_dans_scenario"):
                lines.append(f"- **Rôle** : {i['role_dans_scenario'].strip()}")
            lines.append("")

        toutes_vars = sorted({v for i in trace["instances"] for v in i.get("variables_influencees", [])})
        if toutes_vars:
            vars_labels = [f"{_label_variable(v)} (`{v}`)" if _label_variable(v) != v else v for v in toutes_vars]
            lines.append(f"**Variables systémiques influencées (tous scénarios confondus)** : {', '.join(vars_labels)}")
        toutes_alliances = sorted({a for i in trace["instances"] for a in i.get("alliances", [])})
        toutes_oppositions = sorted({a for i in trace["instances"] for a in i.get("oppositions", [])})
        if toutes_alliances:
            lines.append(f"**Alliances (réseau relationnel)** : {_formater_liste_slugs(toutes_alliances, max_n=8)}")
        if toutes_oppositions:
            lines.append(f"**Oppositions (réseau relationnel)** : {_formater_liste_slugs(toutes_oppositions, max_n=8)}")

    elif trace["type"] == "evenement":
        lines.append(f"- **Date fictive (archétype)** : {trace.get('date_approximative_archetype')}")
        lines.append(f"- **Portée** : {trace.get('portee')} · **Intensité** : {trace.get('intensite')}")
        lines.append(f"- **Injecté dans {len(trace['instances'])}/6 scénarios** : {', '.join(trace['scenarios_injectes']) or '(aucun)'}")
        lines.append("")
        for i in trace["instances"]:
            loc = (i.get("localisation") or {}).get("zone") if i.get("localisation") else None
            zone_desc = _decrire_zone(i["scenario"], loc) if loc else "—"
            acteurs = _formater_liste_slugs(i.get("acteurs_impliques") or [], scenario=i["scenario"])
            lines.append(f"### {i['scenario']} — {i.get('date_fictive') or 'date non précisée'}")
            lines.append(f"- Zone : {zone_desc} · Impossible dans ce scénario : {i.get('impossible_dans_scenario')} · Acteurs : {acteurs}")
            if i.get("realisation"):
                lines.append(f"- **Réalisation** : {i['realisation'].strip()}")
            lines.append("")

        toutes_vars = sorted({imp.get("variable") for i in trace["instances"] for imp in i.get("impact_sur_variables", []) if isinstance(imp, dict) and imp.get("variable")})
        if toutes_vars:
            vars_labels = [f"{_label_variable(v)} (`{v}`)" if _label_variable(v) != v else v for v in toutes_vars]
            lines.append(f"**Variables systémiques impactées (tous scénarios confondus)** : {', '.join(vars_labels)}")

    elif trace["type"] == "signal":
        vc = trace.get('variables_cibles') or []
        vc_labels = [f"{_label_variable(v)} (`{v}`)" if _label_variable(v) != v else v for v in vc]
        lines.append(f"- **Variables cibles** : {', '.join(vc_labels) or '—'}")
        lines.append(f"- **Catégorie** : {trace.get('categorie')} · **Source** : {trace.get('source')}")
        lines.append(f"- **Date de création** : {trace.get('date_creation')}")
        lines.append(f"- **Mentionné dans `registre_evenements.md`** : {trace.get('mentionne_dans_registre_evenements')}")
        for tv in trace.get("trace_par_variable") or []:
            statut_v = "présent en section 12" if tv.get("present_section_12") else ("trouvé, mais pas repéré en section 12" if tv.get("trouve") else "fichier introuvable")
            lines.append(f"- Variable `{tv['variable']}` : {statut_v}")
        lines.append("")
        evolution = trace.get("evolution_par_scenario") or {}
        if evolution:
            lines.append("**Un signal agit directement sur une variable systémique : potentiellement les 6 scénarios à la fois, chacun avec sa propre trajectoire :**")
            lines.append("")
            for sc in SCENARIOS:
                ev = evolution.get(sc)
                if not ev or not isinstance(ev, dict):
                    continue
                lines.append(f"### {sc}")
                if ev.get("date_bascule"):
                    lines.append(f"- Date de bascule : {ev['date_bascule']}")
                if ev.get("evenement_cle"):
                    lines.append(f"- Événement clé : {ev['evenement_cle']}")
                if ev.get("evolution"):
                    lines.append(f"- **Évolution** : {ev['evolution']}")
                lines.append("")
        else:
            lines.append("_Bloc `signal_to_state` non trouvé ou non parsable dans la fiche d'audit -- évolution par scénario indisponible._")

    if "articles_mentionnant" in trace:
        lines += ["", "## 4. Usage dans les articles déjà publiés", ""]
        articles = trace["articles_mentionnant"]
        if not articles:
            lines.append("_Aucune mention trouvée dans `articles/*.md` (scan texte brut, best-effort — un article peut mentionner l'entité sous une formulation différente sans que ce scan la détecte)._")
        else:
            lines.append(f"**{len(articles)} article(s) trouvé(s) :**")
            lines.append("")
            lines.append("| Fichier | Scénario | Date publication | Titre |")
            lines.append("|---|---|---|---|")
            for a in articles:
                lines.append(f"| `{Path(a['fichier']).name}` | {a.get('scenario') or '—'} | {a.get('date_publication') or '—'} | {a.get('titre') or '—'} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Traçabilité d'une instance/événement/signal.")
    parser.add_argument("--slug", default=None)
    parser.add_argument("--type", default=None,
                         help="instance|evenement|signal -- valeurs vides/'undefined' traitées comme absentes (auto-détection).")
    parser.add_argument("--json", action="store_true", help="N'affiche que le JSON sur stdout.")
    parser.add_argument("--report", action="store_true", help="Écrit aussi un rapport .md dans documentation/need_action/trace_<slug>.md")
    parser.add_argument("--skip-articles", action="store_true", help="Saute le scan des articles (plus rapide).")
    parser.add_argument("--list", action="store_true", help="Liste les slugs disponibles (par type si --type est précisé) au lieu de tracer.")
    args = parser.parse_args()

    # Filet de sécurité GUI : un champ select sans valeur choisie peut envoyer
    # la chaîne littérale "undefined" (ou vide) plutôt que d'omettre le flag.
    # Traité comme "non précisé" -> auto-détection, plutôt qu'une erreur.
    if args.type in (None, "", "undefined", "null"):
        args.type = None
    elif args.type not in ("instance", "evenement", "signal"):
        print(f"✗ --type invalide : {args.type!r} (attendu instance/evenement/signal, ou rien).", file=sys.stderr)
        sys.exit(2)

    if args.list:
        disponibles = _lister_slugs(args.type)
        if args.json:
            print(json.dumps(disponibles, ensure_ascii=False, indent=2))
        else:
            for t, slugs in disponibles.items():
                print(f"\n=== {t} ({len(slugs)}) ===")
                for s in slugs:
                    print(f"  - {s}")
        return

    if not args.slug:
        print("✗ --slug requis (ou --list pour voir les slugs disponibles).", file=sys.stderr)
        sys.exit(1)

    # Résolution tolérante : accepte qu'on passe un slug d'instance/event_instance
    # (entité ou archétype + suffixe scénario) à la place du slug attendu au
    # niveau entité/archétype -- voir _resoudre_slug_entite()/_resoudre_slug_evenement()
    # pour le cas réel qui a motivé ce filet de sécurité (2 août 2026).
    slug_resolu = args.slug
    if args.type in (None, "instance"):
        candidat = _resoudre_slug_entite(args.slug)
        if candidat != args.slug:
            slug_resolu = candidat
            args.type = "instance"
    if slug_resolu == args.slug and args.type in (None, "evenement"):
        candidat = _resoudre_slug_evenement(args.slug)
        if candidat != args.slug:
            slug_resolu = candidat
            args.type = "evenement"

    type_ = args.type or _detecter_type(slug_resolu)
    if not type_:
        print(f"✗ Slug {args.slug!r} introuvable dans entites/, evenements/ ni signaux_custom/. "
              f"Vérifie l'orthographe, force le type avec --type, ou utilise --list pour voir ce qui existe.", file=sys.stderr)
        sys.exit(1)

    if type_ == "instance":
        trace = tracer_instance(slug_resolu)
    elif type_ == "evenement":
        trace = tracer_evenement(slug_resolu)
    else:
        trace = tracer_signal(slug_resolu)

    if slug_resolu != args.slug:
        trace["slug_original_fourni"] = args.slug
        trace["note_resolution"] = (f"Le slug fourni ({args.slug!r}) était un slug d'instance/event_instance -- "
                                     f"résolu automatiquement vers le slug d'entité/archétype {slug_resolu!r}.")

    if not args.skip_articles:
        trace["articles_mentionnant"] = _scan_articles(slug_resolu, trace.get("nom"))

    if args.json:
        print(json.dumps(trace, ensure_ascii=False, indent=2, default=str))
        return

    md = _rendre_markdown(trace)
    print(md)

    if args.report:
        out_dir = VAULT_ROOT / "documentation" / "need_action"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"trace_{args.slug}.md"
        out_path.write_text(md, encoding="utf-8")
        json_path = out_dir / f"trace_{args.slug}.json"
        json_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"\n→ Rapport écrit : {out_path}", file=sys.stderr)
        print(f"→ JSON écrit : {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
