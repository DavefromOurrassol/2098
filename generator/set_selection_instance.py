#!/usr/bin/env python3
"""
set_selection_instance.py — Ourrassol 2098 (24 septembre 2026)

Règle la présence d'instances dans les articles, sans appel LLM, par
modification directe du frontmatter des fiches instances/. Deux leviers :

  exclure       exclure_articles: true   — l'instance n'est JAMAIS retenue
                                           par la sélection automatique
                                           des articles (loader.py). Reste
                                           utilisable en "Forcer un élément".
  autoriser     exclure_articles: false
  sans_garantie injection.garantie_selection: false — une instance créée
                                           en mode custom perd sa place
                                           GARANTIE dans les articles, mais
                                           garde son impact sur les
                                           variables. Elle redevient une
                                           candidate ordinaire (pertinence
                                           + rotation).
  garantie      injection.garantie_selection: true

Cible : une instance (--slug) OU toutes les instances d'une entité
(--entite), éventuellement limitées à un scénario (--scenario).

USAGE
    python3 set_selection_instance.py --slug hyphan_raghavan_fortress_world --action exclure
    python3 set_selection_instance.py --entite kindling --action sans_garantie
    python3 set_selection_instance.py --entite ergo_wian_sovereign_holdings --scenario reference --action garantie
    ... --dry-run   # affiche sans écrire
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_DIR = VAULT_ROOT / "instances"
SCENARIOS = ["breakdown", "fortress_world", "new_sustainability",
             "eco_communalism", "policy_reform", "reference"]
ACTIONS = {
    "exclure": ("exclure_articles", True),
    "autoriser": ("exclure_articles", False),
    "sans_garantie": ("garantie_selection", False),
    "garantie": ("garantie_selection", True),
}


def _fm(texte):
    m = re.match(r"^---\n(.*?)\n---", texte, re.S)
    return (m, yaml.safe_load(m.group(1)) or {}) if m else (None, None)


def _poser_exclure(fm_txt, valeur):
    ligne = f"exclure_articles: {str(valeur).lower()}"
    if re.search(r"^exclure_articles:.*$", fm_txt, re.M):
        return re.sub(r"^exclure_articles:.*$", ligne, fm_txt, count=1, flags=re.M)
    return fm_txt.rstrip("\n") + "\n" + ligne


def _poser_garantie(fm_txt, valeur):
    m = re.search(r"^injection:[ \t]*\n((?:[ \t]+.*\n?)*)", fm_txt, re.M)
    if not m:
        return None  # pas de bloc injection : garantie sans objet
    bloc = m.group(1)
    ligne_val = f"garantie_selection: {str(valeur).lower()}"
    if re.search(r"^[ \t]+garantie_selection:.*$", bloc, re.M):
        bloc2 = re.sub(r"^([ \t]+)garantie_selection:.*$", rf"\g<1>{ligne_val}", bloc, count=1, flags=re.M)
    else:
        indent = re.match(r"^([ \t]+)", bloc).group(1) if bloc else "  "
        bloc2 = f"{indent}{ligne_val}\n" + bloc
    return fm_txt[:m.start(1)] + bloc2 + fm_txt[m.end(1):]


def traiter(path, cle, valeur, dry_run):
    texte = path.read_text(encoding="utf-8")
    m, fm = _fm(texte)
    if fm is None:
        return f"✗ {path.stem} : frontmatter illisible"
    fm_txt = m.group(1)
    if cle == "garantie_selection":
        injection = fm.get("injection") or {}
        if injection.get("type") != "custom":
            return f"= {path.stem} : instance canonique, sans garantie de présence (rien à faire)"
        nouveau_txt = _poser_garantie(fm_txt, valeur)
        if nouveau_txt is None:
            return f"✗ {path.stem} : bloc injection introuvable"
    else:
        nouveau_txt = _poser_exclure(fm_txt, valeur)
    relu = yaml.safe_load(nouveau_txt) or {}
    attendu = dict(fm)
    if cle == "garantie_selection":
        attendu["injection"] = dict(fm.get("injection") or {}, garantie_selection=valeur)
    else:
        attendu["exclure_articles"] = valeur
    if relu != attendu:
        return f"✗ {path.stem} : la relecture ne correspond pas — NON modifié"
    if nouveau_txt == fm_txt:
        return f"= {path.stem} : déjà {cle}={str(valeur).lower()}"
    if not dry_run:
        path.write_text(texte[:m.start(1)] + nouveau_txt + texte[m.end(1):], encoding="utf-8")
    return f"✓ {path.stem} : {cle}={str(valeur).lower()}" + (" (dry-run)" if dry_run else "")


def main():
    ap = argparse.ArgumentParser(description="Présence d'instances dans les articles (sans LLM)")
    ap.add_argument("--slug", help="Slug d'une instance (ex. hyphan_raghavan_fortress_world)")
    ap.add_argument("--entite", help="Slug d'une entité : toutes ses instances")
    ap.add_argument("--scenario", choices=SCENARIOS, help="Limiter à ce scénario")
    ap.add_argument("--action", required=True, choices=list(ACTIONS))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if bool(a.slug) == bool(a.entite):
        sys.exit("✗ Indiquer soit --slug (une instance), soit --entite (toutes ses instances).")
    if a.slug:
        cibles = [INSTANCES_DIR / f"{a.slug}.md"]
        if a.scenario and not a.slug.endswith(f"_{a.scenario}"):
            sys.exit(f"✗ {a.slug} n'appartient pas au scénario {a.scenario}.")
    else:
        scs = [a.scenario] if a.scenario else SCENARIOS
        cibles = [INSTANCES_DIR / f"{a.entite}_{sc}.md" for sc in scs]
        cibles = [p for p in cibles if p.exists()]
    manquants = [p for p in cibles if not p.exists()]
    if manquants or not cibles:
        sys.exit("✗ Instance(s) introuvable(s) : " + (", ".join(p.stem for p in manquants) or "aucune"))

    cle, valeur = ACTIONS[a.action]
    print(f"Action : {a.action} ({cle}={str(valeur).lower()}) sur {len(cibles)} instance(s)")
    for p in cibles:
        print("  " + traiter(p, cle, valeur, a.dry_run))


if __name__ == "__main__":
    main()
