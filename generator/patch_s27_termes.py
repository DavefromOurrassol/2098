#!/usr/bin/env python3
"""
patch_s27_termes.py -- simulateur v8.23 : moins de bruit dans « Fiches à relire » (19 octobre 2026)
==================================================================================================
Tiré de l'essai Écosse (40 lignes, dont 32 pour le seul mot « Europe ») :
  1. Territoire qui partage le fond de carte d'un pays (Écosse, Pays de Galles, Irlande du
     Nord → United Kingdom) : on cherche SES villes (petite table), pas toutes celles du pays
     (Londres, Manchester, Leeds…). Édimbourg est ajouté.
  2. Rattachement à une zone existante (absorber) : les pays de la zone d'arrivée et les mots
     de son nom, cités par l'hypothèse (« Royaume-Uni », « Europe »), ne sont plus cherchés :
     ce n'est pas là que les fiches deviennent fausses. Le territoire qui change de mains
     reste toujours cherché ; la zone quittée aussi (Brésil : « Amériques » reste).

Tout ou rien, sauvegarde .bak_termes, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_termes.py            (aperçu)
    python3 generator/patch_s27_termes.py --apply
"""
import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_S27_TERMES"
CHEMIN = Path.cwd() / "generator" / "simuler_et_si.py"

REMPLACEMENTS = [
    ('VERSION = "v8.22"', 'VERSION = "v8.23"'),
    (
        '''def _termes_hypothese(hyp, sc, geo_ops, zones=None):''',
        '''# PATCH_S27_TERMES (v8.23) : territoires qui partagent le fond de carte d'un pays
# (pays_mapping.json) ; leurs villes, au lieu de toutes celles du pays.
VILLES_TERRITOIRE = {
    "Écosse": ["Glasgow", "Édimbourg", "Edinburgh", "Aberdeen", "Dundee", "Inverness"],
    "Pays de Galles": ["Cardiff", "Swansea", "Newport"],
    "Irlande du Nord": ["Belfast", "Derry"],
}


def _termes_hypothese(hyp, sc, geo_ops, zones=None):''',
    ),
    (
        '''        termes.setdefault(p, "pays dont la carte change")
        en = mapping.get(p)''',
        '''        termes.setdefault(p, "pays dont la carte change")
        en = mapping.get(p)
        if p in VILLES_TERRITOIRE:   # PATCH_S27_TERMES : ses villes, pas celles du pays entier
            for v in VILLES_TERRITOIRE[p]:
                termes.setdefault(v, f"ville ({p})")
            en = None''',
    ),
    (
        '''    plies = {t: " ".join(_plie_aligne(t).split()) for t in uniques}
    return {t: o for t, o in uniques.items()
            if not (o == "nom cité par l'hypothèse"
                    and any(u != t and _re.search(r"(?<![a-z0-9])" + _re.escape(plies[t]) + r"(?![a-z0-9])", plies[u])
                            for u in uniques))}''',
        '''    plies = {t: " ".join(_plie_aligne(t).split()) for t in uniques}
    resultat = {t: o for t, o in uniques.items()
                if not (o == "nom cité par l'hypothèse"
                        and any(u != t and _re.search(r"(?<![a-z0-9])" + _re.escape(plies[t]) + r"(?![a-z0-9])", plies[u])
                                for u in uniques))}
    # PATCH_S27_TERMES : zone d'arrivée d'un rattachement (absorber) -- ses pays et les mots de
    # son nom, cités par l'hypothèse, ne sont pas cherchés (les fiches n'y deviennent pas fausses).
    by_z = {z.get("slug"): z for z in zones or [] if isinstance(z, dict)}
    pays_arrivee, mots_arrivee = set(), set()
    for op, g in zip(ops_hyp, geo_ops or []):
        z = by_z.get(op.get("zone")) if op.get("action") == "absorber" and not g.get("erreurs") else None
        if z:
            pays_arrivee |= {" ".join(_plie_aligne(x.get("entite")).split()) for x in z.get("origine_reelle") or []
                             if isinstance(x, dict) and x.get("entite")}
            mots_arrivee |= set(_plie_aligne(z.get("nom")).split())
    gardes = {" ".join(_plie_aligne(p).split()) for p in pays_carte}
    return {t: o for t, o in resultat.items()
            if plies[t] in gardes
            or not ((o == "pays cité par l'hypothèse" and plies[t] in pays_arrivee)
                    or (o == "nom cité par l'hypothèse" and mots_arrivee
                        and set(plies[t].split()) <= mots_arrivee))}''',
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
    print(f"  ✓ generator/simuler_et_si.py : {len(REMPLACEMENTS)} remplacement(s) prêt(s) (v8.23)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    shutil.copy2(CHEMIN, CHEMIN.with_name("simuler_et_si.py.bak_termes"))
    CHEMIN.write_text(texte, encoding="utf-8")
    print("\n✓ Fait (sauvegarde simuler_et_si.py.bak_termes). Resimuler pour voir la nouvelle liste.")


if __name__ == "__main__":
    main()
