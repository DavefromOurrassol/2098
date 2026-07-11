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
        "zones":          _stats_zones(pipeline_dir, cfg.get("scenarios", [])),
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
    for f in sorted(articles_dir.glob("*.md")):
        try:
            txt = f.read_text(encoding="utf-8")
            total += 1
            sc_m = sc_pat.search(txt)
            sc   = sc_m.group(1).strip() if sc_m else "inconnu"
            by_scenario[sc] = by_scenario.get(sc, 0) + 1
            ligne_m = ligne_pat.search(txt)
            ligne   = ligne_m.group(1).strip() if ligne_m else "inconnu"
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
        try:
            txt = f.read_text(encoding="utf-8")
            total += 1
            sc_m = sc_pat.search(txt)
            sc   = sc_m.group(1).strip() if sc_m else "inconnu"
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
    for f in articles_dir.glob("*.md"):
        try:
            txt = f.read_text(encoding="utf-8")
            m = th_pat.search(txt)
            th = m.group(1).strip() if m else "inconnu"
            by_th[th] = by_th.get(th, 0) + 1
        except Exception:
            continue
    return dict(sorted(by_th.items(), key=lambda x: -x[1]))


def _stats_zones(pipeline_dir: Path, scenarios: list) -> dict:
    """
    Format geographie/{scenario}.md :
      zones:
        - slug: afrique_centrale_australe
          nom: ...
          niveau: 1
    Compter les zones de niveau 1 par scénario.
    """
    geo_dir = pipeline_dir / "geographie"
    if not geo_dir.exists():
        return {"total": 0, "by_scenario": {}}
    niveau_pat = re.compile(r"^\s+niveau:\s*(\d+)")
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
    for fname in (("evenements_custom", "needs_review.yaml"), ("instances_custom", "needs_review_enrich.yaml")):
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
