#!/usr/bin/env python3
"""
audit_slugs_s24.py — S24, 31 oct 2026 — LECTURE SEULE

Repère les slugs abîmés par l'ancien slugify (ø, æ, œ, ß, ł… -> « _ »)
dans le lore : fiches .md (entités, instances, événements, archétypes…) et
zones des bibles geographie/*.md. N'écrit rien.

Pour chaque nom contenant une de ces lettres :
  CASSÉ    : le slug contient la forme abîmée du nom (à migrer)
  sans lien: le slug ne dérive pas du nom (choisi autrement, rien à faire)

Usage (depuis la racine du vault) :
  python3 generator/audit_slugs_s24.py
"""

import os
import re
import unicodedata

import yaml

RACINE = os.getcwd()
EXCLUS = {"site", ".git", "_backups", "_a_supprimer", ".obsidian", "__pycache__",
          "articles", "node_modules"}
LETTRES = re.compile(r"[øØæÆœŒßẞłŁđĐðÐþÞı]")
TRANSLIT = {"ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE",
            "ß": "ss", "ẞ": "SS", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D",
            "ð": "d", "Ð": "D", "þ": "th", "Þ": "TH", "ı": "i"}


def ancien(text):
    s = unicodedata.normalize("NFD", text or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def nouveau(text):
    return ancien("".join(TRANSLIT.get(c, c) for c in (text or "")))


def frontmatter(chemin):
    try:
        raw = open(chemin, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return None
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", raw, re.DOTALL)
    if not m:
        return None
    try:
        fm = yaml.safe_load(re.sub(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]", r"\1", m.group(1)))
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def noms(fm):
    return [v for k, v in fm.items()
            if isinstance(v, str) and ("nom" in k.lower() or k.lower() in ("name", "titre", "title"))
            and LETTRES.search(v)]


def verdict(nom, slug):
    a, n = ancien(nom), nouveau(nom)
    if a != n and a and a in slug:
        return "CASSÉ", slug.replace(a, n)
    return "sans lien", ""


def main():
    lignes = []
    for dossier, sous, fichiers in os.walk(RACINE):
        sous[:] = [d for d in sous if d not in EXCLUS]
        rel = os.path.relpath(dossier, RACINE)
        for f in sorted(fichiers):
            if not f.endswith(".md"):
                continue
            chemin = os.path.join(dossier, f)
            fm = frontmatter(chemin)
            if not fm:
                continue
            if rel == "geographie":
                for z in fm.get("zones") or []:
                    if isinstance(z, dict) and isinstance(z.get("nom"), str) and LETTRES.search(z["nom"]):
                        v, prop = verdict(z["nom"], str(z.get("slug", "")))
                        lignes.append((v, "geographie/" + f, z["nom"], z.get("slug", ""), prop))
                continue
            slug = str(fm.get("slug") or f[:-3])
            for nom in noms(fm):
                v, prop = verdict(nom, slug)
                lignes.append((v, os.path.join(rel, f), nom, slug, prop))

    casses = [l for l in lignes if l[0] == "CASSÉ"]
    print("{} nom(s) concerné(s) : {} slug(s) CASSÉ(s), {} sans lien\n".format(
        len(lignes), len(casses), len(lignes) - len(casses)))
    for v, fichier, nom, slug, prop in sorted(lignes):
        print("{:9} {}\n          nom : {}\n          slug: {}{}".format(
            v, fichier, nom, slug, "\n          ->  : " + prop if prop else ""))


if __name__ == "__main__":
    main()
