#!/usr/bin/env python3
"""
patch_u3ba_localisation_apres_injection.py — Ourrassol 2098 (14 novembre 2026)

Constat (injection de « Territoire Autonome de Karachi-BioSyn ») : l'extraction de
localisation avait échoué sur une instance (« Erreurs : 1 ») ; le cycle post-injection
ne la relance pas et le résumé final disait seulement « ✓ entité injectée ».

et_si_injecter.py (injection d'une ENTITÉ) :
  - si le journal du cycle post-injection contient « Erreurs : N » (N > 0) pour
    l'extraction de localisation, relance UNE fois extract_localisation.py (qui ne
    traite que les fiches encore sans localisation) ;
  - si des erreurs subsistent, ou si la relance échoue, le résumé final affiche une ligne ⚠
    avec la marche à suivre. Sinon : « ✓ localisation complétée ».
Les événements et signaux sont inchangés. Prérequis : U3am.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3ba_localisation_apres_injection.py            # aperçu
    python3 generator/patch_u3ba_localisation_apres_injection.py --apply
Sauvegarde .bak_u3ba ; refuse un second passage ; py_compile avec restauration.
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

MARQUEUR = "U3ba"
CIBLE = Path("generator/et_si_injecter.py")

REMPL = [
    (
        "fonction de relance",
        "def _injecter_entite(hid, a):\n",
        '''def _relancer_localisation_u3ba(sortie):
    """U3ba : si l'extraction de localisation du cycle post-injection a signalé des
    erreurs, une seule nouvelle tentative ; puis un message clair."""
    import re
    m = re.search(r"Erreurs\\s*:\\s*(\\d+)", sortie or "")
    if not m or int(m.group(1)) == 0:
        return
    print(f"\\n⚠ localisation : {m.group(1)} fiche(s) sans zone après l'extraction automatique — "
          f"nouvelle tentative…")
    try:
        r = subprocess.run([sys.executable, str(GEN / "extract_localisation.py")], cwd=GEN,
                           capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"⚠ localisation : relance impossible ({e}) — lancer « python3 generator/extract_localisation.py » "
              f"à la main.")
        return
    m2 = re.search(r"Erreurs\\s*:\\s*(\\d+)", r.stdout or "")
    if r.returncode == 0 and m2 and int(m2.group(1)) == 0:
        print("✓ localisation complétée à la deuxième tentative.")
    else:
        print("⚠ localisation : il reste des fiches sans zone — lancer « python3 generator/extract_localisation.py » "
              "(voir documentation/need_action/localisation_review.md).")


def _injecter_entite(hid, a):
''',
    ),
    (
        "appel après injection",
        '    st_i = res.get("instance_stats") or {}\n',
        '    _relancer_localisation_u3ba(sortie)   # U3ba\n    st_i = res.get("instance_stats") or {}\n',
    ),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--file", default=str(CIBLE))
    a = ap.parse_args()
    chemin = Path(a.file)
    if not chemin.exists():
        print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
        return 2
    t = chemin.read_text(encoding="utf-8")
    if "U3am" not in t:
        print("✗ Prérequis U3am absent de et_si_injecter.py.")
        return 1
    if MARQUEUR in t:
        print(f"✗ {MARQUEUR} déjà appliqué — refus d'un second passage.")
        return 1
    nouveau = t
    for libelle, ancre, rempl in REMPL:
        n = nouveau.count(ancre)
        if n != 1:
            print(f"✗ {chemin.name} : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
            return 1
        nouveau = nouveau.replace(ancre, rempl, 1)
        print(f"  ✓ {chemin.name} : {libelle}")
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    bak = chemin.with_name(chemin.name + ".bak_u3ba")
    shutil.copy2(chemin, bak)
    chemin.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(chemin), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, chemin)
        print(f"✗ py_compile a échoué, fichier restauré : {e}")
        return 1
    print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})\n\nAucun redémarrage nécessaire (script relancé à chaque appel).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
