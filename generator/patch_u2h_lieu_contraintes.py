#!/usr/bin/env python3
"""patch_u2h — signaux « et si ? » : champ `lieu` (ancrage géographique) et transmission des
`contraintes` à l'IA du récit. Dry-run par défaut ; --apply écrit (sauvegarde .bak_u2h).
Depuis la racine du vault :  python3 patch_u2h_lieu_contraintes.py [--apply]"""
import sys, shutil, py_compile
from pathlib import Path
APPLY = "--apply" in sys.argv
ROOT = Path(sys.argv[sys.argv.index("--root")+1]) if "--root" in sys.argv else Path(".")
G = ROOT / "generator"

EDITS = {
 "simuler_et_si.py": [
  ('    norm = {\n        "contraintes": contraintes, "carte": carte, "mode": mode, "type": typ,\n',
   '    lieu = " ".join(str(h.get("lieu") or "").split())   # U2h : ancrage géographique d\'un signal\n'
   '    if lieu and not est_signal:\n'
   '        avert.append("`lieu` ne sert qu\'aux signaux (ancrage géographique) : ignoré pour un événement "\n'
   '                     "(voir `geographie`)")\n'
   '        lieu = ""\n'
   '    norm = {\n        "contraintes": contraintes, "lieu": lieu, "carte": carte, "mode": mode, "type": typ,\n', 1),
  ('              "via_matrice_impose": bool(hyp["via_matrice"])}\n    if out is not None:\n',
   '              "via_matrice_impose": bool(hyp["via_matrice"])}\n'
   '    if hyp.get("lieu"):   # U2h : lu par inject_custom_signals.py comme zone_hint\n'
   '        entree["zone_hint"] = hyp["lieu"]\n'
   '    if hyp.get("contraintes"):   # U2h : faits que le récit du signal doit respecter\n'
   '        entree["contraintes"] = list(hyp["contraintes"])\n'
   '    if out is not None:\n', 1),
 ],
 "inject_custom_signals.py": [
  ('    zone_hint = idea.get("zone_hint") or None\n',
   '    zone_hint = idea.get("zone_hint") or None\n'
   '    # U2h : faits imposés par l\'auteur (contraintes de l\'hypothèse « et si ? »)\n'
   '    _c = idea.get("contraintes") or []\n'
   '    _c = [_c] if isinstance(_c, str) else list(_c)\n'
   '    contraintes = [" ".join(str(c).split()) for c in _c if str(c).strip()]\n'
   '    bloc_contraintes = ("\\nFAITS À RESPECTER (imposés par l\'auteur ; priment sur tes connaissances "\n'
   '                        "générales ; le récit ne doit en contredire aucun) :\\n"\n'
   '                        + "\\n".join(f"- {c}" for c in contraintes) + "\\n") if contraintes else ""\n', 1),
  ('impositions_txt=texte_impositions_signal(imp, variable_slug),',
   'impositions_txt=texte_impositions_signal(imp, variable_slug) + bloc_contraintes,', 2),
 ],
}
ok = True
for nom, edits in EDITS.items():
    p = G / nom
    txt = p.read_text(encoding="utf-8")
    for k, (old, new, n) in enumerate(edits, 1):
        c = txt.count(old)
        if c != n:
            print(f"✗ {nom} modif {k} : {c} occurrence(s) trouvée(s), {n} attendue(s)"); ok = False
        else:
            txt = txt.replace(old, new)
    if ok and APPLY:
        shutil.copy2(p, p.with_name(p.name + ".bak_u2h"))
        p.write_text(txt, encoding="utf-8")
        py_compile.compile(str(p), doraise=True)
print(("✓ appliqué" if APPLY else "✓ dry-run : tout s'applique") if ok else "✗ rien écrit")
sys.exit(0 if ok else 1)
