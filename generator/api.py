"""
api.py
------
Envoie le prompt au LLM configuré et sauvegarde l'article généré.

Reçoit :
  - prompt_data : dict construit par prompt_builder.py
  - snapshot    : dict construit par snapshot.py
  - config      : dict depuis config.yaml

Retourne :
  - article     : str — texte de l'article généré
  - filepath    : str — chemin du fichier .md sauvegardé

Fournisseur actif : résolu via le tier "strict" (llm_client.TASK_TIER_DEFAULTS),
sauf override manuel LLM_PROVIDER/LLM_MODEL.
"""

import os
import re
import json
import unicodedata
from datetime import datetime

from llm_client import call_llm, resolve_for_tier
from loader import VAULT_PATH


# ─────────────────────────────────────────
# CONFIGURATION API
# ─────────────────────────────────────────

MAX_TOKENS    = 4000
TEMPERATURE   = 1.0   # Créativité maximale pour la rédaction

# Tier LLM pour la rédaction d'articles : identité journal + journaliste
# imposée sur une sortie longue et créative — voir llm_client.TASK_TIER_DEFAULTS.
TASK_TIER     = "strict"

# Dossier de sortie des articles
ARTICLES_DIR  = os.path.join(VAULT_PATH, "articles")

# ── Retry sur longueur hors plage (ajouté le 10 août 2026) ──
# Décision explicite avec David (chantier "dérive du LLM sur la longueur
# réelle des articles", backlog Partie 1 point 1) : le renforcement du
# prompt seul (contrainte répétée en fin de consigne) n'a pas suffi --
# taux d'incohérence mesuré à 94,4% sur un batch de test post-renforcement,
# avec un biais systématique vers le dépassement. Un seul seuil de
# déclenchement : écart <= 40% de la borne dépassée = accepté tel quel,
# pas de retry. Au-delà, UN SEUL retry, avec rappel explicite de l'écart
# mesuré (pas juste "recommence"). Pas de nouvelle vérification après le
# retry -- le résultat du 2e essai est accepté quoi qu'il arrive, pour
# borner le coût/temps (chaque retry double le temps de génération pour
# l'article concerné).
RETRY_DEVIATION_THRESHOLD = 0.40


# ─────────────────────────────────────────
# VALIDATION LONGUEUR
# ─────────────────────────────────────────

def _parse_longueur_bornes(longueur_label):
    """Extrait (lo, hi) depuis une chaîne du type "600 à 900 mots".
    Retourne None si le format n'est pas reconnu (pas de crash --
    dégradation silencieuse, pas de retry possible dans ce cas)."""
    m = re.match(r"^\s*(\d+)\s*à\s*(\d+)\s*mots?\s*$", longueur_label or "")
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _count_words(text):
    """Même méthode de comptage que audit_longueur_articles.py, pour que
    la mesure faite ici et celle de l'audit externe restent comparables."""
    return len(re.findall(r"\b\w+\b", text, re.UNICODE))


def _deviation_ratio(wc, bornes):
    """Écart relatif à la borne violée (0.0 si dans la plage). Ex. :
    900 mots pour une plage 600-900 -> 0.0 (dans la plage, borne incluse).
    1200 mots pour 600-900 -> (1200-900)/900 = 0.333 (33,3% au-dessus de
    la borne haute)."""
    lo, hi = bornes
    if wc < lo:
        return (lo - wc) / lo
    if wc > hi:
        return (wc - hi) / hi
    return 0.0


def _retry_with_length_feedback(prompt_data, wc_precedent, bornes):
    """Un seul nouvel appel LLM, avec la consigne de longueur d'origine
    ré-augmentée d'un rappel explicite et chiffré de l'écart mesuré --
    plus efficace qu'un simple "recommence", cf. décision du 10 août."""
    lo, hi = bornes
    if wc_precedent > hi:
        ecart_pct = round(100 * (wc_precedent - hi) / hi)
        consigne_ecart = (
            "Ta précédente tentative faisait {} mots, soit {}% de trop par rapport "
            "à la borne haute ({} mots). Coupe le texte pour rester entre {} et {} "
            "mots cette fois.".format(wc_precedent, ecart_pct, hi, lo, hi)
        )
    else:
        ecart_pct = round(100 * (lo - wc_precedent) / lo)
        consigne_ecart = (
            "Ta précédente tentative faisait seulement {} mots, soit {}% de moins "
            "que la borne basse ({} mots). Développe davantage le sujet pour "
            "atteindre entre {} et {} mots cette fois.".format(
                wc_precedent, ecart_pct, lo, lo, hi)
        )

    retry_user_prompt = (
        prompt_data["user_prompt"]
        + "\n\n---\n\n"
        + "RETRY — CONSIGNE DE LONGUEUR NON RESPECTÉE AU PREMIER ESSAI\n"
        + consigne_ecart
        + " Réécris l'article en entier depuis le titre (même sujet, même angle, "
          "mêmes contraintes ci-dessus), en respectant cette fois strictement la "
          "longueur demandée."
    )

    print("[api] Longueur hors plage ({} mots, attendu {}-{}, écart {:.0%}) "
          "— retry unique avec rappel explicite...".format(
              wc_precedent, lo, hi, _deviation_ratio(wc_precedent, bornes)))

    article_retry = call_llm(
        system_prompt=prompt_data["system_prompt"],
        user_prompt=retry_user_prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        task_tier=TASK_TIER,
    )
    # P20 (21 août 2026) : le retry réutilise prompt_data["user_prompt"]
    # en entier (voir retry_user_prompt ci-dessus), qui contient déjà la
    # consigne du bloc métadonnées -- extraction nécessaire ici aussi,
    # AVANT le comptage de mots, sinon le bloc fausserait wc_retry.
    # type_diffusion (P21, 25 août 2026) lu depuis prompt_data["metadata"]
    # -- déjà présent dans ce dict, pas de paramètre supplémentaire à
    # faire remonter jusqu'ici.
    type_diffusion = prompt_data.get("metadata", {}).get("type_diffusion", "ecrit")
    article_retry, meta_retry = _extract_publication_metadata(article_retry, type_diffusion)
    wc_retry = _count_words(article_retry)
    print("[api] Retry terminé : {} mots (attendu {}-{}).".format(wc_retry, lo, hi))
    return article_retry, wc_retry, meta_retry


# ─────────────────────────────────────────
# APPEL API
# ─────────────────────────────────────────

# ─────────────────────────────────────────
# P20 (21 août 2026) — MÉTADONNÉES DE PUBLICATION
# ─────────────────────────────────────────
# Phase A du scoping du 12 juillet 2026 (backlog point 7) : enrichir le
# frontmatter des articles pour anticiper une future publication web,
# sans retraiter des centaines de fichiers a posteriori. Toutes les
# fonctions ci-dessous sont non bloquantes par construction -- un champ
# manquant ou mal formé ne fait jamais échouer la génération/sauvegarde
# de l'article, il reste juste vide dans le frontmatter (même philosophie
# que _parse_longueur_bornes plus haut : dégradation silencieuse).

def _slugify(text):
    """Identique à create_entity.py/create_entities_and_instances.py
    (NFD + suppression des marques diacritiques plutôt qu'une table
    d'accents français en dur -- correctif du 14 août 2026 sur les slugs
    portugais cassés, voir audit_broken_slugs.py). Dupliqué ici à dessein
    -- api.py n'importe aucun de ces scripts pour cette seule fonction
    utilitaire."""
    s = unicodedata.normalize("NFD", text or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def _yaml_escape(text):
    """Échappement minimal pour insérer du texte libre (deux-points,
    guillemets) dans une ligne 'clé: valeur' du frontmatter construit à
    la main par build_article_md() -- pas de dumper YAML ici. Les champs
    existants avant P20 sont tous des valeurs contrôlées (slugs, enums,
    nombres) ; chapo/image_prompt sont les premiers à contenir du texte
    libre potentiellement problématique pour un parseur YAML naïf (ex.
    un chapo contenant ':' casserait 'chapo: Nuuk : la tension monte'
    sans cet échappement)."""
    escaped = (text or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return '"{}"'.format(escaped)


_PUBLICATION_META_RE = re.compile(
    r"===METADONNEES_PUBLICATION===\s*(.*?)\s*===FIN_METADONNEES===",
    re.DOTALL | re.IGNORECASE
)


def _extract_publication_metadata(article_text, type_diffusion="ecrit"):
    """
    Extrait et retire le bloc métadonnées de publication ajouté en fin de
    réponse par la consigne de build_journalistic_brief() (chapo, tags,
    image_prompt -- produits par le LLM dans le MÊME appel que l'article,
    Option 1 actée le 12 juillet 2026).

    type_diffusion (P21, 25 août 2026) : si "oral", deux champs
    supplémentaires sont attendus dans le même bloc --
    LIEU_DIFFUSION/MODE_RECEPTION (consigne ajoutée le 25 août dans
    build_journalistic_brief(), jamais demandée pour un article écrit --
    donc jamais recherchée ici non plus dans ce cas, pas de faux
    avertissement "champ manquant" sur un champ qui n'a jamais été
    sollicité).

    Retourne (article_sans_bloc, meta_dict). meta_dict contient toujours
    les 3 clés (chapo, tags, image_prompt), vides/liste vide si absentes
    ou non parsables — plus lieu_diffusion/mode_reception si oral. Le
    bloc est TOUJOURS retiré du texte s'il est trouvé, même si son
    contenu interne ne parse pas -- pour ne jamais laisser le marqueur
    dans l'article publié ni fausser le comptage de mots (voir
    generate_article() : cette extraction a lieu AVANT _count_words(),
    sinon le bloc fausserait la mesure de longueur et le déclenchement
    du retry, chantier du 10 août 2026).
    """
    meta = {"chapo": "", "tags": [], "image_prompt": ""}
    if type_diffusion == "oral":
        meta["lieu_diffusion"] = ""
        meta["mode_reception"] = ""

    m = _PUBLICATION_META_RE.search(article_text)
    if not m:
        print("[api] [WARN] Bloc ===METADONNEES_PUBLICATION=== absent de la "
              "réponse du LLM — chapo/tags/image_prompt resteront vides "
              "pour cet article.")
        return article_text.strip(), meta

    block = m.group(1)
    clean_text = (article_text[:m.start()] + article_text[m.end():]).rstrip()

    # Correctif du 21 août 2026 (soir) : re.IGNORECASE ajouté après un
    # cas réel sur enrich_articles_pre_p20.py où le bloc externe
    # ===METADONNEES_PUBLICATION=== était bien trouvé (déjà en
    # IGNORECASE) mais aucune des 3 lignes internes ne matchait --
    # signe que le LLM avait probablement répondu en "Chapo:"/"chapo:"
    # plutôt que "CHAPO:" strict. Correctif défensif, sans risque de
    # régression (strictement plus permissif qu'avant) -- profite aussi
    # bien à ce script qu'à la génération live, qui partage cette même
    # fonction.
    chapo_m = re.search(r"^CHAPO:\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
    tags_m  = re.search(r"^TAGS:\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
    img_m   = re.search(r"^IMAGE_PROMPT:\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)

    if chapo_m:
        meta["chapo"] = chapo_m.group(1).strip()
    if tags_m:
        meta["tags"] = [t.strip() for t in tags_m.group(1).split(",") if t.strip()]
    if img_m:
        meta["image_prompt"] = img_m.group(1).strip()

    champs_attendus_ok = chapo_m and tags_m and img_m

    if type_diffusion == "oral":
        lieu_m = re.search(r"^LIEU_DIFFUSION:\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
        mode_m = re.search(r"^MODE_RECEPTION:\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
        if lieu_m:
            meta["lieu_diffusion"] = lieu_m.group(1).strip()
        if mode_m:
            meta["mode_reception"] = mode_m.group(1).strip()
        champs_attendus_ok = champs_attendus_ok and lieu_m and mode_m

    if not champs_attendus_ok:
        print("[api] [WARN] Bloc métadonnées trouvé mais incomplet "
              "(chapo={}, tags={}, image_prompt={}{}) — champ(s) manquant(s) "
              "laissé(s) vide(s).".format(
                  bool(chapo_m), bool(tags_m), bool(img_m),
                  ", lieu_diffusion={}, mode_reception={}".format(
                      bool(lieu_m), bool(mode_m)
                  ) if type_diffusion == "oral" else ""
              ))

    return clean_text, meta


_BYLINE_RE = re.compile(
    r"^\*{0,2}([A-ZÀ-Ý][\w'’\-]+(?:\s+[A-ZÀ-Ý][\w'’\-]+)+)\s+—\s+(.+?)\*{0,2}$",
    re.MULTILINE
)


def _extract_byline(article_text):
    """
    Extrait le nom du·de la journaliste depuis la signature "Prénom Nom —
    Journal" du corps de l'article -- position garantie immédiatement
    sous la date de publication depuis le correctif du 10 août 2026
    (build_system_prompt()). Recherche restreinte aux 8 premières lignes
    non vides pour éviter tout faux positif sur un tiret cadratin
    ailleurs dans le texte (citation, dialogue, ou le dateline en début
    de premier paragraphe type "NUUK-FORTE — Le 18 avril...", exclu
    naturellement par l'exigence d'au moins 2 mots capitalisés avant le
    tiret -- un dateline est presque toujours un seul mot/lieu composé).

    Tolère un habillage Markdown gras optionnel autour de la ligne
    entière ("**Nom — Journal**") -- corrigé le 21 août 2026 après un
    test réel sur 8 articles (fortress_world) : 1 cas sur 8 utilisait ce
    format, non prévu par la version initiale de cette regex, qui exigeait
    que la ligne commence directement par une lettre majuscule.

    Retourne (nom, nom_journal) ou (None, None) si non trouvé -- non
    bloquant, journaliste_slug reste vide dans ce cas plutôt que de
    faire échouer la sauvegarde de l'article. Cas réel observé le 21 août
    2026 : sur 8 articles test, 2 n'avaient tout simplement AUCUNE
    signature dans le corps généré (pas un problème d'extraction, la
    donnée n'existe pas dans le texte) -- gap de conformité à la consigne
    de signature du 10 août 2026, distinct du chantier P20 lui-même, à
    suivre séparément si le taux se confirme sur un plus gros volume.
    """
    head_lines = [l for l in article_text.split("\n") if l.strip()][:8]
    head = "\n".join(head_lines)
    m = _BYLINE_RE.search(head)
    if not m:
        return None, None
    return m.group(1).strip(), m.group(2).strip()


def _extract_title(article_text):
    """Titre = première ligne en gras (**...**) de l'article, format
    imposé par la consigne de rédaction ("Commence directement par le
    titre"). Repli sur la première ligne non vide sans le formatage gras
    si jamais absent -- jamais bloquant, sert uniquement à dériver
    `slug`."""
    for line in article_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^\*\*(.+?)\*\*$", line)
        if m:
            return m.group(1).strip()
        return line
    return ""


def call_claude(prompt_data):
    """
    Envoie le prompt au LLM configuré.
    Retourne le texte de l'article généré.
    """
    provider, model = resolve_for_tier(TASK_TIER)
    print("\n[api] Envoi au LLM ({} — {}, tier={})...".format(provider, model, TASK_TIER))

    article = call_llm(
        system_prompt=prompt_data["system_prompt"],
        user_prompt=prompt_data["user_prompt"],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        task_tier=TASK_TIER,
    )

    print("[api] Article généré : {} caractères".format(len(article)))

    return article


# ─────────────────────────────────────────
# SAUVEGARDE
# ─────────────────────────────────────────

def build_article_filename(snapshot, thematique, article_text, date_fictive=None):
    """
    Construit le nom du fichier de l'article.
    Format : YYYYMMDD_HHMMSS_scenario_thematique_article_datefictive.md
    """
    import re
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    scenario   = snapshot["scenario_slug"]
    thema      = thematique.get("slug", "article")
    # Normaliser la date fictive : "3 février 2098" → "3fevrier2098"
    # Bug corrigé le 10 août 2026 (retour de David) : la regex [^a-z0-9]
    # ne matchait pas les caractères accentués (é, û...) et les
    # supprimait donc silencieusement au lieu de les translittérer —
    # "février" devenait "fvrier". Un passage par unicodedata.normalize
    # (décomposition NFKD, ex. "é" → "e" + accent combinant séparé) avant
    # le filtrage ascii permet de garder la lettre de base et de ne
    # supprimer que le diacritique.
    if date_fictive:
        date_slug = re.sub(r"\s+", "", date_fictive.lower())
        date_slug = unicodedata.normalize("NFKD", date_slug)
        date_slug = date_slug.encode("ascii", "ignore").decode("ascii")
        date_slug = re.sub(r"[^a-z0-9]", "", date_slug)
    else:
        date_slug = ""
    suffix = "_{}".format(date_slug) if date_slug else ""
    return "{}_{}_{}_article{}.md".format(timestamp, scenario, thema, suffix)


def build_article_md(article_text, snapshot, thematique, prompt_data, date_fictive=None, a_une_photo=False, image_credit=""):
    """
    Construit le fichier .md final avec frontmatter + article.
    Inclut les métadonnées de génération pour traçabilité.
    """
    meta = prompt_data["metadata"]
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # P20 (21 août 2026) : slug dérivé du titre réel de l'article (Phase A
    # du scoping du 12 juillet 2026, backlog point 7) -- évite de le
    # dériver du titre à chaque usage ultérieur, risques de collision/
    # accents déjà rencontrés ailleurs (audit_broken_slugs.py). Tronqué à
    # 80 caractères, limite raisonnable pour un slug d'URL sans jamais
    # faire échouer la sauvegarde si le titre est absent/vide.
    titre = _extract_title(article_text)
    slug = _slugify(titre)[:80].strip("_") or "article-sans-titre"

    # Frontmatter YAML
    frontmatter_lines = [
        "---",
        "type: generated_article",
        "date_generation: {}".format(now),
        "scenario: {}".format(meta["scenario"]),
        "thematique: {}".format(meta["thematique"]),
        "format: {}".format(meta["format"]),
        "longueur: {}".format(meta["longueur"]),
        # Traçabilité retry (ajouté le 10 août 2026, chantier longueur) :
        # permet de vérifier l'efficacité du retry directement dans le
        # frontmatter, sans dépendre uniquement d'un re-passage de
        # audit_longueur_articles.py après coup.
        "mots_reels: {}".format(meta.get("mots_reels", "")),
        "retry_longueur: {}".format("oui" if meta.get("retry_longueur") else "non"),
        "model: {}/{}".format(*resolve_for_tier(TASK_TIER)),
        "ligne_editoriale: {}".format(meta.get("ligne_editoriale", "pro_pouvoir")),
        "scenario_state: {}".format(snapshot["scenario"]["state_of_system"]),
        "tension_level: {}".format(snapshot["scenario"]["tension_level"]),
        # ── P20 (21 août 2026) — enrichissement frontmatter publication
        # web future, Phase A du scoping du 12 juillet 2026 (backlog
        # point 7). Phase B (zone_principale, date_publication,
        # articles_lies) et Phase C (image_principale/alt/credit, liées
        # au futur generate_images.py) restent hors scope de ce chantier.
        "slug: {}".format(slug),
        "chapo: {}".format(_yaml_escape(meta.get("chapo", ""))),
        "tags:",
    ]
    for t in meta.get("tags", []):
        frontmatter_lines.append("  - {}".format(t))
    frontmatter_lines += [
        "image_prompt: {}".format(_yaml_escape(meta.get("image_prompt", ""))),
        # a_une_photo : décision manuelle, prise dès l'écriture de
        # l'article (GUI, champ "a_une_photo", décision actée le 21 août
        # 2026 -- avant : toujours false en dur, bascule uniquement après
        # coup). Toujours explicite (jamais de repli sur config.yaml
        # résiduel), reflète l'état de la case à cocher au moment du
        # lancement -- même traitement que --dry-run côté generate.py.
        "a_une_photo: {}".format("true" if a_une_photo else "false"),
        # image_credit : décision manuelle, comme a_une_photo -- vide
        # tant que non tranché. Valeurs attendues (Phase C, 21 août
        # 2026) : "IA_generated" / "personnel" / "autre". Consommé par
        # generate_images.py pour décider du traitement (génération
        # automatique vs placeholder en attente d'upload manuel).
        "image_credit: \"{}\"".format(image_credit or ""),
        "journaliste_slug: {}".format(meta.get("journaliste_slug", "")),
        "date_evenement: {}".format(date_fictive or ""),
        # ── P20 Phase B (21 août 2026) ──
        # zone_principale : corrigé le 25 août 2026 -- l'hypothèse
        # d'origine ("réutilise snapshot['zone_slug'], même valeur, pas
        # un second mécanisme") était fausse dès qu'un choix de zone
        # MANUEL est fait (GUI/CLI, config["zone_slug"]) : build_prompt()
        # priorise ce choix manuel pour résoudre le journal/journaliste
        # (voir zone_slug = config.get('zone_slug') or
        # snapshot.get('zone_slug')), mais ce champ continuait de lire
        # UNIQUEMENT snapshot["zone_slug"] (la zone dominante
        # auto-calculée depuis filtered_instances, indépendante du choix
        # manuel) -- les deux pouvaient diverger silencieusement, jamais
        # remarqué avant P21 (trouvé sur un test réel où le contenu de
        # l'article -- Afrique centrale -- ne correspondait plus du tout
        # à zone_principale -- arc_eurasien_central). Même priorité que
        # build_prompt() désormais : le choix manuel, s'il existe,
        # l'emporte toujours.
        #
        # CRASH corrigé le même jour : première version de ce correctif
        # lisait directement config.get("zone_slug") ici -- mais
        # build_article_md() n'a jamais reçu "config" en paramètre (seul
        # save_article(), son appelant, l'a). save_article() calcule
        # maintenant cette valeur et la dépose dans
        # prompt_data["metadata"]["zone_principale_resolue"] AVANT
        # d'appeler build_article_md(), qui la lit ici via "meta" (déjà
        # accessible, comme tous les autres champs de ce bloc) au lieu
        # de tenter d'accéder à "config" directement.
        "zone_principale: {}".format(meta.get("zone_principale_resolue") or snapshot.get("zone_slug") or ""),
        # date_publication = date_evenement pour l'instant -- aucun délai
        # éditorial simulé, décision actée le 21 août 2026. Champs
        # laissés séparés dans le frontmatter (pas fusionnés) pour ne pas
        # fermer la porte à un vrai décalage plus tard sans migration de
        # schéma.
        "date_publication: {}".format(date_fictive or ""),
        # ── P21 (25 août 2026) — journaux oraux ──
        # type_diffusion : toujours écrit ("ecrit" par défaut, même si
        # le champ n'a jamais existé sur cet article) -- permet de
        # filtrer/auditer les articles oraux plus tard sans dépendre de
        # la présence/absence des 3 champs suivants. duree_estimee/
        # lieu_diffusion/mode_reception : vides pour un article écrit
        # (jamais demandés au LLM ni calculés dans ce cas, voir
        # generate_article()) -- même convention que image_credit
        # ci-dessus (champ toujours présent, vide tant que non
        # applicable), pas de champ manquant selon le cas.
        "type_diffusion: {}".format(meta.get("type_diffusion", "ecrit")),
        "duree_estimee: \"{}\"".format(meta.get("duree_estimee", "")),
        "lieu_diffusion: {}".format(_yaml_escape(meta.get("lieu_diffusion", ""))),
        "mode_reception: {}".format(_yaml_escape(meta.get("mode_reception", ""))),
        # entites_citees : sous-produit de filtered_instances, prépare le
        # futur rapprochement articles_lies (script séparé, non fait à ce
        # stade) sans obliger la génération à relire tout le corpus
        # existant à chaque article.
        "entites_citees:",
    ]
    for inst in snapshot.get("filtered_instances", []):
        inst_slug = inst.get("slug")
        if inst_slug:
            frontmatter_lines.append("  - {}".format(inst_slug))
    frontmatter_lines.append("variables_pilotes:")
    for v in snapshot.get("pilot_variables", []):
        frontmatter_lines.append("  - {}".format(v))
    frontmatter_lines.append("---")
    frontmatter_lines.append("")

    # Section "Voir aussi" (21 août 2026, soir) -- wikilinks Obsidian
    # depuis entites_citees, dans le CORPS (pas le frontmatter) : la vue
    # graphique d'Obsidian suit les [[wikilinks]] du corps, jamais les
    # listes de frontmatter (confirmé sur les fiches entites/*.md
    # existantes, où les liens vers scénario/instances sont déjà dans un
    # tableau en bas de fiche, jamais en frontmatter -- même convention
    # reprise ici). articles_lies n'existe pas encore à ce stade de la
    # génération (calculé après coup par rapprocher_articles.py, qui
    # mettra à jour cette même ligne pour y ajouter les articles liés une
    # fois disponibles) -- seuls entites_citees sont donc listés ici.
    entites_slugs = [inst.get("slug") for inst in snapshot.get("filtered_instances", []) if inst.get("slug")]
    voir_aussi = ""
    if entites_slugs:
        liens = " · ".join("[[{}]]".format(s) for s in entites_slugs)
        voir_aussi = "\n\n---\n**Voir aussi** : {}\n".format(liens)

    return "\n".join(frontmatter_lines) + article_text + voir_aussi


def save_article(article_text, snapshot, thematique, prompt_data, config):
    """
    Sauvegarde l'article dans le vault Obsidian.
    Retourne le chemin du fichier créé.

    Bug corrigé le 10 août 2026 (retour de David) : le dossier de sortie
    était figé sur ARTICLES_DIR (vault/articles/, racine), sans jamais
    lire config["output"]["dossier"] -- generate_series.py et
    generate_manual.py construisaient pourtant ce champ
    ("articles/{scenario}") et créaient même le sous-dossier pour y
    écrire leur _index.md respectif, mais les articles eux-mêmes
    atterrissaient toujours à la racine, orphelins de leur propre index.
    Voir aussi trace_injection.py et audit_longueur_articles.py, dont le
    scan a dû être rendu récursif en même temps pour ne pas perdre de
    visibilité sur les articles désormais rangés en sous-dossier.
    """
    dossier_config = config.get("output", {}).get("dossier") or "articles"
    output_dir = os.path.join(VAULT_PATH, dossier_config)
    os.makedirs(output_dir, exist_ok=True)

    # Date fictive -- remontée avant le if/else (P20, 21 août 2026) : elle
    # ne servait jusqu'ici qu'au nom de fichier en mode "auto", jamais
    # transmise au frontmatter (champ date_evenement, Phase A du scoping
    # du 12 juillet 2026). Calculée une seule fois, utilisée dans les deux
    # cas ci-dessous.
    date_fictive = config.get("article", {}).get("date_fictive", "")

    # zone_principale_resolue (25 août 2026) : calculée ici plutôt que
    # dans build_article_md() -- cette dernière n'a jamais reçu "config"
    # en paramètre (seul save_article(), son appelant, l'a), une
    # première version du correctif du même jour tentait d'y lire
    # config.get(...) directement et faisait planter TOUTE génération
    # d'article (écrit ou oral, P21 sans rapport avec la cause réelle du
    # crash) avec un NameError. Même priorité manuel>auto que
    # build_prompt() -- voir le commentaire complet à l'endroit où cette
    # clé est lue, dans build_article_md().
    prompt_data["metadata"]["zone_principale_resolue"] = (
        config.get("zone_slug") or snapshot.get("zone_slug") or ""
    )

    # a_une_photo / image_credit -- décision prise dès l'écriture de
    # l'article (GUI, generate.py --a-une-photo/--credit, generate_series.py
    # politique aléatoire/toutes/aucune -- décision actée le 21 août 2026).
    a_une_photo = bool(config.get("article", {}).get("a_une_photo", False))
    image_credit = config.get("article", {}).get("image_credit", "") or ""

    # Nom du fichier
    nom_config = config.get("output", {}).get("nom_fichier", "auto")
    if nom_config == "auto":
        filename = build_article_filename(snapshot, thematique, article_text, date_fictive)
    else:
        filename = nom_config if nom_config.endswith(".md") else nom_config + ".md"

    # Contenu complet
    content = build_article_md(article_text, snapshot, thematique, prompt_data, date_fictive=date_fictive,
                                a_une_photo=a_une_photo, image_credit=image_credit)

    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("[api] Article sauvegardé : {}".format(filepath))
    return filepath


# ─────────────────────────────────────────
# FONCTION PRINCIPALE
# ─────────────────────────────────────────

def generate_article(prompt_data, snapshot, thematique, config):
    """
    Fonction principale — appelle le LLM et sauvegarde l'article.

    Args:
        prompt_data : dict — depuis prompt_builder.py
        snapshot    : dict — depuis snapshot.py
        thematique  : dict — depuis loader.py
        config      : dict — depuis config.yaml

    Retourne :
        {
          "article"  : str  — texte brut de l'article
          "filepath" : str  — chemin du fichier sauvegardé
        }
    """
    # Appel LLM
    article = call_claude(prompt_data)

    # P21 (25 août 2026) : lu une seule fois ici, réutilisé pour
    # l'extraction du bloc métadonnées (LIEU_DIFFUSION/MODE_RECEPTION
    # attendus seulement en oral) et pour le calcul de duree_estimee
    # plus bas.
    type_diffusion = prompt_data.get("metadata", {}).get("type_diffusion", "ecrit")

    # P20 (21 août 2026) : extraction du bloc métadonnées de publication
    # (chapo/tags/image_prompt) AVANT tout comptage de mots -- sinon le
    # bloc fausserait la mesure de longueur et le déclenchement du retry
    # ci-dessous (chantier du 10 août 2026, backlog Partie 1 point 1).
    article, meta_publication = _extract_publication_metadata(article, type_diffusion)

    # Validation longueur + retry conditionnel (ajouté le 10 août 2026,
    # décision explicite avec David : seuil unique à 40% d'écart, un seul
    # retry maximum, résultat du retry accepté quoi qu'il arrive -- voir
    # RETRY_DEVIATION_THRESHOLD ci-dessus pour le contexte complet).
    bornes = _parse_longueur_bornes(prompt_data["metadata"].get("longueur", ""))
    wc = _count_words(article)
    retry_effectue = False
    if bornes:
        if _deviation_ratio(wc, bornes) > RETRY_DEVIATION_THRESHOLD:
            article, wc, meta_publication = _retry_with_length_feedback(prompt_data, wc, bornes)
            retry_effectue = True
    else:
        print("[api] [WARN] Longueur '{}' non reconnue par _parse_longueur_bornes "
              "— validation/retry ignorés pour cet article.".format(
                  prompt_data["metadata"].get("longueur", "")))

    prompt_data["metadata"]["mots_reels"] = wc
    prompt_data["metadata"]["retry_longueur"] = retry_effectue
    prompt_data["metadata"]["chapo"] = meta_publication["chapo"]
    prompt_data["metadata"]["tags"] = meta_publication["tags"]
    prompt_data["metadata"]["image_prompt"] = meta_publication["image_prompt"]

    # P21 (25 août 2026) : duree_estimee volontairement PAS demandée au
    # LLM (contrairement à lieu_diffusion/mode_reception) -- calculée
    # après coup depuis mots_reels, plus fiable qu'une estimation a
    # priori qui pourrait diverger du texte réellement produit.
    # ~140 mots/minute : rythme oral posé et clair, cohérent avec un
    # discours de prise de parole publique plutôt qu'un débit rapide de
    # conversation informelle (150-160 mots/minute) ou une lecture lente
    # solennelle (110-120) -- valeur médiane, ouverte à ajustement si
    # les durées calculées semblent irréalistes en pratique une fois
    # observées sur du contenu réel.
    MOTS_PAR_MINUTE_ORAL = 140
    if type_diffusion == "oral":
        minutes = max(1, round(wc / MOTS_PAR_MINUTE_ORAL))
        prompt_data["metadata"]["duree_estimee"] = "{} minute{}".format(
            minutes, "s" if minutes > 1 else ""
        )
        prompt_data["metadata"]["lieu_diffusion"] = meta_publication.get("lieu_diffusion", "")
        prompt_data["metadata"]["mode_reception"] = meta_publication.get("mode_reception", "")

    # P20 -- signature journaliste. Corrigé le 25 août 2026 (diagnostiqué
    # le 23 août sur P25, jamais implémenté à l'époque, devenu nécessaire
    # avec P21 -- voir prompt_builder.py, docstring du champ "journaliste"
    # dans build_prompt()) : priorité au nom déjà résolu par
    # get_journal_profile() (chemin 1, édition locale curatée --
    # déterministe, connu AVANT même l'appel LLM). L'extraction du texte
    # généré (_extract_byline()) ne sert plus qu'en repli, pour le seul
    # cas où aucun nom curaté n'était disponible (chemin 2/3, réseau
    # global/profil hardcodé -- le LLM invente alors un nom que le code
    # ne peut connaître qu'en le relisant après coup). Un article ORAL
    # n'a jamais de ligne "Nom — Journal" formatée en début de texte
    # (STYLE_ORAL, "pas de mise en page journalistique") -- sans ce
    # correctif, _extract_byline() ne pouvait structurellement jamais la
    # trouver, laissant journaliste_slug vide sur 100% des articles
    # oraux malgré un nom pourtant connu avec certitude.
    journaliste_nom = prompt_data.get("metadata", {}).get("journaliste", "").strip()
    if not journaliste_nom:
        journaliste_nom, _ = _extract_byline(article)
    prompt_data["metadata"]["journaliste_slug"] = _slugify(journaliste_nom) if journaliste_nom else ""

    # Sauvegarde
    filepath = save_article(article, snapshot, thematique, prompt_data, config)

    return {
        "article":  article,
        "filepath": filepath,
    }


# ─────────────────────────────────────────
# TEST RAPIDE
# ─────────────────────────────────────────

if __name__ == "__main__":
    from loader      import load_thematique
    from snapshot    import build_snapshot
    from prompt_builder import build_prompt

    print("=== Test api.py ===\n")
    _p, _m = resolve_for_tier(TASK_TIER)
    print("Tier : {} → Fournisseur : {} | Modèle : {}".format(TASK_TIER, _p, _m))

    # Config de test
    config_test = {
        "scenario":   "breakdown",
        "thematique": "actualites_a_la_une",
        "article": {
            "titre_suggere":    "",
            "angle_specifique": "",
            "longueur":         "breve",
        },
        "output": {
            "dossier":     "articles/",
            "nom_fichier": "auto",
        }
    }

    # Pipeline complet
    thematique  = load_thematique("actualites_a_la_une")
    snapshot    = build_snapshot("breakdown", thematique=thematique)
    prompt_data = build_prompt(snapshot, thematique, config_test)

    result = generate_article(prompt_data, snapshot, thematique, config_test)

    print("\n" + "="*60)
    print("ARTICLE GÉNÉRÉ")
    print("="*60)
    print(result["article"])
    print("\n" + "="*60)
    print("Fichier : {}".format(result["filepath"]))
