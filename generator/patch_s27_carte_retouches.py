#!/usr/bin/env python3
"""
patch_s27_carte_retouches.py -- appliquer_et_si.py : sûreté de l'écriture (19 octobre 2026)
============================================================================================
Tiré de l'essai Écosse (branche jetable, 19 oct) :
  1. Sauvegardes .bak_appliquer refaites à CHAQUE écriture (contenu juste avant) : avant,
     seule la première était gardée, et une sauvegarde du 26 septembre « protégeait »
     encore la géographie le 19 octobre. Une opération déjà faite n'écrit rien : relancer
     ne remplace donc pas la sauvegarde par un état déjà modifié.
  2. Carte : le type d'origine du territoire est gardé (Écosse : region_administrative,
     pas « pays » comme l'écrit la Carte par défaut).
  3. Aperçu : « Fichiers modifiés » annonce aussi les fichiers de la carte.

Tout ou rien, sauvegarde .bak_carte_retouches, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_carte_retouches.py            (aperçu)
    python3 generator/patch_s27_carte_retouches.py --apply
"""
import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_S27_CARTE_RETOUCHES"
CHEMIN = Path.cwd() / "generator" / "appliquer_et_si.py"

REMPLACEMENTS = [
    (
        '''Sauvegardes : <fichier>.bak_appliquer (une seule, la première).''',
        '''Sauvegardes : <fichier>.bak_appliquer, refaite à chaque écriture (contenu juste avant).''',
    ),
    (
        '''            bak = p.with_name(p.name + ".bak_appliquer")
            if not bak.exists():
                shutil.copy2(p, bak)
            p.write_text(self.textes[p], encoding="utf-8")''',
        '''            # PATCH_S27_CARTE_RETOUCHES : sauvegarde refaite à chaque écriture (une opération
            # déjà faite n'écrit rien, relancer ne l'écrase donc pas par un état modifié).
            shutil.copy2(p, p.with_name(p.name + ".bak_appliquer"))
            p.write_text(self.textes[p], encoding="utf-8")''',
    ),
    (
        '''    for p in avant:
        bak = p.with_name(p.name + ".bak_appliquer")
        if not bak.exists():
            shutil.copy2(p, bak)
    msgs = []''',
        '''    for p in avant:   # PATCH_S27_CARTE_RETOUCHES : sauvegarde neuve à chaque application
        shutil.copy2(p, p.with_name(p.name + ".bak_appliquer"))
    msgs = []''',
    ),
    (
        '''    hautes = [s for s in simples if by[s].get("parent") not in simples]   # le sous-arbre suit
    if o["action"] == "nouvelle_zone":''',
        '''    hautes = [s for s in simples if by[s].get("parent") not in simples]   # le sous-arbre suit
    # PATCH_S27_CARTE_RETOUCHES : type d'origine du territoire (la Carte écrit « pays » par défaut).
    types = [x.get("type_entite") for z in by.values() for x in z.get("origine_reelle") or []
             if isinstance(x, dict) and plie(x.get("entite")) == plie(pays) and x.get("type_entite")]
    type_orig = types[0] if types else None
    if o["action"] == "nouvelle_zone":''',
    ),
    (
        '''    if gardees:
        gf = repo._load_geo(sc)
        for z in gf.zones:
            if z.get("slug") in gardees:
                z["origine_reelle"] = gardees[z["slug"]]
        repo._save_geo(gf)
        for s in hautes:''',
        '''    type_garde = False
    if gardees or (type_orig and type_orig != "pays"):
        gf = repo._load_geo(sc)
        for z in gf.zones:
            if z.get("slug") in gardees:
                z["origine_reelle"] = gardees[z["slug"]]
            if z.get("slug") == cible and type_orig and type_orig != "pays":
                for x in z.get("origine_reelle") or []:
                    if isinstance(x, dict) and x.get("entite") == pays and x.get("type_entite") != type_orig:
                        x["type_entite"], type_garde = type_orig, True
        if gardees or type_garde:
            repo._save_geo(gf)
        for s in hautes:''',
    ),
    (
        '''    return (f"✓ {o['n']}. {o['texte']}"
            + (f" ; {len(hautes)} sous-zone(s) rattachée(s) : {', '.join(hautes)}" if hautes else ""))''',
        '''    return (f"✓ {o['n']}. {o['texte']}"
            + (f" ; {len(hautes)} sous-zone(s) rattachée(s) : {', '.join(hautes)}" if hautes else "")
            + (f" ; type {type_orig} gardé" if type_garde else ""))''',
    ),
    (
        '''    changes = W.changes()
    print(f"\\nFichiers modifiés : {len(changes)}")''',
        '''    changes = W.changes()
    print(f"\\nFichiers modifiés : {len(changes)}")
    sc_carte = sorted({o["sc"] for o in ops if o["retenue"] and o["genre"] == "carte"})
    if sc_carte:   # PATCH_S27_CARTE_RETOUCHES
        print("  + carte, écrite après les autres : "
              + ", ".join(f"geographie/{sc}.md" for sc in sc_carte) + ", gui/zones_pays.json")''',
    ),
]


def main():
    apply = "--apply" in sys.argv
    if not CHEMIN.exists():
        sys.exit("✗ generator/appliquer_et_si.py introuvable (lancer depuis la racine du coffre). Rien fait.")
    texte = CHEMIN.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit("✗ patch déjà appliqué : rien fait.")
    if "PATCH_S27_CARTE" not in texte:
        sys.exit("✗ appliquer d'abord patch_s27_carte.py : rien fait.")
    for n, (ancien, neuf) in enumerate(REMPLACEMENTS, 1):
        if texte.count(ancien) != 1:
            sys.exit(f"✗ repère n°{n} trouvé {texte.count(ancien)} fois (attendu 1) : rien fait.")
        texte = texte.replace(ancien, neuf)
    try:
        compile(texte, str(CHEMIN), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ erreur de syntaxe après patch ({e}) : rien fait.")
    print(f"  ✓ generator/appliquer_et_si.py : {len(REMPLACEMENTS)} remplacement(s) prêt(s)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CHEMIN, CHEMIN.with_name("appliquer_et_si.py.bak_carte_retouches"))
    CHEMIN.write_text(texte, encoding="utf-8")
    print("\n✓ Fait (sauvegarde appliquer_et_si.py.bak_carte_retouches).")


if __name__ == "__main__":
    main()
