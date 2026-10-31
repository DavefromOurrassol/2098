#!/usr/bin/env python3
"""
patch_s30_relocaliser_evenement.py — Ourrassol 2098 (S30, 31 octobre 2026)
==========================================================================

Défaut trouvé au test réel de S30 (exemple occupation_bresil_2029) : l'événement
est injecté à l'étape ③, AVANT que la carte soit appliquée à l'étape ④. Sa
`localisation.zone` reste donc la zone que le pays vient de quitter
(ameriques_multipolaires au lieu de bresil_occupe).

Correctif dans appliquer_et_si.py :
  - aperçu : sous l'opération de carte, ligne « → événement … relocalisé : A → B »
    quand la zone de l'événement porte le pays et n'est ni la cible, ni une
    sous-zone qui suit le pays, ni une sous-zone à répartir à la main ;
  - écriture : après la carte appliquée avec succès, `localisation.zone` de
    event_instances/<id>_<scénario>.md remplacée (sauvegarde .bak_appliquer) ;
    le lieu n'est pas touché. Carte en échec : rien n'est relocalisé.

USAGE (depuis la racine du vault)
    python3 generator/patch_s30_relocaliser_evenement.py            # aperçu
    python3 generator/patch_s30_relocaliser_evenement.py --apply    # écrit (sauvegarde .bak_s30reloc)
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S30_RELOCALISER"

# 1. Fonctions, insérées avant `def lancer(cmd):`
ANCRE_FONCTIONS = "def lancer(cmd):\n"
FONCTIONS = '''# ---------------------------------------------------------------------------
# PATCH_S30_RELOCALISER (31 oct 2026) : l'événement est injecté (étape ③) avant la carte
# (étape ④) ; sa zone peut être celle que le pays quitte. On la remplace par la cible.
# ---------------------------------------------------------------------------

def evenement_de(hid, sc):
    return VAULT / "event_instances" / f"{hid}_{sc}.md"


def zone_evenement(hid, sc):
    p = evenement_de(hid, sc)
    if not p.exists():
        return None
    d = decoupe(p.read_text(encoding="utf-8"))
    fm = lire_fm(d[1]) if d else None
    loc = (fm or {}).get("localisation")
    return str(loc.get("zone") or "").strip() or None if isinstance(loc, dict) else None


def relocalisation_prevue(hid, o):
    """(zone actuelle, cible) si l'événement est rangé dans une zone que le pays va quitter.
    Calculé AVANT la carte : la zone porte encore le pays. Pas de changement si l'événement est
    déjà dans la cible, dans une sous-zone qui suit le pays, ou dans une sous-zone à répartir."""
    zev = zone_evenement(hid, o["sc"])
    if not zev or zev == o["cible"]:
        return None
    gardees = set(o.get("simples") or []) | {s.get("slug") for s in o.get("a_repartir") or []}
    if zev in gardees:
        return None
    by = {z.get("slug"): z for z in zones_geo(o["sc"])}
    if not (porte_pays(by.get(zev), o["pays"]) or porte_pays_cite(by.get(zev), o["pays"])):
        return None
    return zev, o["cible"]


def relocaliser_evenement(hid, sc, avant, apres):
    """Remplace `localisation.zone` (avant → apres) dans la fiche d'événement ; lève ValueError
    si le frontmatter n'a pas la forme attendue. Sauvegarde .bak_appliquer."""
    p = evenement_de(hid, sc)
    texte = p.read_text(encoding="utf-8")
    d = decoupe(texte)
    if not d:
        raise ValueError("frontmatter introuvable")
    fm_l = d[1].split("\\n")
    debut = [i for i, l in enumerate(fm_l) if re.match(r"^localisation:\\s*$", l)]
    if len(debut) != 1:
        raise ValueError(f"{len(debut)} bloc(s) `localisation:`")
    j, lignes = debut[0] + 1, []
    while j < len(fm_l) and (fm_l[j].startswith((" ", "\\t")) or not fm_l[j].strip()):
        if re.match(r"^\\s+zone:", fm_l[j]):
            lignes.append(j)
        j += 1
    if len(lignes) != 1:
        raise ValueError(f"{len(lignes)} ligne(s) `zone:` dans `localisation`")
    actuel = nettoie(re.sub(r"^\\s+zone:\\s*", "", fm_l[lignes[0]]))
    if actuel != avant:
        raise ValueError(f"zone actuelle « {actuel} », pas « {avant} »")
    fm_l[lignes[0]] = re.sub(r"(zone:\\s*).*", lambda m: m.group(1) + apres, fm_l[lignes[0]])
    fm_txt = "\\n".join(fm_l)
    fm = lire_fm(fm_txt)
    if not fm or (fm.get("localisation") or {}).get("zone") != apres:
        raise ValueError("relecture du frontmatter inattendue")
    shutil.copy2(p, p.with_name(p.name + ".bak_appliquer"))
    p.write_text(d[0] + fm_txt + d[2] + d[3], encoding="utf-8")


'''

# 2. Aperçu : ligne annoncée sous l'opération de carte
ANCRE_APERCU = '''                notes[o["n"]] = note_carte(o)
'''
APERCU = '''                notes[o["n"]] = note_carte(o)
                rl = relocalisation_prevue(a.id, o)   # PATCH_S30_RELOCALISER
                if rl:
                    o["reloc"] = rl
                    notes[o["n"]] = "\\n         → ".join(x for x in (
                        notes[o["n"]], f"événement `{a.id}_{o['sc']}` relocalisé : `{rl[0]}` → `{rl[1]}`") if x)
'''

# 3. Écriture : après la carte appliquée
ANCRE_ECRITURE = '''        for m in msgs:
            print(f"  {m}")
        n += faits
'''
ECRITURE = '''        for m in msgs:
            print(f"  {m}")
        n += faits
        for o in cartes:   # PATCH_S30_RELOCALISER : seulement si la carte est passée
            if faits and o.get("retenue") and o.get("reloc"):
                avant_z, apres_z = o["reloc"]
                try:
                    relocaliser_evenement(a.id, o["sc"], avant_z, apres_z)
                    print(f"  ✓ événement `{a.id}_{o['sc']}` relocalisé : `{avant_z}` → `{apres_z}`")
                    n += 1
                except (ValueError, OSError) as e:
                    print(f"  ⚠ événement `{a.id}_{o['sc']}` non relocalisé ({e}) : corriger "
                          f"`localisation.zone` à la main (→ `{apres_z}`)")
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fichier", default=str(Path(__file__).resolve().parent / "appliquer_et_si.py"))
    a = ap.parse_args()

    cible = Path(a.fichier)
    if not cible.exists():
        sys.exit(f"✗ {cible} introuvable")
    texte = cible.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        print(f"· déjà appliqué ({MARQUEUR} présent) : rien à faire.")
        return

    for nom, ancre in (("fonctions", ANCRE_FONCTIONS), ("aperçu", ANCRE_APERCU), ("écriture", ANCRE_ECRITURE)):
        n = texte.count(ancre)
        if n != 1:
            sys.exit(f"✗ ancre « {nom} » trouvée {n} fois (1 attendue) : fichier différent de celui analysé, rien écrit.")

    nouveau = (texte.replace(ANCRE_FONCTIONS, FONCTIONS + ANCRE_FONCTIONS)
                    .replace(ANCRE_APERCU, APERCU)
                    .replace(ANCRE_ECRITURE, ECRITURE))

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(nouveau)
    try:
        py_compile.compile(tmp.name, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"✗ le fichier patché ne compile pas, rien écrit :\n{e}")
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    print(f"{'ÉCRITURE' if a.apply else 'APERÇU (rien écrit)'} — {cible.name}")
    print("  + 4 fonctions (evenement_de, zone_evenement, relocalisation_prevue, relocaliser_evenement)")
    print("  + aperçu de l'étape ④ : ligne « → événement … relocalisé : A → B » sous l'opération de carte")
    print("  + écriture : relocalisation après la carte appliquée (sauvegarde .bak_appliquer de la fiche)")
    print(f"  compilation : OK ({len(texte.splitlines())} → {len(nouveau.splitlines())} lignes)")
    if not a.apply:
        print("\nRelancer avec --apply pour écrire (sauvegarde .bak_s30reloc).")
        return
    shutil.copy2(cible, cible.with_name(cible.name + ".bak_s30reloc"))
    cible.write_text(nouveau, encoding="utf-8")
    print(f"\n✓ {cible.name} patché (sauvegarde {cible.name}.bak_s30reloc)")


if __name__ == "__main__":
    main()
