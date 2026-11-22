#!/usr/bin/env python3
"""
patch_u4p_cosmetiques.py — Ourrassol 2098 (22 novembre 2026)
============================================================

B9, points cosmétiques (un seul patch, 4 fichiers, tout ou rien) :

1. Date « 2061.01 » (gui/static/app.js) : quand l'article ne donne que l'année
   d'un événement, l'onglet Articles imposait janvier (« 2061.01 »). Le menu des
   mois gagne « (mois inconnu) » ; il est choisi d'office pour un événement sans
   mois, et la date envoyée est alors l'année seule (2061). Le message
   « Événement choisi » n'affiche plus de mois inventé.
2. Citation « « … » » (gui/static/app.js) : une citation qui porte déjà ses
   guillemets n'est plus entourée d'une seconde paire.
3. Suffixe d'id (generator/hypothese_depuis_texte.py) : un id terminé par une
   année différente de la date retenue (methane_…_2098 pour une date 2097) est
   réaligné sur cette date, avec un ⚠ (id libre vérifié).
4. Libellé (generator/extraire_evenements_article.py) : « écarté (plan / projet /
   débat) » devient « écarté (pas un événement) » (le motif dit le reste :
   statistique, citation tronquée, plan…).
5. Contexte U3s (generator/inject_custom_events.py) : le titre de l'article vient
   aussi de son premier titre de corps (# Titre ou **Titre**) avant le nom de
   fichier ; une ligne de séparation (---) n'est plus prise pour un paragraphe.

Non traité ici (donnée, pas code) : le nom d'affichage de l'archétype
evenements/accords_oms_regulation_mondiale_2039.md, à corriger à la main.

Après --apply : Cmd-Maj-R dans le navigateur (app.js) ; pas de relance de Flask.

Usage (depuis la racine du vault) :
    python3 generator/patch_u4p_cosmetiques.py           # dry-run
    python3 generator/patch_u4p_cosmetiques.py --apply   # écrit (.bak_u4p)
"""

import argparse
import shutil
import sys
from pathlib import Path

TAG = "u4p"

REMPLACEMENTS = {
    Path("gui/static/app.js"): [
        ("1a. menu des mois : « (mois inconnu) »",
         "  NOMS_MOIS_U3E.forEach((nom, i) => {\n",
         "  { const oInc = document.createElement('option'); oInc.value = '0';   // U4p : année seule\n"
         "    oInc.textContent = '(mois inconnu)'; selMois.appendChild(oInc); }\n"
         "  NOMS_MOIS_U3E.forEach((nom, i) => {\n"),
        ("1b. événement sans mois : « (mois inconnu) » choisi",
         "champDate.value = String(ev.annee); selMois.value = String(ev.mois);",
         "champDate.value = String(ev.annee); selMois.value = ev.mois_connu ? String(ev.mois) : '0';   // U4p"),
        ("1c. message « Événement choisi » sans mois inventé",
         ": `Événement choisi : ${libelleDate(ev)}${ev.date_explicite ? '' : ' (date déduite)'}.`;",
         ": `Événement choisi : ${ev.mois_connu ? libelleDate(ev) : ev.annee}${ev.date_explicite ? '' : ' (date déduite)'}.`;   // U4p"),
        ("1d. date envoyée : l'année seule si le mois est inconnu",
         "let mo = parseInt(selMois.value, 10) || 1;",
         "let mo = parseInt(selMois.value, 10) || 0;   // U4p : 0 = mois inconnu -> année seule"),
        ("2. citation : pas de double guillemet",
         "if (ev.citation) l.appendChild(mk('div', `« ${ev.citation} »`, 'color:#888;font-style:italic;margin-top:2px'));",
         "if (ev.citation) l.appendChild(mk('div', /^[«“\"]/.test(ev.citation.trim()) ? ev.citation   // U4p\n"
         "        : `« ${ev.citation} »`, 'color:#888;font-style:italic;margin-top:2px'));"),
    ],
    Path("generator/hypothese_depuis_texte.py"): [
        ("3a. appel : suffixe d'id réaligné sur la date",
         '        av += plafonner_article_u4n(h)\n',
         '        av += plafonner_article_u4n(h)\n'
         '    av += aligner_suffixe_id_u4p(h, ids_existants())   # U4p\n'),
        ("3b. fonction aligner_suffixe_id_u4p()",
         "\n\ndef plafonner_article_u4n(h):\n",
         '''

def aligner_suffixe_id_u4p(h, ids_pris):
    """U4p : id terminé par une année différente de la date retenue -> suffixe réaligné.
    Modifie h ; retourne les avertissements."""
    m = re.search(r"_(\\d{4})$", str(h.get("id") or ""))
    try:
        an = int(float(h.get("date")))
    except (TypeError, ValueError):
        return []
    if not m or int(m.group(1)) == an:
        return []
    base = h["id"][: m.start()] + f"_{an}"
    nouvel, n = base, 2
    while nouvel in ids_pris:
        nouvel = f"{base}_{n}"
        n += 1
    ancien = h["id"]
    h["id"] = nouvel
    return [f"id {ancien!r} -> {nouvel!r} (suffixe aligné sur la date {an})"]


def plafonner_article_u4n(h):
'''),
    ],
    Path("generator/extraire_evenements_article.py"): [
        ("4. libellé « écarté (pas un événement) »",
         "écarté (plan / projet / débat) : {motif}",
         "écarté (pas un événement) : {motif}"),
    ],
    Path("generator/inject_custom_events.py"): [
        ("5a. contexte : séparateurs --- ignorés",
         '            paras = [p.strip() for p in re.split(r"\\n\\s*\\n", corps) if p.strip()]\n',
         '            paras = [p.strip() for p in re.split(r"\\n\\s*\\n", corps)\n'
         '                     if p.strip() and not re.fullmatch(r"[-*_\\s]{3,}", p.strip())]   # U4p\n'),
        ("5b. contexte : titre lu dans le corps avant le nom de fichier",
         '            titre = str(fm.get("titre") or fm.get("title") or f.stem) if isinstance(fm, dict) else f.stem\n',
         '            titre_corps = next((re.sub(r"^#+\\s*|^\\*\\*|\\*\\*$", "", p.splitlines()[0]).strip()   # U4p\n'
         '                                for p in paras if re.match(r"^(#+\\s|\\*\\*.+\\*\\*$)", p.splitlines()[0])), "")\n'
         '            titre = str((fm.get("titre") or fm.get("title") if isinstance(fm, dict) else "")\n'
         '                        or titre_corps or f.stem)\n'),
    ],
}


def main():
    ap = argparse.ArgumentParser(description="Patch U4p : points cosmétiques.")
    ap.add_argument("--apply", action="store_true", help="écrit les fichiers (sinon dry-run)")
    args = ap.parse_args()
    manquants = [str(f) for f in REMPLACEMENTS if not f.is_file()]
    if manquants:
        sys.exit("✗ introuvable(s) : " + ", ".join(manquants) + " (lancer depuis la racine du vault)")
    if "aligner_suffixe_id_u4p" in Path("generator/hypothese_depuis_texte.py").read_text(encoding="utf-8"):
        sys.exit("✗ U4p déjà appliqué : rien à faire.")
    a_ecrire, ok = {}, True
    for chemin, rempl in REMPLACEMENTS.items():
        texte = chemin.read_text(encoding="utf-8")
        for nom, ancien, neuf in rempl:
            n = texte.count(ancien)
            if n != 1:
                print(f"✗ {chemin} : {nom} — ancre trouvée {n} fois (attendu 1)")
                ok = False
                continue
            texte = texte.replace(ancien, neuf)
            print(f"✓ {chemin} : {nom}")
        if chemin.suffix == ".py":
            try:
                compile(texte, str(chemin), "exec")
            except SyntaxError as e:
                print(f"✗ {chemin} ne compile plus : {e}")
                ok = False
        a_ecrire[chemin] = texte
    if not ok:
        sys.exit("✗ Patch non appliqué : aucun fichier n'a été modifié.")
    print("✓ Toutes les ancres trouvées ; les fichiers Python patchés compilent.")
    if not args.apply:
        print("\n(dry-run) Rien n'est écrit. Relancer avec --apply.")
        return
    for chemin, texte in a_ecrire.items():
        shutil.copy(chemin, chemin.with_name(chemin.name + f".bak_{TAG}"))
        chemin.write_text(texte, encoding="utf-8")
        print(f"→ {chemin} écrit (sauvegarde {chemin.name}.bak_{TAG})")
    print("\nSuite : Cmd-Maj-R dans le navigateur (app.js). Pas de relance de Flask.")


if __name__ == "__main__":
    main()
