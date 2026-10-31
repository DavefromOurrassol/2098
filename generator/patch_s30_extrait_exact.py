#!/usr/bin/env python3
"""
patch_s30_extrait_exact.py — Ourrassol 2098 (S30, 31 octobre 2026)
==================================================================

Défaut trouvé au test réel de S30 (exemple occupation_bresil_2029) : 3 phrases
« obligatoires » de la passe exhaustive étaient « introuvables mot pour mot » à
l'étape ⑤. L'IA les avait citées de mémoire, réécrites après le début :
    cité  : « …protocole d'urgence climatique et sécuritaire »
    fiche : « …protocole d'urgence écologique — une déclaration… »
Le contrôle anti-invention de et_si_exhaustif.py ne comparait que les 120
premiers caractères de l'extrait : ces citations passaient.

Correctif dans et_si_exhaustif.py (verifier_lot) :
  - l'extrait ENTIER doit se retrouver dans la fiche (espaces, casse, accents près) ;
  - sinon, la phrase de la fiche qui commence pareil et lui ressemble le plus
    remplace la citation (l'étape ⑤ peut alors la corriger), et le changement
    descend en « possible » (motif « citation inexacte… ») : il a été jugé sur
    un texte qui n'est pas celui de la fiche ;
  - aucune phrase proche : « extrait introuvable dans la fiche » (inchangé).
  - la citation de l'IA est gardée dans le résultat (`extrait_ia`).
Les réponses IA en cache sont recontrôlées à la prochaine simulation : pas de
nouvel appel pour la passe elle-même.

USAGE (depuis la racine du vault)
    python3 generator/patch_s30_extrait_exact.py            # aperçu
    python3 generator/patch_s30_extrait_exact.py --apply    # écrit (sauvegarde .bak_s30extrait)
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S30_EXTRAIT"

ANCRE_FONCTION = "def verifier_lot("
FONCTION = '''def _phrase_reelle(extrait, texte):
    """PATCH_S30_EXTRAIT : (phrase, exact). exact = True si l'extrait entier est dans la fiche
    (espaces, casse et accents près). Sinon, la phrase de la fiche qui contient les 60 premiers
    caractères de l'extrait et lui ressemble le plus (citation réécrite par l'IA) ; None si aucune."""
    import difflib
    e = _plie(extrait)
    if e and e in _plie(texte):
        return extrait, True
    phrases = [p.strip() for p in _re.split(r"(?<=[.!?])\\s+", " ".join(str(texte or "").split())) if p.strip()]
    debut = e[:60]
    candidates = [p for p in phrases if debut and debut in _plie(p)]
    if not candidates:
        return None, False
    return max(candidates, key=lambda p: difflib.SequenceMatcher(None, e, _plie(p)).ratio()), False


'''

ANCRE_CONTROLE = '''                trouve = _plie(extrait)[:120] in _plie(_texte_complet(f))
                if not trouve:
                    motifs.append("extrait introuvable dans la fiche")
'''
CONTROLE = '''                # PATCH_S30_EXTRAIT : l'extrait ENTIER doit être dans la fiche (avant : ses 120 premiers
                # caractères). Citation réécrite par l'IA : remplacée par la vraie phrase ; le jugement,
                # porté sur un texte inexact, descend en « possible ».
                extrait_ia = extrait
                reelle, exact = _phrase_reelle(extrait, _texte_complet(f))
                trouve = reelle is not None
                if not trouve:
                    motifs.append("extrait introuvable dans la fiche")
                elif not exact:
                    motifs.append("citation inexacte, remplacée par la phrase de la fiche")
                    extrait = reelle
'''

ANCRE_SORTIE = '''"extrait": extrait, "extrait_trouve": trouve,'''
SORTIE = '''"extrait": extrait, "extrait_trouve": trouve, "extrait_ia": extrait_ia,'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fichier", default=str(Path(__file__).resolve().parent / "et_si_exhaustif.py"))
    a = ap.parse_args()

    cible = Path(a.fichier)
    if not cible.exists():
        sys.exit(f"✗ {cible} introuvable")
    texte = cible.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        print(f"· déjà appliqué ({MARQUEUR} présent) : rien à faire.")
        return
    for nom, ancre in (("fonction", ANCRE_FONCTION), ("contrôle", ANCRE_CONTROLE), ("sortie", ANCRE_SORTIE)):
        n = texte.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (1 attendue) : fichier différent de celui analysé, rien écrit.")

    nouveau = (texte.replace(ANCRE_FONCTION, FONCTION + ANCRE_FONCTION)
                    .replace(ANCRE_CONTROLE, CONTROLE)
                    .replace(ANCRE_SORTIE, SORTIE))

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(nouveau)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ le fichier patché ne compile pas, rien écrit :\n{e}")
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    print(f"{'ÉCRITURE' if a.apply else 'APERÇU (rien écrit)'} — {cible.name}")
    print("  + fonction _phrase_reelle (extrait entier, sinon phrase réelle la plus proche)")
    print("  + verifier_lot : citation inexacte remplacée par la phrase de la fiche, changement en « possible »")
    print("  + résultat : champ extrait_ia (citation d'origine de l'IA)")
    print(f"  compilation : OK ({len(texte.splitlines())} → {len(nouveau.splitlines())} lignes)")
    if not a.apply:
        print("\nRelancer avec --apply pour écrire (sauvegarde .bak_s30extrait).")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_s30extrait"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"\n✓ {cible.name} patché (sauvegarde {cible.name}.bak_s30extrait)")


if __name__ == "__main__":
    main()
