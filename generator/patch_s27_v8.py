#!/usr/bin/env python3
"""
patch_s27_v8.py — Ourrassol 2098 (S27, 10 octobre 2026)

Simulateur « et si ? » v7.9.1 → v8 : liste d'application (phase 3).
À la fin de chaque scénario du rapport, une section « Liste d'application » :
ce que l'hypothèse imposerait de changer, dans l'ordre, avec l'outil à lancer
ou « à la main ». Lecture seule, aucun appel IA. En fin de rapport, l'entrée
de queue commune pour injecter l'événement (mode choc).

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v8.py --dry-run
    python3 generator/patch_s27_v8.py

Sauvegarde : generator/simuler_et_si.py.bak_v8. Refuse un second passage.
"""
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "simuler_et_si.py"
MARQUEUR = "# Liste d'application (phase 3, v8"

BLOC = r'''# ---------------------------------------------------------------------------
# Liste d'application (phase 3, v8, 10 octobre 2026)
# ---------------------------------------------------------------------------
# Tout ce que l'hypothèse imposerait de changer, scénario par scénario, dans
# l'ordre, avec l'outil à lancer ou « à la main ». Lecture seule, aucun appel
# IA : construite à partir des résultats déjà calculés (niveaux, lecture IA
# gardée, carte évaluée) et de trois scans du vault (instances / événements
# localisés, articles, rédactions de journaux.yaml).

SECTIONS_APPLICATION = ["Carte", "Localisation des fiches", "Journaux", "Statuts de zone",
                        "Élément", "Nouvelles entités", "Trajectoires", "Relations", "Lore",
                        "Articles et site", "Contrôles"]
TRAJ_TERMINALES = {"transformé", "disparu", "historique", "mythifié"}


def _frontmatter_fichier(path):
    import re as _re
    try:
        txt = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = _re.match(r"^---\s*\n(.*?)\n---\s*\n", txt, _re.DOTALL)
    if not m:
        return {}
    try:
        fm = yaml.safe_load(_re.sub(r"\[\[([^\]]+)\]\]", r"\1", m.group(1))) or {}
    except yaml.YAMLError:
        return {}
    return fm if isinstance(fm, dict) else {}


def _articles_scenario(sc):
    """Articles du scénario (racine et sous-dossiers, scénario lu dans le
    frontmatter, _index.md ignoré)."""
    racine = VAULT_ROOT / "articles"
    out = []
    if not racine.is_dir():
        return out
    for p in sorted(racine.rglob("*.md")):
        if p.name == "_index.md":
            continue
        fm = _frontmatter_fichier(p)
        if fm.get("scenario") != sc:
            continue
        ent = fm.get("entites_citees") or []
        out.append({"fichier": p.name, "chemin": str(p.relative_to(VAULT_ROOT)),
                    "titre": str(fm.get("titre") or fm.get("slug") or p.stem),
                    "zone": fm.get("zone_principale") or "",
                    "entites": [str(e) for e in ent] if isinstance(ent, list) else []})
    return out


def _redactions_scenario(sc):
    """{zone: [{"ligne", "nom", "type_diffusion"}]} depuis journaux.yaml (None si illisible)."""
    try:
        data = yaml.safe_load((SCRIPT_DIR / "journaux.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    out = {}
    for ligne, contenu in (data.get(sc) or {}).items():
        if not isinstance(contenu, dict) or not isinstance(contenu.get("zones"), dict):
            continue
        for zone, z in contenu["zones"].items():
            z = z if isinstance(z, dict) else {}
            out.setdefault(zone, []).append({"ligne": ligne, "nom": z.get("nom") or "?",
                                             "type_diffusion": z.get("type_diffusion") or "ecrit"})
    return out


def _donnees_application(sc):
    """Les trois scans du vault ; une source illisible donne une liste vide et un avertissement."""
    d = {"instances": [], "evenements": [], "articles": [], "redactions": None, "avert": []}
    try:
        from loader import load_instances_for_scenario, load_event_instances_for_scenario
        d["instances"] = load_instances_for_scenario(sc)
        d["evenements"] = load_event_instances_for_scenario(sc)
    except Exception as e:
        d["avert"].append(f"instances / événements illisibles : {type(e).__name__}: {e}")
    try:
        d["articles"] = _articles_scenario(sc)
    except Exception as e:
        d["avert"].append(f"articles illisibles : {type(e).__name__}: {e}")
    d["redactions"] = _redactions_scenario(sc)
    if d["redactions"] is None:
        d["avert"].append("journaux.yaml illisible : la section Journaux est incomplète")
    return d


def _etape(liste, section, action, commande=None, motif=None):
    liste.append({"section": section, "action": action, "commande": commande, "motif": motif})


def liste_application(hyp, sc, res, cons, geo_ops, donnees):
    """Étapes à valider à la main pour CE scénario. Rien n'est écrit."""
    E = []
    cons = cons if cons and not cons.get("erreur") else {}
    ops_hyp = (hyp.get("geographie") or {}).get(sc) or []
    by_inst = {i.get("slug"): i for i in donnees["instances"]}
    redac = donnees["redactions"] or {}
    zones_mortes, zones_nouvelles, zones_touchees, traces = {}, [], set(), 0
    redaction_a_creer, orateurs_a_creer = [], []

    # 1. Carte -----------------------------------------------------------------
    for op, g in zip(ops_hyp, geo_ops or []):
        pays = g["pays"]
        if g.get("erreurs"):
            _etape(E, "Carte", f"{pays} ({g['action']}) refusé au contrôle : corriger l'hypothèse avant toute application",
                   motif="; ".join(g["erreurs"][:3]))
            continue
        for a in g.get("actuelles") or []:
            zones_touchees.add(a["slug"])
        if g["action"] == "absorber":
            _etape(E, "Carte", f"Rattacher {pays} à `{g['cible']}`",
                   f"Carte → clic sur {pays} → affecter à `{g['cible']}`",
                   "le pays change de mains")
            zones_touchees.add(g["cible"])
        elif g["action"] == "nouvelle_zone":
            nz = op.get("nouvelle_zone") or {}
            _etape(E, "Carte", f"Créer la zone `{g['cible']}` ({nz.get('nom')}) avec {pays}",
                   f"Carte → clic sur {pays} → créer une zone (slug `{g['cible']}`, type {nz.get('type') or 'autre'}, "
                   f"statut {nz.get('statut') or 'emergent'})", "nouvelle zone de niveau 1")
            zones_nouvelles.append({"slug": g["cible"], "pays": pays})
        elif g["action"] == "partition":
            for p in g["parties"]:
                if p["nouvelle"]:
                    zones_nouvelles.append({"slug": p["cible"], "pays": pays})
                    _etape(E, "Carte", f"Créer la zone `{p['cible']}` ({p.get('nom')}) pour la partie {p['numero']}",
                           "Carte → créer une zone vide (avant de dessiner les portions)",
                           "partie confiée à une nouvelle zone")
            for p in g["parties"]:
                if p["principale"]:
                    _etape(E, "Carte", f"Partie {p['numero']} : `{p['cible']}` garde {pays} entier",
                           f"Carte → clic sur {pays} → affecter à `{p['cible']}`", "modèle Allemagne")
                else:
                    traces += 1
                    _etape(E, "Carte", f"Partie {p['numero']} : dessiner « {p['portion']} » dans `{p['cible']}`",
                           f"Carte → ✏️ éditer `{p['cible']}` → ✏️ dessiner ({pays})", "tracé d'une portion")
                zones_touchees.add(p["cible"])
            _etape(E, "Carte", f"Vérifier `zones_pays.json` : {pays} → "
                   + (f"`{g['zones_pays_apres']}`" if g["zones_pays_apres"] else "`null` (modèle France)"),
                   motif="la Carte l'écrit seule ; à contrôler après les tracés")
            for s in g.get("a_repartir") or []:
                _etape(E, "Carte", f"Répartir la sous-zone `{s['slug']}` ({s.get('nom')}) vers la partie qui la contient",
                       "Carte → arbre → ↗️ déplacer", "sous-zone du pays partagé")
        elif g["action"] == "region":
            nz = g["nouvelle_zone"]
            traces += 1
            _etape(E, "Carte", f"Créer la région `{g['cible']}` ({nz.get('nom')}) sous `{g['parent']}`",
                   f"Carte → arbre de `{g['parent']}` → ➕ sous-zone (type {nz.get('type')}, statut {nz.get('statut')}, "
                   f"lieu réel {pays}, portion « {g['portion']} »)", "le pays ne change pas de mains")
            _etape(E, "Carte", f"Dessiner le tracé de `{g['cible']}`",
                   f"Carte → ✏️ éditer → ✏️ dessiner ({pays})", "portion de la région")
            zones_nouvelles.append({"slug": g["cible"], "pays": pays, "region": True,
                                    "redaction": g.get("redaction")})
        for q in g.get("quittees") or []:
            if q["videe"]:
                zones_mortes[q["slug"]] = "vidée par la carte"
                _etape(E, "Carte", f"`{q['slug']}` n'a plus aucun territoire : la garder (vestige, exil) ou la supprimer",
                       "Carte → ✏️ éditer → Zone dangereuse (refusé tant qu'elle a des sous-zones)",
                       "zone quittée par " + pays)
        orph = ((g.get("impact") or {}).get("sous_zones_orphelines") or [])
        if orph and g["action"] in ("absorber", "nouvelle_zone"):
            _etape(E, "Carte", f"{len(orph)} sous-zone(s) de {pays} à rattacher à `{g['cible']}`",
                   f"python3 generator/reparenter_sous_zones_orphelines.py --scenario {sc} --zone-cible {g['cible']}",
                   ", ".join(s.get("slug", "?") for s in orph[:MAX_LISTE]))
        # Rédaction de la zone d'arrivée.
        nouvelle_sans_redac = (g["action"] == "nouvelle_zone"
                               or (g["action"] == "absorber" and g.get("redaction_cible") is False))
        if nouvelle_sans_redac:
            redaction_a_creer.append(g["cible"])
        if g["action"] == "partition":
            redaction_a_creer += [p["cible"] for p in g["parties"] if p.get("redaction") is False]
        if g["action"] == "region" and g.get("redaction") is False:
            redaction_a_creer.append(g["cible"])
        # Oral : la zone d'origine a-t-elle une rédaction orale ou mixte ?
        orales = [(r["ligne"], a["slug"]) for a in g.get("actuelles") or []
                  for r in redac.get(a["slug"], []) if r["type_diffusion"] in ("oral", "mixte")]
        if orales:
            orateurs_a_creer.append({"pays": pays, "origine": orales})
    for nz in zones_nouvelles:
        if nz.get("region"):
            continue
        _etape(E, "Carte", f"Relations (alliés / rivaux) de la nouvelle zone `{nz['slug']}`",
               f"à la main : geographie/{sc}.md, bloc `relations` de `{nz['slug']}`",
               "la création n'en écrit aucune")
    if zones_nouvelles:
        _etape(E, "Carte", "Continent des nouvelles zones sur le site : "
               + ", ".join(f"`{z['slug']}`" for z in zones_nouvelles),
               "python3 generator/export_revues.py --continents",
               "forcer dans generator/continents_zones.yaml si le continent deviné est faux")

    # 4. Statuts de zone (avant la localisation : une zone disparue est une zone morte)
    for z in cons.get("zones_statut") or []:
        _etape(E, "Statuts de zone", f"`{z['zone']}` ({z.get('nom')}) : {z['avant']} → {z['apres']}",
               f"à la main : geographie/{sc}.md, champ `statut` (texte mis à jour par "
               f"regenerer_corps_geographie.py --scenario {sc} --execute)", z.get("raison"))
        zones_touchees.add(z["zone"])
        if z["apres"] == "disparu":
            zones_mortes.setdefault(z["zone"], "statut disparu")

    # 2. Localisation des fiches -----------------------------------------------
    deja = set()
    def _localiser(slug, quoi, motif):
        if slug in deja:
            return
        deja.add(slug)
        _etape(E, "Localisation des fiches", f"{quoi} `{slug}` : {motif}",
               f"python3 generator/extract_localisation.py --scenario {sc} --slug {slug} --force",
               "puis review_localisation.py si la zone reste ambiguë")
    for i in donnees["instances"]:
        z = (i.get("localisation") or {}).get("zone")
        if z in zones_mortes:
            _localiser(i["slug"], "Instance", f"localisée dans `{z}` ({zones_mortes[z]})")
    for ev in donnees["evenements"]:
        z = (ev.get("localisation") or {}).get("zone")
        if z in zones_mortes:
            _localiser(ev.get("slug"), "Événement", f"localisé dans `{z}` ({zones_mortes[z]})")
    for g in geo_ops or []:
        for it in ((g.get("impact") or {}).get("instances_liees") or []):
            if it.get("slug"):
                _localiser(it["slug"], "Fiche", f"liée à une sous-zone de {g['pays']}, à vérifier")

    # 3. Journaux --------------------------------------------------------------
    redaction_a_creer = list(dict.fromkeys(redaction_a_creer))
    if redaction_a_creer:
        _etape(E, "Journaux", "Créer les rédactions de : " + ", ".join(f"`{z}`" for z in redaction_a_creer),
               f"python3 generator/generate_journaux.py --scenario {sc} --update",
               "puis clean_fallback_journaux.py si un lot échoue ; une région hérite sinon de la rédaction parente")
        _etape(E, "Journaux", "Couverture des journalistes des nouvelles rédactions",
               "python3 generator/audit_couverture_journalistes.py --report",
               "inject_journaliste_custom.py --mode auto si trop de thématiques à un seul nom")
        for o in orateurs_a_creer:
            for ligne, origine in o["origine"]:
                for z in redaction_a_creer:
                    _etape(E, "Journaux", f"`{origine}` ({ligne}) est oral ou mixte : faut-il des orateurs à `{z}` ?",
                           f"python3 generator/inject_orateur_custom.py --mode convertir --scenario {sc} "
                           f"--zones {ligne}::{z}", f"territoire venu de {o['pays']}")
    for z, cause in zones_mortes.items():
        for r in redac.get(z, []):
            _etape(E, "Journaux", f"*{r['nom']}* ({r['ligne']}, `{z}`) n'a plus de territoire ({cause})",
                   "à la main : le garder (journal en exil) ou le retirer de journaux.yaml "
                   "(load_journaux / save_journaux, comme le 6 oct)",
                   "aucun outil de migration des journaux")

    # 5. Élément ---------------------------------------------------------------
    if hyp.get("mode") == "rupture":
        _etape(E, "Élément", "Mode rupture : décision S19 à prendre avant toute écriture",
               motif="l'injection réelle ne connaît que le mode choc ; appliquer la rupture = changer la référence")
        for e in (res or {}).get("effets") or []:
            if abs(e.get("reference_apres", e["reference"]) - e["reference"]) >= 0.1:
                _etape(E, "Élément", f"{e['variable']} : référence {_virgule(e['reference'], False)} → "
                       f"{_virgule(e['reference_apres'], False)}",
                       f"à la main : variables/{e['variable']}.md, states.{sc}.level, "
                       f"puis python3 generator/synchroniser_scenarios.py",
                       "seulement si la décision S19 est oui")
    elif hyp.get("impacts"):
        _etape(E, "Élément", f"Injecter l'événement `{hyp['id']}` (entrée commune en fin de rapport)",
               "python3 generator/inject_custom_events.py --mode custom",
               "une seule injection pour tous les scénarios de l'hypothèse")
        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{i['force']:g}"
                           for i in hyp["impacts"] if sc in i["polarites"])
        _etape(E, "Élément", f"Comparer les forces injectées à celles simulées ({cibles})",
               f"event_instances/{hyp['id']}_{sc}.md, bloc impact_sur_variables ; "
               f"python3 generator/trace_injection.py --slug {hyp['id']} --type evenement --scenario {sc}",
               "l'IA de l'injection recalcule les forces : retoucher la fiche si elles s'écartent")
        if sum(i["force"] for i in hyp["impacts"]) >= 30:
            _etape(E, "Élément", "Gros choc : vérifier la lisibilité du moteur",
                   "python3 generator/banc_calibration.py --scenarios all --balayage-k 0.05", "S19")

    # 6. Nouvelles entités -----------------------------------------------------
    if cons.get("nouvelles_entites"):
        _etape(E, "Nouvelles entités", f"{len(cons['nouvelles_entites'])} entrée(s) prête(s) (bloc YAML ci-dessous) "
               "pour entites_custom/queue.yaml — catégorie à choisir",
               "python3 generator/create_entities_and_instances.py --mode custom",
               "la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario")

    # 7. Trajectoires ----------------------------------------------------------
    for t in cons.get("trajectoires") or []:
        inst = by_inst.get(t["instance"]) or {}
        notes = [t.get("raison") or ""]
        cmd = f"à la main : instances/{t['instance']}.md, champ `trajectoire`"
        if t["apres"] in TRAJ_TERMINALES and not inst.get("annee_fin"):
            cmd += " ; puis `annee_fin` (fix_annee_fin_manquant.py)"
        if (inst.get("injection") or {}).get("type") == "custom":
            notes.append("instance custom : ne régénérer qu'avec generate_instances.py --injection-custom")
        if inst.get("exclure_articles") or inst.get("priorite_forcee"):
            notes.append("marqueur exclure_articles / priorite_forcee : à reposer après toute régénération")
        _etape(E, "Trajectoires", f"{t.get('nom')} (`{t['instance']}`) : {t['avant']} → {t['apres']}",
               cmd, " ; ".join(n for n in notes if n))

    # 8. Relations -------------------------------------------------------------
    rels = cons.get("relations") or []
    for r in rels:
        champ = "alliances" if r["type"] == "alliance" else "oppositions"
        if r["action"] == "nouvelle":
            _etape(E, "Relations", f"{r['type']} nouvelle : {r['a_nom']} ↔ {r['b_nom']}",
                   f"à la main : ajouter `{r['b']}` dans `{champ}` de instances/{r['a']}.md", r.get("raison"))
        else:
            _etape(E, "Relations", f"{r['type']} rompue : {r['a_nom']} ↔ {r['b_nom']}",
                   f"à la main : retirer de `{champ}` dans les DEUX fiches ({r['a']}, {r['b']})",
                   "la réciprocité n'enlève rien")
    if any(r["action"] == "nouvelle" for r in rels):
        _etape(E, "Relations", "Rendre les relations réciproques",
               f"python3 generator/fix_alliances_oppositions.py --scenario {sc} --reciprocite-seule --ignorer-exclus",
               "étape 2 de Relations & lore (simulation d'abord)")

    # 9. Lore ------------------------------------------------------------------
    if zones_mortes or hyp.get("contraintes") or cons.get("zones_statut"):
        sujets = [f"zone `{z}`" for z in zones_mortes] + (["faits imposés de l'hypothèse"] if hyp.get("contraintes") else [])
        _etape(E, "Lore", "Règles à ajouter pour que l'audit du lore surveille : " + (", ".join(sujets) or "les statuts changés"),
               f"à la main : documentation/lore_regles.yaml, section {sc}",
               "comme les zones abandonnées de fortress_world (Nordgard, Koursk)")

    # 10. Articles et site -----------------------------------------------------
    entites_changees = {t["instance"] for t in cons.get("trajectoires") or []}
    a_rezoner = [a for a in donnees["articles"] if a["zone"] in zones_mortes]
    a_relire = [a for a in donnees["articles"] if a not in a_rezoner
                and (a["zone"] in zones_touchees or entites_changees & set(a["entites"]))]
    for a in a_rezoner[:MAX_LISTE]:
        _etape(E, "Articles et site", f"Rezoner « {a['titre']} » (`{a['zone']}`, {zones_mortes[a['zone']]})",
               f"python3 generator/rezoner_articles.py --corriger {a['fichier'][:24]}=<zone> --apply",
               "sinon non publiable sur le site ; puis reattribuer_signatures.py")
    if len(a_rezoner) > MAX_LISTE:
        _etape(E, "Articles et site", f"… et {len(a_rezoner) - MAX_LISTE} autre(s) article(s) à rezoner")
    if a_rezoner:
        _etape(E, "Articles et site", "Signatures des articles rezonés",
               "python3 generator/reattribuer_signatures.py", "aperçu, puis --apply")
    if a_relire:
        _etape(E, "Articles et site", f"{len(a_relire)} article(s) à relire (zone touchée ou entité dont la trajectoire change)",
               motif="; ".join(f"« {a['titre']} »" for a in a_relire[:MAX_LISTE])
               + (" …" if len(a_relire) > MAX_LISTE else ""))
    if E:
        _etape(E, "Articles et site", "Résumé du scénario",
               f"python3 generator/generate_resume_scenarios.py --scenario {sc}", "payant, un appel")
        _etape(E, "Articles et site", "Site des revues",
               "python3 generator/chapos_revues.py", "puis bash generator/publier_site.sh")

    # 11. Contrôles ------------------------------------------------------------
    if E:
        _etape(E, "Contrôles", "Base", "python3 generator/validate.py")
        if geo_ops:
            _etape(E, "Contrôles", "Géographie",
                   f"python3 generator/scan_geographie_complet.py --scenario {sc}"
                   + (" --check-overlays" if traces else ""),
                   f"{traces} tracé(s) dessiné(s)" if traces else None)
        _etape(E, "Contrôles", "Lore", f"python3 generator/audit_lore.py --scenario {sc}",
               "puis étapes 2 et 3 de Relations & lore si besoin")

    return {"etapes": E, "avert": donnees["avert"],
            "nouvelles_entites": cons.get("nouvelles_entites") or []}


def construire_application(hyp, resultats, consequences, geo, scenarios):
    out = {}
    for sc in scenarios:
        try:
            out[sc] = liste_application(hyp, sc, resultats.get(sc), consequences.get(sc),
                                        geo.get(sc), _donnees_application(sc))
        except Exception as e:  # la liste ne doit jamais empêcher le reste du rapport
            out[sc] = {"erreur": f"{type(e).__name__}: {e}", "etapes": []}
    return out


def _yaml_bloc(obj):
    return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=100).rstrip()


def _rendre_application(app, hyp, sc):
    L = ["### Liste d'application (à valider à la main — rien n'est écrit)", ""]
    if app.get("erreur"):
        return L + [f"_Liste impossible : {app['erreur']}_", ""]
    for a in app.get("avert") or []:
        L.append(f"- ⚠ {a}")
    if not app["etapes"]:
        return L + ["Rien à appliquer dans ce scénario.", ""]
    n = 0
    for section in SECTIONS_APPLICATION:
        etapes = [e for e in app["etapes"] if e["section"] == section]
        if not etapes:
            continue
        L.append(f"**{section}**")
        for e in etapes:
            n += 1
            txt = f"- [ ] {n}. {e['action']}"
            if e.get("commande"):
                cmd = e["commande"]
                txt += (f"\n  - `{cmd}`" if cmd.startswith(("python3 ", "bash ")) else f"\n  - {cmd}")
            if e.get("motif"):
                txt += f"\n  - _{e['motif']}_"
            L.append(txt)
        L.append("")
    if app.get("nouvelles_entites"):
        entrees = [{"nom": ne["nom"], "category": "<à choisir>", "role": ne["role"], "etat": "émergent",
                    "scenario_ref": sc, "scenario_hint": [sc],
                    **({"zone_hint": ne["zone"]} if ne.get("zone") and ne["zone"] != "transnationale" else {}),
                    "source": f"et_si_{hyp['id']}"} for ne in app["nouvelles_entites"]]
        L += ["Entrées pour `entites_custom/queue.yaml` :", "", "```yaml", _yaml_bloc(entrees), "```", ""]
    return L


def _rendre_injection_commune(hyp, application):
    """Entrée de queue commune aux scénarios (mode choc seulement)."""
    if hyp.get("mode") == "rupture" or not hyp.get("impacts"):
        return []
    scen = [sc for sc in hyp["scenarios"] if sc in application]
    if not scen:
        return []
    geo = any((application.get(sc) or {}).get("etapes") and hyp["geographie"].get(sc) for sc in scen)
    entree = {"id": hyp["id"], "description": hyp["description"] or hyp["nom"],
              "portee": "<locale | regionale | continentale | globale>" if geo else "globale",
              "date_approximative": int(hyp["date"]), "intensite": "<à choisir>",
              "persistance": hyp["persistance"], "scenarios": scen,
              "variables_hint": [i["variable"] for i in hyp["impacts"]],
              "variables_hint_count": len(hyp["impacts"]), "source": f"et_si_{hyp['id']}"}
    return ["## Liste d'application — injection commune", "",
            "Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). "
            "Les forces et polarités simulées ne sont pas transmises : l'injection les recalcule ; "
            "les comparer ensuite scénario par scénario (étape « Élément »).", "",
            "```yaml", _yaml_bloc([entree]), "```", ""]


'''

REMPLACEMENTS = [
    ('VERSION = "v7.9.1"', 'VERSION = "v8"'),
    ("def rendre_markdown(hyp, resultats, date_fin, avert, geo=None, consequences=None):",
     "def rendre_markdown(hyp, resultats, date_fin, avert, geo=None, consequences=None, application=None):"),
    ("    geo = geo or {}\n    consequences = consequences or {}\n",
     "    geo = geo or {}\n    consequences = consequences or {}\n    application = application or {}\n"),
    ("            if sc in geo:\n                L += _rendre_geo(geo[sc])\n            continue\n",
     "            if sc in geo:\n                L += _rendre_geo(geo[sc])\n"
     "            if sc in application:\n                L += _rendre_application(application[sc], hyp, sc)\n"
     "            continue\n"),
    ("        if sc in geo:\n            L += _rendre_geo(geo[sc])\n    return \"\\n\".join(L) + \"\\n\"\n",
     "        if sc in geo:\n            L += _rendre_geo(geo[sc])\n"
     "        if sc in application:\n            L += _rendre_application(application[sc], hyp, sc)\n"
     "    L += _rendre_injection_commune(hyp, application)\n"
     "    return \"\\n\".join(L) + \"\\n\"\n"),
    ('    sortie = {"hypothese": hyp, "date": args.date, "avertissements": avert,\n'
     '              "resultats": resultats, "consequences": consequences, "geographie": geo}\n',
     '    # V8 : liste d\'application (phase 3), lecture seule.\n'
     '    portee = [args.scenario] if args.scenario else hyp["scenarios"]\n'
     '    application = construire_application(hyp, resultats, consequences, geo, portee)\n'
     '    sortie = {"hypothese": hyp, "date": args.date, "avertissements": avert,\n'
     '              "resultats": resultats, "consequences": consequences, "geographie": geo,\n'
     '              "application": application}\n'),
    ("    md = rendre_markdown(hyp, resultats, args.date, avert, geo, consequences)\n",
     "    md = rendre_markdown(hyp, resultats, args.date, avert, geo, consequences, application)\n"),
]
ANCRE_BLOC = ("# ---------------------------------------------------------------------------\n"
              "# main\n")


def main():
    dry = "--dry-run" in sys.argv
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable")
    src = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in src:
        sys.exit("✗ Patch v8 déjà appliqué : rien à faire.")
    if 'VERSION = "v7.9.1"' not in src:
        sys.exit("✗ Ce patch attend simuler_et_si.py en v7.9.1.")
    nouveau = src
    for avant, apres in REMPLACEMENTS:
        n = nouveau.count(avant)
        if n != 1:
            sys.exit(f"✗ Ancre trouvée {n} fois (1 attendue) :\n{avant[:120]}")
        nouveau = nouveau.replace(avant, apres)
    if nouveau.count(ANCRE_BLOC) != 1:
        sys.exit("✗ Ancre de la section main introuvable ou multiple")
    nouveau = nouveau.replace(ANCRE_BLOC, BLOC + ANCRE_BLOC)
    try:
        compile(nouveau, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas : {e}")
    print(f"{len(REMPLACEMENTS) + 1} modifications prêtes ({len(nouveau) - len(src)} caractères ajoutés).")
    if dry:
        print("Aperçu seulement (--dry-run) : rien n'est écrit.")
        return
    sauvegarde = CIBLE.with_name(CIBLE.name + ".bak_v8")
    sauvegarde.write_text(src, encoding="utf-8")
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"✓ {CIBLE.name} passé en v8 (sauvegarde : {sauvegarde.name}).")


if __name__ == "__main__":
    main()
