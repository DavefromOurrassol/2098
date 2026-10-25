#!/usr/bin/env python3
"""
patch_s19_undo_total.py -- S19 : undo_custom.py recalcule la ligne « Total »
du registre aussi quand on retire un ÉVÉNEMENT (c'était déjà le cas pour les
signaux).

Trois changements dans generator/undo_custom.py :
  1. nouvelle fonction _recalculer_total_registre() (même calcul que
     remove_signal_from_registre, qui n'est pas modifiée) ;
  2. remove_from_registre() l'appelle et fait une sauvegarde .bak ;
  3. remove_from_registre() compare le slug EXACTEMENT (3e colonne) au lieu
     d'une sous-chaîne (retirer terres_rares effaçait aussi terres_rares_norvege).

Avant d'écrire, vérifie sur le vrai registre que les lignes « evenement » ont
bien le slug en 3e colonne, et que le calcul du total redonne la valeur actuelle.

Usage (depuis la racine du vault ou depuis generator/) :
  python3 generator/patch_s19_undo_total.py           # aperçu, rien écrit
  python3 generator/patch_s19_undo_total.py --apply   # écrit (.bak_s19)
"""
import re
import shutil
import sys
import py_compile
from pathlib import Path

MARQUEUR = "def _recalculer_total_registre("

ICI = Path(__file__).resolve().parent
GEN = ICI if (ICI / "undo_custom.py").exists() else ICI / "generator"
CIBLE = GEN / "undo_custom.py"
VAULT = GEN.parent

HELPER = '''def _recalculer_total_registre(content):
    """Recalcule la ligne « Total » du registre (même calcul que remove_signal_from_registre)."""
    def _type(l):
        return [c.strip() for c in l.strip("|").split("|")][0:1]
    lignes = content.split("\\n")
    signal_rows = sum(1 for l in lignes if l.startswith("|") and _type(l) == ["signal"])
    evenement_rows = sum(1 for l in lignes if l.startswith("|") and _type(l) == ["evenement"])
    return re.sub(
        r"Total : \\d+ entrées \\(\\d+ signaux uniques × 6 scénarios( \\+ \\d+ entrées d'événements custom)?\\)\\.",
        "Total : {} entrées ({} signaux uniques × 6 scénarios + {} entrées d'événements custom).".format(
            signal_rows + evenement_rows, signal_rows // len(SCENARIOS_SIGNAL), evenement_rows
        ),
        content,
    )


'''

REMPLACEMENTS = [
    ("def remove_from_registre(event_slug, scenario, dry_run, report):",
     HELPER + "def remove_from_registre(event_slug, scenario, dry_run, report):"),
    ('        if line.startswith("|") and "evenement" in line and event_slug in line:',
     '        cols = [c.strip() for c in line.strip("|").split("|")] if line.startswith("|") else None\n'
     '        if cols and len(cols) >= 3 and cols[0] == "evenement" and cols[2] == event_slug:'),
    ('        REGISTRE_PATH.write_text("\\n".join(new_lines), encoding="utf-8")\n'
     '        report.append(f"  [REG] {removed} ligne(s) retirée(s) du registre pour \'{event_slug}\'")',
     '        new_content = _recalculer_total_registre("\\n".join(new_lines))\n'
     '        backup_file(REGISTRE_PATH)\n'
     '        REGISTRE_PATH.write_text(new_content, encoding="utf-8")\n'
     '        report.append(f"  [REG] {removed} ligne(s) retirée(s) du registre pour \'{event_slug}\' "\n'
     '                      f"(total recalculé)")'),
]


def trouver_registre():
    for p in sorted(VAULT.rglob("registre_evenements.md")):
        if "_a_supprimer" not in p.parts and ".bak" not in p.name:
            return p
    return None


def verifier_registre():
    reg = trouver_registre()
    if reg is None:
        sys.exit("✗ registre_evenements.md introuvable : rien écrit.")
    texte = reg.read_text(encoding="utf-8")
    def cols(l):
        return [c.strip() for c in l.strip("|").split("|")]
    ev = [l for l in texte.split("\n") if l.startswith("|") and cols(l)[0:1] == ["evenement"]]
    sig = [l for l in texte.split("\n") if l.startswith("|") and cols(l)[0:1] == ["signal"]]
    print(f"Registre : {reg.relative_to(VAULT)}")
    print(f"  {len(sig)} ligne(s) signal, {len(ev)} ligne(s) evenement")
    for l in ev[:2]:
        c = cols(l)
        print(f"  exemple : 3e colonne = « {c[2] if len(c) > 2 else '?'} »   ({l.strip()[:90]})")
    if ev and any(len(cols(l)) < 3 for l in ev):
        sys.exit("✗ ligne evenement à moins de 3 colonnes : format inattendu, rien écrit.")
    m = re.search(r"Total : \d+ entrées \([^)]*\)\.", texte)
    print(f"  total actuel  : {m.group(0) if m else '(ligne Total absente)'}")
    print(f"  total calculé : {len(sig) + len(ev)} entrées ({len(sig) // 6} signaux uniques "
          f"× 6 scénarios + {len(ev)} entrées d'événements custom).")
    print()


def main():
    apply = "--apply" in sys.argv
    if not CIBLE.exists():
        sys.exit(f"✗ {CIBLE} introuvable.")
    t = CIBLE.read_text(encoding="utf-8")
    if MARQUEUR in t:
        sys.exit("✗ Patch déjà appliqué : rien à faire.")

    verifier_registre()

    for old, _ in REMPLACEMENTS:
        n = t.count(old)
        if n != 1:
            sys.exit(f"✗ motif trouvé {n} fois au lieu de 1, rien écrit :\n  {old.splitlines()[0][:90]}")
    for name in ("SCENARIOS_SIGNAL", "def backup_file", "import re"):
        if name not in t:
            sys.exit(f"✗ « {name} » absent de undo_custom.py : rien écrit.")

    nouveau = t
    for old, new in REMPLACEMENTS:
        nouveau = nouveau.replace(old, new)

    essai = CIBLE.with_name("_essai_patch_s19.py")
    essai.write_text(nouveau, encoding="utf-8")
    try:
        py_compile.compile(str(essai), doraise=True)
    except py_compile.PyCompileError as e:
        essai.unlink()
        sys.exit(f"✗ le fichier patché ne compile pas, rien écrit :\n{e}")
    essai.unlink()

    if not apply:
        print("APERÇU : 3 remplacements valides, le fichier patché compile. Rien écrit.")
        print("Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CIBLE, CIBLE.with_name(CIBLE.name + ".bak_s19"))
    CIBLE.write_text(nouveau, encoding="utf-8")
    print(f"✓ {CIBLE.name} patché (sauvegarde {CIBLE.name}.bak_s19).")


if __name__ == "__main__":
    main()
