#!/usr/bin/env python3
"""
patch_s27_v89.py — Ourrassol 2098 (S27, 10 octobre 2026)

Simulateur « et si ? » v8.8 → v8.9 (liste d'application, après le test sur
extreme_droite_2034) : hypothèse sans pays ni nom propre à chercher, la
section « Fiches à relire » le dit et propose la relecture IA
(audit_lore.py --llm : estimation, 10 fiches de plus fort impact, zones au
statut changé) au lieu de rester vide.

Usage (depuis la racine du vault) :
    python3 generator/patch_s27_v89.py --dry-run
    python3 generator/patch_s27_v89.py
Sauvegarde : generator/simuler_et_si.py.bak_v89. Refuse un second passage.
"""
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "simuler_et_si.py"
DEBUT = ("# ---------------------------------------------------------------------------\n"
         "# Liste d'application (phase 3, v8, 10 octobre 2026 ; v8.1 à v8.8)\n")
FIN = ("# ---------------------------------------------------------------------------\n"
       "# main\n")
BLOC = r'''# ---------------------------------------------------------------------------
# Liste d'application (phase 3, v8, 10 octobre 2026 ; v8.1 à v8.9)
# ---------------------------------------------------------------------------
# Tout ce que l'hypothèse imposerait de changer, scénario par scénario, dans
# l'ordre, avec l'outil à lancer ou « à la main ». Lecture seule, aucun appel
# IA : construite à partir des résultats déjà calculés (niveaux, lecture IA
# gardée, carte évaluée) et de trois scans du vault (instances / événements
# localisés, articles, rédactions de journaux.yaml).

SECTIONS_APPLICATION = ["Carte", "Localisation des fiches", "Journaux", "Statuts de zone",
                        "Élément", "Nouvelles entités", "Trajectoires", "Relations", "Lore",
                        "Fiches à relire", "Articles et site", "Contrôles"]
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


def _titre_corps(path):
    """V8.1 : premier titre du corps (# Titre ou **Titre**)."""
    import re as _re
    try:
        txt = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    corps = _re.sub(r"^---\s*\n.*?\n---\s*\n", "", txt, count=1, flags=_re.DOTALL)
    for ligne in corps.splitlines():
        ligne = ligne.strip()
        m = _re.match(r"^(?:#+\s*(.+)|\*\*(.+?)\*\*)$", ligne)
        if m:
            return (m.group(1) or m.group(2)).strip()
        if ligne:
            break
    return ""


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
        try:
            texte = p.read_text(encoding="utf-8")
        except OSError:
            texte = ""
        ent = fm.get("entites_citees") or []
        out.append({"fichier": p.name, "chemin": str(p.relative_to(VAULT_ROOT)),
                    "titre": str(fm.get("titre") or _titre_corps(p) or fm.get("slug") or p.stem),
                    "zone": fm.get("zone_principale") or "",
                    "entites": [str(e) for e in ent] if isinstance(ent, list) else [],
                    "texte": _plie(texte)})   # V8.2 : pour chercher le pays cité
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
    d = {"instances": [], "evenements": [], "articles": [], "redactions": None, "avert": [], "zones": []}
    try:   # V8.4 : zones chargées une fois (sous-zones citées, recherche de citations)
        repo, _ = charger_zone_repository()
        d["zones"] = repo.load_all_zones(sc) or []
    except Exception as e:
        d["avert"].append(f"zones illisibles : {type(e).__name__}: {e}")
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



# --- V8.3 : fiches qui citent les pays, villes ou noms propres de l'hypothèse ---
MAX_FICHES = 25            # fiches listées par type (le reste est compté)
MOTS_GENERIQUES = {"Invasion", "Conflit", "Crise", "Guerre", "Effondrement", "Percée", "Fusion",
                   "Peste", "Pandémie", "Montée", "Victoire", "Chute", "Arrivée", "Majorité",
                   "États", "Etats", "État", "Etat", "Nations", "République", "Royaume"}


def _plie_aligne(texte):
    """Minuscules sans accents, un caractère pour un caractère (positions conservées)."""
    import unicodedata
    out = []
    for c in str(texte or ""):
        d = unicodedata.normalize("NFKD", c.lower())
        base = next((x for x in d if not unicodedata.combining(x)), c.lower())
        out.append(base if len(base) == 1 else c.lower())
    return "".join(out)


_PAYS_CONNUS = None


def _pays_connus():
    """V8.5 : noms de pays (français) de gui/static/pays_mapping.json, en cache."""
    global _PAYS_CONNUS
    if _PAYS_CONNUS is None:
        try:
            _PAYS_CONNUS = list(json.loads((VAULT_ROOT / "gui" / "static" / "pays_mapping.json")
                                           .read_text(encoding="utf-8")))
        except (OSError, ValueError):
            _PAYS_CONNUS = []
    return _PAYS_CONNUS


def _autres_pays(entite, pays):
    """Pays (autres que `pays`) nommés dans une entrée origine_reelle ; une ville ou une
    région du même pays n'en est pas un."""
    import re as _re
    e = _plie_aligne(entite)
    pp = _plie_aligne(pays)
    # V8.6 : « États-Unis » et « États-Unis d'Amérique » désignent le même pays.
    return [p for p in _pays_connus() if _plie_aligne(p) not in pp and pp not in _plie_aligne(p)
            and _re.search(r"(?<![a-z0-9])" + _re.escape(_plie_aligne(p)) + r"(?![a-z0-9])", e)]


def _termes_hypothese(hyp, sc, geo_ops):
    """{terme: origine} : pays dont la carte change (et leurs grandes villes), pays cités
    dans le nom ou la description, noms propres de l'hypothèse."""
    import re as _re
    termes = {}
    try:
        mapping = json.loads((VAULT_ROOT / "gui" / "static" / "pays_mapping.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        mapping = {}
    try:
        villes = json.loads((VAULT_ROOT / "gui" / "static" / "villes_principales.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        villes = []
    ops_hyp = (hyp.get("geographie") or {}).get(sc) or []
    pays_carte = [op["pays"] for op, g in zip(ops_hyp, geo_ops or []) if not g.get("erreurs")]
    for p in pays_carte:
        termes.setdefault(p, "pays dont la carte change")
        en = mapping.get(p)
        for v in villes if en else []:
            if isinstance(v, dict) and v.get("nom") and str(v.get("pays", "")) == en:
                termes.setdefault(v["nom"], f"ville ({p})")
    texte_h = f"{hyp.get('nom', '')} {hyp.get('description', '')}"
    plie_h = _plie_aligne(texte_h)
    for p in mapping:
        if _re.search(r"(?<![a-z0-9])" + _re.escape(_plie_aligne(p)) + r"(?![a-z0-9])", plie_h):
            termes.setdefault(p, "pays cité par l'hypothèse")
    for texte_part in (hyp.get("nom", ""), hyp.get("description", "")):
        for m in _re.finditer(r"\b[A-ZÉÈÀÂÎÔÛÇ][\wéèêàâîôûçë'-]{3,}", str(texte_part)):
            avant = str(texte_part)[:m.start()]
            # Un mot qui ouvre une phrase n'est pas forcément un nom propre (« Pression sur… »).
            debut_phrase = not avant.strip() or _re.search(r"[.!?:;]\s*$", avant)
            # V8.8 : second membre d'un mot composé (« pétro-États ») : pas un nom propre.
            compose = avant.endswith("-")
            if m.group(0) not in MOTS_GENERIQUES and not debut_phrase and not compose:
                termes.setdefault(m.group(0), "nom cité par l'hypothèse")
    # V8.8 : un même terme écrit deux fois (« Arabie Saoudite » / « Arabie saoudite ») : le premier reste ;
    # un nom propre isolé contenu dans un terme plus long (« Arabie » ⊂ « Arabie saoudite ») : retiré.
    vus, uniques = set(), {}
    for t, o in termes.items():
        k = " ".join(_plie_aligne(t).split())
        if k not in vus:
            vus.add(k)
            uniques[t] = o
    plies = {t: " ".join(_plie_aligne(t).split()) for t in uniques}
    return {t: o for t, o in uniques.items()
            if not (o == "nom cité par l'hypothèse"
                    and any(u != t and _re.search(r"(?<![a-z0-9])" + _re.escape(plies[t]) + r"(?![a-z0-9])", plies[u])
                            for u in uniques))}


def _homonymes_pays(termes):
    """V8.7 : villes qui portent aussi le nom d'un pays (Salvador / El Salvador).
    On ne les cherche pas dans une liste de territoires, où elles désignent le pays."""
    import re as _re
    pays_plies = set()
    for p in _pays_connus():
        fp = " ".join(_re.sub(r"[^a-z0-9]+", " ", _plie_aligne(p)).split())
        pays_plies.add(fp)
        # « El Salvador », « Salvador (El) », « Salvador, El » → « salvador »
        pays_plies.add(_re.sub(r"^(el|le|la|les) | (el|le|la|les)$", "", fp))
    return {t for t, o in termes.items() if str(o).startswith("ville (") and " ".join(_re.sub(r"[^a-z0-9]+", " ", _plie_aligne(t)).split()) in pays_plies}


def _trouve(texte, termes_plies):
    """Premier terme trouvé (mot entier) dans texte : (terme, extrait) ou None."""
    import re as _re
    if not texte:
        return None
    plie = _plie_aligne(texte)
    for terme, motif_re in termes_plies:
        m = motif_re.search(plie)
        if m:
            debut = max(0, m.start() - 60)
            extrait = " ".join(str(texte)[debut:m.end() + 80].split())
            return terme, ("…" if debut else "") + extrait + "…"
    return None


def fiches_citant(hyp, sc, geo_ops, donnees):
    """Instances, événements, zones et lignes du registre (après la date de l'hypothèse)
    qui citent un des termes. Retourne {type: [{"slug", "terme", "extrait"}]} et les termes."""
    import re as _re
    termes = _termes_hypothese(hyp, sc, geo_ops)
    if not termes:
        return {}, termes
    termes_plies = [(t, _re.compile(r"(?<![a-z0-9])" + _re.escape(_plie_aligne(t)) + r"(?![a-z0-9])"))
                    for t in sorted(termes, key=len, reverse=True)]
    homonymes = _homonymes_pays(termes)
    plies_terr = [(t, m) for t, m in termes_plies if t not in homonymes]
    out = {"Instances": [], "Événements": [], "Zones": [], "Registre (après la date)": []}

    def _ajoute(type_, slug, champs, territoires=None):
        for k, champ in enumerate(champs):
            r = _trouve(champ, plies_terr if k == territoires else termes_plies)
            if r:
                out[type_].append({"slug": slug, "terme": r[0], "extrait": r[1]})
                return

    for i in donnees["instances"]:
        _ajoute("Instances", i.get("slug"), [i.get("name"), i.get("role_dans_scenario"), i.get("responsabilites"),
                                            i.get("description_journalistique"), i.get("tensions_narratives"),
                                            i.get("signes_distinctifs"), (i.get("localisation") or {}).get("lieu")])
    for ev in donnees["evenements"]:
        _ajoute("Événements", ev.get("slug"), [ev.get("name"), ev.get("description"), ev.get("consequences"),
                                              ev.get("realisation")])
    for z in donnees.get("zones") or []:
        lieux = " ; ".join(str(l.get("nom") if isinstance(l, dict) else l)
                           for l in (z.get("lieux_emblematiques") or []))
        origines = " ; ".join(str(o.get("entite")) for o in (z.get("origine_reelle") or []) if isinstance(o, dict))
        _ajoute("Zones", z.get("slug"), [z.get("nom"), origines, z.get("description"), z.get("tensions_internes"), lieux],
                territoires=1)
    try:
        texte = (SCRIPT_DIR / "registre_evenements.md").read_text(encoding="utf-8")
        m = _re.search(r"^##\s+" + _re.escape(sc) + r"\s*$(.*?)(?=^##\s|\Z)", texte, _re.M | _re.S)
        for ligne in (m.group(1).splitlines() if m else []):
            if not ligne.startswith("|") or _re.match(r"^\|[\s:|-]+\|?$", ligne):
                continue
            annees = [int(a) for a in _re.findall(r"\b(20\d\d)\b", ligne)]
            if annees and min(annees) > hyp["date"]:
                cellules = [c.strip() for c in ligne.strip("|").split("|")]
                _ajoute("Registre (après la date)", " | ".join(c for c in cellules[:3] if c)[:90], [ligne])
    except OSError:
        donnees["avert"].append("registre_evenements.md introuvable : chronologie non vérifiée")
    return {k: v for k, v in out.items() if v}, termes

def _etape(liste, section, action, commande=None, motif=None):
    liste.append({"section": section, "action": action, "commande": commande, "motif": motif})


def liste_application(hyp, sc, res, cons, geo_ops, donnees):
    """Étapes à valider à la main pour CE scénario. Rien n'est écrit."""
    E = []
    cons = cons if cons and not cons.get("erreur") else {}
    ops_hyp = (hyp.get("geographie") or {}).get(sc) or []
    by_inst = {i.get("slug"): i for i in donnees["instances"]}
    redac = donnees["redactions"] or {}
    # V8.2 : zones_touchees = {zone: {pays perdus ou coupés}} ; zones_statut_chg à part.
    zones_mortes, zones_nouvelles, zones_touchees, traces = {}, [], {}, 0
    zones_statut_chg = set()
    redaction_a_creer, orateurs_a_creer = [], []
    # V8.4 : citations calculées d'abord (servent à la carte et à la localisation).
    cites, termes = fiches_citant(hyp, sc, geo_ops, donnees)
    by_zone = {z.get("slug"): z for z in donnees.get("zones") or []}

    def _du_pays(terme, pays):
        return terme == pays or termes.get(terme) == f"ville ({pays})"

    # 1. Carte -----------------------------------------------------------------
    for op, g in zip(ops_hyp, geo_ops or []):
        pays = g["pays"]
        if g.get("erreurs"):
            if op.get("source") != "ia":   # V8.1 : une proposition IA écartée n'est pas une étape
                _etape(E, "Carte", f"{pays} ({g['action']}) refusé au contrôle : corriger l'hypothèse avant toute application",
                       motif="; ".join(g["erreurs"][:3]))
            continue
        for a in g.get("alertes") or []:   # V8.4 : les alertes de la carte deviennent des étapes
            if "déjà partagé" in a:      # partition : déjà traité par les étapes de retrait (v8.1)
                continue
            _etape(E, "Carte", f"⚠ {pays} : {a}", motif="à trancher avant d'appliquer ce changement")
        cibles_op = ({p["cible"] for p in g.get("parties") or []} if g["action"] == "partition"
                     else ({g["cible"]} if g["action"] in ("absorber", "nouvelle_zone") else set()))
        for a in g.get("actuelles") or []:
            # V8.1 : zones qui PERDENT le pays (ou le voient coupé) ; une zone qui reçoit
            # un morceau n'a pas d'articles à relire pour autant.
            if a["slug"] not in cibles_op or g["action"] == "partition":
                zones_touchees.setdefault(a["slug"], set()).add(pays)
        if g["action"] == "absorber":
            _etape(E, "Carte", f"Rattacher {pays} à `{g['cible']}`",
                   f"Carte → clic sur {pays} → affecter à `{g['cible']}`",
                   "le pays change de mains")
        elif g["action"] == "nouvelle_zone":
            nz = op.get("nouvelle_zone") or {}
            _etape(E, "Carte", f"Créer la zone `{g['cible']}` ({nz.get('nom')}) avec {pays}",
                   f"Carte → clic sur {pays} → créer une zone (slug `{g['cible']}`, type {nz.get('type') or 'autre'}, "
                   f"statut {nz.get('statut') or 'emergent'})", "nouvelle zone de niveau 1")
            zones_nouvelles.append({"slug": g["cible"], "pays": pays})
        elif g["action"] == "partition":
            cibles = {p["cible"] for p in g["parties"]}
            for a in g.get("actuelles") or []:
                if a["slug"] not in cibles and (a.get("portion") or a["type"] == "overlay"):
                    _etape(E, "Carte", f"Retirer la portion actuelle de {pays} dans `{a['slug']}`"
                           + (f" (« {a['portion']} »)" if a.get("portion") else ""),
                           f"Carte → ✏️ éditer `{a['slug']}` → 🗑️ supprimer le masque ({pays})",
                           "la partition remplace les portions et tracés actuels")
                elif a["slug"] in cibles and a["type"] != "overlay" and not a.get("portion"):
                    _etape(E, "Carte", f"`{a['slug']}` porte aujourd'hui {pays} entier : il n'en gardera qu'une portion",
                           f"Carte → ✏️ éditer `{a['slug']}` : vérifier que l'entrée {pays} devient une portion",
                           "sinon la couleur pays entier reste sur tout le pays")
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
        # V8.4 : jamais une sous-zone vers elle-même ; une sous-zone à plusieurs pays n'est
        # pas rattachée en bloc.
        orph = [o for o in ((g.get("impact") or {}).get("sous_zones_orphelines") or [])
                if o.get("slug") and o.get("slug") != g.get("cible")]
        simples = []
        for o in orph:
            autres = []   # V8.5 : seulement d'autres PAYS (pas une ville ou une région du pays)
            for x in ((by_zone.get(o["slug"]) or {}).get("origine_reelle") or []):
                if isinstance(x, dict) and x.get("entite") and _autres_pays(str(x["entite"]), pays):
                    autres.append(str(x["entite"]))
            if autres:
                _etape(E, "Carte", f"`{o['slug']}` porte aussi {', '.join(autres[:3])}"
                       + (" …" if len(autres) > 3 else "") + " : la répartir à la main, pas en bloc",
                       "Carte → arbre → ↗️ déplacer, ou nouvelle sous-zone pour la part de " + pays,
                       f"sous-zone de {pays} à plusieurs pays")
            else:
                simples.append(o)
        if simples and g["action"] in ("absorber", "nouvelle_zone"):
            _etape(E, "Carte", f"{len(simples)} sous-zone(s) de {pays} à rattacher à `{g['cible']}`",
                   f"python3 generator/reparenter_sous_zones_orphelines.py --scenario {sc} --zone-cible {g['cible']}",
                   ", ".join(o["slug"] for o in simples[:MAX_LISTE]))
        # V8.4-V8.8 : zones liées au pays par son nom ou une de ses villes.
        #  - sous-zone d'une zone qui perd le pays : citée n'importe où (nom, territoires, texte) ;
        #  - ailleurs (sous-zone rangée sous une autre zone, ou zone de niveau 1) : seulement si la
        #    ville figure dans son NOM ou ses TERRITOIRES réels (une description qui cite São Paulo
        #    ne fait pas d'une zone de Séoul une zone brésilienne).
        import re as _re
        deja_orph = {o["slug"] for o in orph} | {x.get("slug") for x in g.get("a_repartir") or []}
        actuelles_slugs = {a["slug"] for a in g.get("actuelles") or []}
        perdantes = {a["slug"] for a in g.get("actuelles") or []
                     if (a.get("niveau") or 1) == 1 and (a["slug"] not in cibles_op or g["action"] == "partition")}
        termes_pays = [t for t, o in termes.items() if t == pays or o == f"ville ({pays})"]
        motifs_pays = [(t, _re.compile(r"(?<![a-z0-9])" + _re.escape(_plie_aligne(t)) + r"(?![a-z0-9])"))
                       for t in sorted(termes_pays, key=len, reverse=True)]
        villes_pays = {t for t in termes_pays if t != pays}
        homonymes = _homonymes_pays(termes)
        motifs_terr = [(t, m) for t, m in motifs_pays if t not in homonymes]
        cites_zones = {it["slug"]: it for it in cites.get("Zones") or []}
        dest = (f"`{g['cible']}`" if g["action"] in ("absorber", "nouvelle_zone")
                else "la partie qui la contient" if g["action"] == "partition" else "sa zone actuelle")
        for zslug, z in by_zone.items():
            if not zslug or zslug in deja_orph or zslug == g.get("cible") or zslug in actuelles_slugs:
                continue
            racine = _racine_n1(zslug, by_zone)
            if racine == g.get("cible"):
                continue
            terr = " ; ".join(str(x.get("entite")) for x in (z.get("origine_reelle") or [])
                              if isinstance(x, dict) and x.get("entite"))
            # V8.7 : une ville homonyme d'un pays compte dans le nom, pas dans les territoires.
            r = _trouve(str(z.get("nom") or ""), motifs_pays) or _trouve(terr, motifs_terr)
            if (z.get("niveau") or 1) > 1:
                # V8.8 : sous-zone dont les territoires désignent un autre pays (Haïfa citant Ispahan) : pas à déplacer.
                autre_pays = not r and terr and _autres_pays(terr, pays)
                if racine in perdantes and (r or zslug in cites_zones) and not autre_pays:
                    terme = r[0] if r else cites_zones[zslug]["terme"]
                    extrait = r[1] if r else cites_zones[zslug]["extrait"]
                    if r or _du_pays(terme, pays):
                        _etape(E, "Carte", f"Sous-zone `{zslug}` (cite « {terme} ») : à déplacer avec {pays} ?",
                               f"Carte → arbre → ↗️ déplacer vers {dest}", extrait)
                elif r and r[0] in villes_pays:
                    _etape(E, "Carte", f"Sous-zone `{zslug}` (sous `{racine}`, nom ou territoire « {r[0]} ») : "
                           f"à déplacer avec {pays} ?", f"Carte → arbre → ↗️ déplacer vers {dest}",
                           "rangée hors de la zone qui perd le pays : vérifier")
            elif r and r[0] in villes_pays:
                _etape(E, "Carte", f"Zone de niveau 1 `{zslug}` (nom ou territoire « {r[0]} ») : reste à part ou "
                       f"rejoint {dest} ?", "à décider ; la rattacher = Carte → arbre → ↗️ déplacer",
                       "zone indépendante sur le territoire du pays")
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
        zones_statut_chg.add(z["zone"])
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
    # V8.4 : une fiche d'une sous-zone déplacée en bloc la suit (rien à faire). En
    # partition, une fiche localisée DANS une zone coupée et qui cite le pays ou une de
    # ses villes peut tomber dans une autre portion.
    loc_inst = {i.get("slug"): (i.get("localisation") or {}).get("zone") for i in donnees["instances"]}
    loc_inst.update({ev.get("slug"): (ev.get("localisation") or {}).get("zone") for ev in donnees["evenements"]})
    for g in geo_ops or []:
        if g.get("erreurs") or g["action"] != "partition":
            continue
        coupees = {a["slug"] for a in g.get("actuelles") or []}
        for type_ in ("Instances", "Événements"):
            for it in cites.get(type_) or []:
                if loc_inst.get(it["slug"]) in coupees and _du_pays(it["terme"], g["pays"]):
                    _localiser(it["slug"], type_[:-1], f"localisé(e) dans `{loc_inst[it['slug']]}`, coupée ; "
                               f"cite « {it['terme']} » : lieu à vérifier contre les portions")

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
    if zones_mortes or hyp.get("contraintes"):
        sujets = [f"zone `{z}`" for z in zones_mortes] + (["faits imposés de l'hypothèse"] if hyp.get("contraintes") else [])
        _etape(E, "Lore", "Règles à ajouter pour que l'audit du lore surveille : " + ", ".join(sujets),
               f"à la main : documentation/lore_regles.yaml, section {sc}",
               "comme les zones abandonnées de fortress_world (Nordgard, Koursk)")

    # 9 bis. Fiches à relire (V8.3) ------------------------------------------------
    if cites:
        _etape(E, "Fiches à relire", "Termes cherchés : " + ", ".join(sorted(termes)[:20])
               + (f" … (+{len(termes) - 20})" if len(termes) > 20 else ""),
               motif="mot entier, sans casse ni accents ; le registre seulement après "
               f"{hyp['date']:g} (chronologie)")
        for type_, items in cites.items():
            for it in items[:MAX_FICHES]:
                _etape(E, "Fiches à relire", f"{type_[:-1] if type_.endswith('s') else type_} `{it['slug']}` "
                       f"cite « {it['terme']} »", motif=it["extrait"])
            if len(items) > MAX_FICHES:
                _etape(E, "Fiches à relire", f"… et {len(items) - MAX_FICHES} autre(s) parmi : {type_.lower()}",
                       motif="liste complète : generator/state/dernier_et_si.json, clé application")
        if cites.get("Instances"):
            _etape(E, "Fiches à relire", "Relecture IA ciblée d'une instance (contradictions avec l'hypothèse)",
                   f"python3 generator/audit_lore.py --scenario {sc} --llm --slug <slug>",
                   "payant (≈ 0,5 centime la fiche) ; après application de la carte et de l'événement")

    else:
        # V8.9 : rien à chercher par mots (hypothèse mondiale, sans pays ni nom propre) :
        # une fiche peut la contredire sans la nommer ; seule la relecture IA la trouve.
        _etape(E, "Fiches à relire", "Aucun pays ni nom propre à chercher : la recherche par mots ne cible aucune fiche",
               motif="une hypothèse mondiale peut contredire des fiches sans les nommer : relecture IA ci-dessous, "
               "après l'ajout des faits imposés dans lore_regles.yaml (section Lore)")
        _etape(E, "Fiches à relire", "Estimer la relecture IA des fiches de plus fort impact",
               f"python3 generator/audit_lore.py --scenario {sc} --llm --estimer --limit 10", "aucun appel")
        _etape(E, "Fiches à relire", "Relecture IA des 10 fiches de plus fort impact (contradictions avec l'hypothèse)",
               f"python3 generator/audit_lore.py --scenario {sc} --llm --limit 10",
               "payant (≈ 0,5 centime la fiche) ; après application de l'événement")
        for z in sorted(zones_statut_chg)[:MAX_LISTE]:
            _etape(E, "Fiches à relire", f"Relecture IA des fiches de la zone `{z}` (statut changé)",
                   f"python3 generator/audit_lore.py --scenario {sc} --llm --zone {z}",
                   "estimer d'abord avec --estimer ; payant")

    # 10. Articles et site -----------------------------------------------------
    entites_changees = {t["instance"] for t in cons.get("trajectoires") or []}
    a_rezoner = [a for a in donnees["articles"] if a["zone"] in zones_mortes]
    import re as _re

    def _cite(a, pays):
        return _re.search(r"(?<![a-z0-9])" + _re.escape(_plie(pays)) + r"(?![a-z0-9])", a["texte"]) is not None

    # V8.2 : zone qui perd ou voit couper un pays -> seulement les articles qui citent ce pays.
    a_relire = [a for a in donnees["articles"] if a not in a_rezoner
                and (a["zone"] in zones_statut_chg
                     or any(_cite(a, p) for p in zones_touchees.get(a["zone"], ()))
                     or entites_changees & set(a["entites"]))]
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
        _etape(E, "Articles et site", f"{len(a_relire)} article(s) à relire (zone au statut changé, pays cité ou entité dont la trajectoire change)",
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

    sources_ia = any(op.get("source") == "ia" for op in ops_hyp) or any(
        cons.get(k) for k in ("trajectoires", "relations", "zones_statut", "nouvelles_entites"))
    return {"etapes": E, "avert": donnees["avert"], "sources_ia": sources_ia, "fiches_citant": cites,
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
    if app.get("sources_ia") and app["etapes"]:
        L += ["_Carte et conséquences tirées de la lecture IA (un tirage) : relire chaque étape avant de "
              "l'appliquer ; écarter une proposition suffit à sauter ses étapes._", ""]
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
    partiel = [sc for sc in hyp["scenarios"] if sc not in application]
    return ["## Liste d'application — injection commune", "",
            ("⚠ Simulation limitée à " + ", ".join(scen) + " : ajouter à `scenarios` les autres scénarios "
             "de l'hypothèse (" + ", ".join(partiel) + ") avant d'injecter.\n\n" if partiel else "")
            + "Entrée pour `evenements_custom/queue.yaml` (une seule pour tous les scénarios). "
            "Les forces et polarités simulées ne sont pas transmises : l'injection les recalcule ; "
            "les comparer ensuite scénario par scénario (étape « Élément »).", "",
            "```yaml", _yaml_bloc([entree]), "```", ""]


'''


def main():
    dry = "--dry-run" in sys.argv
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable")
    src = CIBLE.read_text(encoding="utf-8")
    if 'VERSION = "v8.9"' in src:
        sys.exit("✗ Patch v8.9 déjà appliqué : rien à faire.")
    if 'VERSION = "v8.8"' not in src or src.count(DEBUT) != 1 or src.count(FIN) != 1:
        sys.exit("✗ Ce patch attend simuler_et_si.py en v8.8 (lancer d'abord patch_s27_v88.py).")
    i, j = src.index(DEBUT), src.index(FIN)
    if j < i:
        sys.exit("✗ Ordre des sections inattendu.")
    nouveau = src[:i] + BLOC + src[j:]
    nouveau = nouveau.replace('VERSION = "v8.8"', 'VERSION = "v8.9"', 1)
    try:
        compile(nouveau, str(CIBLE), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ Le fichier patché ne compile pas : {e}")
    print(f"Bloc « liste d'application » remplacé ({len(src[i:j])} → {len(BLOC)} caractères), version v8.9.")
    if dry:
        print("Aperçu seulement (--dry-run) : rien n'est écrit.")
        return
    sauvegarde = CIBLE.with_name(CIBLE.name + ".bak_v89")
    sauvegarde.write_text(src, encoding="utf-8")
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"✓ {CIBLE.name} passé en v8.9 (sauvegarde : {sauvegarde.name}).")


if __name__ == "__main__":
    main()
