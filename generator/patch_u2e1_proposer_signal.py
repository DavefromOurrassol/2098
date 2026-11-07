#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unification « et si ? » — étape 2e (1/2) : hypothese_depuis_texte.py sait proposer un SIGNAL.

L'IA choisit `type: evenement` (défaut) ou `type: signal` ; pour un signal, la proposition est
ramenée aux règles du signal (force <= 10, mode choc, carte non, 6 scénarios, année >= année en
cours), chaque correction étant signalée. Pour un événement, rien ne change (aucune clé `type`
écrite dans hypotheses.yaml).

    python3 generator/patch_u2e1_proposer_signal.py            # dry-run
    python3 generator/patch_u2e1_proposer_signal.py --apply    # applique (.bak_u2e1)
"""
import py_compile
import shutil
import sys
from pathlib import Path

F = Path("generator/hypothese_depuis_texte.py")

EDITS = [
    ("import yaml\n\nimport dynamique as dyn\n",
     "from datetime import datetime\n\nimport yaml\n\nimport dynamique as dyn\n"),
    ("FORCE_MAX = 25\n", "FORCE_MAX = 25\nSIGNAL_FORCE_MAX = 10   # plafond d'un signal (inject_custom_signals.py)\n"),
    ('- "mode" : "rupture" si l\'élément change le monde POUR DE BON',
     '- "type" : "evenement" (défaut) pour un fait marquant et daté ; "signal" pour une observation ou\n'
     '  une tendance MINEURE à ses débuts, dont l\'effet reste limité. Un signal : force {SIGNAL_FORCE_MAX} au\n'
     '  plus, toujours mode "choc", "carte" "non", "scenarios" "tous", année entière à partir de\n'
     '  {datetime.now().year}, polarité par scénario (dictionnaire des 6 scénarios) si le sens en dépend.\n'
     '- "mode" : "rupture" si l\'élément change le monde POUR DE BON'),
    ('{{"id": "...", "nom": "...", "description": "...", "date": 2040, "mode": "choc",',
     '{{"id": "...", "nom": "...", "type": "evenement", "description": "...", "date": 2040, "mode": "choc",'),
    ('    h = {"id": id_, "nom": str(brut.get("nom") or id_).strip()}\n',
     '    h = {"id": id_, "nom": str(brut.get("nom") or id_).strip()}\n'
     '    typ = str(brut.get("type") or "evenement").strip().lower()\n'
     '    if typ not in ("evenement", "signal"):\n'
     '        av.append(f"type {typ!r} inconnu -> evenement")\n'
     '        typ = "evenement"\n'
     '    est_signal = typ == "signal"\n'
     '    if est_signal:\n'
     '        h["type"] = "signal"\n'),
    ('        if not 2026 <= date <= 2097:\n'
     '            av.append(f"date {date} hors de 2026-2097 -> ramenée dans la plage")\n'
     '            date = min(2097, max(2026, date))\n',
     '        plancher = max(2026, datetime.now().year) if est_signal else 2026\n'
     '        if not plancher <= date <= 2097:\n'
     '            av.append(f"date {date} hors de {plancher}-2097 -> ramenée dans la plage")\n'
     '            date = min(2097, max(plancher, date))\n'),
    ('    h["mode"] = mode\n',
     '    if est_signal and mode == "rupture":\n'
     '        av.append("un signal n\'a pas de mode rupture -> choc")\n'
     '        mode = "choc"\n'
     '    h["mode"] = mode\n'),
    ('    scen = brut.get("scenarios") or "tous"\n',
     '    if est_signal:\n'
     '        h["carte"] = "non"\n'
     '    scen = brut.get("scenarios") or "tous"\n'),
    ('    h["scenarios"] = scen\n',
     '    if est_signal and scen != "tous":\n'
     '        av.append("un signal couvre toujours les 6 scénarios -> tous")\n'
     '        scen = "tous"\n'
     '    h["scenarios"] = scen\n'),
    ('        if not 1 <= force <= FORCE_MAX:\n'
     '            av.append(f"{var} : force {force} ramenée entre 1 et {FORCE_MAX}")\n'
     '            force = min(FORCE_MAX, max(1, force))\n',
     '        fmax = SIGNAL_FORCE_MAX if est_signal else FORCE_MAX\n'
     '        if not 1 <= force <= fmax:\n'
     '            av.append(f"{var} : force {force} ramenée entre 1 et {fmax}")\n'
     '            force = min(fmax, max(1, force))\n'),
]


def main():
    if not F.is_file():
        print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(F))
        return 1
    src = F.read_text(encoding="utf-8")
    if "SIGNAL_FORCE_MAX" in src:
        print("Déjà appliqué : rien à faire.")
        return 0
    for i, (ancre, _) in enumerate(EDITS, 1):
        n = src.count(ancre)
        if n != 1:
            print("ERREUR : ancre n°{} trouvée {} fois (attendu : 1). Rien modifié.".format(i, n))
            return 1
    print("{} modifications prévues dans {}.".format(len(EDITS), F))
    if "--apply" not in sys.argv:
        print("Dry-run : rien écrit. Relancer avec --apply pour appliquer.")
        return 0
    new = src
    for ancre, rempl in EDITS:
        new = new.replace(ancre, rempl)
    shutil.copy2(F, str(F) + ".bak_u2e1")
    F.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(F), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(str(F) + ".bak_u2e1", F)
        print("ERREUR de syntaxe, fichier restauré :\n{}".format(e))
        return 1
    print("Appliqué (sauvegarde .bak_u2e1). Syntaxe vérifiée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
