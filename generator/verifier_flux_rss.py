#!/usr/bin/env python3
"""
verifier_flux_rss.py — Ourrassol 2098
=====================================

Première étape de la collecte locale RSS (S21, « option 2 », 29 sept 2026) :
trouve et contrôle le flux RSS/Atom de chaque source active de
sources_signaux_faibles.yaml. Aucun appel LLM.

Pour chaque source :
  1. le champ « rss » s'il est déjà rempli ;
  2. sinon l'autodécouverte : les balises <link rel="alternate"
     type="application/rss+xml|atom+xml"> de la page « url », puis de la
     racine du site ;
  3. sinon les adresses courantes (feed/, rss, rss.xml, atom.xml…).
Un flux n'est retenu que s'il se lit ET contient au moins un article.

Le rapport donne, par source : le flux trouvé, le nombre d'articles, la
date du plus récent. Rien n'est écrit sans --apply.

--apply remplit « rss: » dans le YAML pour les flux trouvés (une copie
.bak est faite d'abord). Seule la ligne « rss: » de la source concernée
change : les commentaires et l'ordre du fichier sont conservés. Un
« rss » déjà rempli n'est jamais remplacé.

USAGE
-----
    python3 verifier_flux_rss.py                 # rapport seul
    python3 verifier_flux_rss.py --source grist  # une source (texte du nom)
    python3 verifier_flux_rss.py --apply         # écrit les flux trouvés

PRÉREQUIS
---------
    pip3 install feedparser
"""

import argparse
import re
import shutil
import time
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import yaml

try:
    import feedparser
except ImportError:
    raise SystemExit("[ERREUR] feedparser manquant : pip3 install feedparser")

SOURCES_PATH = Path(__file__).resolve().parent / "sources_signaux_faibles.yaml"

# Certains sites refusent les robots sans navigateur (403) : on se présente
# comme un navigateur ordinaire.
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
SUFFIXES = ["feed/", "feed", "rss", "rss/", "rss.xml", "feed.xml", "atom.xml",
            "index.xml", "articles.atom", "fr/rss", "en/rss"]
LINK_RE = re.compile(r"<link\b[^>]*>", re.I)


def telecharger(url: str, timeout: int):
    """(contenu en octets, url finale) ou (None, motif)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(3_000_000), r.geturl()
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"[:120]


def autodecouverte(html: str, base: str) -> list:
    """Adresses de flux annoncées dans les balises <link> d'une page HTML."""
    res = []
    for tag in LINK_RE.findall(html):
        t = tag.lower()
        if "alternate" not in t or not ("rss+xml" in t or "atom+xml" in t):
            continue
        m = re.search(r'href\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if m:
            u = urljoin(base, unescape(m.group(1).strip()))
            if u not in res and "comments" not in u.lower():
                res.append(u)
    return res


def lire_flux(url: str, timeout: int):
    """Dict {url, titre, nb, recent} si url est un flux avec articles, sinon None."""
    contenu, info = telecharger(url, timeout)
    if contenu is None:
        return None
    f = feedparser.parse(contenu)
    if not f.entries or not (f.version or "").strip():
        return None
    dates = []
    for e in f.entries:
        d = e.get("published_parsed") or e.get("updated_parsed")
        if d:
            dates.append(datetime(*d[:6], tzinfo=timezone.utc))
    return {"url": url, "titre": (f.feed.get("title") or "").strip(),
            "nb": len(f.entries), "recent": max(dates) if dates else None}


def chercher_flux(source: dict, timeout: int, max_jours: int = 180):
    """(flux ou None, liste des essais, flux périmés écartés) pour une source.

    Un flux dont l'article le plus récent a plus de max_jours est écarté
    (constat du 29 sept 2026 : un.org/rss.xml et unep.org/rss.xml, trouvés
    par les adresses courantes, datent de 2023 — flux abandonnés)."""
    perimes = []
    essais = []
    if source.get("rss"):
        essais.append(source["rss"])
    page = source["url"]
    racine = "{0.scheme}://{0.netloc}/".format(urlsplit(page))
    for p in dict.fromkeys([page, racine]):
        contenu, info = telecharger(p, timeout)
        if contenu is not None:
            html = contenu.decode("utf-8", errors="replace")
            essais += [u for u in autodecouverte(html, info) if u not in essais]
    for base in dict.fromkeys([page if page.endswith("/") else page + "/", racine]):
        essais += [urljoin(base, s) for s in SUFFIXES if urljoin(base, s) not in essais]
    maintenant = datetime.now(timezone.utc)
    for u in essais:
        flux = lire_flux(u, timeout)
        if not flux:
            continue
        if flux["recent"] and (maintenant - flux["recent"]).days > max_jours:
            perimes.append(f"{u} ({(maintenant - flux['recent']).days} j)")
            continue
        return flux, essais, perimes
    return None, essais, perimes


def ecrire_rss(texte: str, url_source: str, flux: str) -> str:
    """Remplace « rss: null » dans le bloc de la source dont l'url est url_source."""
    lignes = texte.splitlines(keepends=True)
    i_url = next((i for i, l in enumerate(lignes)
                  if re.match(r"\s*url:\s*" + re.escape(url_source) + r"\s*$", l)), None)
    if i_url is None:
        return texte
    debut = next(i for i in range(i_url, -1, -1) if re.match(r"\s*-\s*nom:", lignes[i]))
    fin = next((i for i in range(i_url + 1, len(lignes))
                if re.match(r"\s*-\s*nom:|\S", lignes[i])), len(lignes))
    for i in range(debut, fin):
        m = re.match(r"(\s*rss:\s*)(null|~)?\s*$", lignes[i])
        if m:
            lignes[i] = f"{m.group(1)}{flux}\n"
            break
    return "".join(lignes)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true",
                        help="Écrit les flux trouvés dans le YAML (.bak fait avant).")
    parser.add_argument("--source", default=None,
                        help="Ne traite que les sources dont le nom contient ce texte.")
    parser.add_argument("--max-jours", type=int, default=180,
                        help="Écarte un flux dont l'article le plus récent est plus "
                             "ancien (défaut 180 jours).")
    parser.add_argument("--timeout", type=int, default=15,
                        help="Délai max par adresse, en secondes (défaut 15).")
    args = parser.parse_args()

    texte = SOURCES_PATH.read_text(encoding="utf-8")
    sources = [s for s in (yaml.safe_load(texte) or {}).get("sources") or []
               if isinstance(s, dict) and s.get("url") and s.get("actif") is not False]
    if args.source:
        sources = [s for s in sources if args.source.lower() in s.get("nom", "").lower()]

    maintenant = datetime.now(timezone.utc)
    trouves, absents = [], []
    for s in sources:
        nom = s.get("nom", s["url"])
        print(f"… {nom}", flush=True)
        t0 = time.time()
        flux, essais, perimes = chercher_flux(s, args.timeout, args.max_jours)
        for p in perimes:
            print(f"  ⚠ flux périmé écarté : {p}")
        if flux:
            age = (f"{(maintenant - flux['recent']).days} j"
                   if flux["recent"] else "date inconnue")
            print(f"  ✓ {flux['url']}  —  {flux['nb']} article(s), "
                  f"le plus récent il y a {age}  ({time.time() - t0:.0f} s)")
            trouves.append((s, flux))
        else:
            print(f"  ✗ aucun flux ({len(essais)} adresse(s) essayée(s), "
                  f"{time.time() - t0:.0f} s)")
            absents.append(nom)

    print(f"\n=== {len(trouves)} flux trouvé(s) sur {len(sources)} source(s) ===")
    if absents:
        print("Sans flux :")
        for n in absents:
            print(f"  - {n}")

    a_ecrire = [(s, f) for s, f in trouves if not s.get("rss")]
    if not args.apply:
        if a_ecrire:
            print(f"\n[aperçu] {len(a_ecrire)} flux à écrire dans le YAML : "
                  "relancer avec --apply.")
        return
    if not a_ecrire:
        print("\n[OK] Rien à écrire.")
        return
    shutil.copy2(SOURCES_PATH, SOURCES_PATH.with_suffix(".yaml.bak"))
    for s, f in a_ecrire:
        texte = ecrire_rss(texte, s["url"], f["url"])
    yaml.safe_load(texte)  # garde-fou : le YAML doit rester lisible
    SOURCES_PATH.write_text(texte, encoding="utf-8")
    print(f"\n[OK] {len(a_ecrire)} flux écrit(s) dans {SOURCES_PATH.name} "
          f"(copie : {SOURCES_PATH.name}.bak).")


if __name__ == "__main__":
    main()
