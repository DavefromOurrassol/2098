#!/usr/bin/env python3
"""
patch_u3s_contexte_article_injection.py — Ourrassol 2098 (U3s, 11 novembre 2026)
================================================================================
L'IA d'injection ne voyait que la description et les faits imposés : elle inventait des
réactions d'autorités, un « débat mondial », des consortiums, des rattachements d'acteurs.
Ce patch lui donne le PASSAGE DE L'ARTICLE d'où vient l'événement.

Fonctionnement (aucun autre fichier à modifier) :
  - la citation exacte de l'article est déjà le premier fait imposé (U3i) ;
  - l'injecteur la retrouve dans articles/<scénario>/*.md (comparaison sans accents ni
    ponctuation, citation d'au moins 8 mots, UN SEUL article correspondant, sinon rien) ;
  - il ajoute au prompt de l'étape 2 un bloc « CONTEXTE DE L'ARTICLE D'ORIGINE » : le
    paragraphe de la citation, avec le précédent et le suivant (2 800 caractères au plus),
    et la règle : reprendre acteurs, lieux et chiffres tels quels, n'inventer ni réaction
    d'autorité, ni débat, ni acteur, ni sigle absent du passage ;
  - uniquement pour le scénario de l'article (pour un autre scénario, l'article ne sert pas
    de référence) ; sans citation retrouvée, le prompt est inchangé.

Modifie generator/inject_custom_events.py (3 modifications). Sauvegarde .bak_u3s.

USAGE (depuis la racine du vault)
  python3 generator/patch_u3s_contexte_article_injection.py            # dry-run
  python3 generator/patch_u3s_contexte_article_injection.py --apply    # applique
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "inject_custom_events.py"
TAG = "u3s"

ANCRE_DEF = "def _plie_v818(s):\n"
FONCTIONS = '''# U3s (11 novembre 2026) -- contexte de l'article d'origine pour l'étape 2
def _norm_ctx_u3s(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def _texte_contexte_article(idea, scenario, max_chars=2800):
    """Bloc du prompt : paragraphe de l'article d'où vient la citation imposée (U3i), avec ses
    voisins. Vide si aucune citation d'au moins 8 mots, ou si elle n'est pas trouvée dans UN
    SEUL article de articles/<scénario>/. Ne lève jamais d'exception."""
    try:
        cands = [f["fait"] for f in _faits_du_scenario(idea, scenario)
                 if (f.get("sort") or "contrainte") == "contrainte"
                 and len(_norm_ctx_u3s(f["fait"]).split()) >= 8]
        dossier = VAULT_ROOT / "articles" / scenario
        if not cands or not dossier.is_dir():
            return ""
        for cand in cands:
            cible = _norm_ctx_u3s(cand)
            trouves = []
            for f in sorted(dossier.glob("*.md")):
                brut = f.read_text(encoding="utf-8", errors="ignore")
                m = re.match(r"^---\\n(.*?)\\n---\\n?(.*)", brut, re.DOTALL)
                fm_txt, corps = (m.group(1), m.group(2)) if m else ("", brut)
                paras = [p.strip() for p in re.split(r"\\n\\s*\\n", corps) if p.strip()]
                for i, p in enumerate(paras):
                    if cible in _norm_ctx_u3s(p):
                        trouves.append((f, fm_txt, paras, i))
                        break
            if len(trouves) != 1:
                continue
            f, fm_txt, paras, i = trouves[0]
            try:
                fm = yaml.safe_load(fm_txt) or {}
            except yaml.YAMLError:
                fm = {}
            titre = str(fm.get("titre") or fm.get("title") or f.stem) if isinstance(fm, dict) else f.stem
            passage = "\\n\\n".join(paras[max(0, i - 1): i + 2]).replace("*", "")
            if len(passage) > max_chars:
                passage = passage[:max_chars].rsplit(" ", 1)[0] + " […]"
            print(f"  [contexte article] {f.name} (paragraphe {i + 1}/{len(paras)})")
            return (f"\\n## CONTEXTE DE L'ARTICLE D'ORIGINE (« {titre} »)\\n{passage}\\n"
                    "Ce passage est la SOURCE de l'événement : reprends les acteurs, lieux, chiffres et "
                    "rattachements tels qu'ils y figurent. N'invente AUCUNE réaction d'autorité, aucun débat, "
                    "consortium, acteur ni sigle qui n'est pas dans ce passage. Pour les conséquences, reste "
                    "sur des tensions ou des tendances plausibles, sans les présenter comme des faits déjà "
                    "survenus.\\n")
        return ""
    except Exception:  # noqa: BLE001 -- le contexte est un plus, jamais un blocage
        return ""


'''

ANCRE_FAITS = "    faits_txt = _texte_faits(idea, scenario)  # PATCH_S27_V818\n"
AJOUT_FAITS = "    contexte_txt = _texte_contexte_article(idea, scenario)  # U3s\n"

ANCRE_PROMPT = "{actors_hint_txt}{zone_hint_txt}{impositions_txt}{faits_txt}\n"
NOUVEAU_PROMPT = "{actors_hint_txt}{zone_hint_txt}{impositions_txt}{faits_txt}{contexte_txt}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not CIBLE.is_file():
        sys.exit(f"✗ introuvable : {CIBLE}")
    src = CIBLE.read_text(encoding="utf-8")
    if "_texte_contexte_article" in src:
        print("= déjà appliqué, rien à faire")
        return
    for nom, ancre in (("def _plie_v818", ANCRE_DEF), ("faits_txt", ANCRE_FAITS), ("prompt", ANCRE_PROMPT)):
        n = src.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (attendu 1) : fichier modifié ?")
    nouveau = (src.replace(ANCRE_DEF, FONCTIONS + ANCRE_DEF)
               .replace(ANCRE_FAITS, ANCRE_FAITS + AJOUT_FAITS)
               .replace(ANCRE_PROMPT, NOUVEAU_PROMPT))
    print(f"{CIBLE.name} : 3 modifications prévues (+{len(nouveau.splitlines()) - len(src.splitlines())} lignes)")
    if not args.apply:
        print("dry-run : rien écrit. Relancer avec --apply.")
        return
    bak = CIBLE.with_name(CIBLE.name + f".bak_{TAG}")
    shutil.copy2(CIBLE, bak)
    CIBLE.write_text(nouveau, encoding="utf-8")
    py_compile.compile(str(CIBLE), doraise=True)
    print(f"✓ appliqué ; sauvegarde {bak.name} ; py_compile OK")


if __name__ == "__main__":
    main()
