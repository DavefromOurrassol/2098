#!/usr/bin/env python3
"""
patch_u3m_rattrapage_notes.py — Ourrassol 2098 (U3m, 11 novembre 2026)

Rattrapage de U3l : dans event_instances/*.md, remplace le corps de « ## Note de cohérence »
(recopie YAML brute : guillemets simples extérieurs, apostrophes doublées) par le texte
propre de la note, lu dans le frontmatter. Ne touche qu'aux fiches dont le corps commence
par une apostrophe ; le frontmatter n'est pas modifié.

Dry-run par défaut ; --apply pour écrire (sauvegarde .bak_u3m par fiche). Idempotent.
À lancer depuis la racine du vault.
"""
import re
import shutil
import sys
from pathlib import Path

import yaml

APPLY = "--apply" in sys.argv
n_total = 0
for f in sorted(Path("event_instances").glob("*.md")):
    t = f.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)\Z", t, re.S)
    if not m:
        continue
    corps = m.group(2)
    mm = re.search(r"(## Note de cohérence\n)('.*?)(?=\n## |\Z)", corps, re.S)
    if not mm:
        continue
    try:
        note = yaml.safe_load(m.group(1)).get("note_coherence")
    except yaml.YAMLError:
        print(f"✗ {f.name} : frontmatter illisible, ignorée")
        continue
    if not isinstance(note, str) or not note.strip():
        print(f"✗ {f.name} : pas de note_coherence lisible, ignorée")
        continue
    propre = " ".join(note.split())
    nouveau_corps = corps[:mm.start(2)] + propre + "\n" + corps[mm.end(2):].lstrip("\n")
    nouveau = t[:m.start(2)] + nouveau_corps
    n_total += 1
    print(f"+ {f.name}\n    avant : {mm.group(2)[:70]!r}\n    après : {propre[:70]!r}")
    if APPLY:
        shutil.copy2(f, str(f) + ".bak_u3m")
        f.write_text(nouveau, encoding="utf-8")
print(f"\n{n_total} fiche(s) concernée(s)." + ("" if APPLY else " (dry-run : rien écrit ; relancer avec --apply)"))
