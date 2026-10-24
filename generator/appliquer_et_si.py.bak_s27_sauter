#!/usr/bin/env python3
"""
appliquer_et_si.py — Ourrassol 2098 (S27, phase 4, 15 octobre 2026)
===================================================================

Applique au vault les conséquences d'une hypothèse « et si ? » ADOPTÉE ET
INJECTÉE, à partir des opérations enregistrées par sa dernière simulation
complète (generator/state/et_si_application/<id>.json, simulateur v8.19+).

Ce qui est appliqué (numéroté dans l'aperçu) :
  - statuts de zone (geographie/<sc>.md), puis texte du corps régénéré ;
  - trajectoires d'instances : une fiche dont la trajectoire actuelle n'est plus
    celle de la simulation est signalée ⚠ et sautée ; « disparu » ⇒ annee_fin =
    année de l'élément (même si elle était remplie) ; autre fin (transformé…) ⇒
    annee_fin remplie seulement si vide ;
  - relations : une entité qui disparaît est retirée de TOUTES les relations du
    scénario (calculé depuis le vault) et ses propres relations sont vidées ;
    relation rompue retirée des deux fiches ; relation nouvelle ajoutée ; puis
    réciprocité (fix_alliances_oppositions.py, opposition prioritaire) ;
  - carte (18 oct 2026) : absorber / nouvelle_zone de l'hypothèse, par la Carte (zone_repository),
    après les autres écritures ; les sous-zones qui ne portent que ce pays le gardent et suivent ;
    partition, région et sous-zones à plusieurs pays restent à la main ;
  - contrôle final : validate.py.
Ce qui est seulement listé (à faire à la main) : phrases à corriger, nouvelles
entités, règles de lore, carte, articles, site.

Tri : tout est inclus, sauf les opérations marquées ⚠ ; --sauter 3,7 retire
des opérations, --inclure 5 reprend une opération ⚠. Les « possibles » de la
passe ne sont jamais appliqués.

USAGE
    python3 generator/appliquer_et_si.py --id <hypothèse>                     # aperçu (rien écrit)
    python3 generator/appliquer_et_si.py --id <hypothèse> --sauter 3,7 --apply
Sauvegardes : <fichier>.bak_appliquer, refaite à chaque écriture (contenu juste avant).
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import yaml

GEN = Path(__file__).resolve().parent
VAULT = GEN.parent
sys.path.insert(0, str(GEN))
APP_DIR = GEN / "state" / "et_si_application"
INSTANCES = VAULT / "instances"
TERMINALES = {"transformé", "disparu", "historique", "mythifié"}
TRAJECTOIRES = ["émergent", "marginal", "ascendant", "dominant", "mature", "déclinant",
                "résiduel", "transformé", "disparu", "historique", "mythifié"]


# ---------------------------------------------------------------------------
# Outils texte
# ---------------------------------------------------------------------------

def plie(s):
    s = unicodedata.normalize("NFKD", str(s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def canon_traj(v):
    return {plie(t): t for t in TRAJECTOIRES}.get(plie(v))


def decoupe(texte):
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", texte, re.S)
    return (m.group(1), m.group(2), m.group(3), texte[m.end():]) if m else None


def lire_fm(fm_txt):
    try:
        fm = yaml.safe_load(re.sub(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]", r"\1", fm_txt)) or {}
        return fm if isinstance(fm, dict) else {}
    except yaml.YAMLError:
        return None


def nettoie(item):
    v = re.sub(r"^\s*-\s*", "", item).strip().strip("'\"")
    m = re.match(r"^\[\[([^\]|]+)(\|[^\]]*)?\]\]$", v)
    return (m.group(1) if m else v).strip()


def fiche(slug):
    return INSTANCES / f"{slug}.md"


def fm_de(slug):
    p = fiche(slug)
    if not p.exists():
        return None
    d = decoupe(p.read_text(encoding="utf-8"))
    return lire_fm(d[1]) if d else None


# ---------------------------------------------------------------------------
# Modifications élémentaires (texte en mémoire)
# ---------------------------------------------------------------------------

def liste_champ(fm_l, champ):
    """(index de la ligne du champ, [index des puces]) ou (None, []) ; liste en ligne : (i, None)."""
    for i, l in enumerate(fm_l):
        m = re.match(r"^" + champ + r":\s*(.*)$", l)
        if m:
            if m.group(1).strip().startswith("["):
                return i, None
            j, puces = i + 1, []
            while j < len(fm_l) and re.match(r"^\s*-\s+", fm_l[j]):
                puces.append(j)
                j += 1
            return i, puces
    return None, []


def retirer_du_champ(fm_l, champ, slug):
    i, puces = liste_champ(fm_l, champ)
    if i is None:
        return fm_l, 0
    if puces is None:
        items = yaml.safe_load(re.sub(r"^" + champ + r":\s*", "", fm_l[i])) or []
        garde = [x for x in items if str(x) != slug]
        if len(garde) == len(items):
            return fm_l, 0
        fm_l = fm_l[:]
        fm_l[i] = f"{champ}: [{', '.join(map(str, garde))}]" if garde else f"{champ}: []"
        return fm_l, 1
    a_retirer = [j for j in puces if nettoie(fm_l[j]) == slug]
    if not a_retirer:
        return fm_l, 0
    out = [l for k, l in enumerate(fm_l) if k not in a_retirer]
    if len(a_retirer) == len(puces):
        out[i] = f"{champ}: []"
    return out, len(a_retirer)


def ajouter_au_champ(fm_l, champ, slug):
    i, puces = liste_champ(fm_l, champ)
    fm_l = fm_l[:]
    if i is None:
        return fm_l + [f"{champ}:", f"- {slug}"], 1
    if puces is None:
        items = yaml.safe_load(re.sub(r"^" + champ + r":\s*", "", fm_l[i])) or []
        if slug in map(str, items):
            return fm_l, 0
        fm_l[i] = f"{champ}:"
        fm_l[i + 1:i + 1] = [f"- {x}" for x in items] + [f"- {slug}"]
        return fm_l, 1
    if any(nettoie(fm_l[j]) == slug for j in puces):
        return fm_l, 0
    pos = (puces[-1] + 1) if puces else i + 1
    retrait = re.match(r"^(\s*)", fm_l[puces[0]]).group(1) if puces else ""
    fm_l.insert(pos, f"{retrait}- {slug}")
    return fm_l, 1


def corps_relations(corps, champ, slug, ajouter):
    """Section « ## Relations » : sous-bloc **Alliés** / **Opposants**."""
    cle = "alli" if champ == "alliances" else "oppos"
    lignes, out, dans, bloc, n, dernier = corps.split("\n"), [], False, None, 0, None
    for l in lignes:
        if re.match(r"^##\s", l):
            dans, bloc = bool(re.match(r"^##\s+Relations\b", l)), None
        elif dans and re.match(r"^\*\*", l):
            bloc = "alli" if "alli" in plie(l) else ("oppos" if "oppos" in plie(l) or "rival" in plie(l) else None)
        if dans and bloc == cle and re.match(r"^\s*-\s+", l):
            if not ajouter and nettoie(l) == slug:
                n += 1
                continue
            if ajouter and nettoie(l) == slug:
                return corps, 0
        out.append(l)
        if dans and bloc == cle and (re.match(r"^\*\*", l) or re.match(r"^\s*-\s+", l)):
            dernier = len(out)
    if ajouter:
        if dernier is None:
            return corps, 0
        out.insert(dernier, f"- [[{slug}]]")
        return "\n".join(out), 1
    return "\n".join(out), n


class Ecritures:
    """Textes modifiés en mémoire ; écrits tous à la fin (sauvegarde .bak_appliquer)."""

    def __init__(self):
        self.textes = {}

    def lire(self, p):
        if p not in self.textes:
            self.textes[p] = p.read_text(encoding="utf-8")
        return self.textes[p]

    def poser(self, p, t):
        self.textes[p] = t

    def changes(self):
        return [p for p, t in self.textes.items() if p.read_text(encoding="utf-8") != t]

    def ecrire(self):
        n = 0
        for p in self.changes():
            # PATCH_S27_CARTE_RETOUCHES : sauvegarde refaite à chaque écriture (une opération
            # déjà faite n'écrit rien, relancer ne l'écrase donc pas par un état modifié).
            shutil.copy2(p, p.with_name(p.name + ".bak_appliquer"))
            p.write_text(self.textes[p], encoding="utf-8")
            n += 1
        return n


def modifier_relation(W, slug, champ, autre, ajouter):
    p = fiche(slug)
    if not p.exists():
        return 0
    d = decoupe(W.lire(p))
    if not d:
        return 0
    fm_l = d[1].split("\n")
    fm_l, n1 = (ajouter_au_champ if ajouter else retirer_du_champ)(fm_l, champ, autre)
    corps, n2 = corps_relations(d[3], champ, autre, ajouter)
    if n1 or n2:
        W.poser(p, d[0] + "\n".join(fm_l) + d[2] + corps)
    return n1


def vider_entite(W, sc, cible):
    """Retire `cible` de toutes les relations du scénario et vide les siennes. Retourne (fiches, retraits)."""
    fiches, retraits = set(), 0
    for p in sorted(INSTANCES.glob(f"*_{sc}.md")):
        d = decoupe(W.lire(p))
        if not d:
            continue
        fm = lire_fm(d[1]) or {}
        propres = p.stem == cible
        for champ in ("alliances", "oppositions"):
            valeurs = [str(x) for x in (fm.get(champ) or []) if x is not None] if isinstance(fm.get(champ), list) else []
            for v in (valeurs if propres else [cible] if cible in valeurs else []):
                if modifier_relation(W, p.stem, champ, v, False):
                    fiches.add(p.stem)
                    retraits += 1
    return fiches, retraits


def changer_trajectoire(W, slug, avant, apres, annee):
    p = fiche(slug)
    d = decoupe(W.lire(p))
    fm_l = d[1].split("\n")
    idx = [i for i, l in enumerate(fm_l) if re.match(r"^trajectoire:", l)]
    if len(idx) != 1:
        raise ValueError(f"{len(idx)} ligne(s) `trajectoire:`")
    fm_l[idx[0]] = f"trajectoire: {apres}"
    note = ""
    if apres in TERMINALES and annee is not None:
        idx_f = [i for i, l in enumerate(fm_l) if re.match(r"^annee_fin:", l)]
        val = re.sub(r"^annee_fin:\s*", "", fm_l[idx_f[0]]).strip() if idx_f else ""
        vide = val in ("", "null", "~", "None")
        if vide or (apres == "disparu" and val != str(annee)):
            if idx_f:
                fm_l[idx_f[0]] = f"annee_fin: {annee}"
            else:
                fm_l.insert(idx[0] + 1, f"annee_fin: {annee}")
            note = f"annee_fin {val or '(vide)'} → {annee}"
        else:
            note = f"annee_fin {val} gardée"
    fm_txt = "\n".join(fm_l)
    fm = lire_fm(fm_txt)
    if fm is None or fm.get("trajectoire") != apres:
        raise ValueError("relecture du frontmatter inattendue")
    W.poser(p, d[0] + fm_txt + d[2] + d[3])
    return note


def changer_statut_zone(W, sc, zone, avant, apres):
    p = VAULT / "geographie" / f"{sc}.md"
    L = W.lire(p).split("\n")
    debut = re.compile(r"^(\s*)-\s+slug:\s*['\"]?" + re.escape(zone) + r"['\"]?\s*$")
    blocs = [i for i, l in enumerate(L) if debut.match(l)]
    if len(blocs) != 1:
        raise ValueError(f"bloc de zone introuvable ou double ({len(blocs)})")
    i = blocs[0]
    ind = len(L[i]) - len(L[i].lstrip())
    fin = next((k for k in range(i + 1, len(L))
                if L[k].strip() and (len(L[k]) - len(L[k].lstrip()) <= ind or L[k].startswith("---"))), len(L))
    retrait = ind + (len(L[i].lstrip()) - len(L[i].lstrip()[1:].lstrip()))
    lignes = [k for k in range(i + 1, fin) if re.match(r"^ {" + str(retrait) + r"}statut:", L[k])]
    if len(lignes) != 1:
        raise ValueError(f"{len(lignes)} ligne(s) `statut` dans le bloc")
    actuel = re.sub(r"^\s+statut:\s*", "", L[lignes[0]]).strip().strip("'\"")
    if plie(actuel) != plie(avant):
        raise ValueError(f"statut actuel « {actuel} », pas « {avant} »")
    L[lignes[0]] = re.sub(r"(statut:\s*).*", lambda m: m.group(1) + apres, L[lignes[0]])
    W.poser(p, "\n".join(L))


def statut_zone(sc, zone):
    p = VAULT / "geographie" / f"{sc}.md"
    if not p.exists():
        return None
    d = decoupe(p.read_text(encoding="utf-8"))
    fm = lire_fm(d[1]) if d else None
    for z in (fm or {}).get("zones") or []:
        if isinstance(z, dict) and z.get("slug") == zone:
            return z.get("statut")
    return None


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

def construire_plan(data):
    annee = int(data["annee"]) if data.get("annee") is not None else None
    ops, a_main = [], []

    def op(sc, genre, texte, alerte=None, **k):
        ops.append(dict(n=len(ops) + 1, sc=sc, genre=genre, texte=texte, alerte=alerte, **k))

    for sc in data["scenarios"]:
        ps = data["par_scenario"].get(sc) or {}
        lec, pas = ps.get("lecture") or {}, ps.get("passe") or {}
        for e in ps.get("erreurs") or []:
            a_main.append(f"[{sc}] ⚠ {e} : ses opérations manquent")
        noms = {}
        for p in INSTANCES.glob(f"*_{sc}.md"):
            fm = fm_de(p.stem) or {}
            noms.setdefault(plie(fm.get("name")), []).append(p.stem)

        # Zones
        for z in lec.get("zones_statut") or []:
            actuel = statut_zone(sc, z["zone"])
            alerte = None
            if actuel is None:
                alerte = "zone introuvable dans la géographie"
            elif plie(actuel) == plie(z["apres"]):
                alerte = "déjà appliqué"
            elif plie(actuel) != plie(z["avant"]):
                alerte = f"statut actuel « {actuel} », pas « {z['avant']} »"
            op(sc, "zone", f"Zone `{z['zone']}` : {z['avant']} → {z['apres']}", alerte,
               zone=z["zone"], avant=z["avant"], apres=z["apres"])

        # Carte (PATCH_S27_CARTE) : absorber / nouvelle_zone ; partition et région à la main.
        by_z = {z.get("slug"): z for z in zones_geo(sc)}
        for c in ps.get("carte") or []:
            if c["action"] not in ("absorber", "nouvelle_zone"):
                a_main.append(f"[{sc}] carte : {c['action']} de {c['pays']} (tracés) : voir la liste "
                              "d'application du rapport")
                continue
            cible, z = c["cible"], by_z.get(c["cible"])
            alerte = None
            if c.get("erreurs"):
                alerte = "refusé au contrôle de la simulation : " + "; ".join(c["erreurs"][:2])
            elif porte_pays(z, c["pays"]):
                alerte = "déjà appliqué"
            elif c["action"] == "nouvelle_zone" and z:
                alerte = "slug déjà pris"
            elif c["action"] == "absorber" and not z:
                alerte = "zone introuvable dans la géographie"
            elif c.get("source") == "ia":
                alerte = "proposé par la lecture IA, absent de l'hypothèse"
            elif c.get("alertes"):
                alerte = "; ".join(c["alertes"][:2])
            texte = (f"Créer la zone `{cible}` ({(c.get('nouvelle_zone') or {}).get('nom')}) avec {c['pays']}"
                     if c["action"] == "nouvelle_zone" else f"Rattacher {c['pays']} à `{cible}`")
            op(sc, "carte", texte, alerte, pays=c["pays"], action=c["action"], cible=cible,
               nouvelle_zone=c.get("nouvelle_zone"), simples=c.get("simples") or [],
               a_repartir=c.get("a_repartir") or [], videes=c.get("videes") or [])

        # Trajectoires (lecture puis passe ; même instance, sorts différents : ⚠ sur les deux)
        trajs = [dict(t, source="lecture") for t in lec.get("trajectoires") or []] + \
                [dict(t, source="passe") for t in pas.get("trajectoires") or []]
        par_inst = {}
        for t in trajs:
            par_inst.setdefault(t["instance"], []).append(t)
        for inst, liste in par_inst.items():
            sorts = {canon_traj(t["apres"]) for t in liste}
            t = liste[-1]
            avant, apres = canon_traj(t["avant"]), canon_traj(t["apres"])
            fm = fm_de(inst)
            alerte = None
            if len(sorts) > 1:
                alerte = "lecture et passe divergent : " + " / ".join(sorted(s or "?" for s in sorts))
            elif fm is None:
                alerte = "fiche introuvable"
            elif not avant or not apres:
                alerte = "trajectoire inconnue"
            else:
                actuel = canon_traj(fm.get("trajectoire"))
                if actuel == apres:
                    alerte = "déjà appliqué"
                elif actuel != avant:
                    alerte = f"trajectoire actuelle « {fm.get('trajectoire')} », pas « {t['avant']} »"
                elif avant in ("émergent", "marginal") and apres in ("dominant", "mature"):
                    alerte = "saut d'un cran (sans passer par ascendant)"
            homon = [s for s in noms.get(plie((fm or {}).get("name")), []) if s != inst]
            if homon and not alerte:
                alerte = f"homonyme dans le scénario ({', '.join(homon)}) : doublon à fusionner d'abord ?"
            op(sc, "trajectoire", f"{(fm or {}).get('name') or inst} (`{inst}`) : {t['avant']} → {t['apres']}"
               f" [{', '.join(sorted({x['source'] for x in liste}))}]", alerte,
               instance=inst, avant=avant, apres=apres, annee=annee)

        # Disparitions : retrait exhaustif des relations, lié à l'opération de trajectoire.
        for o in [o for o in ops if o["sc"] == sc and o["genre"] == "trajectoire" and o["apres"] == "disparu"]:
            f, n = vider_entite(Ecritures(), sc, o["instance"]) if fiche(o["instance"]).exists() else (set(), 0)
            op(sc, "disparition", f"`{o['instance']}` disparaît : la retirer de toutes les relations de {sc}, "
               f"vider les siennes (suit l'opération {o['n']})", None if n else "déjà appliqué",
               instance=o["instance"], depend=o["n"])
        disparues = {o["instance"] for o in ops if o["sc"] == sc and o["genre"] == "trajectoire"
                     and o["apres"] == "disparu"}

        # Relations explicites
        vues = set()
        for r in [dict(x, source="lecture") for x in lec.get("relations") or []] + \
                 [dict(x, source="passe") for x in pas.get("relations") or []]:
            cle = (r["action"], r["type"], frozenset((r["a"], r["b"])))
            if cle in vues:
                continue
            vues.add(cle)
            champ = "alliances" if r["type"] == "alliance" else "oppositions"
            inverse = "oppositions" if champ == "alliances" else "alliances"
            if r["action"] == "rompue" and (r["a"] in disparues or r["b"] in disparues):
                continue   # couverte par l'opération de disparition
            fa, fb = fm_de(r["a"]), fm_de(r["b"])
            alerte = None
            if fa is None or fb is None:
                alerte = "fiche introuvable"
            elif r["action"] == "rompue":
                present = r["b"] in map(str, fa.get(champ) or []) or r["a"] in map(str, fb.get(champ) or [])
                if not present:
                    alerte = "déjà absente"
                elif any(m in plie(r.get("raison")) for m in ("dispar", "detrui", "n'existe plus")):
                    alerte = "justifiée par une disparition que rien ne déclare"
            else:
                if r["b"] in map(str, fa.get(champ) or []):
                    alerte = "déjà présente"
                elif r["b"] in map(str, fa.get(inverse) or []) or r["a"] in map(str, fb.get(inverse) or []):
                    alerte = f"contredit une {inverse[:-1]} existante"
            op(sc, "relation", f"{r['type']} {r['action']} : {r.get('a_nom') or r['a']} ↔ "
               f"{r.get('b_nom') or r['b']} [{r['source']}]", alerte,
               a=r["a"], b=r["b"], champ=champ, action=r["action"])

        # À la main
        for t in pas.get("textes") or []:
            a_main.append(f"[{sc}] phrase à corriger dans `{t['slug']}` : « {str(t.get('extrait'))[:120]} »")
        if lec.get("nouvelles_entites"):
            a_main.append(f"[{sc}] {len(lec['nouvelles_entites'])} nouvelle(s) entité(s) proposée(s) : "
                          "voir le rapport (bloc YAML)")
    if data.get("contraintes"):
        a_main.append("règles de lore pour les contraintes de l'hypothèse : documentation/lore_regles.yaml")
    a_main.append("carte, articles à relire, résumé du scénario, site : voir la liste d'application du rapport")
    return ops, a_main


# ---------------------------------------------------------------------------
# Check-list « reste à faire » (17 oct 2026)
# ---------------------------------------------------------------------------

NEED_ACTION = VAULT / "documentation" / "need_action"


def _titre_article(fm, corps, defaut):
    """Titre d'un article : frontmatter, sinon premier « # » du texte, sinon première ligne non vide."""
    if fm.get("titre") or fm.get("title"):
        return str(fm.get("titre") or fm.get("title")).strip()
    lignes = [l.strip() for l in corps.split("\n") if l.strip()]
    for l in lignes:
        if re.match(r"^#\s+", l):
            return re.sub(r"^#\s+", "", l).strip()
    if lignes:
        return re.sub(r"^[#*\s]+|[*\s]+$", "", lignes[0]) or defaut
    return defaut


def _articles_concernes(sc, entites, zones):
    """Articles du scénario qui citent une entité touchée ou dont la zone principale a changé."""
    trouves = []
    racine = VAULT / "articles"
    if not racine.exists():
        return trouves
    courts = {e: e[: -len(sc) - 1] if e.endswith("_" + sc) else e for e in entites}
    for p in sorted(racine.rglob("*.md")):
        if p.name.startswith("_"):
            continue
        try:
            d = decoupe(p.read_text(encoding="utf-8"))
        except OSError:
            continue
        fm = lire_fm(d[1]) if d else None
        if not fm or fm.get("scenario") != sc:
            continue
        cites = {str(x) for x in (fm.get("entites_citees") or []) if x}
        motifs = [f"cite `{e}`" for e in entites if e in cites or courts[e] in cites]
        if fm.get("zone_principale") in zones:
            motifs.append(f"zone `{fm['zone_principale']}`")
        if motifs:
            titre = _titre_article(fm, d[3], p.stem)
            date = fm.get("date_evenement") or fm.get("date_publication") or ""
            trouves.append((p.relative_to(VAULT), str(titre).strip(), date, motifs))
    return trouves


def ecrire_reste_a_faire(data, ops, rapport_ok=True):
    """Écrit documentation/need_action/et_si_<id>_reste_a_faire.md. Retourne le chemin."""
    hid, annee = data["id"], int(data["annee"]) if data.get("annee") is not None else None
    L = [f"# Reste à faire à la main — {hid}", "",
         f"*Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')} par appliquer_et_si.py, à partir de la "
         f"simulation du {data.get('date_simulation')} ({data.get('version')}). Les opérations mécaniques "
         "(zones, trajectoires, relations) sont déjà appliquées : ne figure ici que ce qui reste à la main.*", ""]
    n = 0

    def case(texte):
        nonlocal n
        n += 1
        L.append(f"- [ ] {n}. {texte}")

    faites = lambda o: o.get("retenue") or o.get("alerte") == "déjà appliqué"
    for sc in data["scenarios"]:
        ps = data["par_scenario"].get(sc) or {}
        lec, pas = ps.get("lecture") or {}, ps.get("passe") or {}
        mes_ops = [o for o in ops if o["sc"] == sc]
        L += [f"## {sc}", ""]

        # Opérations laissées de côté (⚠)
        cote = [o for o in mes_ops if not o.get("retenue") and o.get("alerte")
                and not str(o["alerte"]).startswith("déjà")]
        if cote:
            L += ["### Décisions laissées de côté (⚠)", ""]
            for o in cote:
                case(f"{o['texte']} — ⚠ {o['alerte']}. Garder tel quel, ou "
                     f"`python3 generator/appliquer_et_si.py --id {hid} --inclure {o['n']} --apply`.")
            L.append("")

        # PATCH_S27_CARTE : suites de la carte
        cartes = [o for o in mes_ops if o["genre"] == "carte" and faites(o)]
        if cartes:
            L += ["### Carte", ""]
            for o in cartes:
                for s in o.get("a_repartir") or []:
                    case(f"Sous-zone `{s['slug']}` ({s.get('nom') or s['slug']}) : elle porte aussi "
                         f"{', '.join(s['autres'])} et a perdu {o['pays']}. Au choix : la laisser ainsi ; la "
                         f"déplacer entière sous `{o['cible']}` (Carte → arbre → ↗️ déplacer) ; ou lui rendre une "
                         f"portion de {o['pays']} par un tracé (Carte → ✏️ éditer → ✏️ dessiner).")
                for v in o.get("videes") or []:
                    case(f"`{v}` n'a plus aucun territoire : la garder (vestige, exil) ou la supprimer "
                         "(Carte → ✏️ éditer → Zone dangereuse).")
                if o["action"] == "nouvelle_zone":
                    case(f"Description, relations (alliés / rivaux) de `{o['cible']}` : `geographie/{sc}.md` "
                         "(la création n'en écrit aucune)")
                    case(f"Rédactions de `{o['cible']}` : `python3 generator/generate_journaux.py --scenario {sc} "
                         "--update`, puis `python3 generator/audit_couverture_journalistes.py --report`")
                    case("Continent de la nouvelle zone sur le site : `python3 generator/export_revues.py --continents`")
            case(f"Contrôle de la géographie : `python3 generator/scan_geographie_complet.py --scenario {sc}`")
            L.append("")

        # Phrases à corriger
        textes = pas.get("textes") or []
        if textes:
            L += ["### Phrases à corriger", ""]
            for t in textes:
                dossier = "instances" if t.get("genre", "instance") == "instance" else "event_instances"
                case(f"`{dossier}/{t['slug']}.md` ({t.get('nom') or t['slug']})")
                L.append(f"  - Phrase : « {t.get('extrait')} »")
                if t.get("contredit"):
                    L.append(f"  - Contredite par : {t['contredit']}")
                if not t.get("extrait_trouve", True):
                    L.append("  - ⚠ extrait introuvable mot pour mot dans la fiche : chercher la phrase voisine.")
            L.append("")

        # Nouvelles entités
        nouv = lec.get("nouvelles_entites") or []
        if nouv:
            L += ["### Nouvelles entités proposées (facultatif)", ""]
            case(f"{len(nouv)} entité(s) : choisir `category`, garder ou retirer chaque entrée, coller dans "
                 "`entites_custom/queue.yaml`, puis `python3 generator/create_entities_and_instances.py --mode custom`.")
            L += ["", "```yaml"]
            for e in nouv:
                # PATCH_S27_CATEGORIES : catégorie de la lecture IA si elle existe (v8.21).
                L += [f"- nom: {e.get('nom')}", f"  category: {e.get('category') or '<à choisir>'}",
                      f"  role: {e.get('role')}",
                      "  etat: émergent", f"  scenario_ref: {sc}", "  scenario_hint:", f"  - {sc}"]
                if e.get("zone"):
                    L.append(f"  zone_hint: {e['zone']}")
                L.append(f"  source: et_si_{hid}")
            L += ["```", ""]

        # Règle de lore (brouillon)
        disparues = [o for o in mes_ops if o["genre"] == "trajectoire" and o.get("apres") == "disparu" and faites(o)]
        if disparues or data.get("contraintes"):
            L += ["### Règle de lore (brouillon)", ""]
            case(f"Relire puis ajouter à `documentation/lore_regles.yaml`, section `{sc}` "
                 "(vérifier le format sur une règle existante, par exemple `bruxelles_pas_un_centre`).")
            L += ["", "```yaml", f"# section {sc} > regles"]
            for o in disparues:
                nom = re.sub(r"\s*\(`.*$", "", o["texte"])
                L += [f"- id: {o['instance'][: -len(sc) - 1] if o['instance'].endswith('_' + sc) else o['instance']}_disparu_{annee}",
                      f"  termes: [\"{nom}\"]", "  gravite: a_relire",
                      f"  message: \"{nom} disparaît en {annee} ({data.get('nom') or hid}) : "
                      f"toute mention au présent après {annee} est fausse.\""]
            for c in data.get("contraintes") or []:
                L.append(f"# contrainte à transformer si besoin : {c}")
            L += ["```", ""]

        # Articles
        ents = [o["instance"] for o in mes_ops if o["genre"] == "trajectoire" and faites(o)]
        zones = {o["zone"] for o in mes_ops if o["genre"] == "zone" and faites(o)}
        arts = _articles_concernes(sc, ents, zones)
        L += ["### Articles à relire", ""]
        if arts:
            for chemin, titre, date, motifs in arts:
                case(f"`{chemin}` — *{titre}*" + (f", {date}" if date else "") + f" ({', '.join(motifs)})")
        else:
            L.append("Aucun article du vault ne cite une entité touchée ni n'a pour zone une zone changée.")
        L.append("")

        # Fin
        L += ["### Pour finir", ""]
        case(f"Relecture du lore : `python3 generator/audit_lore.py --scenario {sc}` (puis étapes 2 et 3 de "
             "Relations & lore si besoin)")
        case(f"Résumé du scénario (payant, un appel) : `python3 generator/generate_resume_scenarios.py --scenario {sc}`")
        L.append("")

    L += ["## Site", ""]
    case("Si des articles ont été corrigés : `python3 generator/chapos_revues.py`, puis `bash generator/publier_site.sh`")
    L += ["", "## Non repris ici", "",
          f"Les « possibles » de la passe exhaustive, les tracés de carte et les fiches trouvées par mots-clés restent "
          f"dans le rapport du simulateur : `documentation/need_action/et_si_{hid}.md`"
          + ("" if rapport_ok else " (introuvable : resimuler pour le régénérer)") + "."]
    NEED_ACTION.mkdir(parents=True, exist_ok=True)
    sortie = NEED_ACTION / f"et_si_{hid}_reste_a_faire.md"
    sortie.write_text("\n".join(L) + "\n", encoding="utf-8")
    return sortie


# ---------------------------------------------------------------------------
# Carte (PATCH_S27_CARTE, 18 oct 2026) : absorber / nouvelle_zone par la Carte
# ---------------------------------------------------------------------------

def zones_geo(sc):
    p = VAULT / "geographie" / f"{sc}.md"
    if not p.exists():
        return []
    d = decoupe(p.read_text(encoding="utf-8"))
    fm = lire_fm(d[1]) if d else None
    return [z for z in (fm or {}).get("zones") or [] if isinstance(z, dict)]


def porte_pays(zone, pays):
    return any(isinstance(o, dict) and plie(o.get("entite")) == plie(pays)
               for o in (zone or {}).get("origine_reelle") or [])


def porte_pays_cite(zone, pays):
    """PATCH_S27_CARTE_SOUS_ZONES : la zone cite-t-elle `pays` dans une de ses entrées, lue par
    mots (« Île de Kharg, Iran », « Détroit d'Ormuz (Oman/Iran) ») comme la simulation et la Carte ?"""
    cherche = plie(pays)
    for o in (zone or {}).get("origine_reelle") or []:
        if not isinstance(o, dict):
            continue
        texte = plie(o.get("entite"))
        morceaux = [re.sub(r"\([^)]*\)", "", texte)] + re.findall(r"\(([^)]*)\)", texte)
        if any(t.strip() == cherche for m in morceaux for t in re.split(r"[,/]", m)):
            return True
    return False


def note_carte(o):
    parts = []
    if o.get("simples"):
        parts.append(f"puis sous-zone(s) rattachée(s) à `{o['cible']}` en gardant {o['pays']} : "
                     + ", ".join(o["simples"]))
    if o.get("a_repartir"):
        parts.append("à répartir à la main (étape ⑤) : "
                     + ", ".join(f"{s['slug']} (aussi {', '.join(s['autres'])})" for s in o["a_repartir"]))
    if o.get("videes"):
        parts.append("zone(s) vidée(s) de tout territoire : " + ", ".join(o["videes"]))
    return "\n         → ".join(parts)


def _repo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("zone_repository", VAULT / "gui" / "zone_repository.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ZoneRepository(VAULT, VAULT / "gui")


def appliquer_carte(repo, o):
    """Un changement de carte ; lève une exception si le résultat n'est pas celui attendu."""
    import copy
    sc, pays, cible = o["sc"], o["pays"], o["cible"]
    by = {z.get("slug"): z for z in repo.load_all_zones(sc)}
    simples = [s for s in o.get("simples") or [] if s in by]
    gardees = {s: copy.deepcopy(by[s].get("origine_reelle") or []) for s in simples}
    hautes = [s for s in simples if by[s].get("parent") not in simples]   # le sous-arbre suit
    # PATCH_S27_CARTE_RETOUCHES : type d'origine du territoire (la Carte écrit « pays » par défaut).
    types = [x.get("type_entite") for z in by.values() for x in z.get("origine_reelle") or []
             if isinstance(x, dict) and plie(x.get("entite")) == plie(pays) and x.get("type_entite")]
    type_orig = types[0] if types else None
    if o["action"] == "nouvelle_zone":
        repo.assign_pays(sc, pays, "creer", nouvelle_zone=dict(o.get("nouvelle_zone") or {}))
    else:
        repo.assign_pays(sc, pays, "absorber", zone_slug=cible)
    type_garde = False
    if gardees or (type_orig and type_orig != "pays"):
        gf = repo._load_geo(sc)
        for z in gf.zones:
            if z.get("slug") in gardees:
                z["origine_reelle"] = gardees[z["slug"]]
            if z.get("slug") == cible and type_orig and type_orig != "pays":
                for x in z.get("origine_reelle") or []:
                    if isinstance(x, dict) and x.get("entite") == pays and x.get("type_entite") != type_orig:
                        x["type_entite"], type_garde = type_orig, True
        if gardees or type_garde:
            repo._save_geo(gf)
        for s in hautes:
            if by[s].get("parent") != cible:
                repo.reparent(sc, s, cible, dry_run=False)
    apres = {z.get("slug"): z for z in repo.load_all_zones(sc)}
    if not porte_pays(apres.get(cible), pays):
        raise ValueError(f"{pays} absent de `{cible}` après l'opération")
    for s in hautes:
        if (apres.get(s) or {}).get("parent") != cible or not porte_pays_cite(apres.get(s), pays):
            raise ValueError(f"sous-zone `{s}` mal rattachée après l'opération")
    return (f"✓ {o['n']}. {o['texte']}"
            + (f" ; {len(hautes)} sous-zone(s) rattachée(s) : {', '.join(hautes)}" if hautes else "")
            + (f" ; type {type_orig} gardé" if type_garde else ""))


def appliquer_cartes(cartes):
    """Toutes les opérations de carte retenues, après les autres écritures. Échec : géographie et
    zones_pays.json remis en l'état d'avant la carte. Retourne (nombre fait, messages)."""
    repo = _repo()
    fichiers = [repo._zones_pays_path()] + sorted({VAULT / "geographie" / f"{o['sc']}.md" for o in cartes})
    avant = {p: p.read_text(encoding="utf-8") for p in fichiers if p.exists()}
    for p in avant:   # PATCH_S27_CARTE_RETOUCHES : sauvegarde neuve à chaque application
        shutil.copy2(p, p.with_name(p.name + ".bak_appliquer"))
    msgs = []
    try:
        for o in cartes:
            msgs.append(appliquer_carte(repo, o))
    except Exception as e:
        for p, t in avant.items():
            p.write_text(t, encoding="utf-8")
        for o in cartes:
            o["retenue"], o["alerte"] = False, f"échec à l'écriture : {type(e).__name__}: {e}"
        return 0, [f"✗ carte non appliquée ({type(e).__name__}: {e}) : géographie et zones_pays.json "
                   "remis en l'état ; le reste est écrit."]
    return len(cartes), msgs


def lancer(cmd):
    print(f"  $ {' '.join(cmd)}")
    r = subprocess.run([sys.executable] + cmd, cwd=VAULT, capture_output=True, text=True)
    sortie = (r.stdout + r.stderr).strip().splitlines()
    for l in sortie[-6:]:
        print(f"    {l}")
    return r.returncode == 0


def nombres(s):
    return {int(x) for x in re.findall(r"\d+", s or "")}


def main():
    ap = argparse.ArgumentParser(description="Applique les conséquences d'une hypothèse injectée (aperçu par défaut).")
    ap.add_argument("--id", required=True)
    ap.add_argument("--sauter", default="", help="numéros d'opérations à ne pas appliquer (ex. 3,7)")
    ap.add_argument("--inclure", default="", help="numéros d'opérations ⚠ à appliquer quand même")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--reste-a-faire", action="store_true",
                    help="écrit seulement la check-list des tâches à la main (vault inchangé)")
    a = ap.parse_args()

    src = APP_DIR / f"{a.id}.json"
    if not src.exists():
        sys.exit(f"✗ {src.relative_to(VAULT)} absent : simuler l'hypothèse avec le simulateur v8.19 ou plus "
                 f"(simulation complète, lecture IA et passe exhaustive conseillées).")
    data = json.loads(src.read_text(encoding="utf-8"))
    if not data.get("complet"):
        sys.exit("✗ la dernière simulation est limitée à " + ", ".join(data.get("scenarios") or [])
                 + " : relancer la simulation sans --scenario.")
    import et_si_dossiers as ed
    dossier = ed.charger().get(a.id) or {}
    st = ed.statut(a.id, dossier)
    if st != "injecté":
        sys.exit(f"✗ {a.id} est « {st} » : n'appliquer qu'une hypothèse adoptée ET injectée.")
    sim = dossier.get("simulation") or {}
    if sim.get("empreinte") != data.get("empreinte"):
        sys.exit("✗ les opérations ne viennent pas de la simulation enregistrée au dossier : resimuler.")
    dec = dossier.get("decision") or {}
    if dec.get("empreinte") and dec["empreinte"] != data.get("empreinte"):
        sys.exit("✗ la simulation a changé depuis l'adoption : vérifier avant d'appliquer.")
    if data.get("mode") == "rupture":
        # PATCH_S19_CHAINE : la rupture est jouée par le moteur si les fiches portent `mode: rupture`.
        manque = []
        for sc in data["scenarios"]:
            p = VAULT / "event_instances" / f"{a.id}_{sc}.md"
            d = decoupe(p.read_text(encoding="utf-8")) if p.exists() else None
            fm = lire_fm(d[1]) if d else None
            if not fm or str(fm.get("mode") or "").strip().lower() != "rupture":
                manque.append(f"event_instances/{p.name}" + ("" if p.exists() else " (absente)"))
        if manque:
            sys.exit("✗ mode rupture, mais ces fiches ne portent pas `mode: rupture` : " + ", ".join(manque)
                     + ". Le moteur les jouerait comme un choc : ajouter la ligne `mode: rupture` "
                       "(sous `persistance:`) avant d'appliquer.")

    ops, a_main = construire_plan(data)
    sauter, inclure = nombres(a.sauter), nombres(a.inclure)
    for o in ops:
        o["retenue"] = (o["n"] not in sauter) and (not o["alerte"] or o["n"] in inclure) \
            and o["alerte"] not in ("déjà appliqué", "déjà absente", "déjà présente", "fiche introuvable",
                                    "zone introuvable dans la géographie", "trajectoire inconnue",
                                    "slug déjà pris") \
            and not str(o["alerte"] or "").startswith("refusé")   # PATCH_S27_CARTE
    par_n = {o["n"]: o for o in ops}
    for o in ops:
        dep = par_n.get(o.get("depend"))
        if dep and not (dep["retenue"] or dep["alerte"] == "déjà appliqué"):
            o["retenue"] = False

    W = Ecritures()
    erreurs, notes = [], {}
    for o in [o for o in ops if o["retenue"]]:
        try:
            if o["genre"] == "zone":
                changer_statut_zone(W, o["sc"], o["zone"], o["avant"], o["apres"])
            elif o["genre"] == "trajectoire":
                notes[o["n"]] = changer_trajectoire(W, o["instance"], o["avant"], o["apres"], o["annee"])
            elif o["genre"] == "disparition":
                f, n = vider_entite(W, o["sc"], o["instance"])
                notes[o["n"]] = f"{n} retrait(s) dans {len(f)} fiche(s)"
            elif o["genre"] == "relation":
                ajouter = o["action"] == "nouvelle"
                n = modifier_relation(W, o["a"], o["champ"], o["b"], ajouter)
                if not ajouter:
                    n += modifier_relation(W, o["b"], o["champ"], o["a"], False)
                notes[o["n"]] = f"{n} modification(s)"
            elif o["genre"] == "carte":   # PATCH_S27_CARTE : écrite après les autres (--apply)
                notes[o["n"]] = note_carte(o)
        except (ValueError, OSError) as e:
            erreurs.append(f"{o['n']}. {e}")

    print(("ÉCRITURE" if a.apply else "APERÇU (rien écrit)")
          + f" — {a.id}, simulation du {data.get('date_simulation')} ({data.get('version')})\n")
    sc_courant = None
    for o in ops:
        if o["sc"] != sc_courant:
            sc_courant = o["sc"]
            print(f"=== {sc_courant}")
        marque = "✓" if o["retenue"] else "–"
        ligne = f"  {marque} {o['n']:>3}. {o['texte']}"
        if o["alerte"] and str(o["alerte"]).startswith("déjà"):
            ligne += f"\n         · {o['alerte']}"
        elif o["alerte"]:
            ligne += f"\n         ⚠ {o['alerte']}" + ("" if o["retenue"] else
                                                     ("" if o["alerte"].startswith("déjà") else
                                                      f" — sautée (--inclure {o['n']} pour l'appliquer)"))
        elif not o["retenue"]:
            ligne += "  (sautée)"
        if o["n"] in notes and notes[o["n"]]:
            ligne += f"\n         → {notes[o['n']]}"
        print(ligne)
    if not ops:
        print("  (aucune opération enregistrée : lecture IA et passe exhaustive absentes ?)")
    print("\nÀ faire à la main (non appliqué) :")
    print("\n".join(f"  - {x}" for x in a_main))
    changes = W.changes()
    print(f"\nFichiers modifiés : {len(changes)}")
    sc_carte = sorted({o["sc"] for o in ops if o["retenue"] and o["genre"] == "carte"})
    if sc_carte:   # PATCH_S27_CARTE_RETOUCHES
        print("  + carte, écrite après les autres : "
              + ", ".join(f"geographie/{sc}.md" for sc in sc_carte) + ", gui/zones_pays.json")
    if erreurs:
        print("\n✗ Refusé :\n" + "\n".join(f"  {e}" for e in erreurs))
        sys.exit("✗ Rien n'est écrit tant qu'une opération échoue (--sauter son numéro, ou corriger la fiche).")
    rapport_ok = (VAULT / "documentation" / "need_action" / f"et_si_{a.id}.md").exists()
    if not a.apply:
        if a.reste_a_faire:
            p = ecrire_reste_a_faire(data, ops, rapport_ok)
            print(f"\n✓ check-list : {p.relative_to(VAULT)} (vault inchangé)")
            return
        print("Relancer avec --apply pour écrire (sauvegarde .bak_appliquer), --sauter / --inclure pour trier ;")
        print("--reste-a-faire pour écrire seulement la check-list des tâches à la main.")
        return

    n = W.ecrire()
    cartes = [o for o in ops if o["retenue"] and o["genre"] == "carte"]   # PATCH_S27_CARTE
    print(f"\n✓ {n} fichier(s) écrit(s)" + (" (hors carte, ci-dessous)." if cartes else "."))   # PATCH_S27_LIBELLES
    if cartes:
        print("Carte :")
        faits, msgs = appliquer_cartes(cartes)
        for m in msgs:
            print(f"  {m}")
        n += faits
    retenues = [o for o in ops if o["retenue"]]
    for sc in dict.fromkeys(o["sc"] for o in retenues):
        if any(o["sc"] == sc and o["genre"] in ("zone", "carte") for o in retenues):
            lancer(["generator/regenerer_corps_geographie.py", "--scenario", sc, "--execute"])
        if any(o["sc"] == sc and o["genre"] in ("relation", "disparition") for o in retenues):
            lancer(["generator/fix_alliances_oppositions.py", "--scenario", sc, "--reciprocite-seule",
                    "--ignorer-exclus", "--resoudre-conflits", "--bascule-en-opposition"])
    lancer(["generator/validate.py"])
    p = ecrire_reste_a_faire(data, ops, rapport_ok)
    print(f"✓ check-list : {p.relative_to(VAULT)}")
    journal = APP_DIR / f"{a.id}.applique.json"
    if n == 0 and journal.exists():
        print(f"· rien de nouveau appliqué : journal {journal.relative_to(VAULT)} inchangé")
        return
    journal.write_text(json.dumps({"date": datetime.now().isoformat(timespec="minutes"),
                                   "simulation": data.get("date_simulation"),
                                   "appliquees": [o["n"] for o in retenues],
                                   "sautees": [o["n"] for o in ops if not o["retenue"]]},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ journal : {journal.relative_to(VAULT)}")


if __name__ == "__main__":
    main()
