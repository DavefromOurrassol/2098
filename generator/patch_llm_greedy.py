#!/usr/bin/env python3
"""
patch_llm_greedy.py — Ourrassol 2098 (14 novembre 2026)
Mistral renvoie 400 « top_p must be 1 when using greedy sampling » quand temperature=0.0.
Correctif dans generator/llm_client.py (_call_mistral) : sur cette erreur précise, un seul
nouvel essai avec top_p=1.0 et temperature >= 0.01. Les autres erreurs ne changent pas.

Usage (racine du vault) :
    python3 generator/patch_llm_greedy.py            # dry-run
    python3 generator/patch_llm_greedy.py --apply    # écrit (.bak_greedy)
"""
import argparse, py_compile, shutil, sys, tempfile
from pathlib import Path

CIBLE = Path("generator/llm_client.py")
ANCRE = '''    try:
        response = client.chat.complete(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ]
        )
    except Exception as e:
        raise RuntimeError(f"[llm_client] Erreur API Mistral : {e}")
'''
NOUVEAU = '''    # GREEDY (14 nov. 2026) : temperature=0.0 -> l'API Mistral exige top_p=1 (erreur 400
    # « greedy sampling »). Un seul nouvel essai dans ce cas précis.
    args_mistral = dict(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    try:
        try:
            response = client.chat.complete(**args_mistral)
        except Exception as e:
            if "greedy sampling" not in str(e):
                raise
            args_mistral["top_p"] = 1.0
            args_mistral["temperature"] = max(temperature, 0.01)
            response = client.chat.complete(**args_mistral)
    except Exception as e:
        raise RuntimeError(f"[llm_client] Erreur API Mistral : {e}")
'''

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not CIBLE.exists():
        sys.exit(f"{CIBLE} introuvable : lancer depuis la racine du vault.")
    src = CIBLE.read_text(encoding="utf-8")
    if "GREEDY (14 nov" in src:
        sys.exit("Déjà appliqué : rien à faire.")
    if src.count(ANCRE) != 1:
        sys.exit(f"Abandon, rien écrit : ancre trouvée {src.count(ANCRE)} fois (attendu 1).")
    neuf = src.replace(ANCRE, NOUVEAU)
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "llm_client.py"; t.write_text(neuf, encoding="utf-8")
        try: py_compile.compile(str(t), doraise=True)
        except py_compile.PyCompileError as e: sys.exit(f"Abandon, ne compile pas : {e}")
    print(" · _call_mistral : nouvel essai top_p=1.0 sur erreur « greedy sampling »")
    if not a.apply:
        print("\nDry-run : le résultat compile, rien n'est écrit. Relancer avec --apply."); return
    sauv = CIBLE.with_name(CIBLE.name + ".bak_greedy")
    shutil.copy2(CIBLE, sauv); CIBLE.write_text(neuf, encoding="utf-8")
    py_compile.compile(str(CIBLE), doraise=True)
    print(f"\nÉcrit : {CIBLE} (sauvegarde : {sauv.name}). py_compile OK.")

if __name__ == "__main__":
    main()
