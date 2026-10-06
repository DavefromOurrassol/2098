"""
rezoner_articles.py -- S23, 3 octobre 2026.

Corrige zone_principale des articles hérités. Avant le 21 août 2026, ce
champ a été reconstitué après coup (enrich_articles_pre_p20.py), et les
bugs #26 (avant le 11 juillet) et "zone_principale incohérente" (corrigé
le 25 août) l'ont faussé -- or le site rattache chaque article à son
journal (donc revue, rubrique continent) d'après ce champ.

Périmètre : articles générés jusqu'à --jusqu-au (défaut 2026-08-25),
plus tout article sans zone_principale quelle que soit sa date.

Pour chacun, le LLM lit le titre et le début du texte et choisit, parmi
les zones N1 qui ont une rédaction dans journaux.yaml (scénario + ligne
éditoriale de l'article), celle où se déroule l'action principale -- ou
"aucune" (article transnational). Règles de décision :
  - "aucune"                         -> zone actuelle conservée
  - N1 proposée == N1 actuelle       -> zone actuelle conservée (plus précise)
  - N1 proposée hors liste           -> signalé, non appliqué
  - sinon                            -> changement proposé

Deux passes séparées :
  python3 rezoner_articles.py            # appelle le LLM (cache
                                         # state/rezonage_articles.json, un
                                         # article déjà classé n'est jamais
                                         # rappelé), écrit le rapport
                                         # state/rezonage_rapport.md,
                                         # NE TOUCHE PAS aux articles
  python3 rezoner_articles.py --apply    # lit le cache SEUL (aucun appel),
                                         # réécrit zone_principale
                                         # (.bak_rezonage) -- confiance
                                         # "faible" exclue sauf
                                         # --inclure-faibles
Options : --scenario X, --limite N (essai sur N articles), --tier T.
"""
import argparse
import functools
import glob
import json
import os
import re
import shutil
import time

import yaml

import prompt_builder as pb
from llm_client import call_llm

pb._load_geographie = functools.lru_cache(None)(pb._load_geographie)

ICI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ICI, "state", "rezonage_articles.json")
RAPPORT = os.path.join(ICI, "state", "rezonage_rapport.md")

SYSTEM = (
    "Tu classes des articles de presse fictifs (monde de 2098) par zone "
    "géographique. Tu réponds UNIQUEMENT par un objet JSON, sans aucun "
    "autre texte."
)

CONSIGNE = """Voici les zones possibles (slug : nom — description) :
{zones}

Voici le début de l'article :
---
{texte}
---

Dans quelle zone se déroule l'ACTION PRINCIPALE de l'article (lieu des
faits rapportés, pas les lieux seulement mentionnés en passant) ?
Une zone couvre ses pays ET ses sous-zones : un lieu situé dans une
sous-zone listée appartient à cette zone, même si une autre zone est
géographiquement plus proche.
Si l'article n'a pas de lieu principal (sujet mondial, plusieurs
continents à égalité), réponds "aucune". S'il a un lieu principal
qu'AUCUNE zone de la liste ne couvre (ni par ses pays, ni par ses
sous-zones), réponds "hors_zones" -- ne choisis pas la zone la plus
proche par défaut.

Réponds par ce JSON exact :
{{"zone": "<slug de la liste, aucune ou hors_zones>", "lieu": "<lieu principal cité, quelques mots>", "confiance": "<haute|moyenne|faible>"}}"""


def frontmatter(texte):
    m = re.match(r"^---\n(.*?)\n---\n", texte, re.S)
    if not m:
        return None, None
    return (yaml.safe_load(m.group(1)) or {}), m.end()


def zones_candidates(J, sc, li):
    """Zones N1 ayant une rédaction pour (scénario, ligne), avec nom/description."""
    zones = [z for z in pb._load_geographie(sc) if z.get("slug")]
    geo = {z["slug"]: z for z in zones}
    out = {}
    for slug in (J.get(sc, {}).get(li, {}).get("zones") or {}):
        z = geo.get(slug, {})
        desc = (z.get("description") or "").replace("\n", " ")
        pays = ", ".join(
            str(e.get("entite")) for e in (z.get("origine_reelle") or [])
            if isinstance(e, dict) and e.get("entite"))
        # Sous-zones (tous niveaux) rattachées à cette N1, par leur nom :
        # sans elles, le LLM ne peut pas savoir qu'une sous-zone narrative
        # (ex. Hanse Baltique sous Genève-Bunker, breakdown) appartient à
        # cette N1 et choisit la N1 géographiquement la plus proche.
        sous = sorted(
            g.get("nom", s) for s, g in geo.items()
            if s != slug and pb._resoudre_zone_n1(s, sc) == slug)
        out[slug] = "{} — {}{}{}".format(
            z.get("nom", slug), desc[:110],
            " | pays : {}".format(pays[:140]) if pays else "",
            " | sous-zones : {}".format(", ".join(sous)[:200]) if sous else "")
    return out


def lire_cache():
    try:
        return json.load(open(CACHE, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def ecrire_cache(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(c, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)


def articles(args):
    for f in sorted(glob.glob(os.path.join(ICI, "..", "articles", "*", "*.md"))):
        if f.endswith("_index.md"):
            continue
        sc = os.path.basename(os.path.dirname(f))
        if args.scenario and sc != args.scenario:
            continue
        t = open(f, encoding="utf-8").read()
        fm, fin = frontmatter(t)
        if fm is None:
            continue
        d = str(fm.get("date_generation", ""))[:10]
        z = fm.get("zone_principale") or ""
        if d <= args.jusqu_au or not z:
            yield f, sc, fm, t[fin:]


def classer(f, sc, fm, corps, J, args):
    li = fm.get("ligne_editoriale") or "pro_pouvoir"
    cands = zones_candidates(J, sc, li)
    if not cands:
        return {"erreur": "aucune zone avec rédaction pour {}/{}".format(sc, li)}
    texte = re.sub(r"\n{2,}", "\n", corps.strip())[:1800]
    prompt = CONSIGNE.format(
        zones="\n".join("- {} : {}".format(s, d) for s, d in sorted(cands.items())),
        texte=texte)
    rep = None
    for essai in range(3):
        try:
            rep = call_llm(SYSTEM, prompt, max_tokens=150, task_tier=args.tier)
            break
        except RuntimeError as e:  # 503 / surcharge : passagers
            print("  ⏳ {} — essai {}/3 : {}".format(os.path.basename(f)[:50], essai + 1, str(e)[:90]))
            time.sleep(15 * (essai + 1))
    if rep is None:
        return None  # non mis en cache : repris au prochain lancement
    m = re.search(r"\{.*\}", rep or "", re.S)
    if not m:
        return {"erreur": "réponse illisible : {}".format((rep or "")[:80])}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"erreur": "JSON invalide : {}".format(m.group(0)[:80])}


def decision(sc, fm, rep, J):
    """Retourne (statut, nouvelle_zone)."""
    if "erreur" in rep:
        return "erreur", None
    li = fm.get("ligne_editoriale") or "pro_pouvoir"
    z = fm.get("zone_principale") or ""
    n1_actuelle = pb._resoudre_zone_n1(z, sc) if z else ""
    prop = (rep.get("zone") or "").strip()
    if prop in ("", "aucune"):
        return "inchange_transnational", None
    if prop == "hors_zones":
        return "hors_zones", None
    if prop not in (J.get(sc, {}).get(li, {}).get("zones") or {}):
        return "hors_liste", None
    if prop == n1_actuelle:
        return "inchange", None
    return "change", prop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--inclure-faibles", action="store_true")
    ap.add_argument("--jusqu-au", default="2026-08-25")
    ap.add_argument("--scenario")
    ap.add_argument("--limite", type=int)
    ap.add_argument("--tier", default="structured_strict")
    ap.add_argument("--corriger", action="append", default=[], metavar="DEBUT_FICHIER=ZONE",
                    help="correction manuelle inscrite dans le cache (répétable), "
                         "ex. 20260821_100154=zone_euro_sud")
    args = ap.parse_args()

    J = yaml.safe_load(open(os.path.join(ICI, "journaux.yaml"), encoding="utf-8"))
    cache = lire_cache()
    if args.corriger:
        tous = [os.path.basename(f) for f in glob.glob(os.path.join(ICI, "..", "articles", "*", "*.md"))]
        for item in args.corriger:
            debut, _, zone = item.partition("=")
            trouves = [n for n in tous if n.startswith(debut.strip())]
            if len(trouves) != 1 or not zone.strip():
                print("✗ --corriger {} : {} article(s) correspondant(s) — ignoré".format(item, len(trouves)))
                continue
            cache[trouves[0]] = {"zone": zone.strip(), "lieu": "correction manuelle",
                                 "confiance": "manuelle"}
            print("✓ correction : {} → {}".format(trouves[0][:60], zone.strip()))
        ecrire_cache(cache)
    lignes, compte, n_appels, n_ecrits = [], {}, 0, 0

    for f, sc, fm, corps in articles(args):
        cle = os.path.basename(f)
        if cle not in cache:
            if args.apply:
                continue  # --apply ne fait jamais d'appel
            if args.limite is not None and n_appels >= args.limite:
                continue
            rep_llm = classer(f, sc, fm, corps, J, args)
            n_appels += 1
            if rep_llm is None:
                compte["non_traite"] = compte.get("non_traite", 0) + 1
                continue
            cache[cle] = rep_llm
            ecrire_cache(cache)  # après chaque appel : rien de perdu si interruption
        rep = cache[cle]
        statut, nouvelle = decision(sc, fm, rep, J)
        compte[statut] = compte.get(statut, 0) + 1
        z = fm.get("zone_principale") or "(vide)"
        conf = rep.get("confiance", "?")
        if statut == "change":
            lignes.append("- **{}** `{}` → `{}` ({}, {}) — {}".format(
                sc, z, nouvelle, conf, rep.get("lieu", ""), cle[:60]))
            if args.apply and (conf != "faible" or args.inclure_faibles):
                t = open(f, encoding="utf-8").read()
                t2, n = re.subn(r"^zone_principale:.*$", "zone_principale: " + nouvelle,
                                t, count=1, flags=re.M)
                if n == 0:
                    # Champ absent du frontmatter (articles d'avant P20 Phase B) :
                    # inséré juste avant le --- de fermeture.
                    m_fm = re.match(r"^---\n.*?\n(?=---\n)", t, re.S)
                    if m_fm:
                        t2 = t[:m_fm.end()] + "zone_principale: {}\n".format(nouvelle) + t[m_fm.end():]
                        n = 1
                if n == 1:
                    shutil.copy2(f, f + ".bak_rezonage")
                    open(f, "w", encoding="utf-8").write(t2)
                    n_ecrits += 1
        elif statut in ("hors_liste", "erreur", "hors_zones"):
            lignes.append("- ⚠ {} {} : {} — {}".format(
                statut, sc, rep.get("zone") or rep.get("erreur"), cle[:60]))

    entete = "# Rezonage des articles — {}\n\n{}\n\nAppels LLM ce passage : {}\n\n".format(
        "APPLIQUÉ" if args.apply else "aperçu (rien n'est écrit dans les articles)",
        " | ".join("{} : {}".format(k, v) for k, v in sorted(compte.items())), n_appels)
    open(RAPPORT, "w", encoding="utf-8").write(entete + "\n".join(lignes) + "\n")
    print(entete + "\n".join(lignes))
    if args.apply:
        print("\n{} article(s) réécrit(s).".format(n_ecrits))
    else:
        print("\nRapport : {}".format(RAPPORT))


if __name__ == "__main__":
    main()
