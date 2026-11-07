#!/usr/bin/env python3
"""
et_si_dossiers.py — Ourrassol 2098 (S27, étape « décider », 12 octobre 2026)
============================================================================

Dossier de chaque hypothèse du simulateur « et si ? », dans
generator/state/et_si_dossiers.json :

    {"<id>": {
        "simulation": {date, version, empreinte, scenarios, complet, passe,
                       rapport, entree},     # dernière simulation, réécrite à chaque lancement
        "decision":   {statut: adopté | rejeté, date, motif, empreinte, entree}
    }}

Statut affiché, calculé à la lecture (jamais stocké, donc toujours vrai, y
compris après un undo_custom.py) :
    non simulé · simulé · rejeté · adopté, en attente d'injection ·
    injecté · injecté partiellement · à revoir · adopté, absent de la queue

« Adopter » écrit l'entrée commune de la DERNIÈRE simulation complète dans
evenements_custom/queue.yaml (sauvegarde .bak_et_si) ; l'injection reste à
lancer à part (inject_custom_events.py --mode custom). « Annuler la décision »
retire cette entrée de la queue si elle n'a pas encore été injectée.

Module appelé par simuler_et_si.py (--dossiers, --adopter, --rejeter,
--annuler-decision), lui-même appelé par le GUI (panneau « Décider »).
"""

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
DOSSIERS_PATH = SCRIPT_DIR / "state" / "et_si_dossiers.json"
EVENEMENTS_CUSTOM = VAULT_ROOT / "evenements_custom"
QUEUE_PATH = EVENEMENTS_CUSTOM / "queue.yaml"
NEEDS_REVIEW_PATH = EVENEMENTS_CUSTOM / "needs_review.yaml"
EVENT_INSTANCES = VAULT_ROOT / "event_instances"
SIGNAUX_CUSTOM = VAULT_ROOT / "signaux_custom"          # U2c
QUEUE_SIGNAUX = SIGNAUX_CUSTOM / "queue.yaml"
NEEDS_REVIEW_SIGNAUX = SIGNAUX_CUSTOM / "needs_review.yaml"
PROCESSED_SIGNAUX = SIGNAUX_CUSTOM / "processed.yaml"

PORTEES = ["locale", "regionale", "continentale", "globale"]
INTENSITES = ["faible", "modérée", "forte", "majeure"]


class DossierErreur(Exception):
    """Refus d'une décision (message pour l'utilisateur)."""


# ---------------------------------------------------------------------------
# Lecture / écriture
# ---------------------------------------------------------------------------

def charger():
    try:
        data = json.loads(DOSSIERS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def sauver(data):
    DOSSIERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DOSSIERS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    tmp.replace(DOSSIERS_PATH)


def empreinte_hypothese(brut):
    """Empreinte de l'hypothèse TELLE QU'ÉCRITE dans hypotheses.yaml (avant
    normalisation) : toute modification du bloc change l'empreinte."""
    texte = json.dumps(brut, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(texte.encode("utf-8")).hexdigest()[:16]


def _maintenant():
    return datetime.now().isoformat(timespec="minutes")


def _liste_yaml(path, cle):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    items = data.get(cle) if isinstance(data, dict) else None
    return [x for x in items or [] if isinstance(x, dict)]


def type_dossier(dossier):
    """U2c : « evenement » (défaut) ou « signal », retenu à la simulation puis à la décision."""
    d = dossier or {}
    return ((d.get("decision") or {}).get("type") or (d.get("simulation") or {}).get("type")
            or "evenement")


def _chemin_queue(typ):
    return QUEUE_SIGNAUX if typ == "signal" else QUEUE_PATH


def _etat_signal(hid):
    """(injecté, partiellement injecté, présent dans needs_review) d'après signaux_custom/."""
    traites = [x for x in _liste_yaml(PROCESSED_SIGNAUX, "processed") if (x.get("idea") or {}).get("id") == hid]
    revoir = [x for x in _liste_yaml(NEEDS_REVIEW_SIGNAUX, "needs_review") if (x.get("idea") or {}).get("id") == hid]
    partiel = any(r.get("status") == "injected" for x in revoir for r in x.get("results") or [])
    return bool(traites), partiel, bool(revoir)


def _slug_signal(hid):
    for chemin, cle in ((PROCESSED_SIGNAUX, "processed"), (NEEDS_REVIEW_SIGNAUX, "needs_review")):
        for x in _liste_yaml(chemin, cle):
            slug = (x.get("selection") or {}).get("signal_slug")
            if (x.get("idea") or {}).get("id") == hid and slug:
                return slug
    return None


def slug_evenement(hid):
    """Même règle que inject_custom_events.py (slug imposé depuis l'id)."""
    return re.sub(r"[^a-z0-9_]", "_", str(hid).lower().strip())


# ---------------------------------------------------------------------------
# Enregistrement d'une simulation
# ---------------------------------------------------------------------------

def enregistrer_simulation(brut, hyp, scenarios_simules, version, entree, passe, rapport):
    data = charger()
    d = data.setdefault(hyp["id"], {})
    d["simulation"] = {
        "date": _maintenant(), "version": version, "empreinte": empreinte_hypothese(brut),
        "scenarios": list(scenarios_simules),
        "complet": set(scenarios_simules) >= set(hyp["scenarios"]),
        "passe": bool(passe), "rapport": rapport, "entree": entree,
        "type": hyp.get("type", "evenement"),
    }
    sauver(data)
    return d


# ---------------------------------------------------------------------------
# Statut (calculé)
# ---------------------------------------------------------------------------

def statut(hid, dossier=None):
    dossier = dossier if dossier is not None else charger().get(hid) or {}
    dec = dossier.get("decision") or {}
    if dec.get("statut") == "rejeté":
        return "rejeté"
    if dec.get("statut") != "adopté":
        return "simulé" if dossier.get("simulation") else "non simulé"
    typ_d = type_dossier(dossier)
    if typ_d == "signal":   # U2c
        injecte, partiel, a_revoir = _etat_signal(hid)
        if injecte:
            return "injecté"
        if any(x.get("id") == hid for x in _liste_yaml(QUEUE_SIGNAUX, "queue")):
            return "adopté, en attente d'injection"
        if partiel:
            return "injecté partiellement — à revoir"
        return "à revoir" if a_revoir else "adopté, absent de la queue"
    scen = (dec.get("entree") or {}).get("scenarios") or []
    slug = slug_evenement(hid)
    presents = [sc for sc in scen if (EVENT_INSTANCES / f"{slug}_{sc}.md").exists()]
    a_revoir = any((x.get("idea") or {}).get("id") == hid for x in _liste_yaml(NEEDS_REVIEW_PATH, "needs_review"))
    if scen and len(presents) == len(scen):
        return "injecté"
    if presents:
        return "injecté partiellement" + (" — à revoir" if a_revoir else "")
    if any(x.get("id") == hid for x in _liste_yaml(QUEUE_PATH, "queue")):
        return "adopté, en attente d'injection"
    if a_revoir:
        return "à revoir"
    return "adopté, absent de la queue"


def tableau(hyps):
    """Lignes lisibles pour --dossiers."""
    data = charger()
    lignes = []
    for h in hyps:
        hid = h.get("id")
        d = data.get(hid) or {}
        sim, dec = d.get("simulation") or {}, d.get("decision") or {}
        txt = f"- {hid} : {statut(hid, d)}"
        if sim:
            txt += (f"\n  simulé le {sim.get('date')} ({sim.get('version')}), "
                    + ("tous les scénarios" if sim.get("complet") else "scénarios : " + ", ".join(sim.get("scenarios") or []))
                    + (", passe exhaustive" if sim.get("passe") else ""))
            if sim.get("empreinte") != empreinte_hypothese(h):
                txt += "\n  ⚠ hypothèse modifiée depuis cette simulation : à resimuler"
        if dec:
            txt += f"\n  {dec.get('statut')} le {dec.get('date')}" + (f" — {dec['motif']}" if dec.get("motif") else "")
        lignes.append(txt)
    return lignes


# ---------------------------------------------------------------------------
# Décisions
# ---------------------------------------------------------------------------

def _plie(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _choix(valeur, permises, nom):
    table = {_plie(p): p for p in permises}
    v = table.get(_plie(valeur))
    if not v:
        raise DossierErreur(f"{nom} {valeur!r} invalide ({' | '.join(permises)})")
    return v


def preparer_adoption(brut, hid, portee=None, intensite=None):
    """Contrôles et entrée finale. Ne modifie rien."""
    data = charger()
    d = data.get(hid) or {}
    sim = d.get("simulation") or {}
    if not sim:
        raise DossierErreur(f"{hid} n'a jamais été simulée : lancer d'abord la simulation.")
    if sim.get("empreinte") != empreinte_hypothese(brut):
        raise DossierErreur(f"{hid} a été modifiée dans hypotheses.yaml depuis sa dernière simulation "
                            f"({sim.get('date')}) : la resimuler avant d'adopter.")
    if not sim.get("complet"):
        raise DossierErreur(f"la dernière simulation de {hid} est limitée à {', '.join(sim.get('scenarios') or [])} : "
                            f"la relancer sans --scenario avant d'adopter.")
    entree = dict(sim.get("entree") or {})
    if not entree:
        raise DossierErreur(f"{hid} : la dernière simulation n'a pas produit d'entrée d'injection "
                            f"(hypothèse sans impact ?).")
    st = statut(hid, d)
    if st not in ("simulé", "rejeté"):
        raise DossierErreur(f"{hid} est déjà « {st} » : --annuler-decision d'abord si tu veux la reprendre.")
    if type_dossier(d) == "signal":   # U2c : ni portée ni intensité pour un signal
        if any(x.get("id") == hid for x in _liste_yaml(QUEUE_SIGNAUX, "queue")):
            raise DossierErreur(f"une entrée {hid} est déjà dans signaux_custom/queue.yaml.")
        return entree, sim
    if any(x.get("id") == hid for x in _liste_yaml(QUEUE_PATH, "queue")):
        raise DossierErreur(f"une entrée {hid} est déjà dans evenements_custom/queue.yaml.")
    slug = slug_evenement(hid)
    deja = [sc for sc in entree.get("scenarios") or [] if (EVENT_INSTANCES / f"{slug}_{sc}.md").exists()]
    if deja:
        raise DossierErreur(f"l'événement {slug} existe déjà dans le vault ({', '.join(deja)}).")
    for cle, permises, valeur in (("portee", PORTEES, portee), ("intensite", INTENSITES, intensite)):
        if valeur:
            entree[cle] = _choix(valeur, permises, cle)
        elif str(entree.get(cle, "")).startswith("<"):
            raise DossierErreur(f"--{cle} requis ({' | '.join(permises)}).")
        else:
            entree[cle] = _choix(entree.get(cle), permises, cle)
    return entree, sim


def _sauver_queue(liste, typ="evenement"):
    """Réécrit la queue du type (sauvegarde .bak_et_si), avec l'en-tête modèle du script
    d'injection correspondant s'il est importable, sinon l'en-tête du fichier."""
    chemin = _chemin_queue(typ)
    if chemin.exists():
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_et_si"))
    try:
        mod = __import__("inject_custom_signals" if typ == "signal" else "inject_custom_events")
        if Path(mod.QUEUE_PATH).resolve() != chemin.resolve():
            raise ImportError("chemin de queue différent")
        mod.save_queue_with_template(liste)
    except Exception:
        entete = []
        try:
            for ligne in chemin.read_text(encoding="utf-8").splitlines():
                if ligne.strip() and not ligne.lstrip().startswith("#"):
                    break
                entete.append(ligne)
        except OSError:
            pass
        chemin.parent.mkdir(parents=True, exist_ok=True)
        corps = yaml.dump({"queue": liste}, allow_unicode=True, sort_keys=False, default_flow_style=False)
        chemin.write_text("\n".join(entete) + ("\n" if entete else "") + corps, encoding="utf-8")


def _ecrire_queue(entree, typ="evenement"):
    """Ajoute l'entrée à la queue du type."""
    chemin = _chemin_queue(typ)
    _sauver_queue(_liste_yaml(chemin, "queue") + [entree], typ)
    relue = [x for x in _liste_yaml(chemin, "queue") if x.get("id") == entree.get("id")]
    if len(relue) != 1:
        raise DossierErreur("relecture de queue.yaml impossible après écriture : vérifier le fichier "
                            "(sauvegarde .bak_et_si).")


def _retirer_de_queue(hid, typ="evenement"):
    """Retire l'entrée écrite par « Adopter » (même id ET source et_si_<id>) ;
    une entrée de même id écrite à la main n'est pas touchée. True si retirée."""
    chemin = _chemin_queue(typ)
    existantes = _liste_yaml(chemin, "queue")
    gardees = [x for x in existantes if not (x.get("id") == hid and x.get("source") == f"et_si_{hid}")]
    if len(gardees) == len(existantes):
        return False
    _sauver_queue(gardees, typ)
    if any(x.get("id") == hid and x.get("source") == f"et_si_{hid}" for x in _liste_yaml(chemin, "queue")):
        raise DossierErreur("retrait de queue.yaml non relu : vérifier le fichier (sauvegarde .bak_et_si).")
    return True


def adopter(brut, hid, portee=None, intensite=None, apercu=False):
    entree, sim = preparer_adoption(brut, hid, portee, intensite)
    if apercu:
        return entree
    typ = type_dossier(charger().get(hid))
    _ecrire_queue(entree, typ)
    data = charger()
    data.setdefault(hid, {})["decision"] = {
        "statut": "adopté", "date": _maintenant(), "motif": None, "type": typ,
        "empreinte": sim.get("empreinte"), "simulation_du": sim.get("date"), "entree": entree}
    sauver(data)
    return entree


def rejeter(hid, motif=None):
    data = charger()
    d = data.get(hid) or {}
    if not d.get("simulation"):
        raise DossierErreur(f"{hid} n'a jamais été simulée.")
    st = statut(hid, d)
    if st not in ("simulé", "rejeté"):
        raise DossierErreur(f"{hid} est déjà « {st} » : --annuler-decision d'abord.")
    d["decision"] = {"statut": "rejeté", "date": _maintenant(), "motif": motif or None,
                     "empreinte": (d.get("simulation") or {}).get("empreinte")}
    data[hid] = d
    sauver(data)


def annuler_decision(hid):
    """Retire la décision (le dossier revient à « simulé »). Une entrée adoptée encore
    dans la queue (pas encore injectée) en est retirée (sauvegarde .bak_et_si) ; le vault
    n'est jamais touché. Retourne (ancien statut, messages déjà préfixés ✓ ou ⚠)."""
    data = charger()
    d = data.get(hid) or {}
    if not d.get("decision"):
        raise DossierErreur(f"{hid} n'a aucune décision à annuler.")
    st = statut(hid, d)
    typ = type_dossier(d)
    nom_queue = "signaux_custom/queue.yaml" if typ == "signal" else "evenements_custom/queue.yaml"
    messages = []
    if _retirer_de_queue(hid, typ):
        messages.append(f"✓ entrée {hid} retirée de {nom_queue} (sauvegarde queue.yaml.bak_et_si)")
    d.pop("decision")
    data[hid] = d
    sauver(data)
    if any(x.get("id") == hid for x in _liste_yaml(_chemin_queue(typ), "queue")):
        messages.append(f"⚠ une entrée {hid} écrite à la main reste dans {nom_queue}")
    if st.startswith("injecté"):
        if typ == "signal":
            messages.append(f"⚠ le signal reste dans le vault : python3 generator/undo_custom.py "
                            f"--slug {_slug_signal(hid) or '<slug du signal>'} --type signal (aperçu, puis --execute)")
        else:
            messages.append(f"⚠ l'événement reste dans le vault : python3 generator/undo_custom.py "
                            f"--slug {slug_evenement(hid)} --type evenement --generalisation yes (aperçu, puis --execute)")
    return st, messages
