#!/usr/bin/env python3
"""
fiche_au_passe.py — Ourrassol 2098 (S27, point 9, 24 octobre 2026)
===================================================================

Une entité qui disparaît (trajectoire « disparu », annee_fin posée par la
phase 4) garde une fiche écrite au présent : la phase 4 change la trajectoire,
pas le texte (cas Genève et Mourmansk, réécrits à la main le 23-24 oct). Ce
script met au passé, avec UN appel IA, les champs de texte de la fiche :
role_dans_scenario, responsabilites, description_journalistique,
signes_distinctifs, tensions_narratives (ceux qui sont remplis).

Deux temps :
  1. aperçu (défaut) : appel IA, contrôles, avant / après écrit dans
     documentation/need_action/fiche_au_passe_<slug>.md — rien d'autre n'est écrit.
     Les textes « Après » de ce fichier se retouchent librement dans Obsidian.
  2. --apply : relit ce fichier (sans nouvel appel IA) et remplace chaque texte
     partout où il figure dans la fiche (frontmatter et corps) ; refusé si la fiche
     a changé depuis l'aperçu. Sauvegarde .bak_au_passe.

USAGE (depuis la racine du vault)
    python3 generator/fiche_au_passe.py --slug murmansk_transit_arctique_reference
    python3 generator/fiche_au_passe.py --slug X --contexte "explosion du Polaris-7 (2081)"
    python3 generator/fiche_au_passe.py --slug X --apply
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

GEN = Path(__file__).resolve().parent
VAULT = GEN.parent
sys.path.insert(0, str(GEN))
INSTANCES = VAULT / "instances"
NEED_ACTION = VAULT / "documentation" / "need_action"
CHAMPS = ["role_dans_scenario", "responsabilites", "description_journalistique",
          "signes_distinctifs", "tensions_narratives"]
TERMINALES = {"disparu", "transformé", "historique", "mythifié"}

SYSTEME = ("Tu es le relecteur du lore du monde fictif Ourrassol 2098. Tu réécris des textes au passé en "
           "changeant le moins possible. Réponds UNIQUEMENT en JSON valide, sans texte autour.")


def decoupe(texte):
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", texte, re.S)
    return (m.group(2), texte[m.end():]) if m else (None, None)


def lire_fm(fm_txt):
    try:
        fm = yaml.safe_load(re.sub(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]", r"\1", fm_txt or "")) or {}
        return fm if isinstance(fm, dict) else None
    except yaml.YAMLError:
        return None


def un_espace(s):
    return " ".join(str(s or "").split())


def motif(texte):
    """Texte retrouvé quels que soient retours à la ligne et indentation (blocs YAML > et |)."""
    return re.compile(r"\s+".join(re.escape(m) for m in texte.split()))


def empreinte(texte):
    return hashlib.sha1(texte.encode("utf-8")).hexdigest()[:12]


def rapport_path(slug):
    return NEED_ACTION / f"fiche_au_passe_{slug}.md"


def controles(champ, avant, apres, annee):
    """Avertissements (pas des refus) : longueur, noms propres, années perdues."""
    al = []
    r = len(apres) / max(1, len(avant))
    if not 0.7 <= r <= 1.5:
        al.append(f"longueur ×{r:.2f}")
    # Noms propres : mots à majuscule, sauf le premier mot d'une phrase (« Coordination… »).
    noms = lambda t: set(re.findall(r"\b[A-ZÉÈÀÂÎÔÛ][\w'’-]{3,}",
                                    re.sub(r"(^|[.!?:;]\s+|—\s+)[A-ZÉÈÀÂÎÔÛ][\w'’-]*", r"\1", t)))
    perdus = sorted(noms(avant) - noms(apres))
    if perdus:
        al.append("noms propres absents : " + ", ".join(perdus[:6]))
    annees = lambda t: set(re.findall(r"\b(?:19|20|21)\d\d\b", t))
    a_perdues = sorted(annees(avant) - annees(apres))
    if a_perdues:
        al.append("années disparues : " + ", ".join(a_perdues))
    tard = sorted(a for a in annees(apres) if annee and int(a) > int(annee))
    if tard:
        al.append(f"années après la fin ({annee}) : " + ", ".join(tard))
    return al


def apercu(slug, contexte):
    p = INSTANCES / f"{slug}.md"
    if not p.exists():
        sys.exit(f"✗ {p.relative_to(VAULT)} introuvable")
    brut = p.read_text(encoding="utf-8")
    fm = lire_fm(decoupe(brut)[0])
    if fm is None:
        sys.exit("✗ frontmatter illisible")
    traj, annee = fm.get("trajectoire"), fm.get("annee_fin")
    if traj not in TERMINALES:
        print(f"⚠ trajectoire « {traj} » : la fiche n'est pas terminale, la mettre au passé est-il voulu ?")
    if not annee:
        print("⚠ annee_fin vide : l'IA ne connaîtra pas l'année de fin.")
    textes = {c: un_espace(fm.get(c)) for c in CHAMPS if un_espace(fm.get(c))}
    if not textes:
        sys.exit("✗ aucun champ de texte rempli")

    user = (f"FICHE : « {fm.get('name') or slug} » (scénario {fm.get('scenario')}), trajectoire « {traj} », "
            f"fin en {annee or '?'}." + (f"\nCE QUI S'EST PASSÉ : {contexte}" if contexte else "") + "\n\n"
            "TEXTES (écrits au présent alors que l'entité n'existe plus) :\n"
            + json.dumps(textes, ensure_ascii=False, indent=1) + "\n\n"
            "TÂCHE : réécris chaque texte au passé (imparfait, passé composé), comme l'histoire d'une entité "
            f"qui a pris fin en {annee or 'sa dernière année'}. Garde les faits, les noms et le style ; change le "
            "moins de mots possible. N'ajoute AUCUN fait nouveau, sauf la fin elle-même"
            + (" (telle que décrite ci-dessus)" if contexte else "") + ", en une phrase au plus par texte. "
            f"Un fait daté APRÈS {annee or 'la fin'} doit être ramené avant la fin ou retiré. Longueur proche "
            "de l'original.\n"
            'Format : {"<champ>": "<texte au passé>", ...} avec exactement les mêmes clés.')
    from llm_client import call_llm
    rep = (call_llm(system_prompt=SYSTEME, user_prompt=user, max_tokens=3500, temperature=0.3,
                    task_tier="structured_strict") or "").strip()
    d, f = rep.find("{"), rep.rfind("}")
    try:
        res = json.loads(rep[d:f + 1])
    except ValueError:
        sys.exit(f"✗ réponse IA illisible : {rep[:300]}")

    L = [f"# {fm.get('name') or slug} — fiche au passé", "",
         f"*Aperçu de fiche_au_passe.py — `instances/{slug}.md` (empreinte {empreinte(brut)}). Retouche "
         "librement les textes « Après », puis : "
         f"`python3 generator/fiche_au_passe.py --slug {slug} --apply`.*", ""]
    n_al = 0
    for c, avant in textes.items():
        apres = un_espace(res.get(c))
        if not apres:
            sys.exit(f"✗ l'IA n'a pas rendu le champ {c} : rien écrit")
        al = controles(c, avant, apres, annee)
        n_al += len(al)
        L += [f"## {c}", "", f"**Avant** : {avant}", ""]
        L += [f"> ⚠ {a}" for a in al] + ([""] if al else [])
        L += ["**Après** :", "", apres, ""]
        print(f"  {c} : {len(avant)} → {len(apres)} car." + (f"  ⚠ {' ; '.join(al)}" if al else ""))
    NEED_ACTION.mkdir(parents=True, exist_ok=True)
    rapport_path(slug).write_text("\n".join(L), encoding="utf-8")
    print(f"\nAperçu : {rapport_path(slug).relative_to(VAULT)} ({n_al} avertissement(s)). Rien n'est écrit "
          "dans la fiche : relire (et retoucher), puis l'écrire (étape ⑤ « Écrire dans la fiche », ou --apply).")


def appliquer(slug):
    p, r = INSTANCES / f"{slug}.md", rapport_path(slug)
    if not r.exists():
        sys.exit("✗ pas d'aperçu : lancer d'abord sans --apply")
    rap = r.read_text(encoding="utf-8")
    brut = p.read_text(encoding="utf-8")
    m = re.search(r"empreinte ([0-9a-f]{12})", rap)
    if not m or m.group(1) != empreinte(brut):
        sys.exit("✗ la fiche a changé depuis l'aperçu : relancer l'aperçu")
    fm = lire_fm(decoupe(brut)[0]) or {}
    texte = brut
    for bloc in re.split(r"^## ", rap, flags=re.M)[1:]:
        champ = bloc.split("\n", 1)[0].strip()
        if champ not in CHAMPS:
            continue
        apres = un_espace(bloc.split("**Après** :", 1)[1]) if "**Après** :" in bloc else ""
        avant = un_espace(fm.get(champ))
        if not apres or not avant:
            sys.exit(f"✗ {champ} : texte vide dans l'aperçu ou dans la fiche — rien écrit")
        mo = motif(avant)
        n = len(mo.findall(texte))
        if n == 0:
            sys.exit(f"✗ {champ} : ancien texte introuvable dans la fiche — rien écrit")
        texte = mo.sub(lambda _m: apres, texte)
        print(f"  {champ} : {n} occurrence(s) remplacée(s)")
    apres_fm = lire_fm(decoupe(texte)[0])
    if apres_fm is None:
        sys.exit("✗ le frontmatter ne se lirait plus — rien écrit")
    shutil.copy2(p, p.with_name(p.name + ".bak_au_passe"))
    p.write_text(texte, encoding="utf-8")
    print(f"\n✓ instances/{slug}.md au passé (sauvegarde .bak_au_passe). Vérifier : « Relecture du lore » "
          f"({apres_fm.get('scenario')}).")


def main():
    a = argparse.ArgumentParser(description="Met au passé la fiche d'une entité disparue (un appel IA).")
    a.add_argument("--slug", required=True, help="slug de l'instance (instances/<slug>.md)")
    a.add_argument("--contexte", default="", help="ce qui a mis fin à l'entité (facultatif)")
    a.add_argument("--apply", action="store_true", help="écrit les textes de l'aperçu (sans appel IA)")
    args = a.parse_args()
    appliquer(args.slug) if args.apply else apercu(args.slug, args.contexte.strip())


if __name__ == "__main__":
    main()
