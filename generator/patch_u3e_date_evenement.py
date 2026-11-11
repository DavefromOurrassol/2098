#!/usr/bin/env python3
"""
patch_u3e_date_evenement.py — Ourrassol 2098 (11 nov. 2026)

U3e : date d'un événement tiré d'un article = année + mois (format 2098.03), plafond 2098.12 ;
      jamais postérieure à la date de l'article (contrôle dans le GUI) ;
      un signal reste une année entière, plafond 2097 (inchangé).

Fichiers touchés :
  generator/hypothese_depuis_texte.py   (2 bornes, argument --date en float, date imposée)
  generator/simuler_et_si.py            (borne de validation 2098 -> 2098.12)
  generator/inject_custom_events.py     (borne de date_imposee 2098 -> 2098.12)
  gui/app.py                            (la route transmet la décimale)
  gui/static/app.js                     (menu du mois, plafond selon le type, contrôle article)

Usage (depuis la racine du vault) :
  python3 generator/patch_u3e_date_evenement.py            # dry-run
  python3 generator/patch_u3e_date_evenement.py --apply    # écrit (.bak_u3e) + py_compile
Prérequis : U3c et U3d déjà appliqués. Relancer Flask entièrement ensuite.
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

RACINE = Path(".")

# (fichier, [(ancien, nouveau, libellé)])
EDITS = {
    "generator/hypothese_depuis_texte.py": [
        (
            '        plancher = max(2026, datetime.now().year) if est_signal else 2026\n'
            '        if not plancher <= date <= 2097:\n'
            '            av.append(f"date {date} hors de {plancher}-2097 -> ramenée dans la plage")\n'
            '            date = min(2097, max(plancher, date))\n',
            '        plancher = max(2026, datetime.now().year) if est_signal else 2026\n'
            '        plafond = 2097 if est_signal else 2098   # U3e : un événement peut aller jusqu\'en 2098\n'
            '        if not plancher <= date <= plafond:\n'
            '            av.append(f"date {date} hors de {plancher}-{plafond} -> ramenée dans la plage")\n'
            '            date = min(plafond, max(plancher, date))\n',
            "borne de la réponse de l'IA",
        ),
        (
            '        plancher = max(2026, datetime.now().year) if est_signal else 2026\n'
            '        d2 = min(2097, max(plancher, int(d)))\n'
            '        if d2 != int(d):\n'
            '            av.append(f"date imposée {d} hors de {plancher}-2097 -> {d2}")\n',
            '        plancher = max(2026, datetime.now().year) if est_signal else 2026\n'
            '        if est_signal:   # un signal commence une année entière (plafond 2097)\n'
            '            d2 = min(2097, max(plancher, int(d)))\n'
            '        else:   # U3e : un événement garde l\'année et le mois (2098.03), plafond 2098.12\n'
            '            d2 = round(min(2098.12, max(plancher, float(d))), 2)\n'
            '            if d2 == int(d2):\n'
            '                d2 = int(d2)\n'
            '        if d2 != d:\n'
            '            av.append(f"date imposée {d} hors de {plancher}-{2097 if est_signal else 2098} -> {d2}")\n',
            "date imposée par l'article",
        ),
        (
            'ap.add_argument("--date", type=int, default=None, help="avec --proposer : année imposée")',
            'ap.add_argument("--date", type=float, default=None, help="avec --proposer : date imposée (année, ou année.mois : 2098.03)")',
            "argument --date",
        ),
        (
            'imposes["date"] = args.date',
            'imposes["date"] = int(args.date) if args.date == int(args.date) else args.date',
            "date imposée : entier si pas de mois",
        ),
    ],
    "generator/simuler_et_si.py": [
        (
            'if date is not None and not 2025 <= date <= 2098:\n'
            '        erreurs.append(f"date {date:g} hors de la période 2025-2098")',
            'if date is not None and not 2025 <= date <= 2098.12:   # U3e : 2098.12 = décembre 2098\n'
            '        erreurs.append(f"date {date:g} hors de la période 2025-2098")',
            "validation de la date d'hypothèse",
        ),
    ],
    "generator/inject_custom_events.py": [
        (
            'if date is not None and not 2025 <= date <= 2098:\n'
            '            erreurs.append(f"date_imposee {date:g} hors de 2025-2098")',
            'if date is not None and not 2025 <= date <= 2098.12:   # U3e : 2098.12 = décembre 2098\n'
            '            erreurs.append(f"date_imposee {date:g} hors de 2025-2098")',
            "validation de date_imposee",
        ),
    ],
    "gui/app.py": [
        (
            'cmd += ["--date", str(int(data["date"]))]',
            'cmd += ["--date", f"{round(float(data[\'date\']), 2):g}"]   # U3e : année ou année.mois',
            "route : transmet la décimale",
        ),
    ],
    "gui/static/app.js": [
        (
            "champDate.type = 'number'; champDate.min = '2026'; champDate.max = '2097'; champDate.style.width = '80px';\n"
            "  champDate.value = article.annee != null ? Math.min(2097, Math.max(2026, article.annee)) : '';\n",
            "champDate.type = 'number'; champDate.min = '2026'; champDate.max = '2098'; champDate.style.width = '80px';\n"
            "  champDate.value = article.annee != null ? Math.min(2098, Math.max(2026, article.annee)) : '';\n",
            "case année : plafond 2098",
        ),
        (
            "  lblDate.appendChild(champDate);\n",
            "  lblDate.appendChild(champDate);\n"
            "  // U3e : mois de l'événement (événement seulement) ; par défaut le mois de l'article\n"
            "  const NOMS_MOIS_U3E = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',\n"
            "                         'septembre', 'octobre', 'novembre', 'décembre'];\n"
            "  const selMois = document.createElement('select');\n"
            "  selMois.style.width = 'auto';\n"
            "  NOMS_MOIS_U3E.forEach((nom, i) => {\n"
            "    const o = document.createElement('option'); o.value = String(i + 1); o.textContent = nom;\n"
            "    selMois.appendChild(o);\n"
            "  });\n"
            "  selMois.value = String(article.mois || 1);\n"
            "  lblDate.appendChild(document.createTextNode(' '));\n"
            "  lblDate.appendChild(selMois);\n",
            "menu du mois",
        ),
        (
            "  const majReglages = () => {   // un signal couvre toujours les 6 scénarios, sans mode rupture\n"
            "    const sig = selType.value === 'signal';\n",
            "  const majReglages = () => {   // un signal couvre toujours les 6 scénarios, sans mode rupture\n"
            "    const sig = selType.value === 'signal';\n"
            "    selMois.disabled = sig; selMois.style.opacity = sig ? '0.4' : '';   // U3e : un signal = année entière\n"
            "    champDate.max = sig ? '2097' : '2098';\n",
            "plafond et mois selon le type",
        ),
        (
            "    const extra = { date: champDate.value ? parseInt(champDate.value, 10) : null };\n",
            "    const extra = { date: null };\n"
            "    if (champDate.value) {   // U3e\n"
            "      let an = parseInt(champDate.value, 10);\n"
            "      if (selType.value === 'signal') {\n"
            "        extra.date = Math.min(2097, an);\n"
            "      } else {\n"
            "        let mo = parseInt(selMois.value, 10) || 1;\n"
            "        // un événement ne peut pas être postérieur à l'article qui le raconte\n"
            "        if (article.annee != null && (an * 100 + mo) > (article.annee * 100 + (article.mois || 12))) {\n"
            "          an = article.annee; mo = article.mois || 12;\n"
            "          champDate.value = String(an); selMois.value = String(mo);\n"
            "        }\n"
            "        an = Math.min(2098, an);\n"
            "        extra.date = Math.round((an + mo / 100) * 100) / 100;\n"
            "      }\n"
            "    }\n",
            "date envoyée (année.mois) et contrôle article",
        ),
    ],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    print(f"patch_u3e — mode {'APPLY' if args.apply else 'DRY-RUN'}")
    plan, bloque = [], False
    for fichier, edits in EDITS.items():
        chemin = RACINE / fichier
        if not chemin.exists():
            print(f"✗ {fichier} introuvable (lancer depuis la racine du vault : python3 generator/patch_….py)")
            sys.exit(1)
        texte = chemin.read_text(encoding="utf-8")
        nouveau = texte
        for ancien, neuf, nom in edits:
            n = nouveau.count(ancien)
            if neuf in nouveau:   # déjà appliqué (le nouveau texte peut contenir l'ancien)
                print(f"  · {fichier} : {nom} — déjà appliqué")
            elif n == 1:
                nouveau = nouveau.replace(ancien, neuf)
                print(f"  ✓ {fichier} : {nom}")
            else:
                print(f"  ✗ {fichier} : {nom} — {n} occurrence(s) de l'ancien texte (attendu : 1)")
                bloque = True
        if nouveau != texte:
            plan.append((chemin, texte, nouveau))
    if bloque:
        print("✗ Au moins un remplacement n'est pas applicable : rien n'est écrit.")
        sys.exit(1)
    if not plan:
        print("Rien à faire.")
        return
    if not args.apply:
        print(f"[DRY-RUN] {len(plan)} fichier(s) seraient modifiés. Relancer avec --apply.")
        return
    for chemin, ancien_txt, nouveau_txt in plan:
        shutil.copy2(chemin, str(chemin) + ".bak_u3e")
        chemin.write_text(nouveau_txt, encoding="utf-8")
        if chemin.suffix == ".py":
            try:
                py_compile.compile(str(chemin), doraise=True)
            except py_compile.PyCompileError as e:
                print(f"✗ py_compile {chemin} : {e}\n  Restaurer : cp {chemin}.bak_u3e {chemin}")
                sys.exit(1)
        print(f"  écrit : {chemin} (sauvegarde .bak_u3e)")
    print("Terminé. Relancer Flask entièrement (app.py / app.js modifiés).")


if __name__ == "__main__":
    main()
