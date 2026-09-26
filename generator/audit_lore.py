#!/usr/bin/env python3
"""
audit_lore.py — Ourrassol 2098 (S17, 25 septembre 2026)
=========================================================

Audit de cohérence du lore des instances d'un scénario. N'ÉCRIT JAMAIS dans
les fiches, sauf l'étape explicite --appliquer (propositions validées à la
main). Complète validate.py sans le dupliquer.

SANS LLM (par défaut, gratuit)
  1. Réciprocité : A cite B, B ne cite pas A ; relations contradictoires
     (calcul partagé avec fix_alliances_oppositions.calculer_reciprocite /
     find_conflicts — même règle, aucune réécriture).
  2. Relations inter-scénarios : un allié/opposant d'un AUTRE scénario
     (information seulement — validate.py ne les voit pas).
  3. Transnationale mais localisée dans le texte : zone vide alors que le
     rôle / la description cite une zone du scénario.
  4. Quarantaine : instance localisée dans une zone en quarantaine (ou une de
     ses sous-zones) avec une trajectoire active.
  5. Règles de lore (documentation/lore_regles.yaml) : termes périmés,
     interdits ou à relire, dans tous les textes des fiches.

AVEC LLM (--llm, payant, tier structured_strict)
  6. Contradictions entre la fiche et le lore fourni (zone, sous-zone parente,
     alliés/opposants, faits établis du fichier de règles).
  7. Relations proposées parmi les instances EXISTANTES du scénario —
     écrites dans un fichier de propositions à valider (valide: true), jamais
     appliquées automatiquement.

NON VÉRIFIÉ ICI (déjà dans validate.py) : slugs d'alliés/opposants
inexistants, relations en texte libre, zone de localisation inconnue,
type_lieu invalide, wikilinks cassés.

USAGE (depuis la racine du vault)
    python3 generator/audit_lore.py --scenario fortress_world
    python3 generator/audit_lore.py --all
    python3 generator/audit_lore.py --scenario fortress_world --avec-articles

    # LLM : estimer d'abord (aucun appel), puis lancer sur une cible
    python3 generator/audit_lore.py --scenario fortress_world --llm --estimer --limit 10
    python3 generator/audit_lore.py --scenario fortress_world --llm --slug ergo_wian_sovereign_holdings_fortress_world
    python3 generator/audit_lore.py --scenario fortress_world --llm --zone espace_nordique_arctique
    python3 generator/audit_lore.py --scenario fortress_world --llm --limit 10   # 10 plus fort impact

    # Appliquer les relations validées (valide: true) du fichier de propositions
    python3 generator/audit_lore.py --scenario fortress_world --appliquer --dry-run
    python3 generator/audit_lore.py --scenario fortress_world --appliquer

SORTIES
    documentation/need_action/audit_lore_{scenario}.md               (rapport, réécrit à chaque run)
    documentation/need_action/audit_lore_dernier_lancement.md        (rapports du dernier lancement, pour le GUI)
    documentation/need_action/audit_lore_propositions.yaml     (propositions LLM, tous scénarios, cumulatif)
    state/audit_lore_cache.json                                       (cache LLM ; --no-cache pour ignorer)
    --json : résumé JSON sur la dernière ligne (intégration GUI)
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_alliances_oppositions import (  # noqa: E402
    MAX_FIX_ATTEMPTS,
    SCENARIOS,
    build_instances_summary,
    build_scenario_instances_index,
    calculer_reciprocite,
    call_llm_json_resilient,
    find_conflicts,
    parse_md,
    validate_targeted,
    write_alliances_patch,
)

VAULT_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_DIR = VAULT_ROOT / "instances"
EVENT_INSTANCES_DIR = VAULT_ROOT / "event_instances"
ARTICLES_DIR = VAULT_ROOT / "articles"
GEOGRAPHIE_DIR = VAULT_ROOT / "geographie"
NEED_ACTION_DIR = VAULT_ROOT / "documentation" / "need_action"
REGLES_PATH = VAULT_ROOT / "documentation" / "lore_regles.yaml"
CACHE_PATH = VAULT_ROOT / "state" / "audit_lore_cache.json"
# Relations rejetées dans le GUI (étape 5) : jamais reproposées (26 sept).
REJETS_PATH = VAULT_ROOT / "state" / "audit_lore_rejets.json"
PROPOSITIONS_PATH = NEED_ACTION_DIR / "audit_lore_propositions.yaml"
DERNIER_RAPPORT_PATH = NEED_ACTION_DIR / "audit_lore_dernier_lancement.md"

# Clés de frontmatter qui ne contiennent pas de texte narratif (slugs,
# énumérations, dates) — exclues de la recherche des règles.
CLES_NON_TEXTE = {
    "slug", "entite", "archetype", "scenario", "type", "statut", "alliances",
    "oppositions", "variables_influencees", "zone_geographique",
    "zone_systemique", "date_creation", "generation", "trajectoire",
    "type_dans_scenario", "type_relation_dominante", "est_clandestin",
    "impact_local", "impact_systemique_global", "annee_debut", "annee_fin",
    "retry_signes_distinctifs", "exclure_articles", "zone", "type_lieu",
    "note", "variable", "polarite", "delta_level", "duree", "via_matrice",
    "garantie_selection", "evenements_cites", "entites_citees", "tags",
    "journaliste_slug",
}
CHAMPS_LLM = ["role_dans_scenario", "responsabilites", "description_journalistique",
              "tensions_narratives"]
SEUIL_CONFIRMATION_LLM = 15  # au-delà, --limit / --slug / --zone / --tout requis


# ─────────────────────────────────────────────────────────────────────────
# Outils texte
# ─────────────────────────────────────────────────────────────────────────

def _plier(texte, garder_casse=False):
    """Retire accents (caractère par caractère : longueur conservée, donc
    positions identiques au texte d'origine) et, sauf demande, la casse."""
    out = []
    for c in texte.replace("’", "'"):
        base = unicodedata.normalize("NFD", c)[0]
        out.append(base if garder_casse else base.lower())
    return "".join(out)


def _motif(terme, sensible_casse):
    garder = sensible_casse and terme.isupper()
    t = _plier(terme, garder)
    return re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)"), garder


def _chercher(texte, terme, sensible_casse=False):
    """Positions (debut, fin) des occurrences de `terme` (mot entier)."""
    motif, garder = _motif(terme, sensible_casse)
    return [(m.start(), m.end()) for m in motif.finditer(_plier(texte, garder))]


def _phrase(texte, debut, fin, max_len=240):
    """Phrase contenant [debut, fin], tronquée proprement."""
    g = max(texte.rfind(s, 0, debut) for s in ".!?;\n")
    d_candidats = [texte.find(s, fin) for s in ".!?;\n"]
    d = min([x for x in d_candidats if x != -1] or [len(texte)])
    ph = " ".join(texte[g + 1:d + 1].split())
    if len(ph) > max_len:
        centre = texte[debut:fin]
        i = ph.find(centre)
        a = max(0, i - max_len // 2)
        ph = ("…" if a else "") + ph[a:a + max_len] + "…"
    return ph


def _phrases(texte):
    """Découpe en phrases avec leur position de départ."""
    res, debut = [], 0
    for m in re.finditer(r"[.!?;\n]", texte):
        res.append((debut, texte[debut:m.end()]))
        debut = m.end()
    if debut < len(texte):
        res.append((debut, texte[debut:]))
    return res


def _textes(fm, prefixe=""):
    """(chemin_de_champ, texte) pour toutes les valeurs texte narratives."""
    if isinstance(fm, dict):
        for k, v in fm.items():
            if str(k) in CLES_NON_TEXTE:
                continue
            yield from _textes(v, f"{prefixe}{k}.")
    elif isinstance(fm, list):
        for i, v in enumerate(fm):
            yield from _textes(v, f"{prefixe}{i}.")
    elif isinstance(fm, str) and fm.strip():
        yield prefixe.rstrip("."), fm


# ─────────────────────────────────────────────────────────────────────────
# Chargements
# ─────────────────────────────────────────────────────────────────────────

def charger_regles():
    if not REGLES_PATH.exists():
        return {}
    data = yaml.safe_load(REGLES_PATH.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def regles_du_scenario(regles, scenario):
    tous = regles.get("_tous") or {}
    sc = regles.get(scenario) or {}
    return {
        "regles": list(tous.get("regles") or []) + list(sc.get("regles") or []),
        "zones_quarantaine": list(tous.get("zones_quarantaine") or [])
                             + list(sc.get("zones_quarantaine") or []),
    }


def charger_zones(scenario):
    path = GEOGRAPHIE_DIR / f"{scenario}.md"
    if not path.exists():
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---", path.read_text(encoding="utf-8"), re.DOTALL)
    if not m:
        return {}
    data = yaml.safe_load(m.group(1)) or {}
    return {z["slug"]: z for z in data.get("zones") or []
            if isinstance(z, dict) and z.get("slug")}


def descendants(zones, racine):
    res, pile = {racine}, [racine]
    while pile:
        p = pile.pop()
        for slug, z in zones.items():
            if z.get("parent") == p and slug not in res:
                res.add(slug)
                pile.append(slug)
    return res


def charger_fiches(dossier, scenario):
    fiches = {}
    if not dossier.exists():
        return fiches
    for path in sorted(dossier.glob(f"*_{scenario}.md")):
        fm, body = parse_md(path)
        if not fm or fm.get("scenario", scenario) != scenario:
            continue
        fiches[fm.get("slug", path.stem)] = {"path": path, "fm": fm, "body": body}
    return fiches


def charger_articles(scenario):
    res = {}
    dossier = ARTICLES_DIR / scenario
    if not dossier.exists():
        return res
    for path in sorted(dossier.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        fm, body = parse_md(path)
        champs = {k: fm.get(k) for k in ("titre", "title", "chapo") if fm.get(k)}
        champs["corps"] = body
        res[path.stem] = {"path": path, "fm": champs, "body": body}
    return res


def zone_de(fm):
    loc = fm.get("localisation")
    return (loc.get("zone") if isinstance(loc, dict) else None) or None


def impact(fm):
    total = 0
    for k in ("impact_local", "impact_systemique_global"):
        try:
            total += int(fm.get(k) or 0)
        except (TypeError, ValueError):
            pass
    return total


# ─────────────────────────────────────────────────────────────────────────
# Contrôles sans LLM
# ─────────────────────────────────────────────────────────────────────────

def ctrl_reciprocite(scenario):
    _, additions, _ = calculer_reciprocite(scenario)
    manquantes = []
    for cible, adds in additions.items():
        for champ in ("alliances", "oppositions"):
            for source in sorted(adds[champ]):
                manquantes.append({"source": source, "cible": cible, "champ": champ})
    _, conflits = find_conflicts(scenario)
    return manquantes, conflits


def ctrl_inter_scenarios(fiches, scenario):
    autres = [s for s in SCENARIOS if s != scenario]
    res = []
    for slug, f in fiches.items():
        for champ in ("alliances", "oppositions"):
            for ref in f["fm"].get(champ) or []:
                ref = str(ref)
                sc = next((s for s in autres if ref.endswith(f"_{s}")), None)
                if sc:
                    res.append({"slug": slug, "champ": champ, "ref": ref, "scenario_ref": sc})
    return res


def _noms_de_zone(zones):
    noms = {}
    for slug, z in zones.items():
        for nom in {str(z.get("nom") or ""), str(z.get("nom") or "").split(" — ")[0]}:
            nom = nom.strip()
            if len(nom) >= 5:
                noms[nom] = slug
    return noms


def ctrl_transnationales(fiches, zones):
    noms = _noms_de_zone(zones)
    res = []
    for slug, f in fiches.items():
        fm = f["fm"]
        if zone_de(fm):
            continue
        trouves = {}
        for champ in ("role_dans_scenario", "responsabilites", "description_journalistique"):
            texte = str(fm.get(champ) or "")
            for nom, zslug in noms.items():
                if _chercher(texte, nom):
                    trouves[zslug] = nom
        if trouves:
            res.append({"slug": slug, "zones_citees": trouves})
    return res


def ctrl_quarantaine(fiches, zones, conf):
    res = []
    for q in conf["zones_quarantaine"]:
        zone_q = q.get("zone")
        if not zone_q:
            continue
        couvertes = descendants(zones, zone_q)
        tolerees = set(q.get("trajectoires_tolerees") or [])
        for slug, f in fiches.items():
            z = zone_de(f["fm"])
            traj = f["fm"].get("trajectoire")
            if z in couvertes and traj not in tolerees:
                res.append({"slug": slug, "zone": z, "trajectoire": traj,
                            "zone_quarantaine": zone_q, "message": q.get("message", "")})
    return res


_NEGATION = re.compile(r"(?<!\w)(pas|ni|non|jamais|plus|nullement|aucunement|loin d'etre)(?!\w)[^.;!?]*$")


def ctrl_regles(fiches, conf, type_fiche):
    res, vus = [], set()
    for regle in conf["regles"]:
        rid = regle.get("id", "?")
        casse = bool(regle.get("sensible_casse"))
        sauf = set(regle.get("sauf_zones") or [])
        for slug, f in fiches.items():
            if sauf and zone_de(f["fm"]) in sauf:
                continue
            for champ, texte in _textes(f["fm"]):
                # Zones couvertes par une exception (ex. « Brest-Litovsk » pour
                # la règle qui cherche « Brest ») : une occurrence à l'intérieur
                # est ignorée.
                exclues = [pos for ex in regle.get("exceptions") or []
                           for pos in _chercher(texte, ex, casse)]
                hits = []
                for terme in regle.get("termes") or []:
                    for d, e in _chercher(texte, terme, casse):
                        if not any(xd <= d and e <= xe for xd, xe in exclues):
                            hits.append((terme, d, e))
                groupes = regle.get("meme_phrase")
                if groupes and len(groupes) == 2:
                    for debut, ph in _phrases(texte):
                        a = [(t, x) for t in groupes[0] for x in _chercher(ph, t, casse)]
                        b = []
                        for t in groupes[1]:
                            for bd, _be in _chercher(ph, t, casse):
                                # « n'est pas neutre », « ni neutre », « non neutre »…
                                # confirment la règle au lieu de la contredire.
                                if regle.get("ignorer_negation") and _NEGATION.search(
                                        _plier(ph[max(0, bd - 30):bd])):
                                    continue
                                b.append(t)
                        if a and b:
                            t, (d, e) = a[0]
                            hits.append((f"{t} + {b[0]}", debut + d, debut + e))
                for terme, d, e in hits:
                    cle = (rid, slug, champ, terme)
                    if cle in vus:
                        continue
                    vus.add(cle)
                    res.append({
                        "regle": rid, "gravite": regle.get("gravite", "a_relire"),
                        "type": type_fiche, "slug": slug, "champ": champ,
                        "terme": terme, "extrait": _phrase(texte, d, e),
                        "suggestion": regle.get("suggestion"),
                        "message": " ".join(str(regle.get("message", "")).split()),
                    })
    return res


# ─────────────────────────────────────────────────────────────────────────
# LLM : contradictions + relations proposées
# ─────────────────────────────────────────────────────────────────────────

def _court(texte, n=260):
    texte = " ".join(str(texte or "").split())
    return texte if len(texte) <= n else texte[:n].rsplit(" ", 1)[0] + "…"


def contexte_zone(fm, zones):
    z = zone_de(fm)
    if not z or z not in zones:
        return "(fiche transnationale : aucune zone de rattachement)"
    lignes, courant, vus = [], z, set()
    while courant and courant in zones and courant not in vus:
        vus.add(courant)
        zz = zones[courant]
        lignes.append(f"- {zz.get('nom', courant)} [{courant}] : {_court(zz.get('description'), 600)}")
        if zz.get("tensions_internes"):
            lignes.append(f"  Tensions : {_court(zz.get('tensions_internes'), 300)}")
        courant = zz.get("parent")
    return "\n".join(lignes)


def faits_etablis(conf):
    lignes = [f"- {' '.join(str(q.get('message', '')).split())}" for q in conf["zones_quarantaine"]
              if q.get("message")]
    lignes += [f"- {' '.join(str(r.get('message', '')).split())}" for r in conf["regles"]
               if r.get("message") and r.get("gravite") == "erreur"]
    return "\n".join(lignes) or "(aucun)"


def construire_prompt(slug, fm, scenario, fiches, zones, conf, index):
    relations = []
    for champ, lib in (("alliances", "Allié"), ("oppositions", "Opposant")):
        for ref in fm.get(champ) or []:
            f = fiches.get(ref)
            role = _court(f["fm"].get("role_dans_scenario"), 260) if f else "(autre scénario ou fiche absente)"
            nom = f["fm"].get("name", ref) if f else ref
            relations.append(f"- {lib} : {nom} [{ref}] — {role}")
    champs = "\n".join(f"{c}: {' '.join(str(fm.get(c) or '').split())}" for c in CHAMPS_LLM)
    loc = fm.get("localisation") if isinstance(fm.get("localisation"), dict) else {}

    system = """Tu es le relecteur de cohérence du lore du projet Ourrassol 2098.
Tu compares UNE fiche d'instance au lore établi qui t'est fourni, et rien d'autre.
Tes réponses sont UNIQUEMENT du JSON valide, sans texte avant ou après, sans backticks."""

    user = f"""TÂCHE : relire la fiche ci-dessous (scénario {scenario}) et signaler
(1) ses contradictions avec le lore établi fourni, (2) des relations manquantes
plausibles parmi les instances réelles du scénario.

═══ FICHE À RELIRE ═══
slug: {slug}
name: {fm.get('name', slug)}
localisation: zone={loc.get('zone')} ; lieu={loc.get('lieu')}
trajectoire: {fm.get('trajectoire')}
{champs}

═══ LORE ÉTABLI — ZONE DE RATTACHEMENT (de la plus précise à la plus large) ═══
{contexte_zone(fm, zones)}

═══ LORE ÉTABLI — RELATIONS ACTUELLES DE LA FICHE ═══
{chr(10).join(relations) or "(aucune)"}

═══ LORE ÉTABLI — FAITS DU SCÉNARIO (priorité absolue) ═══
{faits_etablis(conf)}

═══ INSTANCES RÉELLES DU SCÉNARIO (seuls slugs valides) ═══
{build_instances_summary(index, exclude_slug=slug)}

═══ RÉPONSE ATTENDUE ═══
{{
  "contradictions": [
    {{"champ": "role_dans_scenario|responsabilites|description_journalistique|tensions_narratives|localisation",
      "extrait": "citation courte et exacte de la fiche",
      "probleme": "ce qui contredit le lore établi ci-dessus, et lequel",
      "correction": "reformulation proposée de l'extrait"}}
  ],
  "alliances_proposees": [{{"slug": "slug_valide", "raison": "une phrase"}}],
  "oppositions_proposees": [{{"slug": "slug_valide", "raison": "une phrase"}}]
}}

RÈGLES IMPÉRATIVES :
- Une contradiction n'existe QUE par rapport au lore établi fourni ci-dessus
  (zone, relations, faits du scénario). Pas de remarque de style, pas de goût,
  pas d'invention de lore. Aucune contradiction réelle → tableau vide.
- Relations : UNIQUEMENT des slugs de la liste des instances réelles, jamais
  la fiche elle-même, jamais un slug déjà présent dans ses relations actuelles,
  jamais le même slug dans les deux listes. 0 à 3 par liste, seulement si le
  contenu des fiches le justifie clairement. Tableau vide accepté.
"""
    return system, user


def valider_reponse(data, index, slug, fm):
    erreurs = []
    if not isinstance(data, dict):
        return ["la réponse doit être un objet JSON"], data
    contr = data.get("contradictions", [])
    if not isinstance(contr, list) or any(not isinstance(c, dict) or not c.get("probleme") for c in contr):
        erreurs.append("'contradictions' doit être une liste d'objets avec au moins 'probleme'")
    existants = set(fm.get("alliances") or []) | set(fm.get("oppositions") or [])
    plat = {}
    for champ_llm, champ in (("alliances_proposees", "alliances"), ("oppositions_proposees", "oppositions")):
        liste = data.get(champ_llm, [])
        if not isinstance(liste, list) or any(not isinstance(p, dict) or "slug" not in p for p in liste):
            erreurs.append(f"'{champ_llm}' doit être une liste d'objets avec 'slug'")
            plat[champ] = []
            continue
        # Déjà présent ou fiche elle-même : filtré en silence (pas une erreur de fond)
        data[champ_llm] = [p for p in liste if p["slug"] not in existants and p["slug"] != slug]
        plat[champ] = [p["slug"] for p in data[champ_llm]]
    erreurs += validate_targeted(plat, index, slug)
    return erreurs, data


def auditer_llm(slug, fm, scenario, fiches, zones, conf, index):
    system, user = construire_prompt(slug, fm, scenario, fiches, zones, conf, index)
    data = call_llm_json_resilient(system, user, max_tokens=2500)
    erreurs, data = valider_reponse(data, index, slug, fm)
    tentative = 0
    while erreurs and tentative < MAX_FIX_ATTEMPTS:
        tentative += 1
        print(f"    [retry {tentative}/{MAX_FIX_ATTEMPTS}] {len(erreurs)} erreur(s)")
        correctif = (user + "\n═══ CORRECTION REQUISE ═══\n"
                     + "\n".join(f"  - {e}" for e in erreurs)
                     + f"\nJSON précédent : {json.dumps(data, ensure_ascii=False)}\n"
                     "Retourne le JSON complet corrigé.")
        data = call_llm_json_resilient(system, correctif, max_tokens=2500)
        erreurs, data = valider_reponse(data, index, slug, fm)
    if erreurs and isinstance(data, dict):
        # Dernier recours : retirer les slugs hors liste et les doublons entre
        # listes plutôt que perdre toute la relecture (contradictions comprises).
        vus = set()
        for champ_llm in ("alliances_proposees", "oppositions_proposees"):
            gardes = []
            for p in data.get(champ_llm) or []:
                if isinstance(p, dict) and p.get("slug") in index and p["slug"] not in vus:
                    gardes.append(p)
                    vus.add(p["slug"])
            data[champ_llm] = gardes
        erreurs, data = valider_reponse(data, index, slug, fm)
        if not erreurs:
            print("    (propositions invalides retirées après les reprises, relecture conservée)")
    if erreurs:
        raise ValueError("; ".join(erreurs))
    return data


def empreinte(slug, f, zones, conf, index, fiches):
    fm = f["fm"]
    morceaux = [f["path"].read_text(encoding="utf-8"), contexte_zone(fm, zones),
                faits_etablis(conf), json.dumps(sorted(index), ensure_ascii=False)]
    for champ in ("alliances", "oppositions"):
        for ref in fm.get(champ) or []:
            if ref in fiches:
                morceaux.append(str(fiches[ref]["fm"].get("role_dans_scenario") or ""))
    return hashlib.sha256("\n".join(morceaux).encode("utf-8")).hexdigest()[:16]


def lire_json(path, defaut):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return defaut


# Même texte que LORE_ENTETE_PROPOSITIONS dans gui/app.py (qui réécrit aussi
# ce fichier depuis l'étape 5) : garder les deux identiques.
ENTETE_PROPOSITIONS = (
    "# Propositions de relations (audit_lore.py --llm), tous scénarios.\n"
    "# À trier dans le GUI : « Relations & lore » → « 5. Valider les propositions de l'IA ».\n"
    "# (ou à la main : `valide: true` sur celles à garder, puis\n"
    "#   python3 generator/audit_lore.py --all --appliquer --dry-run\n"
    "#   python3 generator/audit_lore.py --all --appliquer)\n"
    "# Les entrées déjà présentes ne sont jamais écrasées par un nouveau run ;\n"
    "# une proposition rejetée est retirée d'ici et notée dans state/audit_lore_rejets.json.\n")


def chemin_propositions(scenario=None):
    # Fichier unique pour tous les scénarios (chaque entrée porte `scenario`),
    # pour un chemin fixe affichable/éditable dans le GUI.
    return PROPOSITIONS_PATH


def ecrire_propositions(liste):
    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    PROPOSITIONS_PATH.write_text(ENTETE_PROPOSITIONS + yaml.safe_dump(
        {"propositions": liste}, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")


def lire_propositions():
    if not PROPOSITIONS_PATH.exists():
        return []
    data = yaml.safe_load(PROPOSITIONS_PATH.read_text(encoding="utf-8")) or {}
    return data.get("propositions") or []


def cles_rejetees():
    """Clés (scenario, slug, relation, cible) rejetées dans le GUI (étape 5)."""
    data = lire_json(REJETS_PATH, {})
    return {tuple(r.get("cle") or []) for r in data.get("relations") or []}


def fusionner_propositions(scenario, nouvelles):
    """Ajoute les nouvelles propositions sans toucher à celles déjà présentes
    (validées ou appliquées), et sans jamais reproposer une relation rejetée
    dans le GUI. Clé : (scenario, slug, relation, cible)."""
    liste = lire_propositions()
    cles = {(p.get("scenario"), p.get("slug"), p.get("relation"), p.get("cible")) for p in liste}
    cles |= cles_rejetees()
    ajoutees = 0
    for p in nouvelles:
        cle = (scenario, p["slug"], p["relation"], p["cible"])
        if cle not in cles:
            liste.append({"scenario": scenario, **p})
            cles.add(cle)
            ajoutees += 1
    if ajoutees:
        ecrire_propositions(liste)
    return ajoutees


def cibles_llm(fiches, zones, args):
    cibles = list(fiches.items())
    if args.slug:
        cibles = [(s, f) for s, f in cibles if s == args.slug]
    if args.zone:
        couvertes = descendants(zones, args.zone)
        cibles = [(s, f) for s, f in cibles if zone_de(f["fm"]) in couvertes]
    cibles.sort(key=lambda sf: (-impact(sf[1]["fm"]), sf[0]))
    if args.limit:
        cibles = cibles[:args.limit]
    return cibles


def passe_llm(scenario, fiches, zones, conf, args):
    cibles = cibles_llm(fiches, zones, args)
    index = build_scenario_instances_index(scenario)
    cache = {} if args.no_cache else lire_json(CACHE_PATH, {})
    a_appeler = []
    for slug, f in cibles:
        cle = f"{scenario}/{slug}"
        emp = empreinte(slug, f, zones, conf, index, fiches)
        if cache.get(cle, {}).get("empreinte") == emp:
            continue
        a_appeler.append((slug, f, emp))

    print(f"\n[LLM] {len(cibles)} fiche(s) ciblée(s) — {len(a_appeler)} appel(s) nécessaire(s), "
          f"{len(cibles) - len(a_appeler)} en cache")
    if args.estimer:
        for slug, f in cibles:
            print(f"  · {slug} (impact {impact(f['fm'])})")
        print("  (--estimer : aucun appel)")
        return None
    if len(a_appeler) > SEUIL_CONFIRMATION_LLM and not (args.slug or args.zone or args.limit or args.tout):
        print(f"  ✗ {len(a_appeler)} appels : préciser --limit N, --slug, --zone ou --tout. Rien lancé.")
        return None

    tous = lire_json(CACHE_PATH, {})
    echecs = []
    for i, (slug, f, emp) in enumerate(a_appeler, 1):
        print(f"  [{i}/{len(a_appeler)}] {slug}")
        try:
            data = auditer_llm(slug, f["fm"], scenario, fiches, zones, conf, index)
        except Exception as e:  # une fiche en échec n'arrête pas les autres
            print(f"    ✗ {e}")
            echecs.append({"slug": slug, "erreur": str(e)})
            continue
        tous[f"{scenario}/{slug}"] = {"empreinte": emp, "date": datetime.now().isoformat(timespec="seconds"),
                                      "resultat": data}
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(tous, ensure_ascii=False, indent=1), encoding="utf-8")

    resultats, nouvelles = {}, []
    for slug, f in cibles:
        entree = tous.get(f"{scenario}/{slug}")
        if not entree:
            continue
        data = entree["resultat"]
        resultats[slug] = data
        for champ_llm, relation in (("alliances_proposees", "alliance"),
                                    ("oppositions_proposees", "opposition")):
            for p in data.get(champ_llm) or []:
                nouvelles.append({"slug": slug, "relation": relation, "cible": p["slug"],
                                  "raison": p.get("raison", ""), "valide": False,
                                  "date": date.today().isoformat()})
    ajoutees = fusionner_propositions(scenario, nouvelles)
    return {"resultats": resultats, "echecs": echecs, "propositions_ajoutees": ajoutees}


# ─────────────────────────────────────────────────────────────────────────
# Application des propositions validées
# ─────────────────────────────────────────────────────────────────────────

def appliquer(scenario, dry_run):
    if not PROPOSITIONS_PATH.exists():
        print(f"Aucun fichier de propositions : {PROPOSITIONS_PATH.relative_to(VAULT_ROOT)}")
        return 0
    props = lire_propositions()
    a_faire = [p for p in props if p.get("scenario") == scenario
               and p.get("valide") is True and not p.get("applique")]
    print(f"[{scenario}] {len(a_faire)} proposition(s) validée(s) à appliquer"
          + (" (dry-run, rien écrit)" if dry_run else ""))
    fiches = charger_fiches(INSTANCES_DIR, scenario)
    par_fiche, n_ok = {}, 0
    for p in a_faire:
        par_fiche.setdefault(p["slug"], []).append(p)
    for slug, liste in par_fiche.items():
        f = fiches.get(slug)
        if not f:
            print(f"  ✗ {slug} : fiche introuvable — ignorée")
            continue
        al = list(f["fm"].get("alliances") or [])
        op = list(f["fm"].get("oppositions") or [])
        faites = []
        for p in liste:
            cible, rel = p["cible"], p["relation"]
            if cible not in fiches:
                print(f"  ✗ {slug} → {cible} : cible introuvable — ignorée")
                continue
            meme, autre = (al, op) if rel == "alliance" else (op, al)
            if cible in autre:
                print(f"  ✗ {slug} → {cible} : déjà dans l'autre liste (conflit) — ignorée")
                continue
            champ_inverse = "oppositions" if rel == "alliance" else "alliances"
            if slug in (fiches[cible]["fm"].get(champ_inverse) or []):
                print(f"  ✗ {slug} → {cible} : {cible} classe {slug} dans ses {champ_inverse} "
                      "(créerait un conflit) — ignorée")
                continue
            if cible not in meme:
                meme.append(cible)
            faites.append(p)
            print(f"  ✓ {slug} : + {rel} {cible}")
        if faites and not dry_run:
            shutil.copy2(f["path"], f["path"].with_suffix(".md.bak"))
            write_alliances_patch(f["path"], al, op)
            for p in faites:
                p["applique"] = date.today().isoformat()
        n_ok += len(faites)
    if n_ok and not dry_run:
        shutil.copy2(PROPOSITIONS_PATH, PROPOSITIONS_PATH.with_suffix(".yaml.bak"))
        ecrire_propositions(props)
        print(f"\n{n_ok} relation(s) écrite(s) (.bak de chaque fiche). Pour propager la réciprocité :")
        print(f"  python3 generator/fix_alliances_oppositions.py --scenario {scenario} --reciprocite-seule --dry-run")
    return n_ok


# ─────────────────────────────────────────────────────────────────────────
# Rapport
# ─────────────────────────────────────────────────────────────────────────

def rapport_md(scenario, r):
    L = [f"# Audit du lore — {scenario}", "",
         f"*Généré par `audit_lore.py` le {datetime.now():%Y-%m-%d %H:%M} — réécrit à chaque run, "
         "ne pas éditer. Règles : `documentation/lore_regles.yaml`.*", "",
         "## Résumé", ""]
    regles_err = [x for x in r["regles"] if x["gravite"] == "erreur"]
    regles_rel = [x for x in r["regles"] if x["gravite"] != "erreur"]
    L += [f"- Fiches analysées : {r['n_fiches']}"
          + (f" (+ {r['n_evenements']} événements)" if r["n_evenements"] else "")
          + (f" (+ {r['n_articles']} articles)" if r["n_articles"] else ""),
          f"- Règles de lore — **erreurs : {len(regles_err)}**, à relire : {len(regles_rel)}",
          f"- Quarantaine (fiche active localisée en zone interdite) : {len(r['quarantaine'])}",
          f"- Transnationales localisées dans le texte (info) : {len(r['transnationales'])}",
          f"- Relations à sens unique à corriger : {_n_a_corriger(r)}"
          + (f" (+ {len(r['reciprocite']) - _n_a_corriger(r)} volontaires : personnages en réserve)"
             if len(r['reciprocite']) != _n_a_corriger(r) else "")
          + f" — contradictoires : {len(r['conflits'])}",
          f"- Relations inter-scénarios (info) : {len(r['inter_scenarios'])}"]
    if r.get("llm"):
        n_c = sum(len(d.get("contradictions") or []) for d in r["llm"]["resultats"].values())
        L.append(f"- LLM : {len(r['llm']['resultats'])} fiche(s) relue(s), {n_c} contradiction(s), "
                 f"{r['llm']['propositions_ajoutees']} nouvelle(s) proposition(s) de relation")
    L += ["", "*Non vérifié ici (voir `validate.py`) : slugs inexistants, relations en texte "
          "libre, zone inconnue, type_lieu, wikilinks cassés.*", ""]

    def section(titre, lignes, vide="Rien à signaler."):
        L.extend([f"## {titre}", ""] + (lignes or [vide]) + [""])

    def bloc_regles(liste):
        out, courant = [], None
        for x in sorted(liste, key=lambda x: (x["regle"], x["type"], x["slug"])):
            if x["regle"] != courant:
                courant = x["regle"]
                out += ([""] if out else []) + [f"**{courant}** — {x['message']}"]
            sug = f" → *{x['suggestion']}*" if x.get("suggestion") else ""
            out.append(f"- `{x['slug']}` ({x['type']}, {x['champ']}) — **{x['terme']}**{sug} : « {x['extrait']} »")
        return out

    section("1. Règles de lore — erreurs", bloc_regles(regles_err))
    section("2. Quarantaine — fiches actives en zone interdite",
            [f"- `{x['slug']}` — zone `{x['zone']}` (sous {x['zone_quarantaine']}), trajectoire "
             f"**{x['trajectoire']}**" for x in r["quarantaine"]])
    section("3. Relations contradictoires (A allié de B, B opposé à A)",
            [f"- `{c['allie_a_corriger']}` liste `{c['opposant']}` en alliance, "
             f"qui le liste en opposition" for c in r["conflits"]]
            + (["", "→ Correction : **2. Rendre les relations réciproques**, case « Résoudre les "
                "conflits » cochée (l'opposition l'emporte)."] if r["conflits"] else []))
    a_corriger = [m for m in r["reciprocite"] if not m.get("reserve")]
    volontaires = [m for m in r["reciprocite"] if m.get("reserve")]
    lignes4 = [f"- `{m['source']}` cite `{m['cible']}` ({m['champ']}), pas l'inverse"
               for m in a_corriger] or ["Rien à corriger."]
    if a_corriger:
        lignes4 += ["", "→ Correction : GUI « Relations & lore » → **2. Rendre les relations réciproques** "
                    f"(CLI : `python3 generator/fix_alliances_oppositions.py --scenario {scenario} "
                    "--reciprocite-seule --ignorer-exclus --dry-run`, puis sans `--dry-run`)."]
    if volontaires:
        lignes4 += ["", f"Volontaires, rien à faire ({len(volontaires)}) — personnages en réserve, "
                    "jamais propagés chez les autres fiches :"]
        lignes4 += [f"- `{m['source']}` cite `{m['cible']}` ({m['champ']})" for m in volontaires]
    section("4. Relations à sens unique", lignes4)
    section("5. Règles de lore — à relire", bloc_regles(regles_rel))
    section("6. Transnationales mais localisées dans le texte (information)",
            ["Souvent légitime (une organisation transnationale nomme les zones où elle agit) ; à rattacher seulement si la fiche vit en réalité dans une seule zone.", ""]
            + [f"- `{x['slug']}` — cite : " + ", ".join(f"{n} (`{s}`)" for s, n in x["zones_citees"].items())
               for x in r["transnationales"]])
    section("7. Relations inter-scénarios (information)",
            [f"- `{x['slug']}` → `{x['ref']}` ({x['champ']}, scénario {x['scenario_ref']})"
             for x in r["inter_scenarios"]]
            + (["", "→ Si elles ne sont pas voulues : **3. Retirer les relations vers un autre "
                "scénario** (en aperçu d'abord ; les exceptions déclarées sont conservées)."]
               if r["inter_scenarios"] else []))
    if r.get("llm"):
        lignes = []
        for slug, d in sorted(r["llm"]["resultats"].items()):
            cs = d.get("contradictions") or []
            ps = (d.get("alliances_proposees") or []) + (d.get("oppositions_proposees") or [])
            if not cs and not ps:
                continue
            lignes.append(f"### `{slug}`")
            for c in cs:
                lignes.append(f"- ⚠ **{c.get('champ', '?')}** : « {c.get('extrait', '')} » — {c.get('probleme')}")
                if c.get("correction"):
                    lignes.append(f"  - Proposé : « {c['correction']} »")
            for p in d.get("alliances_proposees") or []:
                lignes.append(f"- ➕ alliance `{p['slug']}` — {p.get('raison', '')}")
            for p in d.get("oppositions_proposees") or []:
                lignes.append(f"- ➖ opposition `{p['slug']}` — {p.get('raison', '')}")
            lignes.append("")
        for e in r["llm"]["echecs"]:
            lignes.append(f"- ✗ `{e['slug']}` : échec LLM — {e['erreur']}")
        section("8. Relecture LLM (contradictions et relations proposées)", lignes)
        L.append("→ Trier les propositions et relire les contradictions : GUI « Relations & lore » → "
                 "**5. Valider les propositions de l'IA** "
                 f"(fichier : `{chemin_propositions(scenario).relative_to(VAULT_ROOT)}`).")
    return "\n".join(L) + "\n"


# ─────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────

def _n_a_corriger(r):
    return sum(1 for m in r["reciprocite"] if not m.get("reserve"))


def prochaines_etapes(r, scenario):
    """Lignes « À faire ensuite » : quelle étape du GUI lancer pour chaque
    problème trouvé (section « Relations & lore », étapes 1 à 5)."""
    out = []
    err = sum(1 for x in r["regles"] if x["gravite"] == "erreur")
    rel = len(r["regles"]) - err
    if err or r["quarantaine"]:
        out.append(f"  • {err + len(r['quarantaine'])} erreur(s) de lore / quarantaine → à corriger à la "
                   "main dans les fiches (rapport, sections 1 et 2)")
    if rel:
        out.append(f"  • {rel} passage(s) à relire → rapport, section 5 (souvent légitimes)")
    n = _n_a_corriger(r)
    if n or r["conflits"]:
        detail = f"{n} relation(s) à sens unique" + (f", {len(r['conflits'])} contradictoire(s) "
                                                      "(cocher « Résoudre les conflits »)" if r["conflits"] else "")
        out.append(f"  • {detail} → étape 2 « Rendre les relations réciproques »")
    if r["inter_scenarios"]:
        out.append(f"  • {len(r['inter_scenarios'])} relation(s) vers un autre scénario → étape 3 si elles "
                   "ne sont pas voulues (exceptions déclarées conservées)")
    en_attente = sum(1 for p in lire_propositions()
                     if p.get("scenario") == scenario and p.get("valide") is not True and not p.get("applique"))
    if en_attente:
        out.append(f"  • {en_attente} proposition(s) de l'IA à trier → étape 5 « Valider les propositions de l'IA »")
    if not out:
        return ["  À faire ensuite : rien à corriger."
                + ("" if r.get("llm") else " (Étape 4 « Relecture IA » possible pour aller plus loin.)")]
    return ["  À faire ensuite :"] + out


def auditer(scenario, args, regles):
    conf = regles_du_scenario(regles, scenario)
    zones = charger_zones(scenario)
    fiches = charger_fiches(INSTANCES_DIR, scenario)
    evenements = charger_fiches(EVENT_INSTANCES_DIR, scenario)
    articles = charger_articles(scenario) if args.avec_articles else {}

    manquantes, conflits = ctrl_reciprocite(scenario)
    # Personnages en réserve (exclus des articles, outil 🎯) : l'étape 2 les
    # laisse volontairement à sens unique (--ignorer-exclus), ce ne sont donc
    # pas des problèmes à corriger.
    reserve = {s for s, f in fiches.items() if f["fm"].get("exclure_articles")}
    for m in manquantes:
        m["reserve"] = m["source"] in reserve
    r = {
        "scenario": scenario,
        "n_fiches": len(fiches), "n_evenements": len(evenements), "n_articles": len(articles),
        "reciprocite": manquantes, "conflits": conflits,
        "inter_scenarios": ctrl_inter_scenarios(fiches, scenario),
        "transnationales": ctrl_transnationales(fiches, zones),
        "quarantaine": ctrl_quarantaine(fiches, zones, conf),
        "regles": (ctrl_regles(fiches, conf, "instance")
                   + ctrl_regles(evenements, conf, "evenement")
                   + ctrl_regles(articles, conf, "article")),
    }
    if args.llm:
        r["llm"] = passe_llm(scenario, fiches, zones, conf, args)

    NEED_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    chemin = NEED_ACTION_DIR / f"audit_lore_{scenario}.md"
    chemin.write_text(rapport_md(scenario, r), encoding="utf-8")
    r["rapport_md"] = str(chemin.relative_to(VAULT_ROOT))

    err = sum(1 for x in r["regles"] if x["gravite"] == "erreur")
    print(f"\n=== {scenario} === {len(fiches)} instance(s), {len(evenements)} événement(s)"
          + (f", {len(articles)} article(s)" if articles else ""))
    print(f"  Règles : {err} erreur(s), {len(r['regles']) - err} à relire")
    print(f"  Quarantaine : {len(r['quarantaine'])} | Transnationales localisées : {len(r['transnationales'])}")
    n_vol = len(manquantes) - _n_a_corriger(r)
    print(f"  Réciprocité : {_n_a_corriger(r)} à sens unique à corriger"
          + (f" (+ {n_vol} volontaires, personnages en réserve)" if n_vol else "")
          + f", {len(conflits)} contradictoire(s) | Inter-scénarios : {len(r['inter_scenarios'])}")
    if r.get("llm"):
        print(f"  LLM : {len(r['llm']['resultats'])} relue(s), {len(r['llm']['echecs'])} échec(s), "
              f"{r['llm']['propositions_ajoutees']} proposition(s) ajoutée(s)")
    for ligne in prochaines_etapes(r, scenario):
        print(ligne)
    print(f"  → rapport détaillé : {r['rapport_md']}")
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scenario", choices=SCENARIOS)
    g.add_argument("--all", action="store_true", help="Les 6 scénarios")
    ap.add_argument("--avec-articles", action="store_true",
                    help="Applique aussi les règles aux articles publiés (articles/{scenario}/)")
    ap.add_argument("--llm", action="store_true", help="Relecture LLM (payante) des fiches ciblées")
    ap.add_argument("--estimer", action="store_true", help="Avec --llm : liste les cibles et le nombre d'appels, sans appel")
    ap.add_argument("--slug", help="Avec --llm : une seule instance")
    ap.add_argument("--zone", help="Avec --llm : instances de cette zone et de ses sous-zones")
    ap.add_argument("--limit", type=int, help="Avec --llm : les N instances de plus fort impact")
    ap.add_argument("--tout", action="store_true",
                    help=f"Avec --llm : autorise plus de {SEUIL_CONFIRMATION_LLM} appels sans ciblage")
    ap.add_argument("--no-cache", action="store_true", help="Avec --llm : ignore le cache, rappelle le LLM")
    ap.add_argument("--appliquer", action="store_true",
                    help="Écrit les relations marquées valide: true du fichier de propositions")
    ap.add_argument("--dry-run", action="store_true", help="Avec --appliquer : n'écrit rien")
    ap.add_argument("--json", action="store_true", help="Résumé JSON sur la dernière ligne")
    args = ap.parse_args()

    scenarios = SCENARIOS if args.all else [args.scenario]
    if args.appliquer:
        total = sum(appliquer(sc, args.dry_run) for sc in scenarios)
        if args.json:
            print(json.dumps({"ok": True, "appliquees": total}, ensure_ascii=False))
        return
    if (args.slug or args.zone or args.limit or args.estimer or args.tout or args.no_cache) and not args.llm:
        ap.error("--slug/--zone/--limit/--estimer/--tout/--no-cache s'utilisent avec --llm")

    regles = charger_regles()
    if not REGLES_PATH.exists():
        print(f"[info] {REGLES_PATH.relative_to(VAULT_ROOT)} absent : contrôles de règles ignorés")
    resultats = [auditer(sc, args, regles) for sc in scenarios]
    # Rapport consolidé à chemin fixe (affiché par le GUI) : concaténation des
    # rapports des scénarios traités par CE lancement.
    DERNIER_RAPPORT_PATH.write_text(
        f"# Audit du lore — dernier lancement ({datetime.now():%Y-%m-%d %H:%M})\n\n"
        + "Scénarios : " + ", ".join(r["scenario"] for r in resultats) + "\n\n---\n\n"
        + "\n---\n\n".join((VAULT_ROOT / r["rapport_md"]).read_text(encoding="utf-8")
                            for r in resultats), encoding="utf-8")
    if args.json:
        print(json.dumps({"ok": True, "scenarios": [{
            "scenario": r["scenario"], "rapport_md": r["rapport_md"],
            "regles_erreurs": sum(1 for x in r["regles"] if x["gravite"] == "erreur"),
            "regles_a_relire": sum(1 for x in r["regles"] if x["gravite"] != "erreur"),
            "quarantaine": len(r["quarantaine"]), "transnationales": len(r["transnationales"]),
            "reciprocite": len(r["reciprocite"]), "conflits": len(r["conflits"]),
            "inter_scenarios": len(r["inter_scenarios"]),
        } for r in resultats]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
