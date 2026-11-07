#!/usr/bin/env python3
"""
et_si_main.py — Ourrassol 2098 (S27, étape ⑤ « À la main », 17 octobre 2026)
=============================================================================

Aide à la partie mécanique de l'étape ⑤, pour une hypothèse déjà APPLIQUÉE
(phase 4). Aucun appel IA. Rien n'est écrit sans --apply.

  1. Nouvelles entités proposées par la lecture IA : choisir une catégorie, puis
     les ajouter à entites_custom/queue.yaml (même format que la création
     d'entités ; garde-fou anti-doublon). La création elle-même reste
     « Créer des entités » (create_entities_and_instances.py --mode custom).
  2. Règle de lore : ajouter un brouillon relu à documentation/lore_regles.yaml,
     section du scénario (format vérifié, identifiant unique, fichier relu après
     écriture ; commentaires du fichier conservés).
  3. Phrases à corriger : celles de la passe exhaustive, plus celles de la fiche
     d'événement qui contredisent les faits de l'hypothèse (relecture IA) ; l'IA
     propose une réécriture, remplacée dans la fiche après aperçu (--apply).
  4. Articles à relire : repérage par l'IA des passages qui contredisent l'hypothèse
     (aucune écriture dans les articles ; correction à la main, puis « relu »).
  5. Carte (18 oct 2026) : suites de la carte appliquée en phase 4 -- sous-zones à
     plusieurs pays (la laisser, la déplacer entière sous la zone cible, ou tracer une
     portion dans l'onglet Carte), zones vidées et leurs journaux (garder en exil, ou
     retirer de generator/journaux.yaml), nouvelle zone (description, relations).
  6. Commandes de fin : audit du lore (gratuit), contrôle de la géographie (un petit appel IA), résumé
     du scénario (payant).

USAGE (depuis la racine du coffre)
    python3 generator/et_si_main.py --id X --json                      # état (pour le GUI)
    python3 generator/et_si_main.py --id X --entites '[{"cle": "reference:1", "category": "institution"}]'
    python3 generator/et_si_main.py --id X --entites '…' --apply
    python3 generator/et_si_main.py --id X --regle reference < brouillon.yaml           # aperçu
    python3 generator/et_si_main.py --id X --regle reference --apply < brouillon.yaml
    python3 generator/et_si_main.py --id X --phrases-proposer                 # appels IA (en cache)
    python3 generator/et_si_main.py --id X --phrase CLE [--apply] < phrase.txt
    python3 generator/et_si_main.py --id X --phrase CLE --ignorer
    python3 generator/et_si_main.py --id X --articles-verifier                 # appels IA (en cache), lecture seule
    python3 generator/et_si_main.py --id X --article-relu articles/<sc>/<fichier>.md
    python3 generator/et_si_main.py --id X --carte-deplacer reference:sertao_nordeste_bresilien [--apply]
    python3 generator/et_si_main.py --id X --carte-laisser reference:sertao_nordeste_bresilien
    python3 generator/et_si_main.py --id X --journal-garder reference:ecosse_nordique_independante:opposition
    python3 generator/et_si_main.py --id X --journal-retirer reference:ecosse_nordique_independante:opposition [--apply]
    python3 generator/et_si_main.py --id X --lancer audit --scenario reference
    python3 generator/et_si_main.py --id X --lancer resume --scenario reference
Suivi : generator/state/et_si_application/<id>.main.json (ce qui a été ajouté).
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

GEN = Path(__file__).resolve().parent
VAULT = GEN.parent
sys.path.insert(0, str(GEN))
import appliquer_et_si as ap  # noqa: E402

LORE = VAULT / "documentation" / "lore_regles.yaml"
GRAVITES = ("erreur", "a_relire")
SLUG_REGLE = re.compile(r"^[a-z0-9_]+$")
LANCER = {
    "audit": ("Relecture du lore (gratuit)", ["generator/audit_lore.py", "--scenario"], 300),
    "resume": ("Résumé du scénario (payant, un appel IA)", ["generator/generate_resume_scenarios.py", "--scenario"], 600),
    "geo": ("Contrôle de la géographie (un petit appel IA)", ["generator/scan_geographie_complet.py", "--scenario"], 300),
}


def cei():
    """create_entities_and_instances (catégories, file, anti-doublon) : chargé à la demande."""
    import create_entities_and_instances as m
    return m


def charger(hid):
    src = ap.APP_DIR / f"{hid}.json"
    if not src.exists():
        sys.exit(f"✗ {src.relative_to(VAULT)} absent : simuler puis appliquer l'hypothèse d'abord.")
    return json.loads(src.read_text(encoding="utf-8"))


def suivi_path(hid):
    return ap.APP_DIR / f"{hid}.main.json"


def lire_suivi(hid):
    try:
        return json.loads(suivi_path(hid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"entites": {}, "regles": {}}


def ecrire_suivi(hid, s):
    suivi_path(hid).write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def maintenant():
    return datetime.now().isoformat(timespec="minutes")


def noms_de_zones(sc):
    p = VAULT / "geographie" / f"{sc}.md"
    if not p.exists():
        return {}
    d = ap.decoupe(p.read_text(encoding="utf-8"))
    fm = ap.lire_fm(d[1]) if d else None
    return {z["slug"]: z.get("nom") or z["slug"] for z in (fm or {}).get("zones") or []
            if isinstance(z, dict) and z.get("slug")}


# ---------------------------------------------------------------------------
# 1. Nouvelles entités
# ---------------------------------------------------------------------------

# Catégorie devinée d'après le nom, puis le rôle (simulations sans catégorie de l'IA,
# avant v8.21). Premier groupe qui trouve un début de mot ; à défaut « organisation ».
INDICES_CATEGORIE = [
    ("média", ["presse", "journal", "radio", "chaine", "media", "gazette", "tribune", "magazine"]),
    ("IA", ["ia", "intelligence artificielle", "algorithme", "oracle", "cerveau"]),
    ("institution", ["commission", "autorite", "agence", "conseil", "tribunal", "cour", "ministere", "office",
                     "bureau", "parlement", "gouvernement", "administration", "haut-commissariat", "regulat",
                     "secretariat", "assemblee", "senat", "directoire", "observatoire", "institut"]),
    ("entreprise", ["consortium", "holding", "societe", "compagnie", "corporation", "entreprise",
                    "conglomerat", "firme", "industries", "trust", "banque"]),
    ("réseau", ["reseau", "alliance", "network", "maillage", "toile", "circuit", "filiere"]),
    ("infrastructure", ["port", "station", "barrage", "centrale", "cable", "pipeline", "gazoduc", "oleoduc",
                        "plateforme", "terminal", "digue", "usine", "ferme", "chantier", "arche", "silo"]),
    ("système", ["systeme", "protocole", "programme", "mecanisme", "dispositif", "regime", "standard",
                 "norme", "doctrine", "plan"]),
    ("territoire", ["enclave", "territoire", "cite-etat", "zone autonome", "republique", "comte", "canton"]),
    ("humain", ["docteur", "general", "generale", "professeur", "capitaine", "commandant", "pere", "mere",
                "soeur", "frere", "prophete"]),
    ("organisation", ["fonds", "fondation", "mouvement", "ligue", "coalition", "front", "collectif",
                      "association", "union", "federation", "ordre", "confrerie", "syndicat", "milice",
                      "cartel", "brigade", "communaute", "cooperative", "comite", "groupe"]),
]


def _plie(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or "").lower().replace("’", "'"))
    return "".join(c for c in s if not unicodedata.combining(c))


def deviner_categorie(nom, role):
    for texte in (_plie(nom), _plie(role)):
        for cat, mots in INDICES_CATEGORIE:
            # mot court (ia, port, plan…) : mot entier, pluriel admis ; sinon début de mot
            if any(re.search(r"(?<![a-z])" + re.escape(m) + (r"s?(?![a-z])" if len(m) <= 5 else ""), texte)
                   for m in mots):
                return cat
    return "organisation"


def entites_proposees(data, categories=None):
    out = []
    for sc in data["scenarios"]:
        lec = ((data["par_scenario"].get(sc) or {}).get("lecture")) or {}
        zones = noms_de_zones(sc)
        for n, e in enumerate(lec.get("nouvelles_entites") or [], 1):
            z = str(e.get("zone") or "").strip()
            d = {"cle": f"{sc}:{n}", "sc": sc, "nom": str(e.get("nom") or "").strip(),
                 "role": " ".join(str(e.get("role") or "").split()),
                 "raison": " ".join(str(e.get("raison") or "").split()),
                 "zone": z, "zone_nom": zones.get(z) or (z or None)}
            # v8.21 : catégorie de la lecture IA si valide, sinon devinée d'après le nom.
            ia = str(e.get("category") or "").strip()
            if ia and (categories is None or ia in categories):
                d["category_proposee"], d["source_categorie"] = ia, "ia"
            else:
                g = deviner_categorie(d["nom"], d["role"])
                if categories is None or g in categories:
                    d["category_proposee"], d["source_categorie"] = g, "nom"
            out.append(d)
    return out


def statut_entite(e, suivi, m, file_noms, existants):
    if m.slugify(e["nom"]) in existants:
        return "créée", "l'entité existe déjà dans le vault"
    if e["nom"].lower() in file_noms:
        s = suivi["entites"].get(e["cle"])
        return "dans la file", (f"ajoutée le {s['date']} ({s['category']}) : lancer « Créer des entités »"
                                if s else "déjà dans entites_custom/queue.yaml")
    if e["cle"] in suivi["entites"]:
        return "traitée", "ajoutée à la file puis retirée (créée ou rejetée : voir processed / needs_review)"
    return "proposée", ""


def entree_file(e, hid, category):
    return {"nom": e["nom"], "category": category, "role": e["role"], "etat": "émergent",
            "scenario_ref": e["sc"], "scenario_hint": [e["sc"]], "zone_hint": e["zone_nom"],
            "source": f"et_si_{hid}" + (f" — {e['raison']}" if e["raison"] else "")}


def ajouter_entites(hid, data, choix, apply):
    m = cei()
    suivi = lire_suivi(hid)
    proposees = {e["cle"]: e for e in entites_proposees(data)}
    file = m.load_yaml_list(m.QUEUE_PATH)
    file_noms = {str(x.get("nom") or "").strip().lower() for x in file if isinstance(x, dict)}
    existants = {str(x.get("slug") or "") for x in m.load_entities_list() if isinstance(x, dict)}
    nouvelles, erreurs = [], []
    for c in choix:
        e = proposees.get(str(c.get("cle")))
        cat = str(c.get("category") or "").strip()
        if not e:
            erreurs.append(f"{c.get('cle')} : entité proposée inconnue")
            continue
        if cat not in m.VALID_CATEGORIES:
            erreurs.append(f"{e['nom']} : catégorie {cat or '(vide)'} invalide "
                           f"({', '.join(m.VALID_CATEGORIES)})")
            continue
        st, detail = statut_entite(e, suivi, m, file_noms, existants)
        if st in ("créée", "dans la file"):
            erreurs.append(f"{e['nom']} : {detail}")
            continue
        nouvelles.append((e, cat))
    print(("ÉCRITURE" if apply else "APERÇU (rien écrit)") + f" — entités de {hid}\n")
    for e, cat in nouvelles:
        print(f"  + {e['nom']} ({cat}) — {e['sc']}" + (f", ancrée à {e['zone_nom']}" if e["zone_nom"] else ""))
    for x in erreurs:
        print(f"  ✗ {x}")
    if not nouvelles:
        print("\nRien à ajouter.")
        return 1 if erreurs else 0
    if erreurs:
        print("\n✗ Rien n'est écrit tant qu'un choix est refusé : corriger ou décocher les lignes ✗.")
        return 1
    if not apply:
        print(f"\n{len(nouvelles)} entrée(s) prête(s) pour entites_custom/queue.yaml. Relancer avec --apply.")
        return 0
    if m.QUEUE_PATH.exists():
        shutil.copy2(m.QUEUE_PATH, m.QUEUE_PATH.with_name("queue.yaml.bak_et_si_main"))
    m.save_queue_with_template(file + [entree_file(e, hid, cat) for e, cat in nouvelles])
    relue = {str(x.get("nom") or "").strip().lower() for x in m.load_yaml_list(m.QUEUE_PATH)}
    manquantes = [e["nom"] for e, _ in nouvelles if e["nom"].lower() not in relue]
    if manquantes:
        sys.exit("✗ relecture de la file : manquent " + ", ".join(manquantes)
                 + " (sauvegarde : entites_custom/queue.yaml.bak_et_si_main)")
    for e, cat in nouvelles:
        suivi["entites"][e["cle"]] = {"date": maintenant(), "nom": e["nom"], "category": cat}
    ecrire_suivi(hid, suivi)
    print(f"\n✓ {len(nouvelles)} entité(s) ajoutée(s) à entites_custom/queue.yaml "
          "(sauvegarde queue.yaml.bak_et_si_main).")
    print("  Création : « Créer des entités » (python3 generator/create_entities_and_instances.py --mode custom) ;"
          " appels IA, traite toute la file.")
    return 0


# ---------------------------------------------------------------------------
# 2. Règle de lore
# ---------------------------------------------------------------------------

def brouillons_regles(data):
    """Brouillon par scénario : une règle par entité disparue (opération appliquée),
    contraintes de l'hypothèse en commentaires (même contenu que la check-list)."""
    ops, _ = ap.construire_plan(data)
    annee = int(data["annee"]) if data.get("annee") is not None else None
    out = {}
    for sc in data["scenarios"]:
        regles = []
        for o in ops:
            if o["sc"] != sc or o["genre"] != "trajectoire" or o.get("apres") != "disparu":
                continue
            if not str(o.get("alerte") or "").startswith("déjà"):
                continue   # pas (encore) appliquée
            nom = re.sub(r"\s*\(`.*$", "", o["texte"])
            court = o["instance"][: -len(sc) - 1] if o["instance"].endswith("_" + sc) else o["instance"]
            regles.append({"id": f"{court}_disparu_{annee}", "gravite": "a_relire",
                           "termes": ap.termes_disparition(nom, o["instance"], sc),
                           "message": f"{nom} disparaît en {annee} ({data.get('nom') or data['id']}) : "
                                      f"toute mention au présent après {annee} est fausse."})
        texte = yaml.safe_dump(regles, allow_unicode=True, sort_keys=False, width=1000) if regles else ""
        texte += "".join(f"# contrainte à transformer si besoin : {c}\n" for c in data.get("contraintes") or [])
        out[sc] = texte
    return out


def ids_existants(contenu):
    data = yaml.safe_load(contenu) or {}
    ids = []
    for sec in data.values() if isinstance(data, dict) else []:
        for r in ((sec or {}).get("regles") or []) if isinstance(sec, dict) else []:
            if isinstance(r, dict) and r.get("id"):
                ids.append(str(r["id"]))
    return ids


def verifier_regles(texte, existants):
    try:
        regles = yaml.safe_load(texte)
    except yaml.YAMLError as e:
        return None, [f"YAML illisible : {str(e).splitlines()[0]}"]
    if isinstance(regles, dict):
        regles = [regles]
    if not isinstance(regles, list) or not regles:
        return None, ["aucune règle (le brouillon ne contient que des commentaires ?)"]
    err, vus = [], set()
    for n, r in enumerate(regles, 1):
        ou = f"règle n°{n}"
        if not isinstance(r, dict):
            err.append(f"{ou} : doit être un dictionnaire (id, gravite, termes, message)")
            continue
        rid = str(r.get("id") or "")
        ou = f"règle `{rid or n}`"
        if not SLUG_REGLE.match(rid):
            err.append(f"{ou} : `id` en minuscules, chiffres et _ seulement")
        elif rid in existants or rid in vus:
            err.append(f"{ou} : identifiant déjà utilisé dans lore_regles.yaml")
        vus.add(rid)
        if r.get("gravite") not in GRAVITES:
            err.append(f"{ou} : `gravite` doit valoir erreur ou a_relire")
        termes, mp = r.get("termes"), r.get("meme_phrase")
        ok_termes = isinstance(termes, list) and termes and all(isinstance(t, str) and t.strip() for t in termes)
        ok_mp = (isinstance(mp, list) and len(mp) == 2
                 and all(isinstance(g, list) and g and all(isinstance(t, str) for t in g) for g in mp))
        if not (ok_termes or ok_mp):
            err.append(f"{ou} : `termes` (liste de mots) ou `meme_phrase` (deux listes) requis")
        if not str(r.get("message") or "").strip():
            err.append(f"{ou} : `message` requis (il s'affiche dans le rapport d'audit)")
    return regles, err


def inserer_regles(contenu, sc, regles):
    """Insère les règles à la fin de la liste `regles` de la section `sc` (créée si
    besoin), sans toucher au reste du fichier ni à ses commentaires."""
    bloc = ["    " + l if l.strip() else l for l in
            yaml.safe_dump(regles, allow_unicode=True, sort_keys=False, width=100).rstrip("\n").split("\n")]
    L = contenu.split("\n")
    debut = next((i for i, l in enumerate(L) if re.match(rf"^{re.escape(sc)}:\s*$", l)), None)
    if debut is None:
        while L and not L[-1].strip():
            L.pop()
        return "\n".join(L + ["", f"{sc}:", "", "  regles:", ""] + bloc) + "\n"
    fin = next((i for i in range(debut + 1, len(L)) if re.match(r"^[A-Za-z_]", L[i])), len(L))
    k = next((i for i in range(debut + 1, fin) if re.match(r"^  regles:", L[i])), None)
    if k is None:
        der = max([i for i in range(debut, fin) if L[i].strip()] or [debut])
        return "\n".join(L[:der + 1] + ["", "  regles:", ""] + bloc + L[der + 1:])
    if re.match(r"^  regles:\s*\[\s*\]\s*(#.*)?$", L[k]):
        return "\n".join(L[:k] + ["  regles:", ""] + bloc + L[k + 1:])
    fin_regles = next((i for i in range(k + 1, fin)
                       if L[i].strip() and not L[i].lstrip().startswith("#")
                       and len(L[i]) - len(L[i].lstrip()) <= 2), fin)
    der = max(i for i in range(k, fin_regles) if L[i].strip())
    return "\n".join(L[:der + 1] + [""] + bloc + L[der + 1:])


def ajouter_regle(hid, data, sc, texte, apply):
    if sc not in data["scenarios"]:
        sys.exit(f"✗ scénario {sc} hors de l'hypothèse ({', '.join(data['scenarios'])})")
    if not LORE.exists():
        sys.exit(f"✗ {LORE.relative_to(VAULT)} introuvable")
    contenu = LORE.read_text(encoding="utf-8")
    avant = yaml.safe_load(contenu) or {}
    regles, err = verifier_regles(texte, set(ids_existants(contenu)))
    print(("ÉCRITURE" if apply else "APERÇU (rien écrit)") + f" — règle(s) de lore pour {sc}\n")
    if err:
        print("✗ Refusé :\n" + "\n".join(f"  - {e}" for e in err))
        return 1
    nouveau = inserer_regles(contenu, sc, regles)
    try:
        apres = yaml.safe_load(nouveau) or {}
    except yaml.YAMLError as e:
        print(f"✗ le fichier ne serait plus lisible ({e}) : rien écrit.")
        return 1
    ids_sc = [str(r.get("id")) for r in ((apres.get(sc) or {}).get("regles") or [])]
    autres_ok = all(apres.get(k) == v for k, v in avant.items() if k != sc)
    if not all(r["id"] in ids_sc for r in regles) or not autres_ok:
        print("✗ contrôle après insertion en échec (section mal repérée) : rien écrit.")
        return 1
    for r in regles:
        print(f"  + {r['id']} ({r['gravite']}) : {r.get('termes') or r.get('meme_phrase')}")
    if not apply:
        print(f"\nPrête(s) pour documentation/lore_regles.yaml, section {sc}. Relancer avec --apply.")
        return 0
    shutil.copy2(LORE, LORE.with_name("lore_regles.yaml.bak_et_si"))
    LORE.write_text(nouveau, encoding="utf-8")
    suivi = lire_suivi(hid)
    for r in regles:
        suivi["regles"][f"{sc}:{r['id']}"] = maintenant()
    ecrire_suivi(hid, suivi)
    print(f"\n✓ {len(regles)} règle(s) ajoutée(s) (sauvegarde lore_regles.yaml.bak_et_si). "
          f"Vérifier : « Relecture du lore » ({sc}).")
    return 0


# ---------------------------------------------------------------------------
# 2 bis. Phrases à corriger (morceau 2, 18 octobre 2026)
#   - phrases relevées par la passe exhaustive (data.par_scenario.<sc>.passe.textes) ;
#   - phrases de la fiche d'événement qui contredisent les faits de l'hypothèse
#     (vérification IA, une par scénario, gardée seulement si l'extrait est retrouvé).
#   L'IA propose une réécriture ; rien n'est écrit sans --apply ; tout est mis en
#   cache dans le suivi (aucun appel refait sans --refaire).
# ---------------------------------------------------------------------------

def _norm(s):
    return " ".join(str(s or "").split())


def motif_phrase(extrait):
    """Regex tolérante : espaces et retours à la ligne (scalaires YAML repliés),
    apostrophes droites, courbes ou doublées (scalaire entre apostrophes)."""
    mots = _norm(extrait).split(" ")
    morceaux = [re.sub(r"['’]", "['’]{1,2}", re.escape(m).replace("\\'", "'")) for m in mots if m]
    return re.compile(r"\s+".join(morceaux)) if morceaux else None


def chemin_fiche(genre, slug):
    return VAULT / ("instances" if genre == "instance" else "event_instances") / f"{slug}.md"


def cle_phrase(sc, slug, extrait):
    import hashlib
    return f"{sc}:{slug}:{hashlib.sha1(_norm(extrait).encode('utf-8')).hexdigest()[:8]}"


VERSION_RELECTURE = "v3-etats-cites"   # entre dans l'empreinte du cache : changer = relire à nouveau


_RETENUES = {}


def retenues(data):
    """PATCH_S27_APPLIQUEE : None si l'hypothèse n'est pas appliquée (toute la lecture compte) ;
    sinon {(sc, "t"|"z"): slugs} des trajectoires et statuts de zone APPLIQUÉS (état actuel = résultat)."""
    hid = data.get("id")
    if hid not in _RETENUES:
        if not (ap.APP_DIR / f"{hid}.applique.json").exists():
            _RETENUES[hid] = None
        else:
            ops, _ = ap.construire_plan(data)
            r = {}
            for o in ops:
                if o.get("alerte") == "déjà appliqué" and o["genre"] == "trajectoire":
                    r.setdefault((o["sc"], "t"), set()).add(o["instance"])
                elif o.get("alerte") == "déjà appliqué" and o["genre"] == "zone":
                    r.setdefault((o["sc"], "z"), set()).add(o["zone"])
            _RETENUES[hid] = r
    return _RETENUES[hid]


def garde_traj(data, sc, t):
    r = retenues(data)
    return r is None or t.get("instance") in r.get((sc, "t"), set())


def garde_zone(data, sc, z):
    r = retenues(data)
    return r is None or z.get("zone") in r.get((sc, "z"), set())


def _annee(data):
    a = data.get("annee")
    try:
        return int(a) if float(a) == int(float(a)) else a
    except (TypeError, ValueError):
        return a


def etats_entites(data, sc):
    """[(nom, avant, après)] des entités dont l'hypothèse change la trajectoire."""
    ps = data["par_scenario"].get(sc) or {}
    out, vus = [], set()
    for t in ((ps.get("lecture") or {}).get("trajectoires") or []) + ((ps.get("passe") or {}).get("trajectoires") or []):
        if t.get("instance") in vus or not garde_traj(data, sc, t):   # PATCH_S27_APPLIQUEE
            continue
        vus.add(t.get("instance"))
        out.append((t.get("nom") or t.get("instance"), t.get("avant"), t.get("apres")))
    return out


_NOMS_INSTANCES = {}


def trajectoires_du_scenario(sc):
    """{nom: trajectoire actuelle} des instances du scénario (lu une fois)."""
    if sc not in _NOMS_INSTANCES:
        out = {}
        for p in sorted(ap.INSTANCES.glob(f"*_{sc}.md")):
            d = ap.decoupe(p.read_text(encoding="utf-8"))
            fm = ap.lire_fm(d[1]) if d else None
            if fm and fm.get("name") and fm.get("trajectoire"):
                out[str(fm["name"]).strip()] = str(fm["trajectoire"])
        _NOMS_INSTANCES[sc] = out
    return _NOMS_INSTANCES[sc]


def etats_cites(data, sc, texte):
    """Lignes « État de X » pour TOUTES les entités nommées dans `texte` : avant / après pour
    celles que l'hypothèse change, état actuel (inchangé) pour les autres."""
    pt = _plie(texte)
    annee = _annee(data)
    lignes, vus = [], set()
    for nom, av, apr in etats_entites(data, sc):
        if nom and _plie(nom) in pt:
            lignes.append(f"- {nom} : avant {annee} = « {av} » ; après {annee} = « {apr} »")
            vus.add(_plie(nom))
    for nom, traj in trajectoires_du_scenario(sc).items():
        if len(nom) >= 4 and _plie(nom) in pt and _plie(nom) not in vus:
            lignes.append(f"- {nom} : « {traj} », inchangé par l'hypothèse (avant comme après {annee})")
            vus.add(_plie(nom))
    return lignes


def faits_hypothese(data, sc):
    """Faits établis par l'hypothèse dans ce scénario (contraintes, trajectoires, zones)."""
    annee = _annee(data)
    ps = data["par_scenario"].get(sc) or {}
    lec, pas = ps.get("lecture") or {}, ps.get("passe") or {}
    faits = [str(c) for c in data.get("contraintes") or []]
    vus = set()
    for t in (lec.get("trajectoires") or []) + (pas.get("trajectoires") or []):
        if t.get("instance") in vus or not garde_traj(data, sc, t):   # PATCH_S27_APPLIQUEE
            continue
        vus.add(t.get("instance"))
        nom = t.get("nom") or t.get("instance")
        if t.get("apres") == "disparu":
            faits.append(f"{nom} disparaît en {annee} : après {annee}, il n'existe plus (passé seulement).")
        else:
            faits.append(f"{nom} passe de « {t.get('avant')} » à « {t.get('apres')} » après {annee} : "
                         f"avant {annee}, il était « {t.get('avant')} », pas davantage.")
    for z in [z for z in lec.get("zones_statut") or [] if garde_zone(data, sc, z)]:   # PATCH_S27_APPLIQUEE
        faits.append(f"La zone {z.get('zone')} passe de « {z.get('avant')} » à « {z.get('apres')} » ; le lieu subsiste.")
    return faits


def ia_json(system, user, max_tokens=1500):
    from llm_client import call_llm
    texte = call_llm(system_prompt=system, user_prompt=user, max_tokens=max_tokens, temperature=0.3,
                     task_tier="structured_strict")
    texte = (texte or "").strip()
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut < 0 or fin <= debut:
        raise ValueError("réponse IA sans JSON")
    return json.loads(texte[debut:fin + 1])


# Réponses de l'IA qui avouent n'avoir rien trouvé de contraire (omission, simple précision) :
# écartées, malgré la consigne qui le dit déjà.
PAS_UNE_CONTRADICTION = re.compile(r"aucune contradiction|pas de contradiction|pas une contradiction|omission"
                                   r"|pourrait etre (clarifie|precise)|a preciser|manque de precision")


def vraie_contradiction(fait):
    return not PAS_UNE_CONTRADICTION.search(_plie(fait))


# PATCH_S27_RELECTURE (24 oct 2026) : articles seulement. Justification au conditionnel ou par
# sous-entendu = pas une contradiction établie (7 faux positifs sur 7 avec pacte_tabriz_2058).
CONDITIONNEL = re.compile(r"pourrait|pourraient|peut contredire|peut evoquer|peut sembler|sous-entend"
                          r"|implicitement|suggere|laisse entendre|minimis")


def contradiction_article(fait, extrait=None, data=None, sc=None):
    if not vraie_contradiction(fait) or CONDITIONNEL.search(_plie(fait)):
        return False
    if data is None:
        return True
    # PATCH_S27_APPLIQUEE : la justification doit porter sur une conséquence de l'hypothèse.
    pf, pe = _plie(fait), _plie(extrait)
    cite = lambda nom: bool(nom) and (_plie(nom) in pf or forme_approchee(nom, pf))
    changes = [apr for nom, av, apr in etats_entites(data, sc) if cite(nom)]
    zn = noms_de_zones(sc)
    ps = data["par_scenario"].get(sc) or {}
    zones = [z.get("zone") for z in (ps.get("lecture") or {}).get("zones_statut") or []
             if z.get("zone") and garde_zone(data, sc, z)]
    cite_zone = any(_plie(s) in pf or _plie(zn.get(s, "")) in pf for s in zones if s)
    if not changes and not cite_zone:
        if any(len(n) >= 4 and cite(n) for n in trajectoires_du_scenario(sc)):
            return False   # ne parle que d'entités inchangées
    if changes and not cite_zone and all(_plie(a) in MONTEE for a in changes) and not DECLIN.search(pe):
        return False       # rang qui monte, extrait sans déclin ni disparition
    return True


MONTEE = {"ascendant", "dominant", "mature"}
DECLIN = re.compile(r"dispar|effondr|declin|n'existe plus|detrui|dissou|marginal|agonis|moribond|eteint"
                    r"|residuel|abandonn|ruine|chute|vaincu|liquide")


def territoires_zones(data, sc, max_par_zone=25):
    """Lignes « zone : territoires » pour les zones dont l'hypothèse change le statut."""
    ps = data["par_scenario"].get(sc) or {}
    zones = [z.get("zone") for z in (ps.get("lecture") or {}).get("zones_statut") or []
             if z.get("zone") and garde_zone(data, sc, z)]   # PATCH_S27_APPLIQUEE
    if not zones:
        return []
    by = {z.get("slug"): z for z in ap.zones_geo(sc)}
    lignes = []
    for slug in dict.fromkeys(zones):
        z = by.get(slug) or {}
        ents = [str(o.get("entite")) for o in z.get("origine_reelle") or [] if isinstance(o, dict) and o.get("entite")]
        if ents:
            plus = f" (+{len(ents) - max_par_zone})" if len(ents) > max_par_zone else ""
            lignes.append(f"- {z.get('nom') or slug} ({slug}) : {', '.join(ents[:max_par_zone])}{plus}")
    return lignes


SYSTEME_RELECTEUR = ("Tu es le relecteur du lore du monde fictif Ourrassol 2098. Tu corriges le moins possible. "
                     "Réponds UNIQUEMENT en JSON valide, sans texte autour.")


def verifier_evenement(data, sc, suivi, refaire):
    """Phrases de la fiche d'événement qui contredisent les faits (un appel IA, en cache)."""
    p = chemin_fiche("evenement", f"{data['id']}_{sc}")
    if not p.exists():
        return []
    raw = p.read_text(encoding="utf-8")
    import hashlib
    emp = hashlib.sha1((VERSION_RELECTURE + raw).encode("utf-8")).hexdigest()[:12]
    cache = suivi.setdefault("verif_evenement", {})
    if not refaire and (cache.get(sc) or {}).get("empreinte") == emp:
        return cache[sc]["problemes"]
    d = ap.decoupe(raw)
    fm = ap.lire_fm(d[1]) if d else {}
    texte = "\n".join(f"{k} : {_norm(fm.get(k))}" for k in ("realisation", "description", "consequences") if fm.get(k))
    faits = faits_hypothese(data, sc)
    if not texte or not faits:
        return []
    user = (f"FICHE D'ÉVÉNEMENT « {fm.get('name') or data['id']} » (scénario {sc}) :\n{texte}\n\n"
            "FAITS ÉTABLIS (priment sur la fiche) :\n" + "\n".join(f"- {f}" for f in faits) + "\n\n"
            + ("ÉTATS DES ENTITÉS CITÉES DANS LA FICHE (seule référence pour leur rang : une phrase conforme "
               "à ces états n'est JAMAIS une contradiction) :\n" + "\n".join(etats_cites(data, sc, texte)) + "\n\n"
               if etats_cites(data, sc, texte) else "") +
            "TÂCHE : relève UNIQUEMENT les phrases qui contredisent un fait, c'est-à-dire :\n"
            "- une entité à qui la phrase donne, AVANT l'événement, un état plus avancé que son état d'avant "
            "(« déjà dominante » alors qu'elle était émergente) ;\n"
            "- une entité à qui la phrase donne, APRÈS l'événement, un état contraire à son état d'après "
            "(active alors qu'elle a disparu, déclinante alors qu'elle devient dominante) ;\n"
            "- une zone décrite comme détruite ou disparue alors que le lieu subsiste ; une contrainte niée.\n"
            "NE SONT PAS des contradictions : décrire une entité qui se renforce, s'étend ou gagne en influence "
            "quand son état progresse ; parler de sa géographie, de ses activités ou de ses moyens ; une omission. "
            "En cas de doute, ne relève pas la phrase : la réponse attendue la plupart du temps est une liste vide.\n"
            "Pour chaque phrase : \"extrait\" = la phrase entière, MOT POUR MOT ; \"fait\" = le fait contredit ; "
            "\"correction\" = la phrase réécrite en changeant le moins de mots possible, avec l'état d'avant ou "
            "d'après EXACT (jamais un état intermédiaire inventé), sans fait nouveau.\n"
            'Format : {"problemes": [{"extrait": "...", "fait": "...", "correction": "..."}]}')
    res = ia_json(SYSTEME_RELECTEUR, user)
    problemes = []
    for x in res.get("problemes") or []:
        if not isinstance(x, dict) or not x.get("extrait"):
            continue
        m = motif_phrase(x["extrait"])
        if m and m.search(raw) and vraie_contradiction(x.get("fait")):   # extrait retrouvé, vraie contradiction
            problemes.append({"extrait": _norm(x["extrait"]), "fait": _norm(x.get("fait")),
                              "correction": _norm(x.get("correction"))})
    cache[sc] = {"empreinte": emp, "date": maintenant(), "problemes": problemes}
    return problemes


def phrases_a_corriger(data, suivi):
    out = []
    for sc in data["scenarios"]:
        pas = ((data["par_scenario"].get(sc) or {}).get("passe")) or {}
        for t in pas.get("textes") or []:
            genre = t.get("genre", "instance")
            out.append({"sc": sc, "slug": t["slug"], "genre": genre, "nom": t.get("nom") or t["slug"],
                        "extrait": _norm(t.get("extrait")), "contredit": _norm(t.get("contredit")),
                        "source": "passe", "proposition": None})
        for x in ((suivi.get("verif_evenement") or {}).get(sc) or {}).get("problemes") or []:
            out.append({"sc": sc, "slug": f"{data['id']}_{sc}", "genre": "evenement", "nom": "fiche de l'événement",
                        "extrait": x["extrait"], "contredit": x["fait"], "source": "evenement",
                        "proposition": x.get("correction") or None})
    ph = suivi.get("phrases") or {}
    for e in out:
        e["cle"] = cle_phrase(e["sc"], e["slug"], e["extrait"])
        e["fichier"] = str(chemin_fiche(e["genre"], e["slug"]).relative_to(VAULT))
        s = ph.get(e["cle"]) or {}
        e["proposition"] = s.get("proposition") or e["proposition"]
        e["statut"] = s.get("statut") or ""
        p = VAULT / e["fichier"]
        m = motif_phrase(e["extrait"])
        e["trouve"] = bool(p.exists() and m and m.search(p.read_text(encoding="utf-8")))
        if not e["statut"] and not e["trouve"]:
            e["statut"] = "introuvable"
    return out


def proposer_phrases(hid, data, refaire):
    suivi = lire_suivi(hid)
    ph = suivi.setdefault("phrases", {})
    n_ia = 0
    for sc in data["scenarios"]:
        avant = (suivi.get("verif_evenement") or {}).get(sc)
        trouves = verifier_evenement(data, sc, suivi, refaire)
        if (suivi.get("verif_evenement") or {}).get(sc) is not avant:
            n_ia += 1
            print(f"[{sc}] fiche d'événement relue : {len(trouves)} phrase(s) contredisent les faits")
        ecrire_suivi(hid, suivi)
    for e in phrases_a_corriger(data, suivi):
        if e["statut"] or (e["proposition"] and not refaire) or not e["trouve"]:
            continue
        p = VAULT / e["fichier"]
        d = ap.decoupe(p.read_text(encoding="utf-8"))
        fm = ap.lire_fm(d[1]) if d else {}
        contexte = " ".join(_norm(v) for k, v in (fm or {}).items()
                            if isinstance(v, str) and _norm(e["extrait"])[:40] in _norm(v))[:1200]
        etats = etats_cites(data, e["sc"], e["extrait"] + " " + e["contredit"])
        user = (f"FICHE : {e['nom']} ({e['fichier']}), scénario {e['sc']}.\n"
                f"FAIT ÉTABLI PAR L'HYPOTHÈSE {data['id']} (année {_annee(data)}) : {e['contredit']}\n"
                + ("ÉTATS DES ENTITÉS CITÉES (à respecter exactement, jamais d'état intermédiaire) :\n"
                   + "\n".join(etats) + "\n" if etats else "") +
                f"PHRASE DEVENUE FAUSSE : « {e['extrait']} »\n"
                f"TEXTE AUTOUR : {contexte}\n\n"
                "Réécris CETTE phrase seulement, pour qu'elle soit vraie en 2098 compte tenu du fait établi : "
                "garde le ton, la longueur et ce qui reste vrai ; mets au passé ce qui a cessé ; n'ajoute "
                "aucun fait nouveau, aucun nom nouveau.\n"
                'Format : {"phrase": "..."}')
        res = ia_json(SYSTEME_RELECTEUR, user, max_tokens=800)
        if res.get("phrase"):
            ph[e["cle"]] = {"proposition": _norm(res["phrase"]), "date": maintenant()}
            n_ia += 1
            print(f"  ✓ proposition pour `{e['fichier']}`")
        ecrire_suivi(hid, suivi)
    print(f"\n{n_ia} appel(s) IA. Relire chaque proposition avant de remplacer.")
    return 0


def _echapper_pour(raw, debut, texte):
    """Adapte la phrase au style YAML de la ligne où elle tombe (frontmatter seulement)."""
    d = ap.decoupe(raw)
    if not d or debut > len(d[0]) + len(d[1]):
        return texte   # corps du fichier : texte libre
    ligne = raw[raw.rfind("\n", 0, debut) + 1:debut]
    sous = raw[:debut]
    cle = re.findall(r"(?m)^[A-Za-z_]+:\s*(.*)$", sous)
    style = cle[-1].strip()[:1] if cle else ""
    if style == "'" or ligne.lstrip().startswith("'"):
        return texte.replace("'", "''")
    if style == '"':
        return texte.replace("\\", "\\\\").replace('"', '\\"')
    return texte


def remplacer_phrase(hid, data, cle, nouveau, ignorer, apply):
    suivi = lire_suivi(hid)
    items = {e["cle"]: e for e in phrases_a_corriger(data, suivi)}
    e = items.get(cle)
    if not e:
        sys.exit(f"✗ phrase {cle} inconnue")
    ph = suivi.setdefault("phrases", {})
    if ignorer:
        ph.setdefault(cle, {})["statut"] = "ignorée"
        ecrire_suivi(hid, suivi)
        print(f"· phrase de `{e['fichier']}` marquée « ignorée » (rien écrit dans la fiche).")
        return 0
    nouveau = _norm(nouveau)
    print(("ÉCRITURE" if apply else "APERÇU (rien écrit)") + f" — `{e['fichier']}`\n")
    if (ph.get(cle) or {}).get("statut") == "corrigée":
        print(f"· déjà corrigée le {ph[cle].get('date_correction')} : « {ph[cle].get('remplacee_par')} »")
        return 0
    if not nouveau:
        print("✗ phrase de remplacement vide.")
        return 1
    p = VAULT / e["fichier"]
    raw = p.read_text(encoding="utf-8")
    m = motif_phrase(e["extrait"])
    occ = list(m.finditer(raw)) if m else []
    if not occ:
        print("✗ phrase introuvable dans la fiche (déjà modifiée ?) : à faire à la main.")
        return 1
    morceaux, pos = [], 0
    for o in occ:
        texte = nouveau
        # Pas de ponctuation doublée : l'extrait s'arrête souvent avant le point final de la fiche.
        if re.match(r"\s*[.!?…]", raw[o.end():o.end() + 3]) and texte[-1:] in ".!?…":
            texte = texte.rstrip(".!?…").rstrip()
        morceaux += [raw[pos:o.start()], _echapper_pour(raw, o.start(), texte)]
        pos = o.end()
    neuf = "".join(morceaux) + raw[pos:]
    dn = ap.decoupe(neuf)
    fm = ap.lire_fm(dn[1]) if dn else None
    if dn and fm is None:
        print("✗ le frontmatter ne serait plus lisible après remplacement : à faire à la main.")
        return 1
    print(f"Avant : « {e['extrait']} »\nAprès : « {nouveau} »\n({len(occ)} occurrence(s) : frontmatter et corps)")
    if not apply:
        print("\nPrêt. Cliquer sur « Remplacer » pour écrire.")
        return 0
    bak = p.with_name(p.name + ".bak_et_si_main")
    if not bak.exists():
        shutil.copy2(p, bak)
    p.write_text(neuf, encoding="utf-8")
    ph[cle] = dict(ph.get(cle) or {}, statut="corrigée", remplacee_par=nouveau, date_correction=maintenant())
    ecrire_suivi(hid, suivi)
    print(f"\n✓ phrase remplacée (sauvegarde {bak.name}).")
    return 0


# ---------------------------------------------------------------------------
# 2 ter. Articles à relire (morceau 3, 18 octobre 2026) -- REPÉRAGE seulement :
#   les articles publiés ne sont jamais modifiés par l'outil. L'IA relève, dans
#   chaque article concerné, les passages qui contredisent les faits de
#   l'hypothèse (gardés seulement s'ils sont retrouvés mot pour mot) ; la
#   correction se fait à la main dans Obsidian, puis « marquer comme relu ».
# ---------------------------------------------------------------------------

VERSION_ARTICLES = "v3-appliquee"   # PATCH_S27_RELECTURE
MAX_ARTICLE = 14000   # caractères de corps envoyés à l'IA


def articles_a_relire(data):
    """[(sc, chemin relatif, titre, date, motifs)] : articles qui citent une entité touchée
    ou dont la zone principale a changé (même règle que la check-list)."""
    out = []
    for sc in data["scenarios"]:
        ps = data["par_scenario"].get(sc) or {}
        lec, pas = ps.get("lecture") or {}, ps.get("passe") or {}
        ents = sorted({t["instance"] for t in (lec.get("trajectoires") or []) + (pas.get("trajectoires") or [])
                       if t.get("instance") and garde_traj(data, sc, t)})   # PATCH_S27_APPLIQUEE
        zones = {z["zone"] for z in lec.get("zones_statut") or [] if z.get("zone") and garde_zone(data, sc, z)}
        vus = set()
        for chemin, titre, date, motifs in ap._articles_concernes(sc, ents, zones):
            out.append((sc, str(chemin), titre, date, motifs))
            vus.add(str(chemin))
        # Élargissement (18 oct) : articles qui NOMMENT une entité touchée ou une zone changée dans
        # leur texte, sans l'avoir dans entites_citees / zone_principale. Sans IA.
        noms = {t.get("nom") for t in (lec.get("trajectoires") or []) + (pas.get("trajectoires") or [])
                if garde_traj(data, sc, t)}   # PATCH_S27_APPLIQUEE
        zn = noms_de_zones(sc)
        noms |= {zn.get(z) for z in zones}
        motifs_noms = [(n, re.compile(r"(?<![a-z0-9])" + re.escape(_plie(n)) + r"(?![a-z0-9])"))
                       for n in sorted(x for x in noms if x and len(x) >= 6)]
        racine = VAULT / "articles"
        for p in sorted(racine.rglob("*.md")) if racine.exists() and motifs_noms else []:
            chemin = str(p.relative_to(VAULT))
            if p.name.startswith("_") or chemin in vus:
                continue
            try:
                raw = p.read_text(encoding="utf-8")
            except OSError:
                continue
            d = ap.decoupe(raw)
            fm = (ap.lire_fm(d[1]) if d else None) or {}
            if fm.get("scenario") != sc:
                continue
            texte = _plie(d[3] if d else raw)
            trouves = [f"nomme « {n} » dans le texte" for n, m in motifs_noms if m.search(texte)]
            # Forme approchée (« collectifs de pêcheurs inuit » pour « Collectifs de Pêche Inuit et
            # Sami ») : la plupart des mots du nom, par leur début, à moins de 100 caractères.
            trouves += [f"nomme peut-être « {n} » (forme approchée)" for n, _ in motifs_noms
                        if not any(f"« {n} »" in t for t in trouves) and forme_approchee(n, texte)]
            if trouves:
                titre = ap._titre_article(fm, d[3] if d else raw, p.stem)
                date = fm.get("date_evenement") or fm.get("date_publication") or ""
                out.append((sc, chemin, str(titre).strip(), date, trouves))
    return out


MOTS_VIDES = {"des", "les", "aux", "pour", "dans", "avec", "sans", "sous", "vers", "entre", "et", "de", "du",
              "la", "le", "en", "sur", "par", "the", "of", "and"}


def forme_approchee(nom, texte_plie):
    """Au moins 60 % (et au moins 2) des mots distinctifs du nom, reconnus par leurs 5 premières
    lettres, dans une fenêtre de 100 caractères du texte (déjà plié)."""
    mots = [m for m in re.findall(r"[a-z0-9]+", _plie(nom)) if len(m) >= 4 and m not in MOTS_VIDES]
    if len(mots) < 2:
        return False
    racines = [m[:5] for m in mots]
    besoin = max(2, -(-len(racines) * 3 // 5))
    motif = re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(r) for r in racines) + r")")
    for o in motif.finditer(texte_plie):
        fenetre = texte_plie[o.start():o.start() + 100]
        if sum(1 for r in racines if re.search(r"(?<![a-z0-9])" + re.escape(r), fenetre)) >= besoin:
            return True
    return False


def verifier_articles(hid, data, refaire):
    import hashlib
    suivi = lire_suivi(hid)
    cache = suivi.setdefault("articles", {})
    liste = articles_a_relire(data)
    n_ia = 0
    for sc, chemin, titre, date, motifs in liste:
        p = VAULT / chemin
        raw = p.read_text(encoding="utf-8")
        emp = hashlib.sha1((VERSION_ARTICLES + raw).encode("utf-8")).hexdigest()[:12]
        if not refaire and (cache.get(chemin) or {}).get("empreinte") == emp:
            continue
        d = ap.decoupe(raw)
        corps = _norm(d[3] if d else raw)[:MAX_ARTICLE]
        etats = etats_cites(data, sc, corps)
        terr = territoires_zones(data, sc)   # PATCH_S27_RELECTURE
        user = (f"ARTICLE DE PRESSE « {titre} » (scénario {sc}, daté {date or '2098'}) :\n{corps}\n\n"
                "FAITS ÉTABLIS PAR L'HYPOTHÈSE (priment sur l'article) :\n"
                + "\n".join(f"- {f}" for f in faits_hypothese(data, sc)) + "\n\n"
                + ("ÉTATS DES ENTITÉS CITÉES (seule référence pour leur rang ; un passage conforme n'est "
                   "JAMAIS une contradiction) :\n" + "\n".join(etats) + "\n\n" if etats else "")
                + ("TERRITOIRES DES ZONES DONT LE STATUT CHANGE (un lieu absent de ces listes n'est PAS concerné) :\n" + "\n".join(terr) + "\n\n" if terr else "")
                + "TÂCHE : relève UNIQUEMENT les passages qui contredisent un fait à la date de l'article : "
                "entité disparue décrite comme existante ou active au présent ; entité à qui l'article donne un "
                "rang contraire à son état ; zone décrite autrement que son statut ; contrainte niée. Un rappel "
                "historique au passé est CORRECT. Une omission n'est pas une contradiction. "
                "Un statut de zone (en déclin, fragmenté…) ne dit JAMAIS que ses lieux, ses récits ou ses acteurs cessent d'exister. "
                "Une entité dont le rang monte n'est contredite que si l'article la dit disparue, effondrée ou en déclin après la date ; une formulation modeste ou neutre est conforme. "
                "Le rang d'une entité « inchangé par l'hypothèse » ne se discute JAMAIS : tu ne relis que les conséquences de l'hypothèse. "
                "Ne relève que ce qui est CERTAINEMENT faux, sans conditionnel. En cas de doute, ne "
                "relève rien : la réponse attendue est souvent une liste vide.\n"
                "Pour chaque passage : \"extrait\" = la phrase entière, MOT POUR MOT ; \"fait\" = le fait "
                "contredit ; \"suggestion\" = la phrase réécrite en changeant le moins de mots possible.\n"
                'Format : {"passages": [{"extrait": "...", "fait": "...", "suggestion": "..."}]}')
        res = ia_json(SYSTEME_RELECTEUR, user, max_tokens=2000)
        passages = []
        for x in res.get("passages") or []:
            if not isinstance(x, dict) or not x.get("extrait"):
                continue
            m = motif_phrase(x["extrait"])
            if m and m.search(raw) and contradiction_article(x.get("fait"), x.get("extrait"), data, sc):   # PATCH_S27_RELECTURE / APPLIQUEE
                passages.append({"extrait": _norm(x["extrait"]), "fait": _norm(x.get("fait")),
                                 "suggestion": _norm(x.get("suggestion"))})
        ancien = cache.get(chemin) or {}
        cache[chemin] = {"empreinte": emp, "date": maintenant(), "passages": passages,
                         **({"relu": ancien["relu"]} if ancien.get("relu") and not passages else {})}
        n_ia += 1
        ecrire_suivi(hid, suivi)
        print(f"  [{sc}] {chemin} : {len(passages)} passage(s) à revoir")
    print(f"\n{len(liste)} article(s) concerné(s), {n_ia} relu(s) par l'IA "
          f"(les autres n'ont pas changé depuis leur dernière relecture). Rien n'a été modifié.")
    return 0


def marquer_article(hid, data, chemin):
    if chemin not in {c for _, c, _, _, _ in articles_a_relire(data)}:
        sys.exit(f"✗ article inconnu pour cette hypothèse : {chemin}")
    suivi = lire_suivi(hid)
    suivi.setdefault("articles", {}).setdefault(chemin, {})["relu"] = maintenant()
    ecrire_suivi(hid, suivi)
    print(f"✓ `{chemin}` marqué comme relu.")
    return 0


def etat_articles(data, suivi):
    cache = suivi.get("articles") or {}
    out = []
    for sc, chemin, titre, date, motifs in articles_a_relire(data):
        c = cache.get(chemin) or {}
        out.append({"sc": sc, "chemin": chemin, "titre": titre, "date": str(date or ""), "motifs": motifs,
                    "verifie": "empreinte" in c, "passages": c.get("passages") or [], "relu": c.get("relu")})
    return out


# ---------------------------------------------------------------------------
# 5. Carte (18 oct 2026) : suites de la carte appliquée par appliquer_et_si.py
# ---------------------------------------------------------------------------

def _sous_arbre(by, racine):
    """Slugs de `racine` et de tous ses descendants."""
    out, a_voir = {racine}, [racine]
    while a_voir:
        s = a_voir.pop()
        for z in by.values():
            if z.get("parent") == s and z.get("slug") not in out:
                out.add(z["slug"])
                a_voir.append(z["slug"])
    return out


def ops_carte(data, sc):
    return [c for c in (data["par_scenario"].get(sc) or {}).get("carte") or []]


def trouver_carte(data, cle, videes=False):
    """(scénario, opération, entrée) pour une clé « scénario:slug » de sous-zone à répartir
    (ou de zone vidée si `videes`)."""
    if ":" not in str(cle or ""):
        sys.exit("✗ clé attendue : scénario:slug")
    sc, slug = cle.split(":", 1)
    for c in ops_carte(data, sc):
        for s in c.get("a_repartir") or []:
            if s["slug"] == slug:
                return sc, c, s
        if videes and slug in (c.get("videes") or []):
            return sc, c, {"slug": slug}
    sys.exit(f"✗ {cle} : ni sous-zone à répartir{' ni zone vidée' if videes else ''} pour cette hypothèse")


JOURNAUX = GEN / "journaux.yaml"


def lire_journaux():
    try:
        return yaml.safe_load(JOURNAUX.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}


def journaux_zone(sc, zone, dec, journaux):
    """Journaux d'une zone vidée : présents dans journaux.yaml, ou déjà retirés (suivi)."""
    out = []
    for orient, bloc in ((journaux.get(sc) or {}).items() if isinstance(journaux.get(sc), dict) else []):
        j = ((bloc or {}).get("zones") or {}).get(zone) if isinstance(bloc, dict) else None
        if isinstance(j, dict):
            cle = f"{sc}:{zone}:{orient}"
            out.append({"cle": cle, "orientation": orient, "nom": j.get("nom") or zone,
                        "journalistes": len(j.get("journalistes") or []),
                        "etat": "garde" if dec.get(cle) == "garde" else "a_decider"})
    for cle, d in dec.items():
        if str(d).startswith("retire") and cle.startswith(f"{sc}:{zone}:") and not any(x["cle"] == cle for x in out):
            out.append({"cle": cle, "orientation": cle.rsplit(":", 1)[1],
                        "nom": str(d).split(":", 1)[1] if ":" in str(d) else cle.rsplit(":", 1)[1],
                        "journalistes": 0, "etat": "retire"})
    return out


def etat_carte(data, suivi):
    dec = suivi.get("carte") or {}
    dec_j = suivi.get("journaux") or {}
    journaux = None
    out = []
    for sc in data["scenarios"]:
        ops = ops_carte(data, sc)
        if not ops:
            continue
        by = {z.get("slug"): z for z in ap.zones_geo(sc)}
        for c in ops:
            if c["action"] not in ("absorber", "nouvelle_zone"):
                out.append({"sc": sc, "pays": c["pays"], "action": c["action"], "cible": c.get("cible"),
                            "manuel": True})
                continue
            cible = c["cible"]
            item = {"sc": sc, "pays": c["pays"], "action": c["action"], "cible": cible,
                    "nom_cible": (by.get(cible) or {}).get("nom") or (c.get("nouvelle_zone") or {}).get("nom") or cible,
                    "applique": ap.porte_pays(by.get(cible), c["pays"]), "nouvelle": c["action"] == "nouvelle_zone",
                    "sous_zones": [], "videes": []}
            dessous = _sous_arbre(by, cible)
            for s in c.get("a_repartir") or []:
                z = by.get(s["slug"])
                if not item["applique"]:
                    e = "en_attente"
                elif not z:
                    e = "disparue"
                elif s["slug"] in dessous:
                    e = "deplacee"
                elif ap.porte_pays(z, c["pays"]):
                    e = "portion"
                elif dec.get(f"{sc}:{s['slug']}"):
                    e = "laissee"
                else:
                    e = "a_decider"
                item["sous_zones"].append({"cle": f"{sc}:{s['slug']}", "slug": s["slug"],
                                           "nom": (z or {}).get("nom") or s.get("nom") or s["slug"],
                                           "autres": s.get("autres") or [], "etat": e})
            for v in c.get("videes") or []:
                z = by.get(v)
                e = ("supprimee" if not z else "territoire" if z.get("origine_reelle")
                     else "gardee" if dec.get(f"{sc}:{v}") else "a_decider")
                if journaux is None:
                    journaux = lire_journaux()
                item["videes"].append({"cle": f"{sc}:{v}", "slug": v, "nom": (z or {}).get("nom") or v, "etat": e,
                                       "journaux": journaux_zone(sc, v, dec_j, journaux) if item["applique"] else []})
            out.append(item)
    return out


def carte_laisser(hid, data, cle):
    sc, c, s = trouver_carte(data, cle, videes=True)
    suivi = lire_suivi(hid)
    suivi.setdefault("carte", {})[cle] = maintenant()
    ecrire_suivi(hid, suivi)
    print(f"✓ `{s['slug']}` gardée telle quelle ({sc}) : décision notée, rien n'est écrit dans la géographie.")
    return 0


def carte_deplacer(hid, data, cle, apply):
    sc, c, s = trouver_carte(data, cle)
    by = {z.get("slug"): z for z in ap.zones_geo(sc)}
    cible = c["cible"]
    if not ap.porte_pays(by.get(cible), c["pays"]):
        sys.exit(f"✗ `{cible}` ne porte pas encore {c['pays']} : appliquer d'abord la carte (étape ④).")
    if s["slug"] not in by:
        sys.exit(f"✗ `{s['slug']}` n'existe plus dans geographie/{sc}.md.")
    if s["slug"] in _sous_arbre(by, cible):
        print(f"· `{s['slug']}` est déjà sous `{cible}` : rien à faire.")
        return 0
    repo = ap._repo()
    try:
        a = repo.reparent(sc, s["slug"], cible, dry_run=True)
    except Exception as e:
        sys.exit(f"✗ {type(e).__name__}: {e}")
    print(("ÉCRITURE" if apply else "APERÇU (rien écrit)") + f" — {sc}")
    print(f"  `{s['slug']}` ({a['zone']['nom']}) : sous `{a['zone']['ancien_parent']}` → sous `{cible}` "
          f"(niveau {a['zone']['niveau']} → {a['nouveau_niveau_zone']})")
    for d in a.get("descendants_impactes") or []:
        print(f"  suit : `{d['slug']}` (niveau {d['ancien_niveau']} → {d['nouveau_niveau']})")
    print(f"  Elle garde ses territoires ({', '.join(s.get('autres') or [])}) : ils comptent désormais dans "
          f"`{cible}` ({c['pays']} n'y revient pas).")
    if not apply:
        print(f"\nPour écrire : bouton « La déplacer sous {cible} » (terminal : --apply).")
        return 0
    geo = VAULT / "geographie" / f"{sc}.md"
    shutil.copy2(geo, geo.with_name(geo.name + ".bak_et_si_main"))
    try:
        repo.reparent(sc, s["slug"], cible, dry_run=False)
    except Exception as e:
        sys.exit(f"✗ {type(e).__name__}: {e} (rien d'autre n'est modifié ; sauvegarde {geo.name}.bak_et_si_main)")
    apres = {z.get("slug"): z for z in ap.zones_geo(sc)}
    if (apres.get(s["slug"]) or {}).get("parent") != cible:
        shutil.copy2(geo.with_name(geo.name + ".bak_et_si_main"), geo)
        sys.exit("✗ résultat inattendu à la relecture : géographie remise en l'état.")
    print(f"\n✓ `{s['slug']}` déplacée sous `{cible}` (sauvegarde {geo.name}.bak_et_si_main). "
          f"Contrôle : « Contrôle de la géographie » dans « Pour finir ».")
    return 0


def trouver_journal(data, cle):
    """(scénario, zone vidée, orientation) pour une clé « scénario:zone:orientation »."""
    parties = str(cle or "").split(":")
    if len(parties) != 3:
        sys.exit("✗ clé attendue : scénario:zone:orientation")
    sc, zone, orient = parties
    if not any(zone in (c.get("videes") or []) for c in ops_carte(data, sc)):
        sys.exit(f"✗ {zone} n'est pas une zone vidée par cette hypothèse ({sc})")
    return sc, zone, orient


def journal_garder(hid, data, cle):
    sc, zone, orient = trouver_journal(data, cle)
    suivi = lire_suivi(hid)
    suivi.setdefault("journaux", {})[cle] = "garde"
    ecrire_suivi(hid, suivi)
    print(f"✓ journal {orient} de `{zone}` gardé (en exil) : décision notée, journaux.yaml inchangé.")
    return 0


def journal_retirer(hid, data, cle, apply):
    sc, zone, orient = trouver_journal(data, cle)
    j = lire_journaux()
    bloc = ((j.get(sc) or {}).get(orient) or {})
    zones = bloc.get("zones") if isinstance(bloc, dict) else None
    if not isinstance(zones, dict) or zone not in zones:
        sys.exit(f"✗ aucun journal {orient} pour `{zone}` dans journaux.yaml ({sc}) : déjà retiré ?")
    journal = zones[zone] or {}
    nom = journal.get("nom") or zone
    # Articles déjà signés : recherche du nom du journal dans les articles du scénario (information).
    signes = 0
    racine = VAULT / "articles"
    if racine.exists():
        for f in racine.rglob("*.md"):
            try:
                if nom in f.read_text(encoding="utf-8"):
                    signes += 1
            except OSError:
                pass
    print(("ÉCRITURE" if apply else "APERÇU (rien écrit)") + f" — {sc}")
    print(f"  Retirer « {nom} » ({orient}, zone `{zone}`) de generator/journaux.yaml : "
          f"{len(journal.get('journalistes') or [])} journaliste(s) avec lui.")
    print(f"  Articles qui citent ce nom : {signes} (ils ne sont pas modifiés ; plus aucun nouvel article "
          "ne sera écrit pour ce journal).")
    if not apply:
        print(f"\nPour écrire : bouton « Le retirer » (terminal : --apply).")
        return 0
    attendu = {k: v for k, v in zones.items() if k != zone}
    del zones[zone]
    shutil.copy2(JOURNAUX, JOURNAUX.with_name("journaux.yaml.bak_et_si_main"))
    JOURNAUX.write_text(yaml.dump(j, allow_unicode=True, sort_keys=False), encoding="utf-8")
    relu = lire_journaux()
    if ((relu.get(sc) or {}).get(orient) or {}).get("zones") != attendu:
        shutil.copy2(JOURNAUX.with_name("journaux.yaml.bak_et_si_main"), JOURNAUX)
        sys.exit("✗ relecture inattendue : journaux.yaml remis en l'état.")
    suivi = lire_suivi(hid)
    suivi.setdefault("journaux", {})[cle] = f"retire:{nom}"
    ecrire_suivi(hid, suivi)
    print(f"\n✓ « {nom} » retiré (sauvegarde journaux.yaml.bak_et_si_main). Contrôle : "
          "python3 generator/validate.py")
    return 0


# ---------------------------------------------------------------------------
# 6. Commandes de fin
# ---------------------------------------------------------------------------

# PATCH_S27_GUI_AU_PASSE (24 oct 2026) : fiches des entités disparues, à mettre au passé.
def fiches_disparues(data, suivi):
    """Entités que la phase 4 a fait disparaître (trajectoire « disparu » appliquée)."""
    ops, _ = ap.construire_plan(data)
    faites = suivi.get("au_passe") or {}
    out = []
    for o in ops:
        if o["genre"] != "trajectoire" or o.get("apres") != "disparu" or o.get("alerte") != "déjà appliqué":
            continue
        slug = o["instance"]
        rap = VAULT / "documentation" / "need_action" / f"fiche_au_passe_{slug}.md"
        out.append({"slug": slug, "sc": o["sc"], "nom": re.sub(r"\s*\(`.*$", "", o["texte"]),
                    "etat": "ecrite" if slug in faites else ("apercu" if rap.exists() else "a_faire"),
                    "rapport": str(rap.relative_to(VAULT)) if rap.exists() else None,
                    "date": faites.get(slug)})
    return out


def au_passe(hid, data, slug, apply):
    if slug not in {f["slug"] for f in fiches_disparues(data, lire_suivi(hid))}:
        sys.exit(f"✗ {slug} : pas une entité disparue de cette hypothèse (trajectoire appliquée)")
    cmd = [sys.executable, str(GEN / "fiche_au_passe.py"), "--slug", slug]
    cmd += ["--apply"] if apply else ["--contexte", f"{data.get('nom') or hid} ({_annee(data)})"]
    try:
        r = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True, timeout=280, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        print("✗ délai dépassé (280 s)")
        return 1
    print("\n".join(s for s in (r.stdout.strip(), r.stderr.strip()) if s))
    if apply and r.returncode == 0:
        suivi = lire_suivi(hid)
        suivi.setdefault("au_passe", {})[slug] = maintenant()
        ecrire_suivi(hid, suivi)
    return r.returncode


def lancer(action, sc, data):
    if sc not in data["scenarios"]:
        sys.exit(f"✗ scénario {sc} hors de l'hypothèse")
    libelle, cmd, delai = LANCER[action]
    print(f"{libelle} — {sc}\n  $ python3 {' '.join(cmd + [sc])}\n")
    try:
        r = subprocess.run([sys.executable] + cmd + [sc], cwd=VAULT, capture_output=True, text=True,
                           timeout=delai, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        print(f"✗ délai dépassé ({delai} s)")
        return 1
    print("\n".join(s for s in (r.stdout.strip(), r.stderr.strip()) if s))
    return r.returncode


# ---------------------------------------------------------------------------

def etat(hid, data):
    suivi = lire_suivi(hid)
    out = {"id": hid, "scenarios": data["scenarios"], "entites": [], "categories": [], "regles": [],
           "fin": [{"action": a, "libelle": v[0]} for a, v in LANCER.items()], "erreurs": []}
    try:
        m = cei()
        out["categories"] = list(m.VALID_CATEGORIES)
        file_noms = {str(x.get("nom") or "").strip().lower() for x in m.load_yaml_list(m.QUEUE_PATH)
                     if isinstance(x, dict)}
        existants = {str(x.get("slug") or "") for x in m.load_entities_list() if isinstance(x, dict)}
        for e in entites_proposees(data, list(m.VALID_CATEGORIES)):
            e["statut"], e["detail"] = statut_entite(e, suivi, m, file_noms, existants)
            out["entites"].append(e)
    except Exception as e:   # le reste de l'état reste utile
        out["erreurs"].append(f"entités : {type(e).__name__}: {e}")
    try:
        contenu = LORE.read_text(encoding="utf-8") if LORE.exists() else ""
        existants = set(ids_existants(contenu))
        for sc, texte in brouillons_regles(data).items():
            ids = [r.get("id") for r in (yaml.safe_load(texte) or []) if isinstance(r, dict)]
            out["regles"].append({"sc": sc, "brouillon": texte,
                                  "deja": [i for i in ids if i in existants],
                                  "ajoutees": sorted(k.split(":", 1)[1] for k in suivi["regles"]
                                                     if k.startswith(sc + ":"))})
    except Exception as e:
        out["erreurs"].append(f"règles : {type(e).__name__}: {e}")
    try:
        out["phrases"] = phrases_a_corriger(data, suivi)
        out["evenement_verifie"] = sorted((suivi.get("verif_evenement") or {}).keys())
    except Exception as e:
        out["phrases"] = []
        out["erreurs"].append(f"phrases : {type(e).__name__}: {e}")
    try:
        out["carte"] = etat_carte(data, suivi)
    except Exception as e:
        out["carte"] = []
        out["erreurs"].append(f"carte : {type(e).__name__}: {e}")
    try:
        out["articles"] = etat_articles(data, suivi)
    except Exception as e:
        out["articles"] = []
        out["erreurs"].append(f"articles : {type(e).__name__}: {e}")
    try:   # PATCH_S27_GUI_AU_PASSE
        out["disparues"] = fiches_disparues(data, suivi)
    except Exception as e:
        out["disparues"] = []
        out["erreurs"].append(f"fiches disparues : {type(e).__name__}: {e}")
    return out


def main():
    a = argparse.ArgumentParser(description="Étape ⑤ « À la main » : entités, règle de lore, commandes de fin.")
    a.add_argument("--id", required=True)
    a.add_argument("--json", action="store_true", help="état (entités, brouillons de règles), pour le GUI")
    a.add_argument("--entites", help='choix JSON : [{"cle": "reference:1", "category": "institution"}]')
    a.add_argument("--regle", metavar="SCENARIO", help="ajoute la règle lue sur l'entrée standard")
    a.add_argument("--lancer", choices=list(LANCER))
    a.add_argument("--phrases-proposer", action="store_true",
                   help="relit la fiche d'événement et propose les réécritures (appels IA, mis en cache)")
    a.add_argument("--refaire", action="store_true", help="avec --phrases-proposer : ignore le cache")
    a.add_argument("--phrase", metavar="CLE", help="remplace la phrase CLE par le texte lu sur l'entrée standard")
    a.add_argument("--ignorer", action="store_true", help="avec --phrase : marque la phrase « ignorée »")
    a.add_argument("--articles-verifier", action="store_true",
                   help="relit les articles concernés (appels IA, en cache) ; n'écrit jamais dans un article")
    a.add_argument("--article-relu", metavar="CHEMIN", help="marque un article comme relu")
    a.add_argument("--carte-deplacer", metavar="SC:SLUG", help="déplace une sous-zone à répartir sous la zone cible")
    a.add_argument("--carte-laisser", metavar="SC:SLUG", help="note qu'une sous-zone (ou zone vidée) reste telle quelle")
    a.add_argument("--journal-garder", metavar="SC:ZONE:ORIENTATION", help="garde le journal d'une zone vidée (exil)")
    a.add_argument("--journal-retirer", metavar="SC:ZONE:ORIENTATION",
                   help="retire de journaux.yaml le journal d'une zone vidée (avec --apply)")
    a.add_argument("--au-passe", metavar="SLUG",   # PATCH_S27_GUI_AU_PASSE
                   help="fiche d'une entité disparue au passé : aperçu (un appel IA), --apply pour écrire")
    a.add_argument("--scenario")
    a.add_argument("--apply", action="store_true")
    x = a.parse_args()
    data = charger(x.id)
    if x.json:
        print(json.dumps(etat(x.id, data), ensure_ascii=False))
        return 0
    if x.entites:
        try:
            choix = json.loads(x.entites)
        except ValueError:
            sys.exit("✗ --entites : JSON illisible")
        return ajouter_entites(x.id, data, choix if isinstance(choix, list) else [choix], x.apply)
    if x.regle:
        return ajouter_regle(x.id, data, x.regle, sys.stdin.read(), x.apply)
    if x.carte_deplacer:
        return carte_deplacer(x.id, data, x.carte_deplacer, x.apply)
    if x.carte_laisser:
        return carte_laisser(x.id, data, x.carte_laisser)
    if x.journal_garder:
        return journal_garder(x.id, data, x.journal_garder)
    if x.journal_retirer:
        return journal_retirer(x.id, data, x.journal_retirer, x.apply)
    if x.articles_verifier:
        return verifier_articles(x.id, data, x.refaire)
    if x.article_relu:
        return marquer_article(x.id, data, x.article_relu)
    if x.phrases_proposer:
        return proposer_phrases(x.id, data, x.refaire)
    if x.phrase:
        return remplacer_phrase(x.id, data, x.phrase, "" if x.ignorer else sys.stdin.read(), x.ignorer, x.apply)
    if x.au_passe:   # PATCH_S27_GUI_AU_PASSE
        return au_passe(x.id, data, x.au_passe, x.apply)
    if x.lancer:
        if not x.scenario:
            sys.exit("✗ --lancer demande --scenario")
        return lancer(x.lancer, x.scenario, data)
    a.error("préciser --json, --entites, --regle, --phrases-proposer, --phrase, --articles-verifier, --article-relu, --carte-deplacer, --carte-laisser, --journal-garder, --journal-retirer ou --lancer")


if __name__ == "__main__":
    sys.exit(main() or 0)
