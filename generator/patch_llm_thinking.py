#!/usr/bin/env python3
"""
patch_llm_thinking.py — Ourrassol 2098 (14 novembre 2026)
mistral-large-latest « réfléchit » (morceaux de type thinking) et la réflexion consomme tout
max_tokens : réponse vide -> « Expecting value: line 1 column 1 ». Correctif dans
generator/llm_client.py (_call_mistral), pour les modèles « large » :
  1. plafond d'appel = 4 x max_tokens (on ne paie que les tokens réellement produits) ;
  2. si la réponse est vide parce que le plafond est atteint : un nouvel essai à 3 x ce plafond
     (32000 au plus).
Les autres modèles et fournisseurs ne changent pas. Nécessite patch_llm_greedy déjà appliqué.

Usage (racine du vault) :
    python3 generator/patch_llm_thinking.py            # dry-run
    python3 generator/patch_llm_thinking.py --apply    # écrit (.bak_thinking)
"""
import argparse, py_compile, shutil, sys, tempfile
from pathlib import Path

CIBLE = Path("generator/llm_client.py")

A1 = '''    args_mistral = dict(
        model=model,
        max_tokens=max_tokens,
'''
N1 = '''    args_mistral = dict(
        model=model,
        max_tokens=max_tokens * 4 if "large" in str(model) else max_tokens,   # THINKING
'''
A2 = '''    return _texte_reponse(response.choices[0].message.content, model)

'''
N2 = '''    texte = _texte_reponse(response.choices[0].message.content, model)
    # THINKING (14 nov. 2026) : la réflexion du modèle a pris tout le plafond -> un nouvel essai
    if (not texte.strip() and getattr(response.choices[0], "finish_reason", None) == "length"
            and args_mistral["max_tokens"] < 32000):
        args_mistral["max_tokens"] = min(args_mistral["max_tokens"] * 3, 32000)
        print(f"[llm] {model} : réponse vide (réflexion trop longue), nouvel essai à "
              f"{args_mistral['max_tokens']} tokens")
        try:
            response = client.chat.complete(**args_mistral)
        except Exception as e:
            raise RuntimeError(f"[llm_client] Erreur API Mistral : {e}")
        usage = response.usage
        print(f"[llm] Mistral ({model}) — entrée : {usage.prompt_tokens} | sortie : {usage.completion_tokens}")
        texte = _texte_reponse(response.choices[0].message.content, model)
    return texte

'''

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not CIBLE.exists():
        sys.exit(f"{CIBLE} introuvable : lancer depuis la racine du vault.")
    src = CIBLE.read_text(encoding="utf-8")
    if "THINKING (14 nov" in src or "# THINKING" in src:
        sys.exit("Déjà appliqué : rien à faire.")
    if "GREEDY (14 nov" not in src:
        sys.exit("Abandon : appliquer d'abord patch_llm_greedy.py.")
    for ancre in (A1, A2):
        if src.count(ancre) != 1:
            sys.exit(f"Abandon, rien écrit : ancre trouvée {src.count(ancre)} fois (attendu 1) : {ancre[:60]!r}")
    neuf = src.replace(A1, N1).replace(A2, N2)
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "llm_client.py"; t.write_text(neuf, encoding="utf-8")
        try: py_compile.compile(str(t), doraise=True)
        except py_compile.PyCompileError as e: sys.exit(f"Abandon, ne compile pas : {e}")
    print(" · plafond x4 pour les modèles « large »")
    print(" · nouvel essai x3 si la réponse est vide (plafond atteint)")
    if not a.apply:
        print("\nDry-run : le résultat compile, rien n'est écrit. Relancer avec --apply."); return
    sauv = CIBLE.with_name(CIBLE.name + ".bak_thinking")
    shutil.copy2(CIBLE, sauv); CIBLE.write_text(neuf, encoding="utf-8")
    py_compile.compile(str(CIBLE), doraise=True)
    print(f"\nÉcrit : {CIBLE} (sauvegarde : {sauv.name}). py_compile OK.")

if __name__ == "__main__":
    main()
