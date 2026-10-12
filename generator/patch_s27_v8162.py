#!/usr/bin/env python3
"""
patch_s27_v8162.py — Ourrassol 2098 (S27, 12 octobre 2026)
==========================================================

Fin du point 1 (passe branchée dans le simulateur) et point 2 de S27.

simuler_et_si.py (v8.16.1 -> v8.16.2) :
  - acteurs_hint de l'entrée d'injection commune : entités les plus touchées de
    chaque scénario (lecture IA et obligatoires de la passe), 4 au plus par
    scénario, acteurs_hint_count = le plus grand nombre retenu dans un scénario ;
  - liste d'application : une relation rompue « parce que l'entité a disparu »
    alors que cette entité n'est déclarée disparue nulle part est marquée ⚠
    (cas Genève : Archives Neutres « résiduel » d'après la lecture IA).

inject_custom_events.py :
  - point 2 : plus de troncature ni de ⚠ « N variables reçues au lieu de 4 max »
    quand les impacts sont imposés (les variables imposées sont reprises juste
    après) ;
  - acteurs_hint : un slug suffixé d'un AUTRE scénario n'est pas imposé dans ce
    scénario (une entrée commune porte les acteurs des six scénarios) ;
  - QUEUE_TEMPLATE documenté.

Les deux fichiers sont vérifiés avant toute écriture : tout ou rien.
Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v8162.py --dry-run && python3 generator/patch_s27_v8162.py
Sauvegardes .bak_v8162 ; refuse un second passage.
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent

SIMULATEUR = [
    ('VERSION = "v8.16.1"', 'VERSION = "v8.16.2"', 1),

    # Relation rompue qui invoque une disparition non déclarée
    ('        if cle and r["action"] == "rompue":\n'
     '            groupes.setdefault(cle, []).append(r)\n'
     '        else:\n'
     '            rels.append(dict(r, passe=True))\n',
     '        if cle and r["action"] == "rompue":\n'
     '            groupes.setdefault(cle, []).append(r)\n'
     '        else:\n'
     '            # V8.16.2 : rupture justifiée par une disparition que rien ne déclare.\n'
     '            alerte = None\n'
     '            if r["action"] == "rompue":\n'
     '                traj_b = next((t["apres"] for t in (cons.get("trajectoires") or [])\n'
     '                               if t["instance"] == r["b"]), (by_inst.get(r["b"]) or {}).get("trajectoire"))\n'
     '                raison_pliee = _plie(r.get("raison") or "")\n'
     '                if traj_b != "disparu" and any(m in raison_pliee for m in\n'
     '                                               ("dispar", "detrui", "n\'existe_plus", "n\'existent_plus")):\n'
     '                    alerte = (f"`{r[\'b\']}` n\'est déclarée disparue nulle part (trajectoire retenue : "\n'
     '                              f"{traj_b or \'?\'}) : garder la relation, ou faire disparaître l\'entité")\n'
     '            rels.append(dict(r, passe=True, alerte=alerte))\n', 1),
    ('            _etape(E, "Relations", f"{r[\'type\']} rompue : {r[\'a_nom\']} ↔ {r[\'b_nom\']}"\n'
     '                   + (marque if r.get("passe") else ""),\n'
     '                   f"à la main : retirer de `{champ}` dans les DEUX fiches ({r[\'a\']}, {r[\'b\']})",\n'
     '                   "la réciprocité n\'enlève rien")\n',
     '            _etape(E, "Relations", ("⚠ " if r.get("alerte") else "")\n'
     '                   + f"{r[\'type\']} rompue : {r[\'a_nom\']} ↔ {r[\'b_nom\']}"\n'
     '                   + (marque if r.get("passe") else ""),\n'
     '                   f"à la main : retirer de `{champ}` dans les DEUX fiches ({r[\'a\']}, {r[\'b\']})",\n'
     '                   r.get("alerte") or "la réciprocité n\'enlève rien")\n', 1),

    # Entités les plus touchées
    ('    return {"etapes": E, "avert": donnees["avert"], "sources_ia": sources_ia, "fiches_citant": cites,\n'
     '            "nouvelles_entites": cons.get("nouvelles_entites") or []}\n',
     '    # V8.16.2 : entités les plus touchées, pour acteurs_hint de l\'entrée commune.\n'
     '    poids = {}\n'
     '\n'
     '    def _pese(slug, p):\n'
     '        if slug and str(slug).endswith("_" + sc):\n'
     '            poids[slug] = poids.get(slug, 0) + p\n'
     '    for t in cons.get("trajectoires") or []:\n'
     '        _pese(t["instance"], 2)\n'
     '    for t in p_obl["trajectoires"]:\n'
     '        _pese(t["instance"], 3)\n'
     '    for t in p_obl["textes"]:\n'
     '        if t.get("genre") == "instance":\n'
     '            _pese(t["slug"], 2)\n'
     '    for r in p_obl["relations"]:\n'
     '        _pese(r["a"], 1)\n'
     '        _pese(r["b"], 1)\n'
     '    acteurs = [s for s, _ in sorted(poids.items(), key=lambda x: -x[1])][:4]\n'
     '    return {"etapes": E, "avert": donnees["avert"], "sources_ia": sources_ia, "fiches_citant": cites,\n'
     '            "nouvelles_entites": cons.get("nouvelles_entites") or [], "acteurs": acteurs}\n', 1),
    ('    # V8.15 : ce qui a été simulé est imposé à l\'injection (patch_s27_injection_imposee.py).\n',
     '    # V8.16.2 : entités les plus touchées (lecture IA, passe exhaustive), 4 au plus par scénario ;\n'
     '    # inject_custom_events.py n\'impose dans un scénario que les slugs de ce scénario.\n'
     '    par_sc = {sc: (application.get(sc) or {}).get("acteurs") or [] for sc in scen}\n'
     '    acteurs = list(dict.fromkeys(a for sc in scen for a in par_sc[sc]))\n'
     '    if acteurs:\n'
     '        entree["acteurs_hint"] = acteurs\n'
     '        entree["acteurs_hint_count"] = max(len(v) for v in par_sc.values())\n'
     '    # V8.15 : ce qui a été simulé est imposé à l\'injection (patch_s27_injection_imposee.py).\n', 1),
    ('            "```yaml", _yaml_bloc([entree]), "```", ""]',
     '            *(["`acteurs_hint` : entités les plus touchées de chaque scénario (lecture IA, passe "\n'
     '               "exhaustive), 4 au plus par scénario ; chaque slug ne vaut que pour son scénario.", ""]\n'
     '              if entree.get("acteurs_hint") else []),\n'
     '            "```yaml", _yaml_bloc([entree]), "```", ""]', 1),
]

INJECTION = [
    # Point 2
    ('    if len(variables) > max_vars:\n'
     '        hints_valid = [h for h in (variables_hint or []) if h in VALID_VARS]\n',
     '    # PATCH_S27_V8162 : pas de troncature quand les variables sont imposées\n'
     '    # (elles sont reprises juste après) : le ⚠ était trompeur.\n'
     '    if len(variables) > max_vars and not (impositions and impositions["impacts"]):\n'
     '        hints_valid = [h for h in (variables_hint or []) if h in VALID_VARS]\n', 1),

    # Acteurs imposés : seulement ceux de ce scénario
    ('            available_actors = load_available_actors(scenario)\n',
     '            available_actors = load_available_actors(scenario)\n'
     '            # PATCH_S27_V8162 : un slug suffixé d\'un autre scénario n\'est pas imposé ici\n'
     '            # (une entrée commune porte les acteurs de tous les scénarios).\n'
     '            autres_sc = [s for s in SCENARIOS if s != scenario]\n'
     '            actors_hint_sc = [h for h in (actors_hint or [])\n'
     '                              if not any(str(h).endswith("_" + s) for s in autres_sc)] or None\n', 1),
    ('registre_excerpt, available_actors, actors_hint,\n',
     'registre_excerpt, available_actors, actors_hint_sc,\n', 2),
    ('truncate_actors(instance_data, actors_hint, actors_hint_count, available_actors)\n',
     'truncate_actors(instance_data, actors_hint_sc, actors_hint_count, available_actors)\n', 2),

    # Documentation de la queue
    ('#                            ou plusieurs (liste) que tu IMPOSES.\n',
     '#                            ou plusieurs (liste) que tu IMPOSES. Un slug\n'
     '#                            suffixé _<scénario> ne vaut que pour ce scénario.\n', 1),
]


def preparer(chemin, remplacements, deja, attendu):
    texte = chemin.read_text(encoding="utf-8")
    if deja in texte:
        sys.exit(f"✗ {chemin.name} : patch déjà appliqué : rien à faire.")
    if attendu not in texte:
        sys.exit(f"✗ {chemin.name} : version attendue absente ({attendu!r}) : rien écrit.")
    for n, (avant, apres, compte_attendu) in enumerate(remplacements, 1):
        compte = texte.count(avant)
        if compte != compte_attendu:
            sys.exit(f"✗ {chemin.name}, ancre n°{n} trouvée {compte} fois ({compte_attendu} attendue) : "
                     f"rien écrit.\n  Début de l'ancre : {avant[:80]!r}")
        texte = texte.replace(avant, apres)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(texte)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ {chemin.name} patché ne compile pas, rien écrit : {e}")
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass
    return texte


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dossier", default=str(DOSSIER))
    args = ap.parse_args()
    d = Path(args.dossier)
    sim, inj = d / "simuler_et_si.py", d / "inject_custom_events.py"
    t_sim = preparer(sim, SIMULATEUR, "V8.16.2 :", 'VERSION = "v8.16.1"')
    t_inj = preparer(inj, INJECTION, "PATCH_S27_V8162", "PATCH_S27_INJECTION_IMPOSEE")
    if args.dry_run:
        print(f"✓ {len(SIMULATEUR)} + {len(INJECTION)} remplacements possibles, compilation OK "
              f"(dry-run, rien écrit).")
        return
    for chemin, texte in ((sim, t_sim), (inj, t_inj)):
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_v8162"))
        chemin.write_text(texte, encoding="utf-8")
    print("✓ simuler_et_si.py passé en v8.16.2, inject_custom_events.py corrigé ; sauvegardes .bak_v8162.")


if __name__ == "__main__":
    main()
