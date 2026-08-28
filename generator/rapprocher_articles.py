#!/usr/bin/env python3
"""
rapprocher_articles.py — Ourrassol 2098
=========================================

Backlog Partie 1, points 9 (P20, `articles_lies` — le seul champ resté
non calculé de tout le chantier) et 11 (vocabulaire des tags), tous deux
21 août 2026. Les deux mécanismes scannent le même corpus et reposent
sur le même signal de fond (recoupement entre articles) — traités
ensemble plutôt que comme deux scripts séparés.

CE QUE FAIT CE SCRIPT
----------------------
1. Construit/rafraîchit `tags_reference.yaml` (fréquence d'usage de
   chaque tag déjà vu dans `articles/*.md`) — consommé par
   `prompt_builder.py` pour suggérer une réutilisation en priorité
   plutôt qu'une invention systématique à chaque article (Option C
   actée avec David : vocabulaire qui s'auto-construit depuis
   l'existant, pas de taxonomie fermée pré-écrite).

2. Calcule `articles_lies` pour chaque article — 2 à 3 articles les
   plus proches, restreint au MÊME SCÉNARIO uniquement (les 6 scénarios
   sont des futurs alternatifs séparés, un rapprochement cross-scénario
   n'aurait pas de sens narratif). Score pondéré :
     score = 3 × |entités partagées| + 1 × |tags partagés|
   (une entité nommée partagée est un signal plus spécifique et plus
   fort qu'un tag générique partagé — ratio 3:1 acté avec David).

3. Met à jour la ligne "**Voir aussi**" dans le CORPS de chaque article
   traité (wikilinks Obsidian `[[slug]]`, jamais en frontmatter — la vue
   graphique d'Obsidian ne suit que les liens du corps, confirmé sur les
   fiches entites/*.md existantes). Combine entites_citees (déjà présent
   depuis la génération) + articles_lies (calculé ici), dédoublonné.
   Idempotent : un article déjà traité voit sa ligne remplacée, pas
   dupliquée.

CE QUE CE SCRIPT NE FAIT PAS
------------------------------
- Ne traite PAS les articles sans `slug` en frontmatter (générés avant
  P20, 21 août 2026) — hors scope, voir backlog Partie 1 point 12
  (rétro-application sur les articles existants, à scoper séparément).
- Ne rapproche jamais deux articles de scénarios différents.
- Ne modifie jamais le texte de l'article lui-même, seulement le
  frontmatter (`articles_lies`) et une ligne dédiée en fin de corps.

USAGE — COMMENCER PAR UN DRY-RUN (aucune écriture, juste un rapport)
----------------------------------------------------------------------
    python3 rapprocher_articles.py --dry-run
    python3 rapprocher_articles.py --dry-run --scenario fortress_world

Puis pour de vrai (comportement par défaut si --dry-run est omis,
cohérent avec fix_annee_debut_placeholder.py/promote_ville.py/
generate_images.py) :
    python3 rapprocher_articles.py
    python3 rapprocher_articles.py --scenario fortress_world
"""

import argparse
import re
import yaml
from pathlib import Path
from collections import defaultdict

VAULT_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = VAULT_ROOT / "articles"
TAGS_REFERENCE_PATH = Path(__file__).resolve().parent / "tags_reference.yaml"

WEIGHT_ENTITE = 3
WEIGHT_TAG = 1
MAX_LIES = 3

VOIR_AUSSI_RE = re.compile(r"(?m)^\*\*Voir aussi\*\* : .*$")
ARTICLES_LIES_RE = re.compile(r"(?m)^articles_lies:(?:\n  - .+)*")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_md(filepath):
    """Parse un fichier .md : retourne (frontmatter_dict, prefix, fm_block, marker, body)."""
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)", raw, re.DOTALL)
    if not m:
        return {}, None, None, None, raw
    prefix, fm_block, marker, body = m.groups()
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", fm_block)
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, prefix, fm_block, marker, body


def _iter_all_article_files():
    """
    Parcourt TOUS les .md exploitables sous articles/ -- à la racine ET
    dans les sous-dossiers par scénario. Correctif du 21 août 2026
    (soir) : une partie du corpus historique a été générée avec
    config["output"]["dossier"] pointant vers la racine de articles/
    plutôt qu'un sous-dossier par scénario -- ne balayer que
    articles/*/*.md ratait silencieusement ces fichiers.
    """
    if not ARTICLES_DIR.exists():
        return
    for filepath in sorted(ARTICLES_DIR.glob("*.md")):
        if filepath.name != "_index.md":
            yield filepath
    for sub in sorted(ARTICLES_DIR.iterdir()):
        if not sub.is_dir():
            continue
        for filepath in sorted(sub.glob("*.md")):
            if filepath.name != "_index.md":
                yield filepath


def collect_articles(scenario_filter=None):
    """Retourne la liste des articles exploitables (slug présent -- voir
    docstring, articles pré-P20 exclus)."""
    articles = []
    skipped_no_slug = 0
    for filepath in _iter_all_article_files():
        fm, prefix, fm_block, marker, body = parse_md(filepath)
        slug = fm.get("slug")
        if not slug:
            skipped_no_slug += 1
            continue
        # Scénario lu depuis le frontmatter, pas depuis l'emplacement du
        # fichier -- voir _iter_all_article_files().
        scenario = fm.get("scenario")
        if not scenario:
            skipped_no_slug += 1
            continue
        if scenario_filter and scenario != scenario_filter:
            continue
        articles.append({
            "filepath": filepath,
            "scenario": scenario,
            "slug": slug,
            "entites": list(dict.fromkeys(fm.get("entites_citees") or [])),
            "tags": set(fm.get("tags") or []),
            })
    return articles, skipped_no_slug


# ---------------------------------------------------------------------------
# Vocabulaire des tags
# ---------------------------------------------------------------------------

def build_tags_reference(articles):
    counts = defaultdict(int)
    for a in articles:
        for t in a["tags"]:
            counts[t] += 1
    return dict(counts)


def build_entity_frequency(articles):
    """Fréquence de chaque entité dans entites_citees, PAR SCÉNARIO (pas
    en absolu) -- un scénario avec plus d'articles fausserait sinon la
    comparaison. Retourne {scenario: {entite: (count, total_articles_scenario)}}."""
    totals = defaultdict(int)
    counts = defaultdict(lambda: defaultdict(int))
    for a in articles:
        totals[a["scenario"]] += 1
        for e in a["entites"]:
            counts[a["scenario"]][e] += 1
    return counts, totals


SEUIL_OMNIPRESENCE = 0.40


def print_stats(articles):
    """Mode diagnostic (--stats) : détecte les entités quasi-omniprésentes
    dans un scénario -- signal possible de biais de génération (une
    entité "de fond" présente dans une trop grande part des articles),
    utile à David indépendamment du calcul d'articles_lies lui-même.
    Purement en lecture, n'écrit jamais rien."""
    counts, totals = build_entity_frequency(articles)
    print("=" * 60)
    print("-- Fréquence des entités par scénario --")
    print("   (seuil d'alerte : présente dans >{:.0f}% des articles du "
          "scénario)".format(SEUIL_OMNIPRESENCE * 100))
    print("=" * 60)
    for scenario in sorted(totals):
        total = totals[scenario]
        print("\n{} ({} article(s) exploitable(s))".format(scenario, total))
        entites_triees = sorted(counts[scenario].items(), key=lambda x: -x[1])
        for entite, n in entites_triees[:10]:
            ratio = n / total
            alerte = "  ⚠ QUASI-OMNIPRÉSENTE" if ratio > SEUIL_OMNIPRESENCE else ""
            print("  {} : {}/{} articles ({:.0f}%){}".format(entite, n, total, ratio * 100, alerte))

    tags_counts = build_tags_reference(articles)
    print()
    print("=" * 60)
    print("-- Fréquence des tags (tous scénarios confondus) --")
    print("=" * 60)
    for tag, n in sorted(tags_counts.items(), key=lambda x: -x[1])[:15]:
        print("  {} : {}".format(tag, n))


def write_tags_reference(counts, dry_run):
    sorted_counts = dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))
    if dry_run:
        top5 = list(sorted_counts.items())[:5]
        print("[DRY] tags_reference.yaml : {} tags distincts, {} usages cumulés "
              "-- top 5 : {}".format(len(counts), sum(counts.values()), top5))
        return
    data = {"tags": sorted_counts}
    TAGS_REFERENCE_PATH.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8"
    )
    print("[OK] tags_reference.yaml écrit : {} tags distincts, {} usages cumulés.".format(
        len(counts), sum(counts.values())))


# ---------------------------------------------------------------------------
# Articles liés
# ---------------------------------------------------------------------------

def compute_articles_lies(articles):
    """Retourne {slug: [slug_lié, ...]} -- calcul restreint au même
    scénario (voir docstring module)."""
    result = {}
    by_scenario = defaultdict(list)
    for a in articles:
        by_scenario[a["scenario"]].append(a)

    for scenario, group in by_scenario.items():
        for a in group:
            scores = []
            entites_a = set(a["entites"])
            for b in group:
                if a["slug"] == b["slug"]:
                    continue
                score = (WEIGHT_ENTITE * len(entites_a & set(b["entites"]))
                          + WEIGHT_TAG * len(a["tags"] & b["tags"]))
                if score > 0:
                    scores.append((score, b["slug"]))
            scores.sort(key=lambda x: (-x[0], x[1]))
            result[a["slug"]] = [slug for _, slug in scores[:MAX_LIES]]
    return result


def build_voir_aussi_line(entites, articles_lies_slugs):
    slugs = list(dict.fromkeys(list(entites) + list(articles_lies_slugs)))
    if not slugs:
        return None
    return "**Voir aussi** : " + " · ".join("[[{}]]".format(s) for s in slugs)


def patch_article(article, articles_lies_slugs, dry_run):
    filepath = article["filepath"]
    fm, prefix, fm_block, marker, body = parse_md(filepath)

    new_block = "articles_lies:"
    for s in articles_lies_slugs:
        new_block += "\n  - {}".format(s)

    if ARTICLES_LIES_RE.search(fm_block):
        new_fm_block = ARTICLES_LIES_RE.sub(new_block, fm_block, count=1)
    else:
        new_fm_block = fm_block.rstrip("\n") + "\n" + new_block + "\n"

    voir_aussi_line = build_voir_aussi_line(article["entites"], articles_lies_slugs)
    new_body = body
    if voir_aussi_line:
        if VOIR_AUSSI_RE.search(body):
            new_body = VOIR_AUSSI_RE.sub(voir_aussi_line, body, count=1)
        else:
            new_body = body.rstrip("\n") + "\n\n---\n" + voir_aussi_line + "\n"

    if dry_run:
        print("  [DRY] {} -- articles_lies={} -- voir_aussi={}".format(
            article["slug"], articles_lies_slugs, "oui" if voir_aussi_line else "non"))
        return

    filepath.write_text("{}{}{}{}".format(prefix, new_fm_block, marker, new_body), encoding="utf-8")
    print("  [OK] {} -- {} article(s) lié(s).".format(article["slug"], len(articles_lies_slugs)))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default=None, help="Limiter à un scénario (défaut : tous)")
    parser.add_argument("--dry-run", action="store_true", help="N'écrit rien sur disque")
    parser.add_argument("--stats", action="store_true",
                         help="Mode diagnostic uniquement : fréquence des entités/tags par "
                              "scénario, détecte les entités quasi-omniprésentes (biais possible "
                              "de génération). N'écrit jamais rien, ignore --dry-run.")
    args = parser.parse_args()

    articles, skipped = collect_articles(scenario_filter=args.scenario)

    if args.stats:
        print("{} article(s) exploitable(s){}, {} ignoré(s) (pas de slug, pré-P20).\n".format(
            len(articles),
            " pour {}".format(args.scenario) if args.scenario else "",
            skipped
        ))
        if not articles:
            print("Rien à analyser.")
            return
        print_stats(articles)
        return

    print("rapprocher_articles.py — mode {}".format("DRY-RUN" if args.dry_run else "EXECUTE"))
    print("{} article(s) exploitable(s){}, {} ignoré(s) (pas de slug, pré-P20).\n".format(
        len(articles),
        " pour {}".format(args.scenario) if args.scenario else "",
        skipped
    ))

    if not articles:
        print("Rien à traiter.")
        return

    # 1. Vocabulaire des tags
    tags_counts = build_tags_reference(articles)
    write_tags_reference(tags_counts, dry_run=args.dry_run)
    print()

    # 2. Articles liés
    articles_lies_map = compute_articles_lies(articles)
    n_avec_liens = sum(1 for v in articles_lies_map.values() if v)
    print("Rapprochement : {}/{} article(s) avec au moins un lien trouvé.\n".format(
        n_avec_liens, len(articles)))

    for article in articles:
        patch_article(article, articles_lies_map.get(article["slug"], []), dry_run=args.dry_run)

    if args.dry_run:
        print("\n[DRY-RUN] Aucune modification effectuée.")


if __name__ == "__main__":
    main()
