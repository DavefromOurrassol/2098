#!/usr/bin/env python3
"""
reparer_bloc_metadonnees.py — Ourrassol 2098 (5 octobre 2026)

Répare les articles dont le bloc ===METADONNEES_PUBLICATION=== est resté dans
le texte (extraction ratée à la génération) : reporte CHAPO / TAGS /
IMAGE_PROMPT dans le frontmatter (seulement si le champ y est vide) et retire
le bloc du corps. Aucun appel IA.

Usage (depuis la racine du vault) :
    python3 generator/reparer_bloc_metadonnees.py            # aperçu, n'écrit rien
    python3 generator/reparer_bloc_metadonnees.py --apply    # écrit (.bak_meta)
"""
import argparse
import re
import shutil
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
MARQUEUR = "===METADONNEES_PUBLICATION==="
RE_BLOC = re.compile(r"\n*" + re.escape(MARQUEUR) + r"\n(.*?)(?=\n\s*\n|\n---\n|\Z)", re.S)


def q(s):
    """Chaîne YAML entre guillemets doubles."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def champs_du_bloc(bloc):
    out = {}
    for ligne in bloc.split("\n"):
        m = re.match(r"\s*(CHAPO|TAGS|IMAGE_PROMPT)\s*:\s*(.*)$", ligne, re.I)
        if m:
            out[m.group(1).upper()] = m.group(2).strip()
    return out


def reparer(txt):
    m_fm = re.match(r"---\n(.*?)\n---\n", txt, re.S)
    if not m_fm:
        return None, "frontmatter introuvable"
    fm, corps = m_fm.group(1), txt[m_fm.end():]
    m = RE_BLOC.search(corps)
    if not m:
        return None, "bloc introuvable"
    ch = champs_du_bloc(m.group(1))
    faits = []
    if ch.get("CHAPO") and re.search(r'^chapo:\s*(""|\'\')?\s*$', fm, re.M):
        fm = re.sub(r'^chapo:.*$', lambda _: "chapo: " + q(ch["CHAPO"]), fm, count=1, flags=re.M)
        faits.append("chapo")
    if ch.get("IMAGE_PROMPT") and re.search(r'^image_prompt:\s*(""|\'\')?\s*$', fm, re.M):
        fm = re.sub(r'^image_prompt:.*$', lambda _: "image_prompt: " + q(ch["IMAGE_PROMPT"]), fm, count=1, flags=re.M)
        faits.append("image_prompt")
    tags = [t.strip() for t in ch.get("TAGS", "").split(",") if t.strip()]
    if tags and re.search(r'^tags:\s*(\[\])?\s*$\n(?!\s+- )', fm + "\n", re.M):
        bloc_tags = "tags:\n" + "\n".join("  - " + q(t) for t in tags)
        fm = re.sub(r'^tags:.*$', lambda _: bloc_tags, fm, count=1, flags=re.M)
        faits.append(f"tags ({len(tags)})")
    corps = corps[:m.start()].rstrip("\n") + "\n\n" + corps[m.end():].lstrip("\n")
    corps = re.sub(r"\n{3,}", "\n\n", corps)
    return f"---\n{fm}\n---\n{corps}", ", ".join(faits) or "bloc retiré seulement (champs déjà remplis)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--vault", default=str(VAULT), help=argparse.SUPPRESS)
    args = ap.parse_args()
    fichiers = [p for p in Path(args.vault, "articles").rglob("*.md")
                if ".bak" not in p.name and MARQUEUR in p.read_text(encoding="utf-8")]
    print(f"{len(fichiers)} article(s) avec le bloc dans le texte.")
    for p in fichiers:
        nouveau, info = reparer(p.read_text(encoding="utf-8"))
        rel = p.relative_to(args.vault)
        if nouveau is None:
            print(f"  ✗ {rel} : {info}")
            continue
        print(f"  ✓ {rel} : {info}")
        if args.apply:
            shutil.copy2(p, p.with_name(p.name + ".bak_meta"))
            p.write_text(nouveau, encoding="utf-8")
    if fichiers and not args.apply:
        print("Aperçu seulement. Relancer avec --apply pour écrire.")


if __name__ == "__main__":
    main()
