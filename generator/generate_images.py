#!/usr/bin/env python3
"""
generate_images.py — Ourrassol 2098
====================================

P20 Phase C (21 août 2026, backlog Partie 1 point 9) — traite les
articles marqués `a_une_photo: true` : remplit `image_principale` et
`image_alt`, selon la source déclarée dans `image_credit`.

CONTEXTE — trois valeurs possibles pour `image_credit` (champ manuel,
décidé par David, comme `a_une_photo` lui-même — voir `api.py`,
`build_article_md()`, vide par défaut à la génération) :

  - "IA_generated" : génération automatique par ce script, à partir du
    champ `image_prompt` déjà produit par le LLM au moment de la
    rédaction de l'article (même appel API que l'article — Option 1
    actée le 12 juillet 2026, voir USER_MANUAL_COMPLET.md).
  - "personnel" / "autre" : source manuelle (photo personnelle, banque
    d'images, CC...) — ce script ne génère rien, pointe
    `image_principale` vers un placeholder neutre en attendant l'upload
    réel par David.
  - vide (décision pas encore prise) : article ignoré, rien à faire tant
    que `image_credit` n'est pas renseigné, même si `a_une_photo: true`.

SERVICE DE GÉNÉRATION D'IMAGE — décision explicite de David le 21 août
2026 : reportée. `_generate_image_via_api()` ci-dessous est un point
d'intégration générique, AUCUN service n'est branché à ce stade
(Claude/Anthropic n'a pas d'API de génération d'image native — un
service tiers sera nécessaire, OpenAI/Stability/Google Imagen ou
autre, non choisi). Tant que ce point n'est pas branché, les articles
`image_credit: IA_generated` reçoivent eux aussi un placeholder neutre
(distinct de celui du cas manuel, voir PLACEHOLDER_IA_NON_BRANCHE) —
CE placeholder est spécifiquement reconnu comme "encore à faire" par ce
script (voir `_est_placeholder()`), donc un nouveau run après branchement
du vrai service retraitera automatiquement tous les articles concernés
sans action manuelle supplémentaire, sans `--force` nécessaire pour ce
cas précis (`--force` sert uniquement à re-générer une image DÉJÀ
réelle, cas différent).

CONVENTION DE CHEMIN (actée le 21 août 2026) : `images/{scenario}/
{slug}.png` — le `slug` réutilisé est celui déjà présent dans le
frontmatter de l'article (`slug`, ajouté en Phase A), pas re-dérivé.
Chemin relatif à la racine du vault, cohérent avec `articles/{scenario}/`.

`image_alt` : pas d'appel supplémentaire — texte identique à
`image_prompt` (décision actée le 21 août 2026 : `image_prompt` est déjà
une description visuelle en une phrase, format directement adapté à un
attribut alt). Rempli en même temps que `image_principale`, jamais avant
(cohérence : un texte alternatif n'a de sens qu'une fois une image
associée, même provisoire).

USAGE — COMMENCER PAR UN DRY-RUN (aucune écriture, juste un rapport)
----------------------------------------------------------------------
    python3 generate_images.py --dry-run
    python3 generate_images.py --dry-run --scenario fortress_world

Puis pour de vrai (comportement par défaut de ce script si --dry-run
est omis, cohérent avec fix_annee_debut_placeholder.py/promote_ville.py) :
    python3 generate_images.py
    python3 generate_images.py --scenario fortress_world
    python3 generate_images.py --limit 5          # test sur un petit lot
    python3 generate_images.py --force             # retraite aussi les
                                                     # articles ayant déjà
                                                     # une image réelle
                                                     # (pas un placeholder)
"""

import argparse
import re
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = VAULT_ROOT / "articles"
IMAGES_DIR = VAULT_ROOT / "images"

PLACEHOLDER_MANUEL = "images/_placeholder_en_attente_manuel.svg"
PLACEHOLDER_IA_NON_BRANCHE = "images/_placeholder_en_attente_generation.svg"

ALT_MAX_CHARS = 180


def _truncate_alt(text):
    """
    Garde-fou de longueur pour image_alt (21 août 2026) -- sans limite
    stricte imposée par les standards d'accessibilité (WCAG), une phrase
    complète et descriptive est une pratique normale pour un alt de
    presse en ligne. Le vrai risque n'est pas la longueur en soi mais la
    fiabilité du LLM sur la consigne "en une phrase" (déjà vu ailleurs :
    bloc métadonnées, signature -- pas toujours respectées à la lettre).

    Stratégie en deux temps :
    1. Ne garder que la PREMIÈRE phrase complète (jusqu'au premier
       ./!/?) si plusieurs sont présentes -- grammaticalement propre dans
       l'immense majorité des cas, cible directement le vrai risque
       (2-3 phrases au lieu d'une seule) plutôt qu'une troncature
       aveugle en plein milieu de phrase.
    2. Repli seulement si cette phrase unique dépasse elle-même
       ALT_MAX_CHARS : troncature au dernier espace avant la limite
       (jamais en plein mot), avec ellipse.
    """
    if not text:
        return text
    text = text.strip()
    m = re.match(r"^(.+?[.!?])(\s|$)", text)
    first_sentence = m.group(1).strip() if m else text
    if len(first_sentence) <= ALT_MAX_CHARS:
        return first_sentence
    truncated = first_sentence[:ALT_MAX_CHARS].rsplit(" ", 1)[0]
    return truncated + "…"


# ---------------------------------------------------------------------------
# Point d'intégration générique — AUCUN service branché (voir docstring)
# ---------------------------------------------------------------------------

def _generate_image_via_api(prompt, output_path):
    """
    Génère une image à partir de `prompt` et l'écrit à `output_path`.

    STUB -- aucun service branché à ce stade (décision du 21 août 2026).
    Remplacer le corps de cette fonction par un vrai appel HTTP vers le
    service choisi le moment venu. Signature stable à conserver (prompt
    en entrée, chemin de sortie en second argument, retourne True/False)
    pour ne toucher aucun autre endroit du script lors du branchement
    réel.

    Retourne True si l'image a été générée et écrite avec succès, False
    sinon (dans ce dernier cas l'appelant retombe sur le placeholder
    PLACEHOLDER_IA_NON_BRANCHE).
    """
    print("  [TODO] Aucun service de génération d'image branché — "
          "appel non effectué (prompt : {}...)".format(prompt[:60]))
    return False


# ---------------------------------------------------------------------------
# Parsing / patch frontmatter (même style que fix_annee_debut_placeholder.py
# / fix_alliances_oppositions.py — patch ciblé du bloc brut, pas de
# ré-écriture YAML complète qui reformatterait tout le fichier)
# ---------------------------------------------------------------------------

def parse_md(filepath):
    """Parse un fichier .md : retourne (frontmatter_dict, body_str)."""
    raw = filepath.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
    if not m:
        return {}, raw
    import yaml
    fm_str = re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))
    try:
        fm = yaml.safe_load(fm_str) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2).strip()


def patch_image_fields(raw_frontmatter_block, image_principale, image_alt):
    """
    Remplace UNIQUEMENT les clés image_principale/image_alt dans le bloc
    frontmatter brut, en laissant tous les autres champs strictement
    intacts. image_alt échappé en guillemets doubles (texte libre,
    voir _yaml_escape() dans api.py — même logique dupliquée ici, ce
    script ne dépend pas de api.py pour rester un outil autonome comme
    les autres scripts d'audit/migration du projet).
    """
    result = raw_frontmatter_block

    new_line_principale = "image_principale: {}".format(image_principale)
    pattern_principale = re.compile(r"(?m)^image_principale:.*$")
    if pattern_principale.search(result):
        result = pattern_principale.sub(new_line_principale, result, count=1)
    else:
        result = result.rstrip("\n") + "\n{}\n".format(new_line_principale)

    escaped_alt = (image_alt or "").replace("\\", "\\\\").replace('"', '\\"')
    new_line_alt = 'image_alt: "{}"'.format(escaped_alt)
    pattern_alt = re.compile(r"(?m)^image_alt:.*$")
    if pattern_alt.search(result):
        result = pattern_alt.sub(new_line_alt, result, count=1)
    else:
        result = result.rstrip("\n") + "\n{}\n".format(new_line_alt)

    return result


def write_image_patch(path, image_principale, image_alt):
    """Applique le patch frontmatter et réécrit le fichier."""
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)", raw, re.DOTALL)
    if not m:
        raise ValueError("Frontmatter introuvable dans {}".format(path))
    prefix, fm_block, marker, body = m.groups()
    new_fm_block = patch_image_fields(fm_block, image_principale, image_alt)
    path.write_text("{}{}{}{}".format(prefix, new_fm_block, marker, body), encoding="utf-8")


# ---------------------------------------------------------------------------
# Découverte des articles concernés
# ---------------------------------------------------------------------------

def _est_placeholder(chemin):
    """True si `chemin` pointe vers l'un des deux placeholders neutres --
    ces articles restent éligibles à un nouveau traitement (pas
    considérés comme "déjà faits"), contrairement à une vraie image."""
    return chemin in (PLACEHOLDER_MANUEL, PLACEHOLDER_IA_NON_BRANCHE)


def find_target_articles(scenario_filter=None):
    """
    Parcourt articles/{scenario}/*.md, retourne la liste des
    (filepath, frontmatter) pour les articles a_une_photo: true.
    """
    targets = []
    if not ARTICLES_DIR.exists():
        return targets
    for scenario_dir in sorted(ARTICLES_DIR.iterdir()):
        if not scenario_dir.is_dir():
            continue
        if scenario_filter and scenario_dir.name != scenario_filter:
            continue
        for filepath in sorted(scenario_dir.glob("*.md")):
            if filepath.name == "_index.md":
                continue
            fm, _ = parse_md(filepath)
            if fm.get("a_une_photo") is True:
                targets.append((filepath, fm))
    return targets


# ---------------------------------------------------------------------------
# Traitement principal
# ---------------------------------------------------------------------------

def process_article(filepath, fm, dry_run, force):
    """
    Traite un article ciblé. Retourne une chaîne de statut pour le
    récapitulatif final : "generee" / "placeholder_manuel" /
    "placeholder_ia_non_branche" / "deja_fait" / "en_attente_credit".
    """
    slug = fm.get("slug") or filepath.stem
    scenario = fm.get("scenario") or filepath.parent.name
    credit = (fm.get("image_credit") or "").strip()
    image_prompt = fm.get("image_prompt") or ""
    image_principale_actuelle = fm.get("image_principale") or ""

    deja_reelle = bool(image_principale_actuelle) and not _est_placeholder(image_principale_actuelle)
    if deja_reelle and not force:
        print("  [SKIP] {} — image déjà présente ({}), utiliser --force pour "
              "retraiter.".format(slug, image_principale_actuelle))
        return "deja_fait"

    if credit == "":
        print("  [ATTENTE] {} — a_une_photo: true mais image_credit non "
              "renseigné, ignoré.".format(slug))
        return "en_attente_credit"

    if credit == "IA_generated":
        rel_path = "images/{}/{}.png".format(scenario, slug)
        if dry_run:
            print("  [DRY] {} — génèrerait via API : {} → {}".format(
                slug, image_prompt[:60], rel_path))
            return "generee"

        output_path = VAULT_ROOT / rel_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ok = _generate_image_via_api(image_prompt, output_path)
        if ok:
            write_image_patch(filepath, rel_path, _truncate_alt(image_prompt))
            print("  [OK] {} — image générée : {}".format(slug, rel_path))
            return "generee"
        else:
            write_image_patch(filepath, PLACEHOLDER_IA_NON_BRANCHE, _truncate_alt(image_prompt))
            print("  [PLACEHOLDER] {} — service non branché, placeholder "
                  "posé (retraité automatiquement une fois le service "
                  "branché).".format(slug))
            return "placeholder_ia_non_branche"

    elif credit in ("personnel", "autre"):
        if dry_run:
            print("  [DRY] {} — placerait un placeholder manuel "
                  "(credit={}).".format(slug, credit))
            return "placeholder_manuel"
        write_image_patch(filepath, PLACEHOLDER_MANUEL, _truncate_alt(image_prompt))
        print("  [PLACEHOLDER] {} — credit={}, placeholder posé, upload "
              "manuel attendu à {}.".format(slug, credit, PLACEHOLDER_MANUEL))
        return "placeholder_manuel"

    else:
        print("  [WARN] {} — image_credit='{}' non reconnu (attendu "
              "IA_generated/personnel/autre), ignoré.".format(slug, credit))
        return "en_attente_credit"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default=None, help="Limiter à un scénario (défaut : tous)")
    parser.add_argument("--dry-run", action="store_true", help="N'écrit rien sur disque")
    parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre d'articles traités (test)")
    parser.add_argument("--force", action="store_true", help="Retraiter aussi les articles ayant déjà une vraie image")
    args = parser.parse_args()

    targets = find_target_articles(scenario_filter=args.scenario)
    if args.limit:
        targets = targets[:args.limit]

    print("generate_images.py — mode {}".format("DRY-RUN" if args.dry_run else "EXECUTE"))
    print("{} article(s) a_une_photo=true trouvé(s){}.\n".format(
        len(targets),
        " pour {}".format(args.scenario) if args.scenario else ""
    ))

    stats = {}
    for filepath, fm in targets:
        statut = process_article(filepath, fm, dry_run=args.dry_run, force=args.force)
        stats[statut] = stats.get(statut, 0) + 1

    print("\n{}".format("=" * 60))
    print("Récapitulatif :")
    for statut, count in sorted(stats.items()):
        print("  {} : {}".format(statut, count))
    if args.dry_run:
        print("\n[DRY-RUN] Aucune modification effectuée.")


if __name__ == "__main__":
    main()
