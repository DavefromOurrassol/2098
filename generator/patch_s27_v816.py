#!/usr/bin/env python3
"""
patch_s27_v816.py — Ourrassol 2098 (S27, 12 octobre 2026)
=========================================================

Branche la passe exhaustive (et_si_exhaustif.py) dans le simulateur
(simuler_et_si.py v8.15 -> v8.16) :
  - option --passe-exhaustive (payant : ≈ 0,05 à 0,11 $ par scénario, cache) ;
  - section « Passe exhaustive » du rapport, dans chaque scénario ;
  - obligatoires de la passe dans la liste d'application (Trajectoires,
    Relations, Fiches à relire), marqués « [passe exhaustive] » ;
  - relations rompues d'une entité qui disparaît regroupées en une étape ;
  - 20 possibles prioritaires en étapes facultatives (« Possibles (facultatif) ») ;
  - clé « passe » dans generator/state/dernier_et_si.json.
Les acteurs (acteurs_hint) de l'entrée commune ne sont PAS encore remplis :
étape suivante, avec inject_custom_events.py.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v816.py            # applique (sauvegarde .bak_v816)
    python3 generator/patch_s27_v816.py --dry-run  # vérifie sans écrire
Refuse un second passage.
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "simuler_et_si.py"

REMPLACEMENTS = [
    # 1. Version
    ('VERSION = "v8.15"', 'VERSION = "v8.16"'),

    # 2. Usage
    ('    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --json\n"""',
     '    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --json\n'
     '    python3 generator/simuler_et_si.py --id invasion_bresil_2029 --consequences-ia --passe-exhaustive --report\n"""'),

    # 3. Nouvelle section de la liste
    ('"Fiches à relire", "Articles et site", "Contrôles"]',
     '"Fiches à relire", "Possibles (facultatif)", "Articles et site", "Contrôles"]'),

    # 4. Signature et préparation
    ('def liste_application(hyp, sc, res, cons, geo_ops, donnees):\n'
     '    """Étapes à valider à la main pour CE scénario. Rien n\'est écrit."""\n'
     '    E = []\n'
     '    cons = cons if cons and not cons.get("erreur") else {}\n',
     'def liste_application(hyp, sc, res, cons, geo_ops, donnees, passe=None):\n'
     '    """Étapes à valider à la main pour CE scénario. Rien n\'est écrit."""\n'
     '    E = []\n'
     '    cons = cons if cons and not cons.get("erreur") else {}\n'
     '    # V8.16 : passe exhaustive (obligatoires dans la liste, possibles prioritaires en facultatif).\n'
     '    passe = passe if passe and not passe.get("erreur") else {}\n'
     '    p_obl = passe.get("obligatoire") or {"trajectoires": [], "relations": [], "textes": []}\n'
     '    marque = " [passe exhaustive]"\n'),

    # 5. Trajectoires : lecture IA + obligatoires de la passe
    ('    for t in cons.get("trajectoires") or []:\n'
     '        inst = by_inst.get(t["instance"]) or {}\n',
     '    for t in (cons.get("trajectoires") or []) + [dict(x, passe=True) for x in p_obl["trajectoires"]]:\n'
     '        inst = by_inst.get(t["instance"]) or {}\n'),
    ('        _etape(E, "Trajectoires", ("⚠ " if saut else "") + f"{t.get(\'nom\')} (`{t[\'instance\']}`) : {t[\'avant\']} → {t[\'apres\']}",\n',
     '        _etape(E, "Trajectoires", ("⚠ " if saut else "") + f"{t.get(\'nom\')} (`{t[\'instance\']}`) : {t[\'avant\']} → {t[\'apres\']}"\n'
     '               + (marque if t.get("passe") else ""),\n'),

    # 6. Relations : obligatoires de la passe, regroupement des disparitions
    ('    rels = cons.get("relations") or []\n'
     '    for r in rels:\n',
     '    # V8.16 : relations de la passe ; les relations rompues d\'une entité qui disparaît\n'
     '    # sont regroupées en une seule étape (cas Genève : 24 obligatoires).\n'
     '    disparues = {t["instance"]: t.get("nom") for t in (cons.get("trajectoires") or []) + p_obl["trajectoires"]\n'
     '                 if t.get("apres") == "disparu"}\n'
     '    rels = list(cons.get("relations") or [])\n'
     '    groupes = {}\n'
     '    for r in p_obl["relations"]:\n'
     '        cle = r["a"] if r["a"] in disparues else (r["b"] if r["b"] in disparues else None)\n'
     '        if cle and r["action"] == "rompue":\n'
     '            groupes.setdefault(cle, []).append(r)\n'
     '        else:\n'
     '            rels.append(dict(r, passe=True))\n'
     '    for cle, liste_r in groupes.items():\n'
     '        autres = list(dict.fromkeys(r["b"] if r["a"] == cle else r["a"] for r in liste_r))\n'
     '        _etape(E, "Relations", f"{disparues[cle] or cle} (`{cle}`) disparaît : retirer ses "\n'
     '               f"{len(liste_r)} relation(s) rompue(s){marque}",\n'
     '               f"à la main : retirer `{cle}` des alliances / oppositions de "\n'
     '               + ", ".join(f"`{a}`" for a in autres[:MAX_LISTE]) + (" …" if len(autres) > MAX_LISTE else "")\n'
     '               + f", puis vider celles de instances/{cle}.md",\n'
     '               "regroupé sous l\'entité disparue ; la réciprocité n\'enlève rien")\n'
     '    for r in rels:\n'),
    ('            _etape(E, "Relations", f"{r[\'type\']} nouvelle : {r[\'a_nom\']} ↔ {r[\'b_nom\']}",\n',
     '            _etape(E, "Relations", f"{r[\'type\']} nouvelle : {r[\'a_nom\']} ↔ {r[\'b_nom\']}"\n'
     '                   + (marque if r.get("passe") else ""),\n'),
    ('            _etape(E, "Relations", f"{r[\'type\']} rompue : {r[\'a_nom\']} ↔ {r[\'b_nom\']}",\n',
     '            _etape(E, "Relations", f"{r[\'type\']} rompue : {r[\'a_nom\']} ↔ {r[\'b_nom\']}"\n'
     '                   + (marque if r.get("passe") else ""),\n'),

    # 7. Textes obligatoires, en tête des fiches à relire
    ('    # 9 bis. Fiches à relire (V8.3) ------------------------------------------------\n',
     '    # V8.16 : phrases que la passe exhaustive juge fausses (obligatoires).\n'
     '    for t in p_obl["textes"]:\n'
     '        dossier = "instances" if t.get("genre") == "instance" else "event_instances"\n'
     '        _etape(E, "Fiches à relire", f"Corriger une phrase de `{t[\'slug\']}`{marque}",\n'
     '               f"à la main : {dossier}/{t[\'slug\']}.md",\n'
     '               f"« {_court(t[\'extrait\'], 160)} » — contredit par : {t.get(\'contredit\') or \'?\'}")\n'
     '\n'
     '    # 9 bis. Fiches à relire (V8.3) ------------------------------------------------\n'),

    # 8. Relecture IA par mots : inutile quand la passe a tout relu
    ('    else:\n'
     '        # V8.9 : rien à chercher par mots',
     '    elif passe:\n'
     '        _etape(E, "Fiches à relire", "Aucun pays ni nom propre à chercher : la passe exhaustive a relu "\n'
     '               "toutes les fiches du scénario (obligatoires ci-dessus et dans les autres sections)")\n'
     '    else:\n'
     '        # V8.9 : rien à chercher par mots'),

    # 9. Possibles prioritaires, avant les articles
    ('    # 10. Articles et site -----------------------------------------------------\n',
     '    # V8.16 : possibles prioritaires de la passe, en étapes facultatives.\n'
     '    if passe:\n'
     '        import et_si_exhaustif as ex\n'
     '        fiches_p = ex.grouper_possibles(passe.get("possible")\n'
     '                                        or {"trajectoires": [], "relations": [], "textes": []})\n'
     '        prio = [c for c in passe.get("classement") or [] if c.get("slug") in fiches_p][:ex.PRIORITE_MAX]\n'
     '        for c in prio:\n'
     '            f = fiches_p[c["slug"]]\n'
     '            items = [(g, x) for g, x in f["items"] if not ex._disqualifie(x)] or f["items"]\n'
     '            _etape(E, "Possibles (facultatif)", f"{f[\'nom\']} (`{c[\'slug\']}`) : "\n'
     '                   + ex._resume_fiche({"items": items}) + marque, motif=c.get("pourquoi") or None)\n'
     '        if len(fiches_p) > len(prio):\n'
     '            _etape(E, "Possibles (facultatif)",\n'
     '                   f"… et {len(fiches_p) - len(prio)} autre(s) fiche(s) avec des changements possibles",\n'
     '                   motif="détail dans la section « Passe exhaustive » de ce scénario")\n'
     '\n'
     '    # 10. Articles et site -----------------------------------------------------\n'),
    ('    entites_changees = {t["instance"] for t in cons.get("trajectoires") or []}\n',
     '    entites_changees = ({t["instance"] for t in cons.get("trajectoires") or []}\n'
     '                        | {t["instance"] for t in p_obl["trajectoires"]})\n'),

    # 10. Avertissement « tirage IA »
    ('        cons.get(k) for k in ("trajectoires", "relations", "zones_statut", "nouvelles_entites"))\n'
     '    return {"etapes": E,',
     '        cons.get(k) for k in ("trajectoires", "relations", "zones_statut", "nouvelles_entites")) or bool(passe)\n'
     '    return {"etapes": E,'),

    # 11. construire_application
    ('def construire_application(hyp, resultats, consequences, geo, scenarios):\n'
     '    out = {}\n'
     '    for sc in scenarios:\n'
     '        try:\n'
     '            out[sc] = liste_application(hyp, sc, resultats.get(sc), consequences.get(sc),\n'
     '                                        geo.get(sc), _donnees_application(sc))\n',
     'def construire_application(hyp, resultats, consequences, geo, scenarios, passe=None):\n'
     '    out = {}\n'
     '    for sc in scenarios:\n'
     '        try:\n'
     '            out[sc] = liste_application(hyp, sc, resultats.get(sc), consequences.get(sc),\n'
     '                                        geo.get(sc), _donnees_application(sc), (passe or {}).get(sc))\n'),

    # 12. Rendu : section Passe exhaustive après la lecture IA
    ('def rendre_markdown(hyp, resultats, date_fin, avert, geo=None, consequences=None, application=None):\n',
     'def _rendre_passe(p):\n'
     '    """V8.16 : section du rapport produite par et_si_exhaustif.rendre()."""\n'
     '    import et_si_exhaustif as ex\n'
     '    return ex.rendre(p)\n'
     '\n'
     '\n'
     'def rendre_markdown(hyp, resultats, date_fin, avert, geo=None, consequences=None, application=None,\n'
     '                    passe=None):\n'),
    ('    application = application or {}\n'
     '    for sc in SCENARIOS:\n',
     '    application = application or {}\n'
     '    passe = passe or {}\n'
     '    for sc in SCENARIOS:\n'),
    ('            if sc in consequences:\n'
     '                L += _rendre_consequences(consequences[sc])\n',
     '            if sc in consequences:\n'
     '                L += _rendre_consequences(consequences[sc])\n'
     '            if sc in passe:\n'
     '                L += _rendre_passe(passe[sc])\n'),
    ('        if sc in consequences:\n'
     '            L += _rendre_consequences(consequences[sc])\n'
     '        if sc in geo:\n',
     '        if sc in consequences:\n'
     '            L += _rendre_consequences(consequences[sc])\n'
     '        if sc in passe:\n'
     '            L += _rendre_passe(passe[sc])\n'
     '        if sc in geo:\n'),

    # 13. main : option, calcul, transmission
    ('    ap.add_argument("--refaire", action="store_true", help="ignore le cache de la lecture des conséquences")\n',
     '    ap.add_argument("--refaire", action="store_true", help="ignore le cache de la lecture des conséquences"\n'
     '                    " (et de la passe exhaustive si elle est demandée)")\n'
     '    ap.add_argument("--passe-exhaustive", action="store_true",\n'
     '                    help="relit toutes les fiches de chaque scénario (et_si_exhaustif.py, payant : "\n'
     '                         "≈ 0,05 à 0,11 $ par scénario, cache)")\n'),
    ('    # V8 : liste d\'application (phase 3), lecture seule.\n'
     '    portee = [args.scenario] if args.scenario else hyp["scenarios"]\n'
     '    application = construire_application(hyp, resultats, consequences, geo, portee)\n',
     '    portee = [args.scenario] if args.scenario else hyp["scenarios"]\n'
     '    # V8.16 : passe exhaustive, avant la liste d\'application.\n'
     '    passe = {}\n'
     '    if args.passe_exhaustive:\n'
     '        import et_si_exhaustif as ex\n'
     '        for sc in portee:\n'
     '            effets = (resultats.get(sc) or {}).get("effets") or []\n'
     '            lecture = consequences.get(sc)\n'
     '            if not lecture or lecture.get("erreur"):\n'
     '                lecture = ex.lecture_en_cache(hyp, sc, effets)\n'
     '            if lecture is None:\n'
     '                avert.append(f"passe exhaustive ({sc}) : lecture IA absente, passe faite sans "\n'
     '                             f"(cocher aussi la lecture IA)")\n'
     '            print(f"[passe exhaustive] {sc}…", file=sys.stderr)\n'
     '            try:\n'
     '                passe[sc] = ex.passe_exhaustive(hyp, sc, effets, lecture, refaire=args.refaire)\n'
     '            except Exception as e:  # la passe ne doit jamais empêcher le reste du rapport\n'
     '                passe[sc] = {"erreur": f"{type(e).__name__}: {e}"}\n'
     '\n'
     '    # V8 : liste d\'application (phase 3), lecture seule.\n'
     '    application = construire_application(hyp, resultats, consequences, geo, portee, passe)\n'),
    ('              "application": application}\n',
     '              "application": application, "passe": passe}\n'),
    ('    md = rendre_markdown(hyp, resultats, args.date, avert, geo, consequences, application)\n',
     '    md = rendre_markdown(hyp, resultats, args.date, avert, geo, consequences, application, passe)\n'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cible", default=str(CIBLE))
    args = ap.parse_args()
    cible = Path(args.cible)
    texte = cible.read_text(encoding="utf-8")
    if 'VERSION = "v8.16"' in texte or "V8.16 :" in texte:
        sys.exit("✗ Patch déjà appliqué (v8.16) : rien à faire.")
    if 'VERSION = "v8.15"' not in texte:
        sys.exit("✗ simuler_et_si.py n'est pas en v8.15 : patch non appliqué.")
    for n, (avant, apres) in enumerate(REMPLACEMENTS, 1):
        compte = texte.count(avant)
        if compte != 1:
            sys.exit(f"✗ Ancre n°{n} trouvée {compte} fois (1 attendue) : patch non appliqué, rien écrit.\n"
                     f"  Début de l'ancre : {avant[:80]!r}")
        texte = texte.replace(avant, apres)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(texte)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas, rien écrit : {e}")
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass
    if args.dry_run:
        print(f"✓ {len(REMPLACEMENTS)} remplacements possibles, compilation OK (dry-run, rien écrit).")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_v816"))
    cible.write_text(texte, encoding="utf-8")
    print(f"✓ simuler_et_si.py passé en v8.16 ({len(REMPLACEMENTS)} remplacements) ; sauvegarde .bak_v816.")


if __name__ == "__main__":
    main()
