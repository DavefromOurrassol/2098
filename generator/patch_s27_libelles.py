#!/usr/bin/env python3
"""
patch_s27_libelles.py -- trois libellés justes (21 octobre 2026)
================================================================
  generator/simuler_et_si.py (v8.25)
    1. Liste d'application, « Nouvelles entités » : « catégorie à choisir » seulement si
       une entrée n'a pas de catégorie (la lecture IA en propose une depuis la v8.21) ;
       le rappel renvoie à l'étape ⑤ du panneau.
    2. « Propositions écartées au contrôle » : celles de la carte en premier (elles
       étaient cachées derrière « … », seules 8 étant montrées).
  generator/appliquer_et_si.py
    3. « ✓ N fichier(s) écrit(s) » précise « hors carte » quand une carte suit
       (la carte a son propre compte rendu juste après).

Tout ou rien, sauvegardes .bak_libelles, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_libelles.py            (aperçu)
    python3 generator/patch_s27_libelles.py --apply
"""
import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_S27_LIBELLES"
VAULT = Path.cwd()
R = {
    "generator/simuler_et_si.py": [
        ('VERSION = "v8.24"', 'VERSION = "v8.25"'),
        (
            '''        _etape(E, "Nouvelles entités", f"{len(cons['nouvelles_entites'])} entrée(s) prête(s) (bloc YAML ci-dessous) "
               "pour entites_custom/queue.yaml — catégorie à choisir",
               "python3 generator/create_entities_and_instances.py --mode custom",
               "la lecture IA ne donne pas de catégorie ; scenario_hint limite à ce scénario")''',
            '''        # PATCH_S27_LIBELLES : « à choisir » seulement si une catégorie manque (v8.21 : proposée par l'IA).
        sans_cat = sum(1 for n in cons["nouvelles_entites"] if not n.get("category"))
        _etape(E, "Nouvelles entités", f"{len(cons['nouvelles_entites'])} entrée(s) prête(s) (bloc YAML ci-dessous) "
               "pour entites_custom/queue.yaml"
               + (f" — catégorie à choisir pour {sans_cat}" if sans_cat else " — catégorie proposée, à relire"),
               "étape ⑤ du panneau (« Ajouter à la file »), puis python3 generator/create_entities_and_instances.py --mode custom",
               "scenario_hint limite à ce scénario")''',
        ),
        (
            '''    if c.get("ecartees"):
        L.append(f"_Propositions écartées au contrôle ({len(c['ecartees'])}) : " + " ; ".join(c["ecartees"][:8])
                 + (" …" if len(c["ecartees"]) > 8 else "") + "_")''',
            '''    if c.get("ecartees"):
        # PATCH_S27_LIBELLES : la carte d'abord (elle passait derrière « … »).
        ec = sorted(c["ecartees"], key=lambda x: not str(x).startswith("carte"))
        L.append(f"_Propositions écartées au contrôle ({len(ec)}) : " + " ; ".join(ec[:8])
                 + (" …" if len(ec) > 8 else "") + "_")''',
        ),
    ],
    "generator/appliquer_et_si.py": [
        (
            '''    n = W.ecrire()
    print(f"\\n✓ {n} fichier(s) écrit(s).")
    cartes = [o for o in ops if o["retenue"] and o["genre"] == "carte"]   # PATCH_S27_CARTE''',
            '''    n = W.ecrire()
    cartes = [o for o in ops if o["retenue"] and o["genre"] == "carte"]   # PATCH_S27_CARTE
    print(f"\\n✓ {n} fichier(s) écrit(s)" + (" (hors carte, ci-dessous)." if cartes else "."))   # PATCH_S27_LIBELLES''',
        ),
    ],
}
PREREQUIS = {"generator/simuler_et_si.py": ["PATCH_S27_ZONE_ENTITE"], "generator/appliquer_et_si.py": ["PATCH_S27_CARTE"]}


def main():
    apply = "--apply" in sys.argv
    nouveaux, erreurs = {}, []
    for nom, reps in R.items():
        chemin = VAULT / nom
        if not chemin.exists():
            erreurs.append(f"{nom} : introuvable (lancer depuis la racine du coffre)")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if MARQUEUR in texte:
            erreurs.append(f"{nom} : déjà patché ({MARQUEUR} présent)")
            continue
        for p in PREREQUIS.get(nom, []):
            if p not in texte:
                erreurs.append(f"{nom} : « {p} » absent (patch précédent non appliqué ?)")
        for n, (ancien, neuf) in enumerate(reps, 1):
            nb = texte.count(ancien)
            if nb != 1:
                erreurs.append(f"{nom} : repère n°{n} trouvé {nb} fois (attendu 1)")
                continue
            texte = texte.replace(ancien, neuf)
        try:
            compile(texte, str(chemin), "exec")
        except SyntaxError as e:
            erreurs.append(f"{nom} : erreur de syntaxe après patch ({e})")
        nouveaux[nom] = texte
    if erreurs:
        print("✗ Rien n'a été écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
        sys.exit(1)
    for nom in R:
        print(f"  ✓ {nom} : {len(R[nom])} remplacement(s) prêt(s)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    for nom, texte in nouveaux.items():
        chemin = VAULT / nom
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_libelles"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Libellés corrigés (sauvegardes .bak_libelles).")


if __name__ == "__main__":
    main()
