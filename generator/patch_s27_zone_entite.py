#!/usr/bin/env python3
"""
patch_s27_zone_entite.py -- simulateur v8.24 : zone des nouvelles entités (19 octobre 2026)
==========================================================================================
Tiré de l'essai Brésil : « Bureau de Liaison Brésil-États-Unis » était rattaché à
`ameriques_multipolaires`, zone que le Brésil quitte. Désormais, quand l'hypothèse déclare
la carte d'un pays (absorber / nouvelle_zone), une nouvelle entité proposée par la lecture
IA qui NOMME ce pays et qui est rattachée à une zone de niveau 1 qu'il quitte reçoit la zone
de destination (`bresil_occupe`). Signalé dans « Corrections automatiques » du rapport ;
aucun appel IA de plus (correction faite après la lecture, cache inchangé).
Les entités des sous-zones (Sertão, Amazonie) ne bougent pas : leur sort se décide à l'étape ⑤.

Tout ou rien, sauvegarde .bak_zone_entite, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_zone_entite.py            (aperçu)
    python3 generator/patch_s27_zone_entite.py --apply
"""
import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_S27_ZONE_ENTITE"
CHEMIN = Path.cwd() / "generator" / "simuler_et_si.py"

REMPLACEMENTS = [
    ('VERSION = "v8.23"', 'VERSION = "v8.24"'),
    (
        '''        if out[sc].get("geographie") and sc not in hyp["geographie"]:
            hyp["geographie"][sc] = [dict(g, source="ia") for g in out[sc]["geographie"]]
    return out''',
        '''        # PATCH_S27_ZONE_ENTITE (v8.24) : nouvelle entité qui nomme un pays dont la carte est
        # déclarée, rattachée à une zone qu'il quitte -> zone de destination.
        try:
            _zone_des_entites(hyp, sc, out[sc])
        except Exception as e:  # ne doit jamais empêcher le rapport
            out[sc]["corrigees"] = (out[sc].get("corrigees") or []) + [
                f"zone des nouvelles entités non vérifiée ({type(e).__name__}: {e})"]
        if out[sc].get("geographie") and sc not in hyp["geographie"]:
            hyp["geographie"][sc] = [dict(g, source="ia") for g in out[sc]["geographie"]]
    return out


def _zone_des_entites(hyp, sc, cons):
    """PATCH_S27_ZONE_ENTITE : voir ajouter_consequences."""
    import re as _re
    ops = [g for g in (hyp.get("geographie") or {}).get(sc) or []
           if g.get("source") != "ia" and g.get("action") in ("absorber", "nouvelle_zone")]
    if not ops or not cons.get("nouvelles_entites"):
        return
    repo, _m = charger_zone_repository()
    for g in ops:
        cible = g.get("zone") if g["action"] == "absorber" else (g.get("nouvelle_zone") or {}).get("slug")
        if not cible:
            continue
        quittees = {a["slug"] for a in repo.zones_portant_un_pays(sc, g["pays"])
                    if (a.get("niveau") or 1) == 1 and a["slug"] != cible}
        motif = _re.compile(r"(?<![a-z0-9])" + _re.escape(_plie_aligne(g["pays"])) + r"(?![a-z0-9])")
        for n in cons["nouvelles_entites"]:
            if n.get("zone") in quittees and motif.search(_plie_aligne(f"{n.get('nom', '')} {n.get('role', '')}")):
                cons["corrigees"] = (cons.get("corrigees") or []) + [
                    f"nouvelle entité {n['nom']} : zone {n['zone']!r} → {cible!r} ({g['pays']} y passe)"]
                n["zone"] = cible''',
    ),
]


def main():
    apply = "--apply" in sys.argv
    if not CHEMIN.exists():
        sys.exit("✗ generator/simuler_et_si.py introuvable (lancer depuis la racine du coffre). Rien fait.")
    texte = CHEMIN.read_text(encoding="utf-8")
    if MARQUEUR in texte:
        sys.exit("✗ patch déjà appliqué : rien fait.")
    for n, (ancien, neuf) in enumerate(REMPLACEMENTS, 1):
        if texte.count(ancien) != 1:
            sys.exit(f"✗ repère n°{n} trouvé {texte.count(ancien)} fois (attendu 1) : rien fait.")
        texte = texte.replace(ancien, neuf)
    try:
        compile(texte, str(CHEMIN), "exec")
    except SyntaxError as e:
        sys.exit(f"✗ erreur de syntaxe après patch ({e}) : rien fait.")
    print(f"  ✓ generator/simuler_et_si.py : {len(REMPLACEMENTS)} remplacement(s) prêt(s) (v8.24)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CHEMIN, CHEMIN.with_name("simuler_et_si.py.bak_zone_entite"))
    CHEMIN.write_text(texte, encoding="utf-8")
    print("\n✓ Fait (sauvegarde simuler_et_si.py.bak_zone_entite).")


if __name__ == "__main__":
    main()
