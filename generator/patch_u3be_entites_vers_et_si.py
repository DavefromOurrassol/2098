#!/usr/bin/env python3
"""
patch_u3be_entites_vers_et_si.py — Ourrassol 2098 (14 novembre 2026)

Ferme les deux dernières entrées d'ENTITÉS qui contournaient « et si ? » :

 1. « Lecture IA » (étape ⑤ « À la main », panneau d'une hypothèse appliquée) : les
    « Nouvelles entités proposées par la lecture IA » n'étaient plus écrites dans
    entites_custom/queue.yaml (puis « Créer des entités », toute la file). Elles deviennent
    des HYPOTHÈSES d'entité dans hypotheses.yaml, avec les contrôles habituels (doublons
    d'entités, catégorie, id unique) et SANS appel IA (rôle et raison repris tels quels).
    Le suivi par entité garde « en hypothèse » tant que l'hypothèse existe ; si elle est
    supprimée, l'entité peut être reproposée. La suite : onglet « Et si ? » (Vérifier,
    Adopter, Injecter, ou 📦 lot). Le bouton devient « Créer les hypothèses « et si ? » »
    et n'a plus de confirm() (bloqué dans ton navigateur) : l'aperçu sert de garde-fou.
 2. Onglet Articles, « ✨ Envoyer vers « et si ? » » : nouveau choix « comme entité ».
    Tu écris le nom de l'entité et ce que l'article en dit ; l'IA n'invente rien d'autre
    (scénario de l'article et source ajoutés). Pas de détection d'événement, pas de date.

  generator/et_si_main.py : statut_entite / ajouter_entites réécrits (U3be) ;
  gui/static/app.js       : bouton du panneau ⑤ ; choix « comme entité » dans Articles.
Prérequis : U3ak (doublons d'entités) et U3b (Articles → « et si ? »).
Après application : redémarrer Flask ; Cmd+Maj+R.

    python3 generator/patch_u3be_entites_vers_et_si.py            # aperçu
    python3 generator/patch_u3be_entites_vers_et_si.py --apply
Sauvegardes .bak_u3be ; refuse un second passage ; contrôles de syntaxe avec restauration.
"""
import argparse
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3be"
MAIN_PY = Path("generator/et_si_main.py")
HYP_PY = Path("generator/hypothese_depuis_texte.py")
APP_JS = Path("gui/static/app.js")

DEBUT_PY = "def statut_entite("
FIN_PY = "# ---------------------------------------------------------------------------\n# 2. Règle de lore"
BLOC_PY = 'def _hyp():\n    """hypothese_depuis_texte (contrôles, doublons, ajout à hypotheses.yaml), chargé à la demande. U3be."""\n    import hypothese_depuis_texte as h\n    return h\n\n\ndef statut_entite(e, suivi, m, file_noms, existants, ids_hyp=None):\n    if m.slugify(e["nom"]) in existants:\n        return "créée", "l\'entité existe déjà dans le vault"\n    s = suivi["entites"].get(e["cle"]) or {}\n    hid_h = s.get("hypothese")   # U3be : l\'entité est devenue une hypothèse « et si ? »\n    if hid_h:\n        if ids_hyp is None:\n            ids_hyp = set(_hyp().ids_existants())\n        if hid_h in ids_hyp:\n            return "en hypothèse", (f"hypothèse {hid_h} ajoutée le {s.get(\'date\', \'?\')} : suite dans l\'onglet "\n                                    "« Et si ? » (mode Simuler : Vérifier, Adopter, Injecter)")\n        return "proposée", ""   # l\'hypothèse a été supprimée depuis : l\'entité peut être reproposée\n    if e["nom"].lower() in file_noms:\n        return "dans la file", "déjà dans entites_custom/queue.yaml (ancien chemin) : lancer « Créer des entités »"\n    if e["cle"] in suivi["entites"]:\n        return "traitée", "ajoutée à la file puis retirée (créée ou rejetée : voir processed / needs_review)"\n    return "proposée", ""\n\n\ndef _phrase(texte):\n    t = " ".join(str(texte or "").split())\n    return t if not t or t[-1] in ".!?…" else t + "."\n\n\ndef bloc_hypothese(e, category, id_):\n    """U3be : entité proposée par la lecture IA -> bloc d\'hypothèse `type: entite`.\n    Aucun appel IA : rien n\'est ajouté à ce que la lecture a déjà dit (rôle, raison)."""\n    desc = " ".join(x for x in (_phrase(e["role"]), _phrase(e["raison"])) if x)\n    h = {"id": id_, "nom": e["nom"], "type": "entite"}\n    if desc:\n        h["description"] = desc\n    h["categorie"] = category\n    h["scenario_ref"] = e["sc"]\n    if e["role"]:\n        h["role"] = e["role"]\n    h["scenarios"] = [e["sc"]]\n    return _hyp().bloc_yaml(h)\n\n\ndef ajouter_entites(hid, data, choix, apply):\n    """U3be : les entités choisies deviennent des hypothèses « et si ? » (type entité) dans\n    hypotheses.yaml, avec les contrôles habituels (doublons d\'entités, catégorie, id unique).\n    N\'écrit plus dans entites_custom/queue.yaml."""\n    m = cei()\n    hy = _hyp()\n    suivi = lire_suivi(hid)\n    proposees = {e["cle"]: e for e in entites_proposees(data)}\n    file = m.load_yaml_list(m.QUEUE_PATH)\n    file_noms = {str(x.get("nom") or "").strip().lower() for x in file if isinstance(x, dict)}\n    existants = {str(x.get("slug") or "") for x in m.load_entities_list() if isinstance(x, dict)}\n    ids_hyp = set(hy.ids_existants())\n    pris = set(ids_hyp)\n    noms_lot = set()\n    nouvelles, erreurs, avert = [], [], []\n    for c in choix:\n        e = proposees.get(str(c.get("cle")))\n        cat = str(c.get("category") or "").strip()\n        if not e:\n            erreurs.append(f"{c.get(\'cle\')} : entité proposée inconnue")\n            continue\n        if cat not in m.VALID_CATEGORIES:\n            erreurs.append(f"{e[\'nom\']} : catégorie {cat or \'(vide)\'} invalide "\n                           f"({\', \'.join(m.VALID_CATEGORIES)})")\n            continue\n        st, detail = statut_entite(e, suivi, m, file_noms, existants, ids_hyp)\n        if st in ("créée", "dans la file", "en hypothèse"):\n            erreurs.append(f"{e[\'nom\']} : {detail}")\n            continue\n        if e["nom"].lower() in noms_lot:\n            erreurs.append(f"{e[\'nom\']} : cochée deux fois")\n            continue\n        noms_lot.add(e["nom"].lower())\n        base = hy.slugifier(e["nom"]) or "entite"\n        id_, n = base, 2\n        while id_ in pris:\n            id_ = f"{base}_{n}"\n            n += 1\n        pris.add(id_)\n        bloc = bloc_hypothese(e, cat, id_)\n        v = hy.verifier_bloc(bloc, pour_ajout=True)\n        for x in v["erreurs"]:\n            erreurs.append(f"{e[\'nom\']} : {x}")\n        for x in v["avertissements"]:\n            avert.append(f"{e[\'nom\']} : {x}")\n        if v["ok"]:\n            nouvelles.append((e, cat, id_, bloc))\n    print(("ÉCRITURE" if apply else "APERÇU (rien écrit)") + f" — entités de {hid} → hypothèses « et si ? »\\n")\n    for e, cat, id_, _ in nouvelles:\n        print(f"  + {e[\'nom\']} ({cat}) — {e[\'sc\']} → hypothèse {id_}")\n    for x in avert:\n        print(f"  ⚠ {x}")\n    for x in erreurs:\n        print(f"  ✗ {x}")\n    if not nouvelles:\n        print("\\nRien à ajouter.")\n        return 1 if erreurs else 0\n    if erreurs:\n        print("\\n✗ Rien n\'est écrit tant qu\'un choix est refusé : corriger ou décocher les lignes ✗.")\n        return 1\n    if not apply:\n        print(f"\\n{len(nouvelles)} hypothèse(s) prête(s) pour {hy.se.HYPOTHESES_PATH.name}. Relancer avec --apply.")\n        return 0\n    faites = []\n    for e, cat, id_, bloc in nouvelles:\n        r = hy.ajouter_bloc(bloc)\n        if not r.get("ok"):\n            print(f"  ✗ {e[\'nom\']} : " + " ; ".join(r.get("erreurs") or ["ajout refusé"]))\n            continue\n        faites.append((e, cat, id_))\n        suivi["entites"][e["cle"]] = {"date": maintenant(), "nom": e["nom"], "category": cat,\n                                      "hypothese": id_}\n        ecrire_suivi(hid, suivi)\n    print(f"\\n✓ {len(faites)} hypothèse(s) d\'entité ajoutée(s) à {hy.se.HYPOTHESES_PATH.name} "\n          f"(sauvegarde {hy.se.HYPOTHESES_PATH.name}.bak_ajout).")\n    if faites:\n        print("  Suite : onglet « Et si ? », mode Simuler : choisir l\'hypothèse, puis Vérifier, Adopter, Injecter "\n              "(ou « Traiter en lot » pour plusieurs entités).")\n    return 0 if len(faites) == len(nouvelles) else 1\n\n\n'

JS_ENTITE_UI = r"""
  // U3be : « comme entité » -- on écrit le nom et ce que l'article en dit ; l'IA n'ajoute rien.
  const zoneEntite = mk('div', '', 'display:none;margin-bottom:8px;font-size:11px');
  zoneEntite.appendChild(mk('div',
    "Entité à créer : son nom, puis ce que l'article en dit (rien de plus : l'IA ne doit rien inventer).",
    'margin-bottom:4px'));
  const champEntite = mk('textarea', '', 'width:100%;min-height:60px');
  champEntite.placeholder = "Ex. : Le Consortium des Eaux du Rhône, cité dans l'article comme gestionnaire du barrage de Génissiat.";
  zoneEntite.appendChild(champEntite);
  boite.insertBefore(zoneEntite, zoneDetect);
  const texteEntite = () => [
    champEntite.value.trim(),
    `Située dans le scénario ${article.scenario}.`,
    `Source : article ${article.fichier}.`,
  ].filter(Boolean).join(' ');
  const appliquerEntite = () => {
    const ent = selType.value === 'entite';
    zoneEntite.style.display = ent ? '' : 'none';
    if (ent) zoneDetect.style.display = 'none';
    reglages.style.display = ent ? 'none' : '';
  };
  selType.addEventListener('change', appliquerEntite);
  appliquerEntite();
"""

# (libellé, ancre, remplacement)
JS_REMPL = [
    ("panneau ⑤ : libellé du bouton",
     "const bE = bouton('Ajouter à la file', 'yaml-btn yaml-btn-save');",
     "const bE = bouton('Créer les hypothèses « et si ? »', 'yaml-btn yaml-btn-save');   // U3be"),
    ("panneau ⑤ : plus de confirm()",
     "        if (!confirm(`Ajouter ${c.length} entité(s) à entites_custom/queue.yaml ?`)) return;\n",
     "        // U3be : pas de confirm() (bloqué dans certains navigateurs) ; l'aperçu fait garde-fou\n"),
    ("panneau ⑤ : texte d'aide",
     "'Entités : coche celles à garder et choisis leur catégorie ; l\\'aperçu montre les entrées, « Ajouter » les ' +\n"
     "      'écrit dans entites_custom/queue.yaml (sauvegarde .bak_et_si_main, refus si l\\'entité existe déjà ou est ' +\n"
     "      'déjà dans la file). La création reste « Créer des entités » (appels IA, traite toute la file).\\n' +",
     "'Entités : coche celles à garder et choisis leur catégorie ; l\\'aperçu montre les hypothèses, « Créer les ' +\n"
     "      'hypothèses » les ajoute à hypotheses.yaml (contrôle des doublons, sans appel IA). La suite se fait dans ' +\n"
     "      'l\\'onglet « Et si ? » (Vérifier, Adopter, Injecter).\\n' +   // U3be"),
    ("panneau ⑤ : indication de sortie",
     "'main/entites': '« Ajouter à la file »',",
     "'main/entites': '« Créer les hypothèses »',   // U3be\n                     "),
    ("Articles : choix « comme entité »",
     "[['evenement', 'comme événement'], ['signal', 'comme signal faible']].forEach(([v, l]) => {",
     "[['evenement', 'comme événement'], ['signal', 'comme signal faible'], ['entite', 'comme entité']].forEach(([v, l]) => {   // U3be"),
    ("Articles : zone de saisie de l'entité",
     "  selType.addEventListener('change', appliquerVerrou);\n  cbForcer.addEventListener('change', appliquerVerrou);\n  appliquerVerrou();\n",
     "  selType.addEventListener('change', appliquerVerrou);\n  cbForcer.addEventListener('change', appliquerVerrou);\n  appliquerVerrou();\n" + "__UI__"),
    ("Articles : nom de l'entité obligatoire",
     "    if (selType.value !== 'signal' && !evChoisi) {   // U3f\n",
     "    if (selType.value === 'entite' && !champEntite.value.trim()) {   // U3be\n"
     "      etat.style.color = '#b03a2e';\n"
     "      etat.textContent = \"✗ Écris le nom de l'entité et ce que l'article en dit.\";\n"
     "      return;\n"
     "    }\n"
     "    if (selType.value === 'evenement' && !evChoisi) {   // U3f\n"),
    ("Articles : doublon d'événement seulement pour un événement",
     "    if (selType.value !== 'signal' && evChoisi && evChoisi.deja_connu && !cbDoublon.checked) {   // U3o\n",
     "    if (selType.value === 'evenement' && evChoisi && evChoisi.deja_connu && !cbDoublon.checked) {   // U3o\n"),
    ("Articles : appel Proposer pour une entité",
     "    const data = await appeler('proposer',\n"
     "      (selType.value !== 'signal' && evChoisi) ? texteEvenement(evChoisi) : texte,   // U3f\n"
     "      selType.value, extra);\n",
     "    const data = (selType.value === 'entite')   // U3be\n"
     "      ? await appeler('proposer', texteEntite(), 'entite', {})\n"
     "      : await appeler('proposer',\n"
     "          (selType.value !== 'signal' && evChoisi) ? texteEvenement(evChoisi) : texte,   // U3f\n"
     "          selType.value, extra);\n"),
]
JS_REMPL = [(a, b, c.replace("__UI__", JS_ENTITE_UI)) for a, b, c in JS_REMPL]


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
    ap.add_argument("--main", default=str(MAIN_PY))
    ap.add_argument("--hyp", default=str(HYP_PY))
    ap.add_argument("--js", default=str(APP_JS))
    a = ap.parse_args()
    py, hyp, js = Path(a.main), Path(a.hyp), Path(a.js)
    for p in (py, hyp, js):
        if not p.exists():
            print(f"✗ Introuvable : {p} (lancer depuis la racine du vault)")
            return 2
    t_py = py.read_text(encoding="utf-8")
    t_js = js.read_text(encoding="utf-8")
    if "U3ak" not in hyp.read_text(encoding="utf-8"):
        print("✗ Prérequis U3ak absent de hypothese_depuis_texte.py (doublons d'entités).")
        return 1
    if "U3b" not in t_js or "renderArticlesVersEtSi" not in t_js:
        print("✗ Prérequis U3b absent de app.js (Articles → « et si ? »).")
        return 1
    if MARQUEUR in t_py or MARQUEUR in t_js:
        print(f"✗ {MARQUEUR} déjà appliqué — refus d'un second passage.")
        return 1
    if t_py.count(DEBUT_PY) != 1 or t_py.count(FIN_PY) != 1 or t_py.index(DEBUT_PY) > t_py.index(FIN_PY):
        print("✗ et_si_main.py : repères du bloc « entités » introuvables ou ambigus — rien écrit.")
        return 1
    n_py = t_py[:t_py.index(DEBUT_PY)] + BLOC_PY + t_py[t_py.index(FIN_PY):]
    print("  ✓ et_si_main.py : statut_entite / ajouter_entites réécrits")
    n_js = t_js
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
        bak = chemin.with_name(chemin.name + ".bak_u3be")
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
