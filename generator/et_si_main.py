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
  4. Commandes de fin : audit du lore (gratuit), résumé du scénario (payant).

USAGE (depuis la racine du coffre)
    python3 generator/et_si_main.py --id X --json                      # état (pour le GUI)
    python3 generator/et_si_main.py --id X --entites '[{"cle": "reference:1", "category": "institution"}]'
    python3 generator/et_si_main.py --id X --entites '…' --apply
    python3 generator/et_si_main.py --id X --regle reference < brouillon.yaml           # aperçu
    python3 generator/et_si_main.py --id X --regle reference --apply < brouillon.yaml
    python3 generator/et_si_main.py --id X --phrases-proposer                 # appels IA (en cache)
    python3 generator/et_si_main.py --id X --phrase CLE [--apply] < phrase.txt
    python3 generator/et_si_main.py --id X --phrase CLE --ignorer
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
            regles.append({"id": f"{court}_disparu_{annee}", "gravite": "a_relire", "termes": [nom],
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


def faits_hypothese(data, sc):
    """Faits établis par l'hypothèse dans ce scénario (contraintes, trajectoires, zones)."""
    annee = data.get("annee")
    ps = data["par_scenario"].get(sc) or {}
    lec, pas = ps.get("lecture") or {}, ps.get("passe") or {}
    faits = [str(c) for c in data.get("contraintes") or []]
    vus = set()
    for t in (lec.get("trajectoires") or []) + (pas.get("trajectoires") or []):
        if t.get("instance") in vus:
            continue
        vus.add(t.get("instance"))
        nom = t.get("nom") or t.get("instance")
        if t.get("apres") == "disparu":
            faits.append(f"{nom} disparaît en {annee} : après {annee}, il n'existe plus (passé seulement).")
        else:
            faits.append(f"{nom} passe de « {t.get('avant')} » à « {t.get('apres')} » après {annee} : "
                         f"avant {annee}, il était « {t.get('avant')} », pas davantage.")
    for z in lec.get("zones_statut") or []:
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


SYSTEME_RELECTEUR = ("Tu es le relecteur du lore du monde fictif Ourrassol 2098. Tu corriges le moins possible. "
                     "Réponds UNIQUEMENT en JSON valide, sans texte autour.")


def verifier_evenement(data, sc, suivi, refaire):
    """Phrases de la fiche d'événement qui contredisent les faits (un appel IA, en cache)."""
    p = chemin_fiche("evenement", f"{data['id']}_{sc}")
    if not p.exists():
        return []
    raw = p.read_text(encoding="utf-8")
    import hashlib
    emp = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
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
            "TÂCHE : relève les phrases de la fiche qui CONTREDISENT un fait (par exemple : entité décrite "
            "comme déjà dominante alors qu'elle ne fait que devenir ascendante ; entité disparue décrite comme "
            "active ; zone décrite comme détruite alors que le lieu subsiste). Une omission n'est pas une "
            "contradiction. Pour chaque phrase : \"extrait\" = la phrase entière, MOT POUR MOT ; \"fait\" = le "
            "fait contredit ; \"correction\" = la phrase réécrite, en changeant le moins de mots possible, sans "
            "ajouter de fait nouveau. Aucune contradiction → liste vide.\n"
            'Format : {"problemes": [{"extrait": "...", "fait": "...", "correction": "..."}]}')
    res = ia_json(SYSTEME_RELECTEUR, user)
    problemes = []
    for x in res.get("problemes") or []:
        if not isinstance(x, dict) or not x.get("extrait"):
            continue
        m = motif_phrase(x["extrait"])
        if m and m.search(raw):   # gardé seulement si l'extrait est retrouvé dans la fiche
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
        user = (f"FICHE : {e['nom']} ({e['fichier']}), scénario {e['sc']}.\n"
                f"FAIT ÉTABLI PAR L'HYPOTHÈSE {data['id']} (année {data.get('annee')}) : {e['contredit']}\n"
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
        morceaux += [raw[pos:o.start()], _echapper_pour(raw, o.start(), nouveau)]
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
# 3. Commandes de fin
# ---------------------------------------------------------------------------

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
    if x.phrases_proposer:
        return proposer_phrases(x.id, data, x.refaire)
    if x.phrase:
        return remplacer_phrase(x.id, data, x.phrase, "" if x.ignorer else sys.stdin.read(), x.ignorer, x.apply)
    if x.lancer:
        if not x.scenario:
            sys.exit("✗ --lancer demande --scenario")
        return lancer(x.lancer, x.scenario, data)
    a.error("préciser --json, --entites, --regle, --phrases-proposer, --phrase ou --lancer")


if __name__ == "__main__":
    sys.exit(main() or 0)
