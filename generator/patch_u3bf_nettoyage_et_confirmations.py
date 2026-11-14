#!/usr/bin/env python3
"""
patch_u3bf_nettoyage_et_confirmations.py — Ourrassol 2098 (14 novembre 2026)

Deux nettoyages du chantier « unification » :

 1. CODE MORT (app.py, app.js) : les routes /api/edition/articles et
    /api/edition/injecter_evenement n'ont plus aucun appelant depuis la fermeture des accès
    directs (U3ai) ; elles sont retirées (/api/edition/active, utilisée par le bandeau
    « Mois de parution », est conservée). Le long commentaire d'app.js qui décrit
    l'ancien « Promouvoir un article en événement » est remplacé par un commentaire exact.
 2. confirm() BLOQUÉ : dans ton navigateur, confirm() ne répond pas et le clic ne fait
    « rien ». Quinze emplacements du parcours « et si ? » et de la veille passent à la
    confirmation en deux clics déjà utilisée pour Injecter/Annuler (armer2) : 1er clic = le
    bouton change de texte (« ⚠ Cliquer encore… », 8 s), 2e clic = l'action. Concerne :
    Adopter, Appliquer, les actions de l'étape ⑤ (déplacer une sous-zone, retirer un
    journal, relire la fiche d'événement, remplacer une phrase, avant / après, relire les
    articles, ajouter une règle de lore, résumé du scénario), « Remettre à trier » (veille),
    « Utiliser cette idée » et « Proposer » (remplacement d'un texte déjà saisi).
 Les « Outils directs » repliés et les autres onglets (carte, lore…) ne sont pas touchés.

Prérequis : U3az (armer2 présent dans app.js).
Après application : redémarrer Flask ; Cmd+Maj+R.

    python3 generator/patch_u3bf_nettoyage_et_confirmations.py            # aperçu
    python3 generator/patch_u3bf_nettoyage_et_confirmations.py --apply
Sauvegardes .bak_u3bf ; refuse un second passage ; contrôles de syntaxe avec restauration.
"""
import argparse
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3bf"
APP_PY = Path("gui/app.py")
APP_JS = Path("gui/static/app.js")

PY_DEBUT = '@app.route("/api/edition/articles", methods=["GET"])\n'
PY_FIN = "# ---------------------------------------------------------------------------\n# Simulateur « et si ? » v7.8"
PY_NOUVEAU = ("# U3bf : /api/edition/articles et /api/edition/injecter_evenement retirées (plus d'appelant depuis U3ai :\n"
              "# les événements entrent par « et si ? »). /api/edition/active ci-dessus est conservée.\n\n\n")

JS_COMM_DEBUT = "// Promouvoir un article en événement custom depuis l'onglet Articles (5\n"
JS_COMM_FIN = "function renderArticlesVersEtSi(article, container) {\n"
JS_COMM_NOUVEAU = (
    "// Onglet Articles -> « et si ? » (U3b ... U3be) : l'article devient une hypothèse. Type « événement » :\n"
    "// l'IA lit l'article, on choisit l'événement (date verrouillée) ; « signal faible » ; « entité » : on\n"
    "// écrit son nom et ce que l'article en dit. Écriture seulement par « Ajouter » (hypotheses.yaml).\n"
)

# (libellé, ancre, remplacement)
JS_REMPL = [
 [
  "Parcours ⑤ : déplacer une sous-zone",
  "             [`La déplacer sous ${c.cible}`, () => {\n               if (!confirm(`Déplacer ${z.slug} (et ses ${(z.autres || []).join(', ')}) sous ${c.cible} ? `\n                            + '(sauvegarde .bak_et_si_main)')) return;\n",
  "             [`La déplacer sous ${c.cible}`, (ev) => {\n               if (!armer2(ev.currentTarget, '⚠ Cliquer encore pour déplacer (sauvegarde .bak_et_si_main)')) return;   // U3bf\n"
 ],
 [
  "Parcours ⑤ : retirer un journal",
  "               ['Le retirer', () => {\n                 if (!confirm(`Retirer « ${j.nom} » de journaux.yaml ? Les articles déjà signés ne changent pas `\n                              + '(sauvegarde journaux.yaml.bak_et_si_main).')) return;\n",
  "               ['Le retirer', (ev) => {\n                 if (!armer2(ev.currentTarget, '⚠ Cliquer encore pour retirer (sauvegarde .bak_et_si_main)')) return;   // U3bf\n"
 ],
 [
  "Parcours ⑤ : relecture de la fiche (IA)",
  "      if (!confirm('Appels IA (quelques centimes) : relecture de la fiche d\\'événement, puis une proposition '\n                   + 'par phrase sans proposition. Continuer ?')) return;\n",
  "      if (!armer2(bProp, '⚠ Cliquer encore : appels IA (quelques centimes)')) return;   // U3bf\n"
 ],
 [
  "Parcours ⑤ : remplacer une phrase",
  "          if (!confirm(`Remplacer la phrase dans ${x.fichier} ? (sauvegarde .bak_et_si_main)`)) return;\n",
  "          if (!armer2(bR, '⚠ Cliquer encore pour remplacer (sauvegarde .bak_et_si_main)')) return;   // U3bf\n"
 ],
 [
  "Parcours ⑤ : écrire l'avant / après",
  "            if (!confirm('Écrire dans la fiche les textes « Après » de l\\'avant / après (retouches comprises) ?'\n                         + '\\n(Sauvegarde .bak_au_passe.)')) return;\n",
  "            if (!armer2(bE, '⚠ Cliquer encore pour écrire dans la fiche (sauvegarde .bak_au_passe)')) return;   // U3bf\n"
 ],
 [
  "Parcours ⑤ : refaire l'avant / après (IA)",
  "          if (!confirm('Un appel IA : nouvel avant / après (les retouches faites dans l\\'ancien sont perdues) ; '\n                       + 'la fiche n\\'est pas modifiée. Continuer ?')) return;\n",
  "          if (!armer2(bP, '⚠ Cliquer encore : appel IA, les retouches de l\\'ancien sont perdues')) return;   // U3bf\n"
 ],
 [
  "Parcours ⑤ : relire les articles (IA)",
  "        if (!confirm('Appels IA (quelques centimes par article) : repérage seulement, aucun article n\\'est '\n                     + 'modifié. Continuer ?')) return;\n",
  "        if (!armer2(bV, '⚠ Cliquer encore : appels IA, aucun article modifié')) return;   // U3bf\n"
 ],
 [
  "Parcours ⑤ : ajouter une règle de lore",
  "        if (!confirm(`Ajouter cette règle à lore_regles.yaml (section ${r.sc}) ?`)) return;\n",
  "        if (!armer2(bE, '⚠ Cliquer encore pour ajouter la règle')) return;   // U3bf\n"
 ],
 [
  "Parcours ⑤ : résumé du scénario (IA)",
  "          if (f.action === 'resume' && !confirm(`Régénérer le résumé du scénario ${sc} ? (un appel IA payant)`)) return;\n",
  "          if (f.action === 'resume' && !armer2(b, '⚠ Cliquer encore : un appel IA payant')) return;   // U3bf\n"
 ],
 [
  "Parcours : Adopter",
  "    if (!confirm(typeCourant === 'signal' ? 'Adopter : placer le signal simulé dans la file d\\'injection des signaux ?' : 'Adopter : placer l\\'événement simulé dans la file d\\'injection ?')) return;\n",
  "    if (!armer2(btnAdopter, '⚠ Cliquer encore pour adopter')) return;   // U3bf\n"
 ],
 [
  "Parcours : Appliquer",
  "    if (!confirm('Appliquer au vault les opérations retenues par l\\'aperçu ?\\n' +\n                 '(Sauvegarde .bak_appliquer ; commit git conseillé avant.)')) return;\n",
  "    if (!armer2(btnAppliquer, '⚠ Cliquer encore pour appliquer (sauvegarde .bak_appliquer ; commit git conseillé)')) return;   // U3bf\n"
 ],
 [
  "Veille : remettre à trier (hypothèse)",
  "    document.getElementById('veille-btn-retrier').addEventListener('click', async () => {\n      const ok = confirm(`Remettre « ${c.titre} » à trier ?\\n\\nL'hypothèse « ${c.hypothese_id} » n'est PAS retirée de hypotheses.yaml : supprime-la dans l'onglet « Et si ? » si tu n'en veux plus.`);\n      if (ok) await _veilleChangerStatut(c, 'a_trier');\n",
  "    document.getElementById('veille-btn-retrier').addEventListener('click', async (ev) => {\n      // U3bf : double clic ; l'hypothèse reste dans hypotheses.yaml (à supprimer dans « Et si ? » si besoin)\n      const ok = armer2(ev.currentTarget, '⚠ Cliquer encore (l\\'hypothèse reste dans hypotheses.yaml)');\n"
 ],
 [
  "Veille : remettre à trier (queue)",
  "    document.getElementById('veille-btn-retrier').addEventListener('click', async () => {\n      const ok = confirm(`Remettre « ${c.titre} » à trier ?\\n\\nL'entrée « ${c.queue_id} » `\n        + `n'est PAS retirée de ${queue} : supprime-la à la main si elle n'a pas encore été injectée.`);\n",
  "    document.getElementById('veille-btn-retrier').addEventListener('click', async (ev) => {\n      // U3bf : double clic ; l'entrée de la queue n'est PAS retirée (à supprimer à la main)\n      const ok = armer2(ev.currentTarget, '⚠ Cliquer encore (l\\'entrée de la queue n\\'est pas retirée)');\n"
 ],
 [
  "Suggestions : utiliser cette idée",
  "        if (idee.value.trim() && idee.value.trim() !== s.texte && !confirm('Remplacer l\\'idée actuelle ?')) return;\n",
  "        if (idee.value.trim() && idee.value.trim() !== s.texte && !armer2(b, '⚠ Cliquer encore pour remplacer l\\'idée actuelle')) return;   // U3bf\n"
 ],
 [
  "Nouvelle hypothèse : remplacer le bloc",
  "    if (bloc.value.trim() && !confirm('Remplacer le bloc actuel par une nouvelle proposition ?')) return;\n",
  "    if (bloc.value.trim() && !armer2(btnProposer, '⚠ Cliquer encore pour remplacer le bloc')) return;   // U3bf\n"
 ]
]


def _node_check(chemin):
    try:
        r = subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None, "node absent"
    return r.returncode == 0, r.stderr.strip()


def _premiere_erreur(msg):
    lignes = [l for l in msg.splitlines() if l.strip()]
    return " | ".join(l.strip() for l in lignes[:4] if "SyntaxError" in l or l.strip().startswith("("))[:300]


def verifier_js(chemin, original):
    """Ne bloque que sur une erreur NOUVELLE (un vieux node refuse déjà « ||= » dans l'original)."""
    ok, msg = _node_check(chemin)
    if ok:
        return True, "node --check OK"
    if ok is False:
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "original.js"
            copie.write_text(Path(original).read_text(encoding="utf-8"), encoding="utf-8")
            ok0, msg0 = _node_check(copie)
        if ok0 is False and _premiere_erreur(msg) == _premiere_erreur(msg0):
            return True, "node --check refuse une syntaxe déjà présente dans l'original : aucune erreur nouvelle"
        return False, msg[:400]
    t = chemin.read_text(encoding="utf-8")
    ok2 = t.count("{") == t.count("}") and t.count("(") == t.count(")")
    return ok2, "accolades/parenthèses équilibrées (node absent)" if ok2 else "accolades/parenthèses déséquilibrées"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--py", default=str(APP_PY))
    ap.add_argument("--js", default=str(APP_JS))
    a = ap.parse_args()
    py, js = Path(a.py), Path(a.js)
    for p in (py, js):
        if not p.exists():
            print(f"✗ Introuvable : {p} (lancer depuis la racine du vault)")
            return 2
    t_py = py.read_text(encoding="utf-8")
    t_js = js.read_text(encoding="utf-8")
    if "function armer2(" not in t_js:
        print("✗ Prérequis U3az absent (armer2 introuvable dans app.js) : appliquer d'abord U3az.")
        return 1
    if MARQUEUR in t_py or MARQUEUR in t_js:
        print(f"✗ {MARQUEUR} déjà appliqué — refus d'un second passage.")
        return 1

    # --- app.py : routes mortes
    if t_py.count(PY_DEBUT) != 1 or t_py.count(PY_FIN) != 1:
        print("✗ app.py : repères des routes d'édition introuvables ou ambigus — rien écrit.")
        return 1
    d, f = t_py.index(PY_DEBUT), t_py.index(PY_FIN)
    morceau = t_py[d:f]
    routes = [l for l in morceau.splitlines() if l.startswith("@app.route")]
    defs = [l for l in morceau.splitlines() if l.startswith("def ")]
    if (f <= d or routes != ['@app.route("/api/edition/articles", methods=["GET"])',
                              '@app.route("/api/edition/injecter_evenement", methods=["POST"])']
            or defs != ["def edition_articles():", "def edition_injecter_evenement():"]):
        print("✗ app.py : le bloc à retirer ne contient pas exactement les deux routes attendues — rien écrit.")
        return 1
    n_py = t_py[:d] + PY_NOUVEAU + t_py[f:]
    print(f"  ✓ app.py : 2 routes mortes retirées ({morceau.count(chr(10))} lignes)")

    # --- app.js : commentaire périmé
    n_js = t_js
    if n_js.count(JS_COMM_DEBUT) != 1 or n_js.count(JS_COMM_FIN) != 1:
        print("✗ app.js : repères du commentaire « Promouvoir » introuvables ou ambigus — rien écrit.")
        return 1
    d, f = n_js.index(JS_COMM_DEBUT), n_js.index(JS_COMM_FIN)
    if f <= d or any(l.strip() and not l.startswith("//") for l in n_js[d:f].splitlines()):
        print("✗ app.js : le bloc « Promouvoir » n'est pas un simple commentaire — rien écrit.")
        return 1
    n_js = n_js[:d] + JS_COMM_NOUVEAU + n_js[f:]
    print("  ✓ app.js : commentaire périmé « Promouvoir » remplacé")

    # --- app.js : confirm() -> armer2
    for libelle, ancre, rempl in JS_REMPL:
        n = n_js.count(ancre)
        if n != 1:
            print(f"✗ app.js : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
            return 1
        n_js = n_js.replace(ancre, rempl, 1)
        print(f"  ✓ app.js : {libelle}")

    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, nouveau in ((py, n_py), (js, n_js)):
        bak = chemin.with_name(chemin.name + ".bak_u3bf")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(nouveau, encoding="utf-8")

    def restaurer():
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)

    try:
        py_compile.compile(str(py), doraise=True)
    except py_compile.PyCompileError as e:
        restaurer()
        print(f"✗ py_compile a échoué, fichiers restaurés : {e}")
        return 1
    ok, msg = verifier_js(js, baks[1][1])
    if not ok:
        restaurer()
        print(f"✗ Contrôle de syntaxe app.js échoué, fichiers restaurés : {msg}")
        return 1
    print(f"  (app.js : {msg})")
    for chemin, bak in baks:
        print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})")
    print("\nÀ faire : redémarrer Flask ; Cmd+Maj+R dans le navigateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
