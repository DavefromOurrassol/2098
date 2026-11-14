#!/usr/bin/env python3
"""
patch_u3ab_titres_article.py — Ourrassol 2098 (14 novembre 2026)
Suite de U3aa. Pour un événement d'article, `nom` et `evenement_cle` restent écrits par l'IA et
dérivent (test du 14 nov. : « File d'attente silencieuse au quai Wilson réaménagé »). Contrôle
mécanique, sans IA supplémentaire : tout mot de 4 lettres ou plus de `nom` / `evenement_cle`
absent de la description de l'hypothèse (comparaison sur les 5 premières lettres) est signalé :
  - aux essais 1 et 2 : compté comme problème de validation -> l'IA reformule avec les mots de la
    description (la réécriture existante) ;
  - au dernier essai : simple ⚠, la fiche n'est jamais bloquée pour cela.
Sans passage d'article retrouvé, rien ne change. Nécessite U3aa déjà appliqué.

Usage (racine du vault) :
    python3 generator/patch_u3ab_titres_article.py            # dry-run
    python3 generator/patch_u3ab_titres_article.py --apply    # écrit (.bak_u3ab)
"""
import argparse, py_compile, shutil, sys, tempfile
from pathlib import Path

CIBLE = Path("generator/inject_custom_events.py")

BLOC = r'''# U3ab (14 novembre 2026) -- nom / evenement_cle d'un événement d'article : mots de l'hypothèse.
def _mots_titres_u3ab(instance_data, idea, scenario):
    """Mots (4 lettres ou plus) de nom / evenement_cle absents de la description de l'hypothèse.
    Liste de « champ : mot » ; vide sans article retrouvé ou sans description."""
    if not _DERNIER_ARTICLE_U3S.get(scenario):
        return []
    desc = _norm_ctx_u3s(idea.get("description"))
    if not desc:
        return []
    racines = {w[:5] for w in desc.split() if len(w) >= 4}
    out = []
    for champ in ("nom", "evenement_cle"):
        for w in _norm_ctx_u3s(instance_data.get(champ)).split():
            if len(w) >= 4 and not w.isdigit() and w[:5] not in racines and f"{champ} : {w}" not in out:
                out.append(f"{champ} : {w}")
    return out


def _issues_titres_u3ab(instance_data, idea, scenario):
    mots = _mots_titres_u3ab(instance_data, idea, scenario)
    if not mots:
        return []
    desc = " ".join(str(idea.get("description") or "").split())
    return ["'nom' et 'evenement_cle' doivent reprendre les mots de la description de l'hypothèse, "
            f"sans rien y ajouter (mots absents : {', '.join(mots)}). Description : « {desc} »"]


'''

def une_fois(texte, ancre, nouveau):
    n = texte.count(ancre)
    if n != 1:
        raise ValueError(f"ancre trouvée {n} fois (attendu 1) : {ancre[:70]!r}")
    return texte.replace(ancre, nouveau)

def appliquer(src):
    msgs = []
    src = une_fois(src, 'def process_idea(client, idea, dry_run=False):\n',
                   BLOC + 'def process_idea(client, idea, dry_run=False):\n')
    msgs.append("fonctions U3ab insérées avant process_idea")
    a = ('                issues = validate_instance(\n'
         '                    instance_data, variables, scenario, registre_text, available_actors\n'
         '                )\n')
    src = une_fois(src, a, a +
        '                if not issues and attempt < MAX_FIX_ATTEMPTS:   # U3ab\n'
        '                    issues = _issues_titres_u3ab(instance_data, idea, scenario)\n')
    msgs.append("contrôle nom / evenement_cle dans la boucle de validation")
    a = ('            for nom_abs in _noms_absents_u3aa(instance_data, scenario):   # U3aa\n'
         '                print(f"  ⚠ [{scenario}] nom propre absent de l\'article et du vault : « {nom_abs} »")\n')
    src = une_fois(src, a, a +
        '            for mot_abs in _mots_titres_u3ab(instance_data, idea, scenario):   # U3ab\n'
        '                print(f"  ⚠ [{scenario}] mot absent de la description de l\'hypothèse ({mot_abs})")\n')
    msgs.append("⚠ final si l'écart subsiste au dernier essai")
    return src, msgs

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not CIBLE.exists():
        sys.exit(f"{CIBLE} introuvable : lancer depuis la racine du vault.")
    src = CIBLE.read_text(encoding="utf-8")
    if "U3ab" in src:
        sys.exit("U3ab déjà appliqué : rien à faire.")
    if "U3aa" not in src:
        sys.exit("Abandon : appliquer d'abord patch_u3aa_fiche_depuis_article.py.")
    try:
        neuf, msgs = appliquer(src)
    except ValueError as e:
        sys.exit(f"Abandon, rien écrit : {e}")
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "inject_custom_events.py"; t.write_text(neuf, encoding="utf-8")
        try: py_compile.compile(str(t), doraise=True)
        except py_compile.PyCompileError as e: sys.exit(f"Abandon, ne compile pas : {e}")
    for m in msgs: print(" ·", m)
    if not a.apply:
        print("\nDry-run : le résultat compile, rien n'est écrit. Relancer avec --apply."); return
    sauv = CIBLE.with_name(CIBLE.name + ".bak_u3ab")
    shutil.copy2(CIBLE, sauv); CIBLE.write_text(neuf, encoding="utf-8")
    py_compile.compile(str(CIBLE), doraise=True)
    print(f"\nÉcrit : {CIBLE} (sauvegarde : {sauv.name}). py_compile OK.")

if __name__ == "__main__":
    main()
