#!/usr/bin/env python3
"""
patch_llm_large4.py — Ourrassol 2098 (9 octobre 2026)

Mistral Large 4 (`mistral-large-4`) raisonne avant de répondre : son
`message.content` n'est plus une chaîne mais une LISTE de morceaux
(réflexion + texte). `llm_client._call_mistral()` renvoyait cette liste
telle quelle -> api.py recevait un objet de longueur 2 (« Article généré :
2 caractères ») puis TypeError.

Correctif : `_texte_reponse()` ne garde que les morceaux de type texte
(la réflexion est ignorée) ; une chaîne simple (Large 3, Small) passe
inchangée. Une ligne de log signale quand une réflexion a été écartée.

Usage (depuis la racine du vault) :
    python3 generator/patch_llm_large4.py --dry-run
    python3 generator/patch_llm_large4.py
Sauvegarde : generator/llm_client.py.bak_large4. Refuse un second passage.
"""
import argparse
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "llm_client.py"
MARQUEUR = "# LARGE4 (9 octobre 2026)"

HELPER = MARQUEUR + ''' -- réponses en morceaux (modèles qui raisonnent)
def _texte_reponse(content, model):
    """Renvoie le texte d'une réponse Mistral. Une chaîne passe telle quelle ;
    une liste de morceaux (Mistral Large 4, Magistral : réflexion + texte) est
    réduite à ses morceaux de type texte, la réflexion étant écartée."""
    if content is None or isinstance(content, str):
        return content or ""
    textes, autres = [], []
    for morceau in content:
        if isinstance(morceau, str):
            textes.append(morceau)
            continue
        typ = getattr(morceau, "type", None)
        if typ is None and isinstance(morceau, dict):
            typ = morceau.get("type")
        if typ == "text":
            txt = getattr(morceau, "text", None)
            if txt is None and isinstance(morceau, dict):
                txt = morceau.get("text")
            textes.append(txt or "")
        else:
            autres.append(str(typ))
    if autres:
        print(f"[llm] {model} : morceau(x) écarté(s) {sorted(set(autres))}, "
              f"texte gardé : {sum(len(t) for t in textes)} caractères")
    return "".join(textes)


# ─────────────────────────────────────────
# BACKEND OPENAI
# ─────────────────────────────────────────
'''

REMPLACEMENTS = [
    (
        "    return response.choices[0].message.content\n\n\n"
        "# ─────────────────────────────────────────\n"
        "# BACKEND OPENAI\n"
        "# ─────────────────────────────────────────\n",
        "    return _texte_reponse(response.choices[0].message.content, model)\n\n\n" + HELPER,
    ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fichier", default=str(CIBLE))
    args = ap.parse_args()
    cible = Path(args.fichier)
    texte = cible.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit(f"Déjà appliqué ({MARQUEUR} présent dans {cible.name}). Rien à faire.")
    for i, (avant, apres) in enumerate(REMPLACEMENTS, 1):
        n = texte.count(avant)
        if n != 1:
            sys.exit(f"Ancre {i} trouvée {n} fois (attendu 1) : patch abandonné, rien écrit.")
        texte = texte.replace(avant, apres)
    compile(texte, str(cible), "exec")
    if args.dry_run:
        print(f"OK (simulation) : {len(REMPLACEMENTS)} remplacement possible, rien écrit.")
        return
    bak = cible.with_name(cible.name + ".bak_large4")
    bak.write_text(cible.read_text(encoding="utf-8"), encoding="utf-8")
    cible.write_text(texte, encoding="utf-8")
    print(f"OK : {len(REMPLACEMENTS)} remplacement, sauvegarde {bak.name}.")


if __name__ == "__main__":
    main()
