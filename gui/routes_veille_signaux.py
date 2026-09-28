"""
routes_veille_signaux.py — Ourrassol 2098
==========================================

Onglet GUI « 🔭 Veille signaux faibles » (28 septembre 2026) : tri des
candidats produits par generator/import_signaux_faibles.py
(state/veille_signaux.json).

Blueprint séparé (même patron que routes_carte.py / routes_dashboard.py),
pour qu'app.py ne reçoive que deux lignes.

Routes :
  GET  /api/veille_signaux/liste    candidats de tous les lots, à plat
  POST /api/veille_signaux/statut   change le statut d'un candidat
                                    {id, statut, queue_id?, queue_type?}

Statuts : a_trier (défaut à l'import) | ecarte | en_queue.
« en_queue » est posé par le GUI APRÈS un /api/yaml/append réussi : ce
fichier n'écrit jamais dans une queue lui-même (un seul chemin d'écriture
vers queue.yaml, cf. idees_vers_queue.py).

Écriture : .bak avant chaque modification, écriture atomique (fichier
temporaire puis remplacement), verrou pour deux clics rapprochés.
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request

veille_signaux_bp = Blueprint("veille_signaux", __name__)

CONFIG_PATH = Path(os.path.abspath(__file__)).parent / "config.json"
STATUTS = ("a_trier", "ecarte", "en_queue")
_verrou = threading.Lock()


def _chemin_candidats() -> Path:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    vault_root = Path(cfg.get("vault_root", ""))
    # Même règle que import_signaux_faibles.py : state/ à la racine du
    # vault, sinon generator/state/.
    for d in (vault_root / "state", vault_root / "generator" / "state"):
        if (d / "veille_signaux.json").exists():
            return d / "veille_signaux.json"
    return vault_root / "state" / "veille_signaux.json"


def _lire(chemin: Path) -> dict:
    if not chemin.exists():
        return {"lots": []}
    return json.loads(chemin.read_text(encoding="utf-8"))


@veille_signaux_bp.route("/api/veille_signaux/liste", methods=["GET"])
def veille_signaux_liste():
    chemin = _chemin_candidats()
    try:
        data = _lire(chemin)
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({"error": f"{chemin.name} illisible : {e}"}), 500

    candidats, lots = [], []
    for lot in data.get("lots", []):
        lots.append({
            "lot": lot.get("lot"),
            "date": lot.get("date"),
            "reponses": lot.get("reponses", []),
            "couverture": lot.get("couverture", []),
            "rejets": lot.get("rejets", []),
        })
        for c in lot.get("candidats", []):
            # Les variantes (fiches d'origine avant fusion) restent dans le
            # JSON mais ne sont renvoyées que résumées : le panneau n'en a
            # besoin que pour afficher titres et notes par IA.
            c2 = {k: v for k, v in c.items() if k != "variantes"}
            c2["variantes_resume"] = [
                {"ia": v.get("ia"), "numero": v.get("numero"), "titre": v.get("titre")}
                for v in c.get("variantes", [])
            ]
            c2["lot"] = lot.get("lot")
            candidats.append(c2)
    return jsonify({"ok": True, "fichier": str(chemin), "lots": lots, "candidats": candidats})


@veille_signaux_bp.route("/api/veille_signaux/statut", methods=["POST"])
def veille_signaux_statut():
    body = request.get_json() or {}
    id_ = body.get("id")
    statut = body.get("statut")
    if not id_ or statut not in STATUTS:
        return jsonify({"error": f"id requis et statut parmi {', '.join(STATUTS)}"}), 400

    chemin = _chemin_candidats()
    with _verrou:
        try:
            data = _lire(chemin)
        except (json.JSONDecodeError, OSError) as e:
            return jsonify({"error": f"{chemin.name} illisible : {e}"}), 500

        cible = None
        for lot in data.get("lots", []):
            for c in lot.get("candidats", []):
                if c.get("id") == id_:
                    cible = c
                    break
            if cible:
                break
        if cible is None:
            return jsonify({"error": f"candidat {id_} introuvable"}), 404

        cible["statut"] = statut
        cible["date_statut"] = datetime.now().isoformat(timespec="seconds")
        # Le motif d'un écart automatique (sources introuvables) n'a plus
        # de sens dès que David change lui-même le statut.
        cible.pop("motif_ecart", None)
        if statut == "en_queue":
            cible["queue_id"] = body.get("queue_id")
            cible["queue_type"] = body.get("queue_type")
        else:
            cible.pop("queue_id", None)
            cible.pop("queue_type", None)

        texte = json.dumps(data, ensure_ascii=False, indent=2)
        bak = chemin.with_suffix(".json.bak")
        bak.write_text(chemin.read_text(encoding="utf-8"), encoding="utf-8")
        tmp = chemin.with_suffix(".json.tmp")
        tmp.write_text(texte, encoding="utf-8")
        os.replace(tmp, chemin)

    return jsonify({"ok": True, "id": id_, "statut": statut})
