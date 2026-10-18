#!/usr/bin/env python3
"""
patch_s27_categories.py -- catégorie des nouvelles entités proposée (18 octobre 2026)
=====================================================================================
  generator/simuler_et_si.py  (v8.21) la lecture IA donne aussi la catégorie de chaque
        nouvelle entité (liste de entites_custom/queue.yaml), contrôlée ; rapport et
        bloc YAML l'affichent (« <à choisir> » seulement si absente ou invalide).
        Le cache des lectures n'est pas invalidé : une ancienne lecture reste sans
        catégorie (et_si_main.py la devine alors d'après le nom).
  generator/appliquer_et_si.py  la check-list reprend la catégorie si elle existe.
  gui/static/app.js  étape ⑤ : catégorie pré-choisie et case cochée, avec sa source
        (« proposée par l'IA » ou « devinée d'après le nom ») ; tout reste modifiable.

À placer avec la nouvelle version de generator/et_si_main.py (catégorie devinée).
Tout ou rien, sauvegardes .bak_categories, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_categories.py            (aperçu)
    python3 generator/patch_s27_categories.py --apply
Puis redémarrer le GUI.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_CATEGORIES"
VAULT = Path.cwd()
R = {}

R["generator/simuler_et_si.py"] = [
    ('VERSION = "v8.20"', 'VERSION = "v8.21"'),
    (
        '''PLAFONDS = {"trajectoires": 8, "alliances": 6, "geographie": 4, "zones_statut": 4, "nouvelles_entites": 3}''',
        '''PLAFONDS = {"trajectoires": 8, "alliances": 6, "geographie": 4, "zones_statut": 4, "nouvelles_entites": 3}
# PATCH_S27_CATEGORIES (v8.21) : catégories d'entité, même liste que VALID_CATEGORIES de
# create_entities_and_instances.py (entites_custom/queue.yaml) -- à garder identiques.
CATEGORIES_ENTITE = ["IA", "organisation", "entreprise", "institution", "infrastructure",
                     "réseau", "humain", "système", "hybride", "autre", "média", "territoire"]
CATEGORIES_TXT = " | ".join(CATEGORIES_ENTITE)''',
    ),
    (
        '''{PLAFONDS['nouvelles_entites']} nouvelles entités. Chaque proposition a une raison courte (une phrase).''',
        '''{PLAFONDS['nouvelles_entites']} nouvelles entités. Chaque proposition a une raison courte (une phrase).
Nouvelle entité : "category" vaut EXACTEMENT une de ces valeurs : {CATEGORIES_TXT}.''',
    ),
    (
        '''  "nouvelles_entites": [{{"nom": "...", "role": "...", "zone": "slug", "raison": "..."}}]''',
        '''  "nouvelles_entites": [{{"nom": "...", "category": "...", "role": "...", "zone": "slug", "raison": "..."}}]''',
    ),
    (
        '''        ne.append({"nom": str(n["nom"]), "role": str(n.get("role") or ""), "zone": zone,
                   "raison": str(n.get("raison") or "")})''',
        '''        # PATCH_S27_CATEGORIES : catégorie gardée si elle est dans la liste (casse et accents tolérés).
        brute = str(n.get("category") or "").strip()
        cat = next((c for c in CATEGORIES_ENTITE if _plie(c) == _plie(brute)), None)
        if brute and not cat:
            corrigees.append(f"nouvelle entité {n.get('nom')} : catégorie {brute!r} hors liste (à choisir)")
        ne.append({"nom": str(n["nom"]), "role": str(n.get("role") or ""), "zone": zone,
                   "raison": str(n.get("raison") or ""), **({"category": cat} if cat else {})})''',
    ),
    (
        '''            L.append(f"- {n['nom']}" + (f" ({n['zone']})" if n.get("zone") else "") + f" : {n['role']} — {n['raison']}")''',
        '''            L.append(f"- {n['nom']}" + (f" ({n['zone']})" if n.get("zone") else "")
                     + (f" [{n['category']}]" if n.get("category") else "") + f" : {n['role']} — {n['raison']}")''',
    ),
    (
        '''        entrees = [{"nom": ne["nom"], "category": "<à choisir>", "role": ne["role"], "etat": "émergent",''',
        '''        entrees = [{"nom": ne["nom"], "category": ne.get("category") or "<à choisir>", "role": ne["role"], "etat": "émergent",''',
    ),
]

R["generator/appliquer_et_si.py"] = [(
    '''                L += [f"- nom: {e.get('nom')}", "  category: <à choisir>", f"  role: {e.get('role')}",''',
    '''                # PATCH_S27_CATEGORIES : catégorie de la lecture IA si elle existe (v8.21).
                L += [f"- nom: {e.get('nom')}", f"  category: {e.get('category') or '<à choisir>'}",
                      f"  role: {e.get('role')}",''',
)]

R["gui/static/app.js"] = [
    (
        '''      garde.checked = libre && !!memo.garde[k];''',
        '''      // PATCH_S27_CATEGORIES : catégorie proposée (IA, ou devinée d'après le nom) = case cochée.
      garde.checked = libre && ((k in memo.garde) ? memo.garde[k] : !!e.category_proposee);''',
    ),
    (
        '''      cat.value = memo.cat[k] || '';''',
        '''      cat.value = memo.cat[k] || (libre ? (e.category_proposee || '') : '');''',
    ),
    (
        '''      ligne.appendChild(cat);
''',
        '''      ligne.appendChild(cat);
      if (libre && e.category_proposee) {
        const src = mk('span', 'option-desc', e.source_categorie === 'ia'
          ? `(${e.category_proposee} : proposée par l'IA) ` : `(${e.category_proposee} : devinée d'après le nom) `);
        ligne.appendChild(src);
      }
''',
    ),
]
PREREQUIS = {
    "generator/simuler_et_si.py": ["PATCH_S19_RETOUCHES", "def _plie("],
    "gui/static/app.js": ["PATCH_S27_GUI_MAIN"],
}
DEBUT_PANNEAU = "// PATCH_S27_GUI_PARCOURS — PANNEAU"
FIN_PANNEAU = "// PATCH_GUI_OBSIDIAN_PANNEAUX"


def controle_js(js):
    i = js.find(DEBUT_PANNEAU)
    j = js.find(FIN_PANNEAU, i)
    if i < 0 or j < 0:
        return "bornes du panneau introuvables"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js[i:j])
    try:
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True, timeout=30)
        return None if r.returncode == 0 else r.stderr.strip()
    except FileNotFoundError:
        print("  (node absent : contrôle JS sauté)")
        return None
    finally:
        Path(f.name).unlink()


def main():
    apply = "--apply" in sys.argv
    main_py = VAULT / "generator" / "et_si_main.py"
    if not main_py.exists() or "deviner_categorie" not in main_py.read_text(encoding="utf-8"):
        sys.exit("✗ placer d'abord la nouvelle version de generator/et_si_main.py (catégorie devinée). Rien fait.")
    nouveaux, erreurs = {}, []
    for nom, reps in R.items():
        chemin = VAULT / nom
        if not chemin.exists():
            erreurs.append(f"{nom} : introuvable (lancer depuis la racine du coffre)")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if MARQUEUR in texte:
            erreurs.append(f"{nom} : déjà patché ({MARQUEUR} présent)")
            continue
        for p in PREREQUIS.get(nom, []):
            if p not in texte:
                erreurs.append(f"{nom} : « {p} » absent (patch précédent non appliqué ?)")
        for n, (ancien, neuf) in enumerate(reps, 1):
            nb = texte.count(ancien)
            if nb != 1:
                erreurs.append(f"{nom} : repère n°{n} trouvé {nb} fois (attendu 1)")
                continue
            texte = texte.replace(ancien, neuf)
        if nom.endswith(".py"):
            try:
                compile(texte, str(chemin), "exec")
            except SyntaxError as e:
                erreurs.append(f"{nom} : erreur de syntaxe après patch ({e})")
        else:
            err = controle_js(texte)
            if err:
                erreurs.append(f"{nom} : JavaScript invalide après patch : {err}")
        nouveaux[nom] = texte
    if erreurs:
        print("✗ Rien n'a été écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
        sys.exit(1)
    for nom in R:
        print(f"  ✓ {nom} : {len(R[nom])} remplacement(s) prêt(s)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    for nom, texte in nouveaux.items():
        chemin = VAULT / nom
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_categories"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Catégories proposées en place (sauvegardes .bak_categories). Redémarrer le GUI.")


if __name__ == "__main__":
    main()
