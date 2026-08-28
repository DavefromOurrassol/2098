#!/usr/bin/env python3
"""
audit_longueur_articles.py — Ourrassol 2098
==============================================

Diagnostic en lecture seule (aucune écriture, aucun appel LLM) : compare
trois informations pour chaque article de articles/*.md :
  1. La longueur RÉELLE (comptage de mots du corps)
  2. Le champ `format` du frontmatter — nom de catégorie (ex. "analyse"),
     TOUJOURS dérivé de `thematique.get("format_dominant")`, jamais de
     l'override de config (voir prompt_builder.py ligne ~1661)
  3. Le champ `longueur` du frontmatter — plage textuelle déjà résolue
     (ex. "600 à 900 mots"), qui elle TIENT COMPTE de l'override de
     config si un override a été fourni

CONTEXTE (9 août 2026, backlog point 1 — metadata["longueur"])
-----------------------------------------------------------------
Bug corrigé le 3 août : `metadata["longueur"]` ignorait parfois
l'override de config, recalculé depuis `format_dominant` au lieu de la
valeur réellement utilisée. Le prompt envoyé au LLM était toujours
correct (le contenu réel de l'article reflète la bonne longueur voulue
au moment de la génération) — seule l'étiquette écrite dans le
frontmatter pouvait être fausse sur les articles publiés avant ce
correctif.

CORRECTIONS APPORTÉES À CE SCRIPT (même session, 9 août 2026) :
  - v1 : cherchait `longueur` comme un nom de catégorie — faux, c'est une
    plage textuelle déjà résolue. 100% "étiquette inconnue" à tort.
  - v2 : corrigé pour parser la plage textuelle directement (regex),
    comparée au seul comptage de mots. Fonctionnel, mais reconstruisait
    une réponse binaire cohérent/incohérent sans exploiter une info déjà
    disponible : le champ `format` du frontmatter EST le nom de
    catégorie recherché, pas besoin de le deviner depuis le comptage.
  - v3 (celle-ci) : utilise `format` comme vérité terrain pour la
    catégorie prévue par la thématique, et distingue deux situations
    bien différentes qu'un simple taux d'incohérence global mélangeait :
      a) `format` et `longueur` pointent vers la MÊME plage — aucun
         override n'a dû être utilisé ; si le comptage réel est hors de
         cette plage commune, c'est un vrai signal (dérive du LLM par
         rapport à la consigne, ou effet du bug du 3 août si articles
         générés avant cette date).
      b) `format` et `longueur` pointent vers des plages DIFFÉRENTES —
         un override de config a probablement été utilisé délibérément ;
         ce n'est PAS en soi un signe du bug, `longueur` (qui tient
         compte de l'override) fait foi, pas `format`.

Décision du 9 août : pas de correction rétroactive de toute façon — même
avec `format` disponible comme vérité terrain sur la catégorie
DÉFAUT de la thématique, on ne peut pas savoir a posteriori si un
override explicite avait été demandé pour un article donné (rien ne
l'enregistre séparément). Aucun script en aval ne consomme `longueur`
(seul `trace_injection.py` lit le frontmatter des articles, jamais ce
champ) — l'impact reste cosmétique. Ce script sert à mesurer précisément
l'ampleur du problème, pas à le corriger.

Usage :
    python3 audit_longueur_articles.py                  # dossier articles/ par défaut
    python3 audit_longueur_articles.py --dossier /chemin/vers/articles
"""
import argparse
import os
import re
from collections import Counter

# Même mapping que FORMAT_LONGUEUR dans prompt_builder.py — dupliqué ici
# en lecture seule à dessein (ce script vit hors du pipeline de
# génération), utilisé uniquement pour interpréter le champ `format`
# (nom de catégorie déjà connu, pas une reconstruction devinée).
FORMAT_LONGUEUR = {
    "utilitaire": (100, 200),
    "informatif": (150, 300),
    "breve":      (200, 400),
    "brève":      (200, 400),  # VALID_FORMATS (validate.py) accepte les deux orthographes
    "narratif":   (400, 700),
    "chronique":  (400, 700),
    "editorial":  (500, 800),
    "éditorial":  (500, 800),  # même remarque, cf. VALID_FORMATS
    "reflexif":   (500, 800),
    "réflexif":   (500, 800),  # idem
    "analyse":    (600, 900),
    "reportage":  (700, 1000),
}


def find_default_articles_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "articles")


def parse_frontmatter(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not m:
        return {}, content
    fm_text, body = m.group(1), m.group(2)
    fm = {}
    for line in fm_text.split("\n"):
        line = line.rstrip()
        if not line or line.startswith(" ") or line.startswith("-"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body


def count_words(body_text):
    words = re.findall(r"\b\w+\b", body_text, re.UNICODE)
    return len(words)


def parse_declared_range(label):
    """Extrait (lo, hi) depuis une chaîne du type "600 à 900 mots"."""
    m = re.match(r"^\s*(\d+)\s*à\s*(\d+)\s*mots?\s*$", label)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dossier", type=str, default=find_default_articles_dir(),
        help="Dossier articles/ à scanner (défaut : articles/ du vault courant)"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.dossier):
        print("Dossier introuvable : {}".format(args.dossier))
        print("Relance avec : python3 {} --dossier /chemin/vers/vault/articles".format(__file__))
        raise SystemExit(1)

    total = 0
    word_counts = []
    format_counter = Counter()
    scenario_counter = Counter()
    thematique_counter = Counter()

    # Cas A : format et longueur pointent vers la même plage (pas
    # d'override probable) — le vrai signal de qualité à surveiller.
    a_coherent = 0
    a_incoherent = 0
    a_exemples_incoherents = []

    # Cas B : format et longueur divergent — override probable,
    # informatif seulement, PAS un signe du bug.
    b_count = 0
    b_exemples = []

    # Cas restants : format absent/inconnu, ou longueur dans un format
    # non reconnu — ni A ni B, juste comptés à part.
    non_analysable = 0
    non_analysable_exemples = []

    # Récursif depuis le 10 août 2026 (fix save_article dans api.py) : les
    # articles générés en série/manuel sont désormais réellement rangés
    # dans articles/{scenario}/, plus seulement à la racine -- un scan à
    # plat (os.listdir) les aurait rendus invisibles à cet audit. Chemin
    # relatif au dossier scanné utilisé comme identifiant d'affichage,
    # pour distinguer un fichier de la racine d'un fichier de sous-dossier
    # en cas d'ambiguïté. Les fichiers d'index (_index.md, écrits par
    # generate_series.py/generate_manual.py) sont ignorés -- ce ne sont
    # pas des articles, inutile de les faire remonter en "non analysable".
    md_files = []
    for root, _dirs, files in os.walk(args.dossier):
        for f in sorted(files):
            if f.endswith(".md") and not f.startswith("_"):
                md_files.append(os.path.relpath(os.path.join(root, f), args.dossier))
    md_files.sort()

    for fname in md_files:
        filepath = os.path.join(args.dossier, fname)
        fm, body = parse_frontmatter(filepath)
        total += 1

        wc = count_words(body)
        word_counts.append(wc)

        format_cat = fm.get("format", "")
        longueur_label = fm.get("longueur", "")
        if format_cat:
            format_counter[format_cat] += 1
        scenario_counter[fm.get("scenario", "?")] += 1
        thematique_counter[fm.get("thematique", "?")] += 1

        format_bornes = FORMAT_LONGUEUR.get(format_cat)
        longueur_bornes = parse_declared_range(longueur_label) if longueur_label else None

        if format_bornes is None or longueur_bornes is None:
            non_analysable += 1
            non_analysable_exemples.append((fname, format_cat, longueur_label, wc))
            continue

        if format_bornes == longueur_bornes:
            # Cas A — même plage, aucun override probable
            lo, hi = format_bornes
            if lo <= wc <= hi:
                a_coherent += 1
            else:
                a_incoherent += 1
                a_exemples_incoherents.append((fname, format_cat, format_bornes, wc))
        else:
            # Cas B — divergence probablement due à un override délibéré
            b_count += 1
            b_exemples.append((fname, format_cat, format_bornes, longueur_label, longueur_bornes, wc))

    print("=" * 60)
    print("AUDIT longueur articles — {} fichiers scannés".format(total))
    print("=" * 60)
    print()

    if not total:
        print("Aucun article trouvé dans {}".format(args.dossier))
        return

    print("-- Statistiques de longueur réelle (comptage de mots du corps) --")
    print("  Min    : {}".format(min(word_counts)))
    print("  Max    : {}".format(max(word_counts)))
    print("  Moyenne: {:.0f}".format(sum(word_counts) / len(word_counts)))
    print()

    print("-- Distribution du format (catégorie de la thématique) --")
    for cat, count in format_counter.most_common():
        print("  {} : {}".format(cat, count))
    print()

    print("-- CAS A : format et longueur pointent vers la même plage --")
    print("   (pas d'override probable — le vrai signal de qualité)")
    print("  Cohérentes   : {}".format(a_coherent))
    print("  Incohérentes : {}".format(a_incoherent))
    if a_coherent + a_incoherent:
        taux = 100 * a_incoherent / (a_coherent + a_incoherent)
        print("  Taux d'incohérence réel (cas A uniquement) : {:.1f}%".format(taux))
    print()

    if a_exemples_incoherents:
        print("-- Détail cas A incohérentes (vrai signal, à examiner) --")
        for fname, cat, bornes, wc in a_exemples_incoherents:
            print("  {} : format='{}' (attendu {}-{} mots) — {} mots réels".format(
                fname, cat, bornes[0], bornes[1], wc))
        print()

    print("-- CAS B : format et longueur divergent (override probable) --")
    print("   ({} articles — informatif seulement, PAS un signe du bug)".format(b_count))
    if b_exemples:
        for fname, cat, fb, llabel, lb, wc in b_exemples:
            dans_plage = "✓" if lb[0] <= wc <= lb[1] else "✗"
            print("  {} : format='{}' ({}-{}) vs longueur déclarée '{}' ({}-{}) — {} mots réels [{}]".format(
                fname, cat, fb[0], fb[1], llabel, lb[0], lb[1], wc, dans_plage))
    print()

    if non_analysable:
        print("-- Non analysables (format ou longueur absent/non reconnu) : {} --".format(non_analysable))
        for fname, cat, llabel, wc in non_analysable_exemples:
            print("  {} : format='{}' longueur='{}' — {} mots réels".format(
                fname, cat or "(absent)", llabel or "(absent)", wc))
        print()

    print("-- Distribution par scénario --")
    for sc, count in scenario_counter.most_common():
        print("  {} : {}".format(sc, count))
    print()

    print("-- Distribution par thématique --")
    for th, count in thematique_counter.most_common():
        print("  {} : {}".format(th, count))


if __name__ == "__main__":
    main()
