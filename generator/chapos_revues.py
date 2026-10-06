#!/usr/bin/env python3
"""
chapos_revues.py — Chapô de rédaction des 12 revues (Ourrassol 2098).

Pour chaque article PUBLIÉ sur le site (mêmes règles que export_revues.py :
journal identifié, thématique non exclue, daté jusqu'au mois de parution),
écrit le chapô que la rédaction de la revue place sous le titre : qui parle,
d'où, avec quel parti pris, et ce que l'article apporte. Comme sur Courrier
International, c'est la voix de la revue, pas celle du journal source.

  - 1 appel LLM par article (call_llm, task_tier="creative_souple")
  - résultat mis en cache dans state/chapos_revues.json : jamais régénéré
    tant que le texte de l'article ne change pas
  - les articles du vault ne sont JAMAIS modifiés
  - jamais lancé automatiquement : à lancer avant publier_site.sh

Usage :
  python3 generator/chapos_revues.py --dry-run          # combien, et coût estimé
  python3 generator/chapos_revues.py                    # génère les manquants
  python3 generator/chapos_revues.py --limit 5          # essai sur 5 articles
  python3 generator/chapos_revues.py --scenario reference
  python3 generator/chapos_revues.py --refaire reference/<fichier>.md   # régénère un article
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys

GEN_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GEN_DIR)
import yaml  # noqa: E402
import export_revues as er  # noqa: E402

TEXTE_MAX = 4000   # caractères du corps envoyés au LLM


def revue_et_charte(revues, journaux, sc, lg):
    rv = revues[sc][lg]
    charte = (((journaux.get(sc) or {}).get(lg) or {}).get("_reseau") or {}).get("charte", "")
    return rv, charte


def system_prompt(rv, charte, lg):
    camp = "proche des pouvoirs en place" if lg == "pro_pouvoir" else "d'opposition"
    statut = ""
    if rv.get("statut") == "privee_toleree":
        statut = " C'est une revue privée, tolérée par tous les blocs, qui défend l'ordre en général sans servir aucun bloc."
    if rv.get("diffusion") == "radio_transcriptions":
        statut += " C'est une radio clandestine dont la revue publie les transcriptions."
    return f"""Tu es la rédaction de « {rv['nom']} » ({rv.get('sous_titre', '')}), revue de presse {camp}, fondée en {rv.get('fondation', '')}, siège : {rv.get('ville_siege', '')}.{statut}
Chaque mois, la revue choisit, traduit et présente en français des articles de la presse de son réseau, dont la charte est : « {charte} »

Ta tâche : écrire le CHAPÔ de la revue pour un article repris, comme le fait Courrier International : un texte de présentation sobre, informatif, écrit par des journalistes.
Règles :
- 2 ou 3 phrases, 35 à 60 mots, en français, au présent.
- Commence par le FAIT ou l'enjeu (ce qui se passe, où), jamais par le nom du journal.
- Cite le journal source une seule fois, en italique avec des *astérisques*, de façon simple : « raconte *X* », « selon *X* », « *X*, quotidien de …, … ».
- N'utilise pas la formule « voix (…) de » et aucune métaphore sur le journal lui-même ; pas d'adjectifs lyriques.
- Le parti pris du journal ne se mentionne que s'il éclaire la lecture, en quelques mots. Le journal appartient au réseau de la revue : présente-le avec respect, sans qualificatif péjoratif (ni « paranoïaque », ni « propagandiste »…), même si son profil le décrit ainsi.
- 60 mots au maximum, et n'ajoute aucune conclusion ou estimation absente de l'article.
- Le ton suit la ligne de la revue, mais reste factuel et précis : des lieux, des acteurs, un enjeu.
- N'invente aucun fait, chiffre ou nom absent de l'article.
- Le monde est celui de 2098 : ne parle jamais de fiction, de scénario ni de simulation.
Réponds uniquement par le chapô : pas de titre, pas de guillemets autour, pas de préfixe."""


def user_prompt(a):
    _, blocs = er.nettoyer_corps(a["corps"], "")
    texte = "\n\n".join(blocs)[:TEXTE_MAX]
    return f"""JOURNAL SOURCE : {a['journal']}
Zone : {a['zone_journal_nom']}
Présentation du journal : {a['journal_presentation']}
Langue d'origine : {er.langue_principale(a['langue_style'])[0] if er.langue_principale(a['langue_style']) else 'non précisée'}
Date de parution : {er.date_fr(a['date'])}

CHAPÔ D'ORIGINE DU JOURNAL :
{a['fm'].get('chapo') or '(aucun)'}

TEXTE DE L'ARTICLE :
{texte}"""


def nettoyer_reponse(r):
    r = (r or "").strip().strip('"«»“” ').strip()
    r = re.sub(r"^(chap[ôo]\s*(de la revue)?\s*:\s*)", "", r, flags=re.I)
    r = r.strip().strip('"«»“” ').strip()
    r = re.sub(r"\s+", " ", r)
    r = r.replace("**", "")
    return r


def main():
    ap = argparse.ArgumentParser(description="Chapôs de rédaction des revues")
    ap.add_argument("--dry-run", action="store_true", help="compte seulement, aucun appel")
    ap.add_argument("--scenario", choices=er.SCENARIOS)
    ap.add_argument("--limit", type=int, help="nombre maximum d'appels")
    ap.add_argument("--refaire", metavar="SCENARIO/FICHIER.md", help="force la régénération d'un article")
    ap.add_argument("--mois", metavar="AAAA-MM", help="mois de parution (défaut : state/editions.json)")
    args = ap.parse_args()

    journaux = yaml.safe_load(open(er.trouver("journaux.yaml"), encoding="utf-8"))
    revues = yaml.safe_load(open(er.trouver("revues.yaml"), encoding="utf-8"))
    scenarios = [args.scenario] if args.scenario else er.SCENARIOS
    geos = {sc: er.charger_geo(sc) for sc in scenarios}
    articles = er.scanner(scenarios, journaux, revues, geos)
    liste, _, _ = er.publiables(articles, er.mois_parution(args.mois))
    liste = [a for a in liste if a["fm"].get("thematique") not in er.THEMES_SANS_CHAPO_REVUE]

    cache = er.charger_chapos()
    a_faire, modifies = [], 0
    for a in liste:
        cle = er.cle_article(a)
        c = cache.get(cle)
        emp = er.empreinte(a["corps"])
        if args.refaire and cle == args.refaire:
            a_faire.append(a)
        elif not c or not c.get("chapo"):
            a_faire.append(a)
        elif c.get("empreinte") != emp:
            a_faire.append(a)
            modifies += 1
    if args.refaire and not any(er.cle_article(a) == args.refaire for a in a_faire):
        sys.exit(f"❌ {args.refaire} n'est pas un article publié (vérifie scenario/fichier.md)")
    deja = len(liste) - len(a_faire)
    if args.limit:
        a_faire = a_faire[:args.limit]

    car = sum(len(system_prompt(*revue_et_charte(revues, journaux, a["scenario"], a["ligne_editoriale"]),
                                a["ligne_editoriale"])) + len(user_prompt(a)) for a in a_faire)
    print(f"\n=== Chapôs de rédaction — {len(liste)} articles publiés ===")
    print(f"  déjà faits           : {deja}")
    print(f"  à générer            : {len(a_faire)}" + (f" (dont {modifies} dont le texte a changé)" if modifies else ""))
    print(f"  volume estimé envoyé : ~{car // 4} jetons en entrée, ~{len(a_faire) * 120} en sortie")
    if args.dry_run or not a_faire:
        print("  (rien n'a été appelé)" if args.dry_run else "  ✓ Rien à faire.")
        return

    from llm_client import call_llm

    os.makedirs(os.path.dirname(er.CACHE_CHAPOS), exist_ok=True)
    if os.path.exists(er.CACHE_CHAPOS):
        shutil.copy2(er.CACHE_CHAPOS, er.CACHE_CHAPOS + ".bak")

    ok = echecs = 0
    for i, a in enumerate(a_faire, 1):
        rv, charte = revue_et_charte(revues, journaux, a["scenario"], a["ligne_editoriale"])
        try:
            rep = call_llm(system_prompt(rv, charte, a["ligne_editoriale"]), user_prompt(a),
                           max_tokens=300, temperature=0.6, task_tier="creative_souple")
            chapo = nettoyer_reponse(rep)
            if len(chapo.split()) < 12:
                raise ValueError(f"réponse trop courte : {chapo!r}")
        except Exception as ex:
            echecs += 1
            print(f"  [{i}/{len(a_faire)}] ✗ {er.cle_article(a)} — {ex}")
            continue
        cache[er.cle_article(a)] = {
            "chapo": chapo,
            "revue": rv["nom"],
            "journal": a["journal"],
            "empreinte": er.empreinte(a["corps"]),
            "date_generation": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        # écriture à chaque article : une interruption ne perd rien
        tmp = er.CACHE_CHAPOS + ".tmp"
        json.dump(cache, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.replace(tmp, er.CACHE_CHAPOS)
        ok += 1
        print(f"  [{i}/{len(a_faire)}] ✓ {rv['nom']} · {a['journal']}\n      {chapo}")

    print(f"\n  ✓ {ok} chapô(s) écrit(s) dans {er.CACHE_CHAPOS}" + (f" — {echecs} échec(s), relance le script pour les reprendre" if echecs else ""))
    print("  Prochaine étape : bash generator/publier_site.sh")


if __name__ == "__main__":
    main()
