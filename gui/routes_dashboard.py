"""
routes_dashboard.py
--------------------
Routes du dashboard GUI Ourrassol 2098, extraites de app.py (P5 du backlog,
4 juillet 2026) pour éviter que /api/dashboard soit régulièrement écrasé par
des patches sur app.py. Isolé dans un Blueprint Flask, importé et enregistré
depuis app.py (à ajouter après la définition de `app = Flask(__name__)`) :

    from routes_dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

load_config() est importé depuis app.py à l'intérieur de la fonction (import
différé) plutôt qu'en tête de fichier, pour éviter l'import circulaire
(app.py importe ce module, ce module ne doit donc pas importer app.py au
chargement — seulement au moment de l'appel, quand app.py est déjà chargé).
"""

import json
import re
from pathlib import Path

from flask import Blueprint, jsonify

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    from app import load_config  # import différé — voir docstring du module
    cfg = load_config()
    vault_root   = Path(cfg.get("vault_root", ""))
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    llm          = cfg.get("llm", {})

    stats = {
        "llm": {
            "provider": llm.get("provider", "—"),
            "model": llm.get("model_mistral") if llm.get("provider") == "mistral"
                     else llm.get("model_claude", "—"),
        },
        "articles":       _stats_articles(vault_root),
        "instances":      _stats_instances(vault_root),
        "entites":        _stats_entites(vault_root, pipeline_dir),
        "journaux":       _stats_journaux(pipeline_dir),
        "enrichissement": _stats_enrichissement(vault_root),
        "thematiques":    _stats_thematiques(vault_root),
        "zones":          _stats_zones(vault_root, cfg.get("scenarios", [])),
        "review_count":   _count_review_items(vault_root),  # bug #15 : était pipeline_dir
        "vault_ok":       vault_root.exists() and pipeline_dir.exists(),
    }
    return jsonify(stats)


def _stats_articles(vault_root: Path) -> dict:
    articles_dir = vault_root / "articles"
    if not articles_dir.exists():
        return {"total": 0, "by_scenario": {}, "by_ligne": {}}
    total = 0
    by_scenario: dict = {}
    by_ligne: dict = {}
    sc_pat    = re.compile(r"^scenario:\s*(.+)$", re.MULTILINE)
    ligne_pat = re.compile(r"^ligne_editoriale:\s*(.+)$", re.MULTILINE)
    # Récursif depuis le 23 août 2026 (repéré par David : dashboard à "0"
    # articles après l'uniformisation du 22 août -- generate.py range
    # désormais dans articles/{scenario}/ même en génération unitaire, plus
    # seulement les séries). Même correctif déjà appliqué le 10 août à
    # trace_injection.py/audit_longueur_articles.py pour la même raison,
    # jamais répercuté ici -- routes_dashboard.py vit hors du flux de
    # patches habituel sur app.py (voir docstring du module), ce qui l'a
    # fait passer sous le radar. Fichiers d'index (_index.md, écrits par
    # generate_series.py/generate_manual.py) exclus -- ce ne sont pas des
    # articles, même filtre qu'audit_longueur_articles.py.
    for f in sorted(articles_dir.glob("**/*.md")):
        if f.name.startswith("_"):
            continue
        try:
            txt = f.read_text(encoding="utf-8")
            total += 1
            sc_m = sc_pat.search(txt)
            sc   = sc_m.group(1).strip() if sc_m else "inconnu"
            if not sc:
                # même bug que _stats_instances (voir §1.6 du backlog) —
                # corrigé le 2 août 2026 par symétrie, préventivement.
                sc = "inconnu"
            by_scenario[sc] = by_scenario.get(sc, 0) + 1
            ligne_m = ligne_pat.search(txt)
            ligne   = ligne_m.group(1).strip() if ligne_m else "inconnu"
            if not ligne:
                ligne = "inconnu"
            by_ligne[ligne] = by_ligne.get(ligne, 0) + 1
        except Exception:
            continue
    return {"total": total, "by_scenario": by_scenario, "by_ligne": by_ligne}


def _stats_instances(vault_root: Path) -> dict:
    instances_dir = vault_root / "instances"
    if not instances_dir.exists():
        return {"total": 0, "by_scenario": {}}
    total = 0
    by_scenario: dict = {}
    sc_pat = re.compile(r"^scenario:\s*(.+)$", re.MULTILINE)
    for f in instances_dir.glob("*.md"):
        if f.name == "instance_template.md":
            # Le gabarit vit dans instances/ (comme toutes les vraies fiches)
            # et était compté comme une 711e instance, avec "scenario:
            # <slug_scenario>" jamais rempli — d'où l'entrée fantôme
            # affichée " : 1" dans le dashboard (le navigateur avale la
            # balise <slug_scenario> comme du HTML non échappé). Même
            # filtre déjà appliqué dans officialize_alliances.py — corrigé
            # ici aussi le 2 août 2026.
            continue
        try:
            txt = f.read_text(encoding="utf-8")
            total += 1
            sc_m = sc_pat.search(txt)
            sc   = sc_m.group(1).strip() if sc_m else "inconnu"
            if not sc:
                # Garde-fou défensif supplémentaire (cas différent : une
                # vraie fiche avec "scenario:" présent mais vide/espaces).
                sc = "inconnu"
            by_scenario[sc] = by_scenario.get(sc, 0) + 1
        except Exception:
            continue
    return {"total": total, "by_scenario": by_scenario}


def _stats_entites(vault_root: Path, pipeline_dir: Path) -> dict:
    for p in [pipeline_dir / "_entities_list.json", vault_root / "_entities_list.json"]:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return {"total": len(data)}
                if isinstance(data, dict):
                    return {"total": len(data)}
            except Exception:
                pass
    entites_dir = vault_root / "entites"
    if entites_dir.exists():
        return {"total": len(list(entites_dir.glob("*.md")))}
    return {"total": 0}


def _stats_journaux(pipeline_dir: Path) -> dict:
    """
    Format journaux.yaml :
      breakdown:
        pro_pouvoir:
          _reseau:
            nom: ...
            zones:
              - zone_slug
    Compter le nombre de réseaux (journaux) par scénario.
    """
    journaux_path = pipeline_dir / "journaux.yaml"
    if not journaux_path.exists():
        return {"total": 0, "missing": True, "by_scenario": {}}
    try:
        txt = journaux_path.read_text(encoding="utf-8")
        # Chaque journal = un bloc "_reseau:" ou une clé de réseau sous une ligne éditoriale
        # On compte les occurrences de "nom:" au niveau réseau (indentation 3)
        # Format : scenario > ligne > reseau_key > { nom: ... }
        # Compter les clés de scénario (niveau 0, pas d'indentation, se termine par ":")
        by_scenario: dict = {}
        current_sc = None
        sc_re  = re.compile(r"^(\w+):$")
        # Compter les réseaux : ligne "    _reseau:" ou "    nom_journal:" à indent 4
        reseau_re = re.compile(r"^    \w")
        for line in txt.splitlines():
            sc_m = sc_re.match(line)
            if sc_m:
                current_sc = sc_m.group(1)
                if current_sc not in by_scenario:
                    by_scenario[current_sc] = 0
            elif current_sc and reseau_re.match(line) and line.strip().endswith(":"):
                # Clé de réseau (indent 4, pas de valeur inline)
                by_scenario[current_sc] = by_scenario.get(current_sc, 0) + 1
        total = sum(by_scenario.values())
        return {"total": total, "missing": False, "by_scenario": by_scenario}
    except Exception:
        return {"total": 0, "missing": False, "by_scenario": {}}


def _stats_enrichissement(vault_root: Path) -> dict:
    instances_dir = vault_root / "instances"
    if not instances_dir.exists():
        return {"minimal": 0, "enrichi": 0, "autre": 0, "total": 0}
    minimal = enrichi = autre = 0
    status_pat = re.compile(r"^statut:\s*(.+)$", re.MULTILINE)
    for f in instances_dir.glob("*.md"):
        if f.name == "instance_template.md":
            # Même pollution que _stats_instances() ci-dessus : le gabarit
            # n'a pas de champ "statut:", il tombait donc dans "autre".
            # Corrigé le 2 août 2026.
            continue
        try:
            txt = f.read_text(encoding="utf-8")
            m = status_pat.search(txt)
            if m:
                s = m.group(1).strip()
                if "enrichi" in s:
                    enrichi += 1
                elif "minimal" in s:
                    minimal += 1
                else:
                    autre += 1
            else:
                autre += 1
        except Exception:
            continue
    return {"minimal": minimal, "enrichi": enrichi, "autre": autre,
            "total": minimal + enrichi + autre}


def _stats_thematiques(vault_root: Path) -> dict:
    articles_dir = vault_root / "articles"
    if not articles_dir.exists():
        return {}
    by_th: dict = {}
    th_pat = re.compile(r"^thematique:\s*(.+)$", re.MULTILINE)
    # Récursif depuis le 23 août 2026 -- même correctif et même cause que
    # _stats_articles() ci-dessus, mêmes _index.md exclus.
    for f in articles_dir.glob("**/*.md"):
        if f.name.startswith("_"):
            continue
        try:
            txt = f.read_text(encoding="utf-8")
            m = th_pat.search(txt)
            th = m.group(1).strip() if m else "inconnu"
            by_th[th] = by_th.get(th, 0) + 1
        except Exception:
            continue
    return dict(sorted(by_th.items(), key=lambda x: -x[1]))


def _stats_zones(vault_root: Path, scenarios: list) -> dict:
    """
    Format geographie/{scenario}.md :
      zones:
        - slug: afrique_centrale_australe
          nom: ...
          niveau: 1
    Compter les zones de niveau 1 par scénario.

    Correctif du 16 août 2026 : prenait pipeline_dir en paramètre alors que
    geographie/ vit à la racine du vault (vault_root), pas dans
    generator/ -- contrairement à journaux.yaml (_stats_journaux, qui reste
    dans pipeline_dir à raison, lui est bien dans generator/). Deuxième bug
    distinct de celui du 16 août sur niveau_pat (re.MULTILINE manquant) --
    les deux masquaient le même symptôme (total toujours à 0), trouvés l'un
    après l'autre en testant sur le vrai dashboard de David.
    """
    geo_dir = vault_root / "geographie"
    if not geo_dir.exists():
        return {"total": 0, "by_scenario": {}}
    # Correctif du 16 août 2026 : re.MULTILINE manquant sur ce pattern
    # (présent sur toutes les autres regex de ce fichier) -- sans lui, "^"
    # ne matche que la toute première position du fichier entier, jamais
    # le début de chaque ligne. Comme geographie/{scenario}.md commence
    # toujours par "---" (frontmatter), "niveau: 1" ne pouvait JAMAIS
    # matcher, quel que soit le contenu réel -- d'où le "0" systématique
    # affiché sur la carte "ZONES GÉO (NIVEAU 1)" du dashboard, repéré par
    # David en regardant le dashboard.
    niveau_pat = re.compile(r"^\s+niveau:\s*(\d+)", re.MULTILINE)
    by_scenario: dict = {}
    total = 0
    for sc in scenarios:
        geo_file = geo_dir / f"{sc}.md"
        if not geo_file.exists():
            continue
        txt   = geo_file.read_text(encoding="utf-8")
        count = sum(1 for m in niveau_pat.finditer(txt) if int(m.group(1)) == 1)
        by_scenario[sc] = count
        total += count
    return {"total": total, "by_scenario": by_scenario}


def _count_review_items(vault_root: Path) -> int:
    count = 0
    for fname in (
        ("entites_custom", "needs_review.yaml"),      # manquait — ajouté le 2 août 2026
        ("evenements_custom", "needs_review.yaml"),
        ("signaux_custom", "needs_review.yaml"),       # manquait — ajouté le 2 août 2026
        ("instances_custom", "needs_review_enrich.yaml"),
    ):
        p = vault_root / fname[0] / fname[1]
        if p.exists():
            try:
                count += len(re.findall(r"^- ", p.read_text(encoding="utf-8"), re.MULTILINE))
            except Exception:
                pass
    review_md = vault_root / "documentation" / "need_action" / "localisation_review.md"
    if review_md.exists():
        try:
            count += len(re.findall(r"review_manuelle", review_md.read_text(encoding="utf-8")))
        except Exception:
            pass
    return count
