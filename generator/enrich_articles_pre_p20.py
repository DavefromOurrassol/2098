#!/usr/bin/env python3
"""
enrich_articles_pre_p20.py — Ourrassol 2098
==============================================

Backlog Partie 1, point 12 (21 août 2026) : rattrape le frontmatter P20
complet sur les articles générés AVANT ce chantier (pas de champ `slug`
— c'est le marqueur de détection utilisé partout ailleurs dans le
projet, `rapprocher_articles.py` notamment). Portée : tout le corpus
pré-P20 en une fois (décision explicite de David, 21 août 2026).

TROIS NIVEAUX DE RÉCUPÉRATION, TRAITÉS DIFFÉREMMENT
------------------------------------------------------
1. MÉCANIQUE, sans appel LLM -- réutilise les fonctions déjà testées
   d'api.py (aucune duplication de logique) :
   - `slug`            ← _extract_title() + _slugify()
   - `journaliste_slug`← _extract_byline() + _slugify() (peut rester
                          vide -- même taux d'échec que P25 ailleurs,
                          non spécifique à ce script)
   - `date_evenement`/`date_publication` ← extraits du corps (la date
     apparaît déjà en clair, ex. "3 janvier 2098", juste sous le titre
     -- PAS reconstruits depuis le nom de fichier, dont le suffixe est
     translittéré sans accents et non fiable à re-décoder)
   - `a_une_photo: false`, `image_credit: ""` -- défauts, décisions
     manuelles par nature, rien à récupérer

2. APPROXIMATION, sans appel LLM -- décision explicite de David
   (tenter plutôt que laisser vide) :
   - `entites_citees` ← recoupement du corps de l'article contre le nom
     de chaque entité connue du scénario (instances/*_{scenario}.md,
     champ `name`) -- correspondance insensible à la casse, imparfaite
     par nature (une entité mentionnée sous une forme abrégée ou un
     surnom ne sera pas détectée), mais sans risque d'hallucination
     contrairement à une extraction par LLM.
   - `zone_principale` ← vote majoritaire sur `localisation.zone` des
     entités approximées ci-dessus (même principe que _dominant_zone()
     dans snapshot.py, appliqué après coup sur l'approximation plutôt
     que sur de vraies filtered_instances). Vide si aucune entité
     approximée n'a de zone renseignée.

3. LLM NÉCESSAIRE -- un seul appel par article, réutilise le même
   format de bloc que la génération normale (===METADONNEES_
   PUBLICATION===, voir _extract_publication_metadata() dans api.py,
   importée telle quelle, aucune divergence de format à maintenir) :
   - `chapo`, `tags` (bénéficie du vocabulaire déjà accumulé, voir
     _load_tags_suggeres() dans prompt_builder.py), `image_prompt`.

   ATTENTION -- ce niveau ne peut être vérifié qu'en conditions
   réelles, par David : aucun accès à un LLM configuré côté Claude au
   moment de l'écriture de ce script. Le flag --skip-llm permet de
   valider les niveaux 1 et 2 indépendamment, sans consommer de budget
   API ni dépendre d'une clé configurée, avant de lancer le rattrapage
   complet.

CE QUE CE SCRIPT NE FAIT PAS
------------------------------
- Ne touche jamais au texte de l'article lui-même (le corps entre le
  frontmatter et la fin, hors ajout de la section "Voir aussi").
- Ne traite pas les articles ayant déjà un `slug` (P20 natif) --
  `rapprocher_articles.py` s'en charge séparément.
- N'invente pas de zone/entités quand aucun recoupement n'est trouvé --
  laisse vide plutôt que d'halluciner via le LLM sur ces deux champs
  précis (seuls chapo/tags/image_prompt passent par le LLM).

USAGE
------
    # Aperçu des niveaux 1+2 (mécanique + approximation), sans LLM,
    # sans rien écrire -- à faire en premier pour juger la qualité de
    # l'approximation avant tout appel API :
    python3 enrich_articles_pre_p20.py --dry-run --skip-llm

    # ATTENTION -- --skip-llm est un outil de PRÉVISUALISATION,
    # toujours à combiner avec --dry-run. Ne JAMAIS le lancer pour de
    # vrai (sans --dry-run) comme "première passe" avant une seconde
    # passe complète plus tard : le premier passage écrirait un `slug`
    # sur chaque article traité, et le critère de détection de ce
    # script ("pas de slug = à traiter") exclurait alors ces articles
    # de tout passage ultérieur -- chapo/tags/image_prompt resteraient
    # vides DÉFINITIVEMENT, sans avertissement. Toujours aller
    # directement à la passe complète ci-dessous pour l'exécution
    # réelle, jamais en deux temps.

    # Aperçu de la passe complète (avec LLM, sur un petit lot d'abord
    # pour juger la qualité et le coût réel) :
    python3 enrich_articles_pre_p20.py --dry-run --scenario fortress_world --limit 3

    # Exécution réelle complète (comportement par défaut si --dry-run
    # est omis, cohérent avec fix_annee_debut_placeholder.py/
    # promote_ville.py/generate_images.py/rapprocher_articles.py) :
    python3 enrich_articles_pre_p20.py
    python3 enrich_articles_pre_p20.py --scenario fortress_world --limit 5
"""

import argparse
import re
import unicodedata
import yaml
from pathlib import Path
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from api import _extract_title, _extract_byline, _slugify, _extract_publication_metadata, _BYLINE_RE
from prompt_builder import _load_tags_suggeres

VAULT_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = VAULT_ROOT / "articles"
INSTANCES_DIR = VAULT_ROOT / "instances"

TASK_TIER = "strict"  # même tier que la génération normale (api.py)

DATE_LINE_RE = re.compile(
    r"(\d{1,2}\s+[a-zà-ÿ]+\s+\d{4})", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Index des entités connues par scénario (pour l'approximation)
# ---------------------------------------------------------------------------

def build_entity_index(scenario):
    """
    Retourne [(slug, name, zone_ou_None), ...] pour toutes les instances
    du scénario donné. Lecture directe des fichiers instances/*.md --
    pas besoin du pipeline de chargement complet (loader.py) pour un
    simple index nom/zone en lecture seule.
    """
    index = []
    if not INSTANCES_DIR.exists():
        return index
    suffix = "_{}.md".format(scenario)
    for filepath in sorted(INSTANCES_DIR.glob("*{}".format(suffix))):
        raw = filepath.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            continue
        slug = fm.get("slug") or filepath.stem
        name = fm.get("name") or ""
        zone = ((fm.get("localisation") or {}) or {}).get("zone")
        if name:
            index.append((slug, name, zone))
    return index


def approximate_entites_et_zone(article_body, entity_index):
    """
    Recoupe le corps de l'article contre l'index d'entités du scénario
    (correspondance insensible à la casse sur le champ `name`). Retourne
    (entites_citees_approx, zone_principale_approx).
    """
    body_lower = article_body.lower()
    matched = []
    for slug, name, zone in entity_index:
        # Le nom peut contenir un sous-titre après un tiret cadratin
        # ("Gelecek Meclisi — Les Échos du Demain") -- on cherche la
        # partie principale avant le tiret, plus significative pour la
        # correspondance qu'un sous-titre parfois absent du texte.
        nom_principal = name.split("—")[0].strip()
        if len(nom_principal) < 3:
            continue  # évite les faux positifs sur un nom trop court
        if nom_principal.lower() in body_lower:
            matched.append((slug, zone))

    entites_citees = [slug for slug, _ in matched]
    zones = [z for _, z in matched if z]
    zone_principale = ""
    if zones:
        counts = defaultdict(int)
        for z in zones:
            counts[z] += 1
        zone_principale = max(counts.items(), key=lambda x: (x[1], x[0]))[0]
    return entites_citees, zone_principale


# ---------------------------------------------------------------------------
# Extraction mécanique (date)
# ---------------------------------------------------------------------------

def extract_date_from_body(article_body):
    """Cherche une ligne de date en clair ("3 janvier 2098") dans les 8
    premières lignes non vides -- fiable, pas de reconstruction
    d'accents depuis un slug de nom de fichier. Vide si non trouvée."""
    head_lines = [l for l in article_body.split("\n") if l.strip()][:8]
    head = "\n".join(head_lines)
    m = DATE_LINE_RE.search(head)
    return m.group(1).strip() if m else ""


def extract_byline_with_tail_fallback(article_body):
    """
    Étend _extract_byline() (api.py, limitée aux 8 premières lignes --
    inchangée, utilisée telle quelle en génération live) d'un second
    essai sur les 5 DERNIÈRES lignes non vides du corps, spécifique à
    ce script de rattrapage.

    Justifié ici et pas en génération live : le pattern "signature
    repoussée en pied d'article, après un séparateur ---" est déjà
    documenté comme fréquent sur ce corpus (P25, backlog Partie 1 point
    10, ~25-33% observé) -- un second essai CIBLÉ sur la fin du texte
    couvre ce cas précis sans élargir la recherche à tout le corps
    (le risque de faux positif sur un tiret cadratin en dialogue/
    citation resterait entier si on scannait tout le texte plutôt que
    juste les extrémités).

    Retourne (nom, journal) ou (None, None) si non trouvé nulle part.
    """
    nom, journal = _extract_byline(article_body)
    if nom:
        return nom, journal

    tail_lines = [l for l in article_body.split("\n") if l.strip()][-5:]
    tail = "\n".join(tail_lines)
    m = _BYLINE_RE.search(tail)
    if not m:
        return None, None
    return m.group(1).strip(), m.group(2).strip()


# ---------------------------------------------------------------------------
# Appel LLM (niveau 3)
# ---------------------------------------------------------------------------

def call_llm_for_metadata(article_body, scenario, thematique):
    """
    Un seul appel, réutilise le même format de bloc que la génération
    normale (===METADONNEES_PUBLICATION===...) -- parsé ensuite par
    _extract_publication_metadata() importée d'api.py, aucune logique de
    parsing dupliquée pour chapo/tags/image_prompt. Retourne le dict meta
    (chapo/tags/image_prompt/journaliste), vide en cas d'échec (non
    bloquant, comme partout ailleurs dans le pipeline).

    JOURNALISTE (21 août 2026, soir) : 4e ligne ajoutée au bloc,
    spécifique à ce script -- remplace l'extraction mécanique par regex
    (extract_byline_with_tail_fallback()) qui ne sait pas distinguer un
    nom de personne d'un nom d'institution/lieu (ex. réel rencontré :
    "Bratislava Secteur Alpha" capté comme si c'était un nom de
    journaliste). Le LLM lit l'article complet et peut trancher
    sémantiquement -- problème de sens, pas de motif, donc pas
    résoluble par une règle mécanique supplémentaire. Coût marginal
    quasi nul : l'appel LLM est de toute façon déjà fait pour chapo/
    tags/image_prompt sur ce script (contrairement à la génération
    live, où cet appel "gratuit" n'existe pas -- extraction mécanique
    inchangée là-bas, voir api.py::_extract_byline()).
    """
    from llm_client import call_llm

    tags_suggeres = _load_tags_suggeres()
    tags_hint = ""
    if tags_suggeres:
        tags_hint = (" Réutilise en priorité un tag déjà existant si "
                     "pertinent, n'en invente un nouveau que si aucun ne "
                     "convient. Tags déjà existants : {}.".format(", ".join(tags_suggeres)))

    system_prompt = (
        "Tu es un assistant éditorial qui complète des métadonnées "
        "manquantes pour un article déjà publié et jamais modifié -- tu "
        "ne réécris jamais le texte, tu le lis seulement pour en tirer "
        "les métadonnées demandées."
    )
    user_prompt = (
        "Voici un article déjà publié (scénario : {}, rubrique : {}). "
        "Lis-le et produis UNIQUEMENT le bloc suivant, rien d'autre, "
        "aucun texte avant ou après :\n\n"
        "===METADONNEES_PUBLICATION===\n"
        "CHAPO: [résumé de 2 à 3 lignes de l'article, pour une page de liste d'articles]\n"
        "TAGS: [3 à 5 mots-clés séparés par des virgules, orientés recherche lecteur, distincts de la rubrique.{}]\n"
        "IMAGE_PROMPT: [description visuelle en une phrase -- SI l'article porte principalement sur une personne, une entité ou un lieu nommé précis, l'image doit le représenter explicitement (nom/rôle mentionné) ; SINON, décris la scène de façon neutre -- lieu, ambiance, éléments clés]\n"
        "JOURNALISTE: [le prénom et nom de la PERSONNE qui signe cet article, UNIQUEMENT s'il s'agit du nom d'un individu -- PAS un nom de média, d'organisation, de lieu ou de section. Laisse ce champ vide si la signature est un nom d'organisation/média, ou si aucune signature n'est identifiable dans le texte]\n"
        "===FIN_METADONNEES===\n\n"
        "Article :\n{}"
    ).format(scenario, thematique, tags_hint, article_body)

    try:
        response = call_llm(system_prompt=system_prompt, user_prompt=user_prompt,
                             max_tokens=500, temperature=0.7, task_tier=TASK_TIER)
    except Exception as e:
        print("  [WARN] Appel LLM échoué : {}".format(e))
        return {"chapo": "", "tags": [], "image_prompt": "", "journaliste": ""}

    _, meta = _extract_publication_metadata(response)
    # JOURNALISTE : 4e champ, non géré par _extract_publication_metadata()
    # (fonction partagée avec la génération live, qui n'a pas ce champ --
    # voir docstring ci-dessus). Parsing dédié sur la réponse brute,
    # même bloc, avant que _extract_publication_metadata() ne le retire.
    m = re.search(r"^JOURNALISTE:[ \t]*(.+)$", response, re.MULTILINE | re.IGNORECASE)
    meta["journaliste"] = m.group(1).strip() if m else ""
    return meta


# ---------------------------------------------------------------------------
# Découverte et patch des articles
# ---------------------------------------------------------------------------

def parse_md(filepath):
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
    Parcourt TOUS les .md exploitables sous articles/ -- à la racine
    ET dans les sous-dossiers par scénario. Correctif du 21 août 2026
    (soir) : une partie du corpus historique a été générée avec
    config["output"]["dossier"] pointant vers la racine de articles/
    plutôt qu'un sous-dossier par scénario (convention différente avant
    un certain point) -- ne balayer que articles/*/*.md ratait
    silencieusement ces fichiers. _index.md exclu partout.
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


def find_pre_p20_articles(scenario_filter=None, limit=None):
    articles = []
    for filepath in _iter_all_article_files():
        fm, prefix, fm_block, marker, body = parse_md(filepath)
        if fm.get("slug"):
            continue  # déjà P20, hors scope de ce script
        # Scénario lu depuis le frontmatter (toujours présent, ancien
        # comme nouveau format) -- pas depuis l'emplacement du fichier,
        # qui n'est pas fiable (voir _iter_all_article_files()).
        scenario = fm.get("scenario")
        if not scenario:
            continue  # frontmatter incomplet/illisible, hors scope
        if scenario_filter and scenario != scenario_filter:
            continue
        articles.append({
            "filepath": filepath, "scenario": scenario,
            "fm": fm, "prefix": prefix, "fm_block": fm_block,
            "marker": marker, "body": body,
        })
        if limit and len(articles) >= limit:
            return articles
    return articles


def build_new_fields_block(article, entity_index, skip_llm, used_slugs):
    body = article["body"]
    fm = article["fm"]

    titre = _extract_title(body)
    slug = _slugify(titre)[:80].strip("_") or "article-sans-titre"

    # Déduplication (21 août 2026, soir) : sur un lot réel de 56
    # articles pré-P20, deux titres identiques ("Bruxelles-Forteresse,
    # 12 octobre 2098") ont produit le même slug -- cause racine :
    # _extract_title() retombe sur la première ligne non vide quand
    # aucune ligne en gras n'est trouvée (articles antérieurs à la
    # convention "titre toujours en gras"), et cette ligne de repli est
    # parfois une dateline plutôt qu'un vrai titre. Plutôt que de
    # deviner un meilleur titre, désambiguïsation mécanique : suffixe
    # numérique incrémental sur collision, garantit l'unicité sans
    # halluciner un contenu qui n'existe pas.
    base_slug = slug
    n = 2
    while slug in used_slugs:
        slug = "{}-{}".format(base_slug, n)
        n += 1
    used_slugs.add(slug)

    nom, _ = extract_byline_with_tail_fallback(body)
    if nom:
        # Préfixe "Par"/"par" parfois capturé avec le nom par le regex de
        # signature (ex. "Par Elias Mwangi — Journal") -- retiré avant
        # slugification. Découvert le 21 août 2026 (soir) sur un lot de
        # 56 articles pré-P20 réels.
        nom = re.sub(r"^(par|by)\s+", "", nom, flags=re.IGNORECASE).strip()

    date = extract_date_from_body(body)

    entites_citees, zone_principale = approximate_entites_et_zone(body, entity_index)

    if skip_llm:
        # Pas d'appel LLM dans ce mode -- repli sur l'extraction
        # mécanique (regex) déjà calculée ci-dessus. Connue pour
        # confondre parfois un nom d'institution/lieu avec un nom de
        # personne (voir docstring de call_llm_for_metadata()) --
        # limite acceptée pour ce mode aperçu, corrigée par le LLM dans
        # la passe complète ci-dessous.
        meta = {"chapo": "", "tags": [], "image_prompt": "", "journaliste": ""}
        journaliste_slug = _slugify(nom) if nom else ""
    else:
        # Passe complète : le LLM déjà appelé pour chapo/tags/
        # image_prompt tranche aussi journaliste -- meilleur juge qu'un
        # regex pour distinguer un nom de personne d'un nom
        # d'institution (problème de sens, pas de motif). Remplace
        # entièrement l'extraction mécanique ci-dessus dans ce mode --
        # ne pas mélanger les deux sources pour un même champ.
        meta = call_llm_for_metadata(body, article["scenario"], fm.get("thematique", ""))
        journaliste_slug = _slugify(meta["journaliste"]) if meta.get("journaliste") else ""

    return {
        "slug": slug, "chapo": meta["chapo"], "tags": meta["tags"],
        "image_prompt": meta["image_prompt"], "journaliste_slug": journaliste_slug,
        "date_evenement": date, "date_publication": date,
        "zone_principale": zone_principale, "entites_citees": entites_citees,
    }


def patch_article(article, fields, dry_run):
    filepath = article["filepath"]

    lines = [
        "slug: {}".format(fields["slug"]),
        "chapo: \"{}\"".format((fields["chapo"] or "").replace('"', '\\"')),
        "tags:",
    ]
    for t in fields["tags"]:
        lines.append("  - {}".format(t))
    lines += [
        "image_prompt: \"{}\"".format((fields["image_prompt"] or "").replace('"', '\\"')),
        "a_une_photo: false",
        "image_credit: \"\"",
        "journaliste_slug: {}".format(fields["journaliste_slug"]),
        "date_evenement: {}".format(fields["date_evenement"]),
        "zone_principale: {}".format(fields["zone_principale"]),
        "date_publication: {}".format(fields["date_publication"]),
        "entites_citees:",
    ]
    for e in fields["entites_citees"]:
        lines.append("  - {}".format(e))
    new_block = "\n".join(lines)

    voir_aussi = ""
    if fields["entites_citees"]:
        liens = " · ".join("[[{}]]".format(s) for s in fields["entites_citees"])
        voir_aussi = "\n\n---\n**Voir aussi** : {}\n".format(liens)

    if dry_run:
        print("  [DRY] {}".format(filepath.name))
        print("        slug={}".format(fields["slug"]))
        print("        entites={} zone={} journaliste={} date={}".format(
            len(fields["entites_citees"]), fields["zone_principale"] or "(vide)",
            fields["journaliste_slug"] or "(vide)", fields["date_evenement"] or "(vide)"))
        print("        chapo        : {}".format(fields["chapo"] or "(vide)"))
        print("        tags         : {}".format(", ".join(fields["tags"]) if fields["tags"] else "(vide)"))
        print("        image_prompt : {}".format(fields["image_prompt"] or "(vide)"))
        print()
        return

    new_fm_block = article["fm_block"].rstrip("\n") + "\n" + new_block + "\n"
    new_content = "{}{}{}{}{}".format(
        article["prefix"], new_fm_block, article["marker"], article["body"].rstrip("\n"), voir_aussi
    )
    filepath.write_text(new_content, encoding="utf-8")
    print("  [OK] {} -- slug={}".format(filepath.name, fields["slug"]))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def reorganize_articles(dry_run):
    """
    Déplace les articles posés à la racine de articles/ vers leur
    sous-dossier par scénario (fm["scenario"]), en créant le dossier si
    besoin. Ne touche qu'au CHEMIN du fichier, jamais à son contenu.
    Vérifie l'absence de collision avant tout déplacement -- refuse de
    déplacer si un fichier de même nom existe déjà à destination
    (signal une vraie collision à traiter à la main plutôt que
    d'écraser silencieusement).
    """
    import shutil
    moved, skipped = 0, 0
    for filepath in sorted(ARTICLES_DIR.glob("*.md")):
        if filepath.name == "_index.md":
            continue
        fm, _, _, _, _ = parse_md(filepath)
        scenario = fm.get("scenario")
        if not scenario:
            print("  [SKIP] {} -- pas de champ scenario, ne peut pas être classé.".format(filepath.name))
            skipped += 1
            continue
        dest_dir = ARTICLES_DIR / scenario
        dest = dest_dir / filepath.name
        if dest.exists():
            print("  [SKIP] {} -- collision, un fichier du même nom existe déjà dans {}/.".format(
                filepath.name, scenario))
            skipped += 1
            continue
        if dry_run:
            print("  [DRY] {} -- déplacerait vers {}/{}".format(filepath.name, scenario, filepath.name))
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(filepath), str(dest))
            print("  [OK] {} -- déplacé vers {}/".format(filepath.name, scenario))
        moved += 1
    print("\n{} fichier(s) {} , {} ignoré(s) (collision ou scenario manquant).".format(
        moved, "à déplacer" if dry_run else "déplacé(s)", skipped))


def retry_empty_date(dry_run, scenario_filter=None):
    """
    Retente UNIQUEMENT date_evenement/date_publication sur les articles
    déjà slugifiés dont la date est restée vide -- purement mécanique
    (extract_date_from_body(), pas d'appel LLM), donc gratuit et rapide.
    Utile après un élargissement du regex de date (comme celui du 21
    août 2026, soir, qui a débloqué le format "Lieu — Date" combiné) --
    permet de rattraper les articles traités AVANT le correctif sans
    tout retraiter (chapo/tags/entites déjà bons restent intacts).
    """
    targets = []
    for filepath in _iter_all_article_files():
        fm, prefix, fm_block, marker, body = parse_md(filepath)
        if not fm.get("slug") or fm.get("date_evenement"):
            continue
        if scenario_filter and fm.get("scenario") != scenario_filter:
            continue
        targets.append({"filepath": filepath, "prefix": prefix,
                         "fm_block": fm_block, "marker": marker, "body": body})

    print("{} article(s) avec date vide à retenter.\n".format(len(targets)))
    trouvees = 0
    for article in targets:
        date = extract_date_from_body(article["body"])
        if dry_run:
            print("  [DRY] {} -- date={}".format(article["filepath"].name, date or "(toujours vide)"))
            if date:
                trouvees += 1
            continue

        if not date:
            print("  [SKIP] {} -- toujours introuvable.".format(article["filepath"].name))
            continue

        new_fm_block = re.sub(r'(?m)^date_evenement:.*$', "date_evenement: {}".format(date), article["fm_block"], count=1)
        new_fm_block = re.sub(r'(?m)^date_publication:.*$', "date_publication: {}".format(date), new_fm_block, count=1)
        new_content = "{}{}{}{}".format(article["prefix"], new_fm_block, article["marker"], article["body"])
        article["filepath"].write_text(new_content, encoding="utf-8")
        print("  [OK] {} -- date={}".format(article["filepath"].name, date))
        trouvees += 1

    print("\n{}/{} date(s) {}.".format(
        trouvees, len(targets), "trouvables" if dry_run else "corrigée(s)"))


def retry_empty_chapo(dry_run, scenario_filter=None):
    """
    Retente UNIQUEMENT chapo/tags/image_prompt/journaliste_slug sur les
    articles déjà slugifiés dont chapo est resté vide (échec du bloc
    métadonnées lors d'un run précédent) -- slug/date/entites_citees/
    zone_principale déjà corrects, jamais retouchés ici.
    """
    targets = []
    for filepath in _iter_all_article_files():
        fm, prefix, fm_block, marker, body = parse_md(filepath)
        if not fm.get("slug") or fm.get("chapo"):
            continue
        scenario = fm.get("scenario")
        if scenario_filter and scenario != scenario_filter:
            continue
        targets.append({"filepath": filepath, "fm": fm, "prefix": prefix,
                         "fm_block": fm_block, "marker": marker, "body": body,
                         "scenario": scenario})

    print("{} article(s) avec chapo vide à retenter.\n".format(len(targets)))
    for article in targets:
        meta = call_llm_for_metadata(article["body"], article["scenario"], article["fm"].get("thematique", ""))
        if dry_run:
            print("  [DRY] {} -- chapo={}".format(
                article["filepath"].name, "OK" if meta["chapo"] else "toujours vide"))
            continue

        new_lines = [
            'chapo: "{}"'.format((meta["chapo"] or "").replace('"', '\\"')),
            "tags:",
        ]
        for t in meta["tags"]:
            new_lines.append("  - {}".format(t))
        new_fm_block = re.sub(r'(?m)^chapo:.*$', new_lines[0], article["fm_block"], count=1)
        new_fm_block = re.sub(r'(?m)^tags:(?:\n  - .+)*', "\n".join(new_lines[1:]), new_fm_block, count=1)
        new_fm_block = re.sub(
            r'(?m)^image_prompt:.*$',
            'image_prompt: "{}"'.format((meta["image_prompt"] or "").replace('"', '\\"')),
            new_fm_block, count=1
        )
        if meta.get("journaliste") and not article["fm"].get("journaliste_slug"):
            new_fm_block = re.sub(
                r'(?m)^journaliste_slug:.*$',
                "journaliste_slug: {}".format(_slugify(meta["journaliste"])),
                new_fm_block, count=1
            )

        new_content = "{}{}{}{}".format(article["prefix"], new_fm_block, article["marker"], article["body"])
        article["filepath"].write_text(new_content, encoding="utf-8")
        print("  [OK] {} -- chapo={}".format(
            article["filepath"].name, "rempli" if meta["chapo"] else "toujours vide"))


def run_audit(scenario_filter=None):
    """
    Mode diagnostic (21 août 2026, soir) -- balaie TOUS les articles déjà
    slugifiés (natifs P20 ou rattrapés par ce script) et rapporte trois
    points de propreté distincts, demandés par David après le rattrapage
    complet du corpus historique :
    1. Rangement : racine de articles/ vs sous-dossier par scénario.
    2. date_evenement encore vide malgré le rattrapage.
    3. chapo vide (échec du bloc métadonnées LLM, à retenter).
    Purement en lecture, n'écrit jamais rien.
    """
    a_la_racine, dates_vides, chapo_vides = [], [], []
    for filepath in _iter_all_article_files():
        fm, _, _, _, _ = parse_md(filepath)
        if not fm.get("slug"):
            continue  # pas encore P20 du tout, hors scope de cet audit
        if scenario_filter and fm.get("scenario") != scenario_filter:
            continue
        if filepath.parent == ARTICLES_DIR:
            a_la_racine.append((filepath, fm.get("scenario", "?")))
        if not fm.get("date_evenement"):
            dates_vides.append(filepath)
        if not fm.get("chapo"):
            chapo_vides.append(filepath)

    print("=" * 60)
    print("-- Audit propreté (articles déjà slugifiés) --")
    print("=" * 60)
    print("\n1. À la racine de articles/ (devraient être dans un sous-dossier "
          "par scénario) : {}".format(len(a_la_racine)))
    for fp, scenario in a_la_racine:
        print("     {} (scenario: {})".format(fp.name, scenario))

    print("\n2. date_evenement vide : {}".format(len(dates_vides)))
    for fp in dates_vides:
        print("     {}".format(fp.name))

    print("\n3. chapo vide (échec bloc métadonnées, à retenter) : {}".format(len(chapo_vides)))
    for fp in chapo_vides:
        print("     {}".format(fp.name))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-llm", action="store_true",
                         help="Niveaux 1+2 seulement (mécanique + approximation), "
                              "aucun appel LLM, aucun coût API. À COMBINER AVEC "
                              "--dry-run (prévisualisation uniquement) -- lancé pour "
                              "de vrai seul, exclurait ces articles de tout passage "
                              "ultérieur avant que chapo/tags/image_prompt soient "
                              "remplis (voir docstring du module).")
    parser.add_argument("--audit", action="store_true",
                         help="Diagnostic pur (aucune écriture) : rangement racine/"
                              "sous-dossier, date_evenement vide, chapo vide sur tous "
                              "les articles déjà slugifiés.")
    parser.add_argument("--reorganize", action="store_true",
                         help="Déplace les articles à la racine de articles/ vers "
                              "leur sous-dossier par scénario (lu en frontmatter). "
                              "Combiner avec --dry-run pour prévisualiser.")
    parser.add_argument("--retry-empty-date", action="store_true",
                         help="Retente uniquement date_evenement/date_publication sur "
                              "les articles déjà slugifiés dont la date est restée "
                              "vide -- mécanique, pas d'appel LLM, gratuit.")
    parser.add_argument("--retry-empty-chapo", action="store_true",
                         help="Retente chapo/tags/image_prompt/journaliste_slug "
                              "uniquement sur les articles déjà slugifiés dont chapo "
                              "est resté vide. Combiner avec --dry-run pour "
                              "prévisualiser (l'appel LLM a quand même lieu en "
                              "dry-run, comme le reste du script, pour permettre de "
                              "juger le résultat avant d'écrire).")
    args = parser.parse_args()

    if args.audit:
        run_audit(scenario_filter=args.scenario)
        return

    if args.reorganize:
        reorganize_articles(dry_run=args.dry_run)
        return

    if args.retry_empty_date:
        retry_empty_date(dry_run=args.dry_run, scenario_filter=args.scenario)
        return

    if args.retry_empty_chapo:
        retry_empty_chapo(dry_run=args.dry_run, scenario_filter=args.scenario)
        return

    if args.skip_llm and not args.dry_run:
        print("[ERREUR] --skip-llm sans --dry-run refusé : lancé pour de vrai, "
              "ça écrirait un slug sur chaque article traité, qui serait ensuite "
              "exclu de tout passage ultérieur avant que chapo/tags/image_prompt "
              "soient jamais remplis (voir docstring du module, section USAGE). "
              "Utilise --dry-run --skip-llm pour prévisualiser, puis lance la "
              "passe complète (sans --skip-llm) pour l'exécution réelle.")
        return

    articles = find_pre_p20_articles(scenario_filter=args.scenario, limit=args.limit)
    print("enrich_articles_pre_p20.py — mode {}{}".format(
        "DRY-RUN" if args.dry_run else "EXECUTE",
        " (--skip-llm)" if args.skip_llm else ""))
    print("{} article(s) pré-P20 trouvé(s){}.\n".format(
        len(articles), " pour {}".format(args.scenario) if args.scenario else ""))

    if not articles:
        print("Rien à traiter.")
        return

    # Amorce used_slugs avec les slugs déjà en usage sur les articles
    # DÉJÀ P20 (pas seulement entre les 56 articles de ce lot) -- évite
    # qu'un slug nouvellement rattrapé entre en collision avec un
    # article natif P20 existant.
    used_slugs = set()
    for filepath in _iter_all_article_files():
        fm, _, _, _, _ = parse_md(filepath)
        if fm.get("slug"):
            used_slugs.add(fm["slug"])

    entity_index_cache = {}
    for article in articles:
        scenario = article["scenario"]
        if scenario not in entity_index_cache:
            entity_index_cache[scenario] = build_entity_index(scenario)
        fields = build_new_fields_block(article, entity_index_cache[scenario],
                                         skip_llm=args.skip_llm, used_slugs=used_slugs)
        patch_article(article, fields, dry_run=args.dry_run)

    if args.dry_run:
        print("\n[DRY-RUN] Aucune modification effectuée.")


if __name__ == "__main__":
    main()
