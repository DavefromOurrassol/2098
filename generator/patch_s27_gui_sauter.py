#!/usr/bin/env python3
"""
patch_s27_gui_sauter.py — 24 octobre 2026 (S27, point 5, panneau).

Étape ③ « Injecter » du panneau 🧭 : bouton « Liste de l'étape ④ » (sans IA) et
champs « Sauter » / « Inclure (⚠) », passés à et_si_injecter.py (--plan,
--sauter, --inclure ; voir patch_s27_sauter_avant_injection.py, à appliquer
d'abord). L'étape ④ reprend ces numéros si son propre champ reste vide.

Cibles (tout ou rien, sauvegardes .bak_s27_gui_sauter) :
  gui/app.py           route /api/et_si/injecter/<action> : action « liste », sauter / inclure
  gui/static/app.js    étape ③ : bouton et champs, aide
  generator/et_si_injecter.py  libellé « --inclure » → « Inclure » (si l'ancienne version
                               du patch précédent a été appliquée ; sinon rien)
Refuse un second passage. Redémarrer Flask ensuite.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_gui_sauter.py
"""

import shutil
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
VAULT = GEN.parent
MARQUEUR = "PATCH_S27_GUI_SAUTER"

APP_PY = [
    (
        '    if action not in ("apercu", "injecter"):\n',
        '    if action not in ("apercu", "injecter", "liste"):   # PATCH_S27_GUI_SAUTER\n',
    ),
    (
        '    cmd = [sys.executable, "et_si_injecter.py", "--id", hid] + (["--dry-run"] if action == "apercu" else [])\n',
        '    corps = request.get_json() or {}   # PATCH_S27_GUI_SAUTER\n'
        '    cmd = [sys.executable, "et_si_injecter.py", "--id", hid]\n'
        '    if action == "liste":\n'
        '        cmd.append("--plan")\n'
        '    else:\n'
        '        if action == "apercu":\n'
        '            cmd.append("--dry-run")\n'
        '        for cle in ("sauter", "inclure"):\n'
        '            valeur = re.sub(r"[^0-9,]", "", str(corps.get(cle) or "")).strip(",")\n'
        '            if valeur:\n'
        '                cmd += [f"--{cle}", valeur]\n',
    ),
]

APP_JS = [
    (
        "  const btnInjecter = bouton('Injecter', 'yaml-btn yaml-btn-save');\n"
        "  ligneInjecter.appendChild(btnInjApercu);\n",
        "  const btnInjecter = bouton('Injecter', 'yaml-btn yaml-btn-save');\n"
        "  // PATCH_S27_GUI_SAUTER : tri dès l'injection (mêmes numéros qu'à l'étape ④).\n"
        "  const ligneTri3 = mk('div');\n"
        "  const btnInjListe = bouton('Liste de l\\'étape ④');\n"
        "  ligneTri3.appendChild(btnInjListe);\n"
        "  ligneTri3.appendChild(mk('span', 'option-label', 'Sauter '));\n"
        "  const sauter3 = champ('ex : 3,4');\n"
        "  ligneTri3.appendChild(sauter3);\n"
        "  ligneTri3.appendChild(mk('span', 'option-label', 'Inclure (⚠) '));\n"
        "  const inclure3 = champ('ex : 7');\n"
        "  ligneTri3.appendChild(inclure3);\n"
        "  ligneInjecter.appendChild(ligneTri3);\n"
        "  ligneInjecter.appendChild(btnInjApercu);\n",
    ),
    (
        "    'une double injection, la retire de la file et fait passer le parcours à ④.'));\n",
        "    'une double injection, la retire de la file et fait passer le parcours à ④.\\n' +\n"
        "    'Sauter / Inclure : « Liste de l\\'étape ④ » montre les opérations numérotées (sans IA). Décide ici ce ' +\n"
        "    'que tu sauteras à l\\'étape ④ : les numéros mis dans « Sauter », et les ⚠ sauf ceux mis dans ' +\n"
        "    '« Inclure », ne sont pas donnés comme faits à l\\'IA de l\\'injection (ni leurs acteurs). L\\'étape ④ ' +\n"
        "    'reprend ces numéros si son propre champ reste vide.'));\n",
    ),
    (
        "  const tous = [btnActualiser, btnApercu, btnAdopter, btnRejeter, btnAnnuler, btnInjApercu, btnInjecter,\n",
        "  const tous = [btnActualiser, btnApercu, btnAdopter, btnRejeter, btnAnnuler, btnInjApercu, btnInjecter,\n"
        "                btnInjListe,   // PATCH_S27_GUI_SAUTER\n",
    ),
    (
        "  btnInjApercu.addEventListener('click', () => appeler('injecter', 'apercu', {}));\n"
        "  btnInjecter.addEventListener('click', () => {\n"
        "    if (!confirm('Injecter cet événement dans le vault ? (appels IA ; plusieurs minutes)')) return;\n"
        "    appeler('injecter', 'injecter', {});\n"
        "  });\n",
        "  const tri3 = () => ({ sauter: sauter3.value, inclure: inclure3.value });   // PATCH_S27_GUI_SAUTER\n"
        "  btnInjListe.addEventListener('click', () => appeler('injecter', 'liste', {}));\n"
        "  btnInjApercu.addEventListener('click', () => appeler('injecter', 'apercu', tri3()));\n"
        "  btnInjecter.addEventListener('click', () => {\n"
        "    if (!confirm('Injecter cet événement dans le vault ? (appels IA ; plusieurs minutes)')) return;\n"
        "    appeler('injecter', 'injecter', tri3());\n"
        "  });\n",
    ),
]

INJ_OPTIONNEL = [(" ; --inclure pour les garder)", " ; « Inclure » pour les garder)")]


def preparer(cible, rempl, optionnel=False):
    if not cible.exists():
        return None, f"{cible} introuvable"
    texte = cible.read_text(encoding="utf-8")
    if not optionnel and MARQUEUR in texte:
        return None, f"{cible.name} : déjà patché"
    for i, (ancien, nouveau) in enumerate(rempl, 1):
        n = texte.count(ancien)
        if optionnel:
            if n == 1:
                texte = texte.replace(ancien, nouveau)
            continue
        if n != 1:
            return None, f"{cible.name} : remplacement {i}, {n} occurrence(s) au lieu d'une"
        texte = texte.replace(ancien, nouveau)
    if cible.suffix == ".py":
        try:
            compile(texte, str(cible), "exec")
        except SyntaxError as e:
            return None, f"{cible.name} ne compile pas ({e})"
    return texte, None


def main() -> int:
    inj = GEN / "et_si_injecter.py"
    if "PATCH_S27_SAUTER" not in (inj.read_text(encoding="utf-8") if inj.exists() else ""):
        print("✗ Appliquer d'abord patch_s27_sauter_avant_injection.py — rien fait.")
        return 1
    prets = []
    for cible, rempl, opt in [(VAULT / "gui" / "app.py", APP_PY, False),
                              (VAULT / "gui" / "static" / "app.js", APP_JS, False),
                              (inj, INJ_OPTIONNEL, True)]:
        texte, err = preparer(cible, rempl, opt)
        if err:
            print(f"✗ {err} — rien écrit.")
            return 1
        if texte != cible.read_text(encoding="utf-8"):
            prets.append((cible, texte))
    for cible, texte in prets:
        shutil.copy2(cible, cible.with_name(cible.name + ".bak_s27_gui_sauter"))
        cible.write_text(texte, encoding="utf-8")
        print(f"✓ {cible.relative_to(VAULT)} patché ; sauvegarde .bak_s27_gui_sauter")
    print("  Redémarrer Flask, puis recharger la page.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
