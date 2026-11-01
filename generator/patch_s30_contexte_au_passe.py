#!/usr/bin/env python3
"""patch_s30_contexte_au_passe.py — Ourrassol 2098, 1er novembre 2026

Défaut trouvé au test réel de S30 (chute_holdfast_2072, branche test-s30b) :
les deux appelants de fiche_au_passe.py passent comme --contexte
« <data.get('nom') or id> (<année>) » — l'étape ④ (appliquer_et_si.py, l. 1070)
et l'étape ⑤ (et_si_main.py, au_passe()). Le JSON d'application n'a pas de clé
`nom` : l'IA recevait « CE QUI S'EST PASSÉ : chute_holdfast_2072 (2072.0) »,
sans description, et inventait la fin (« chute de la dernière citadelle »,
« ruines oubliées » au lieu de « saisies, devenues sites publics »).

Correctif, dans fiche_au_passe.py seul (les deux appelants en profitent) :
si le contexte désigne une hypothèse de et_si/hypotheses.yaml (par id ou par
nom, suffixe « (année) » ignoré), il est remplacé par son nom, sa date, sa
description et ses contraintes (faits imposés). Un contexte libre
(« explosion du Polaris-7 (2081) ») reste inchangé.

Usage (depuis la racine du vault) :
    python3 generator/patch_s30_contexte_au_passe.py
Idempotent (marqueur PATCH_S30_CONTEXTE_AU_PASSE) ; sauvegarde
fiche_au_passe.py.bak_s30contexte ; contrôle de compilation, restauration si échec.
"""
import py_compile
import shutil
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parent
CIBLE = GEN / "fiche_au_passe.py"
MARQUEUR = "PATCH_S30_CONTEXTE_AU_PASSE"

ANCRE_DEF = "def apercu(slug, contexte):"
ANCRE_USER = "    user = (f\"FICHE : « {fm.get('name') or slug} »"

FONCTION = '''# PATCH_S30_CONTEXTE_AU_PASSE (1er nov 2026) : les appelants (étape ④ appliquer_et_si.py,
# étape ⑤ et_si_main.py) passent « <nom ou id> (<année>) » sans description : l'IA inventait
# la fin. Si le contexte désigne une hypothèse de et_si/hypotheses.yaml (id ou nom), il est
# remplacé par son nom, sa date, sa description et ses faits imposés.
def _contexte_hypothese(contexte):
    if not contexte:
        return contexte
    cle = re.sub(r"\\s*\\([^()]*\\)\\s*$", "", contexte).strip()
    try:
        brut = (VAULT / "et_si" / "hypotheses.yaml").read_text(encoding="utf-8")
        hyps = (yaml.safe_load(brut) or {}).get("hypotheses") or []
    except (OSError, yaml.YAMLError, AttributeError):
        return contexte
    for h in hyps:
        if not isinstance(h, dict):
            continue
        if cle not in (str(h.get("id") or ""), str(h.get("nom") or "").strip()):
            continue
        texte = f"{h.get('nom') or h.get('id')} ({h.get('date')})"
        if h.get("description"):
            texte += " : " + " ".join(str(h["description"]).split())
        faits = [" ".join(str(c).split()) for c in (h.get("contraintes") or []) if c]
        if faits:
            texte += ("\\nFAITS IMPOSÉS (à respecter, ne pas contredire) :\\n"
                      + "\\n".join(f"- {c}" for c in faits))
        print(f"  [contexte] hypothèse `{h.get('id')}` : description et {len(faits)} fait(s) imposé(s) transmis")
        return texte
    return contexte


'''

APPEL = "    contexte = _contexte_hypothese(contexte)  # PATCH_S30_CONTEXTE_AU_PASSE\n"


def main():
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable — lancer depuis la racine du vault.")
    src = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in src:
        print("· déjà appliqué — rien fait.")
        return
    for ancre in (ANCRE_DEF, ANCRE_USER):
        n = src.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre trouvée {n} fois (attendu 1) : {ancre!r} — rien fait.")
    for mod in ("import re", "import yaml"):
        if mod not in src:
            sys.exit(f"✗ « {mod} » absent de fiche_au_passe.py — rien fait.")

    nouveau = src.replace(ANCRE_DEF, FONCTION + ANCRE_DEF, 1)
    nouveau = nouveau.replace(ANCRE_USER, APPEL + ANCRE_USER, 1)

    bak = CIBLE.with_name(CIBLE.name + ".bak_s30contexte")
    shutil.copy2(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(CIBLE), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, CIBLE)
        sys.exit(f"✗ compilation échouée, fichier restauré : {e}")
    print(f"✓ {CIBLE.name} patché (sauvegarde {bak.name})")
    print("  Test : python3 generator/fiche_au_passe.py --slug holdfast_reference "
          "--contexte \"chute_holdfast_2072 (2072.0)\"")


if __name__ == "__main__":
    main()
