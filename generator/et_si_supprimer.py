#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
et_si_supprimer.py (U3ax) — supprime des hypothèses d'ENTITÉ de et_si/hypotheses.yaml
(bloc retiré du fichier + dossier de décision effacé de state/et_si_dossiers.json).

Garde-fous :
  - seules les hypothèses `type: entite` ; événements et signaux sont refusés ;
  - refus si l'entité est « injectée » (elle existe dans le vault : cette commande ne
    touche jamais à entites/ ni aux instances) ;
  - aperçu par défaut ; --apply écrit, avec sauvegarde hypotheses.yaml.bak_suppr ;
  - le fichier est revérifié (ids attendus, YAML valide) avant d'être écrit.

  python3 generator/et_si_supprimer.py --id a --id b            # aperçu
  python3 generator/et_si_supprimer.py --id a --id b --apply
  python3 generator/et_si_supprimer.py --non-injectees          # toutes les entités non injectées (aperçu)
  ... --json : sortie machine (dernière ligne JSON), utilisée par le GUI.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

GEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))
import et_si_dossiers as ed  # noqa: E402


def _ids_du_fichier(texte):
    data = yaml.safe_load(texte) or {}
    return [str(h.get("id")) for h in (data.get("hypotheses") or []) if isinstance(h, dict)]


def retirer_blocs(texte, ids):
    """Retire du texte les blocs `- id: <id>` demandés ; (nouveau_texte, ids_retirés)."""
    lignes = texte.split("\n")
    retires = []
    for hid in ids:
        motif = re.compile(r"^(\s*)-\s+id:\s*['\"]?" + re.escape(hid) + r"['\"]?\s*(#.*)?$")
        debut = next((i for i, l in enumerate(lignes) if motif.match(l)), None)
        if debut is None:
            continue
        indent = motif.match(lignes[debut]).group(1)
        fin = len(lignes)
        for j in range(debut + 1, len(lignes)):
            l = lignes[j]
            if not l.strip():
                continue
            marge = len(l) - len(l.lstrip())
            if marge < len(indent) or (marge == len(indent) and l.lstrip().startswith("- ")):
                fin = j
                break
        # les lignes vides / commentaires juste avant le bloc suivant lui appartiennent
        while fin > debut + 1 and (not lignes[fin - 1].strip() or lignes[fin - 1].lstrip().startswith("#")):
            fin -= 1
        del lignes[debut:fin]
        if debut > 0 and not lignes[debut - 1].strip() and (debut >= len(lignes) or not lignes[debut].strip()):
            del lignes[debut - 1]   # évite une double ligne vide
        retires.append(hid)
    return "\n".join(lignes).rstrip("\n") + "\n", retires


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--id", action="append", default=[], help="id d'une hypothèse d'entité (répétable)")
    ap.add_argument("--non-injectees", action="store_true",
                    help="toutes les hypothèses d'entité qui ne sont pas encore injectées")
    ap.add_argument("--apply", action="store_true", help="écrit (sinon aperçu)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    chemin = ed.HYPOTHESES_PATH
    try:
        texte = chemin.read_text(encoding="utf-8")
        presents = _ids_du_fichier(texte)
    except (OSError, yaml.YAMLError) as e:
        return _fin(a, {"ok": False, "error": f"hypotheses.yaml illisible : {e}"})

    demandes = list(dict.fromkeys(a.id))
    if a.non_injectees:
        demandes += [h for h in presents if ed.est_entite(h) and h not in demandes]
    if not demandes:
        return _fin(a, {"ok": False, "error": "aucune hypothèse demandée (--id ou --non-injectees)"})

    dossiers = ed.charger()
    ok_ids, refus = [], []
    for hid in demandes:
        if hid not in presents:
            refus.append({"id": hid, "motif": "introuvable dans hypotheses.yaml"})
        elif not ed.est_entite(hid):
            refus.append({"id": hid, "motif": "pas une entité (seules les entités se suppriment ici)"})
        elif ed.statut(hid, dossiers.get(hid) or {}) == "injecté":
            refus.append({"id": hid, "motif": "entité injectée : elle existe dans le vault, rien n'est supprimé"})
        else:
            ok_ids.append(hid)
    if not ok_ids:
        return _fin(a, {"ok": False, "supprimees": [], "refusees": refus,
                        "error": "; ".join(f"{r['id']} : {r['motif']}" for r in refus) or "rien à supprimer"})

    nouveau, retires = retirer_blocs(texte, ok_ids)
    try:
        attendus = [h for h in presents if h not in ok_ids]
        if sorted(retires) != sorted(ok_ids) or _ids_du_fichier(nouveau) != attendus:
            raise ValueError("contrôle des ids après retrait")
    except (ValueError, yaml.YAMLError) as e:
        return _fin(a, {"ok": False, "refusees": refus, "error": f"retrait refusé, rien écrit ({e})"})

    res = {"ok": True, "supprimees": ok_ids, "refusees": refus, "applique": bool(a.apply)}
    if a.apply:
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_suppr"))
        chemin.write_text(nouveau, encoding="utf-8")
        for hid in ok_ids:
            dossiers.pop(hid, None)
        ed.sauver(dossiers)
        res["message"] = (f"{len(ok_ids)} hypothèse(s) supprimée(s) : {', '.join(ok_ids)} "
                          f"(sauvegarde {chemin.name}.bak_suppr)")
    else:
        res["message"] = f"APERÇU : {len(ok_ids)} hypothèse(s) seraient supprimée(s) : {', '.join(ok_ids)}"
    return _fin(a, res)


def _fin(a, res):
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
    else:
        print(res.get("message") or f"✗ {res.get('error')}")
        for r in res.get("refusees") or []:
            print(f"  ⚠ {r['id']} : {r['motif']}")
        if res.get("ok") and not res.get("applique"):
            print("Relancer avec --apply pour écrire.")
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
