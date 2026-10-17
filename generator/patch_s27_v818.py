#!/usr/bin/env python3
"""
patch_s27_v818.py — Ourrassol 2098 (S27, 13 octobre 2026)
=========================================================

v8.18 : la simulation transmet à l'injection le SORT des entités du récit.

simuler_et_si.py (v8.17.1 → v8.18)
  - liste_application() calcule des « faits » par scénario : pour chaque
    acteur de l'entrée commune (acteurs_hint), son sort après l'élément
    (disparaît / change de trajectoire / reste tel quel), plus les statuts
    de zone changés ;
  - l'entrée commune porte `faits_imposes: {scénario: [{fait, slug, sort}]}`,
    avec en tête les `contraintes` de l'hypothèse.

inject_custom_events.py
  - bloc « FAITS IMPOSÉS » dans le prompt de l'étape 2 ;
  - la ligne « Propagation via la matrice » devient « Effet propagé aux
    autres variables » avec l'interdiction de nommer ce mécanisme (cause de
    « la matrice » dans les récits) ;
  - ⚠ (sans rejet) quand une entité censée survivre est associée à une
    destruction dans une même phrase, ou quand le récit emploie « matrice ».

Refuse un second passage. Sauvegardes .bak_v818. Vérifie la syntaxe des
deux fichiers avant d'écrire.

USAGE
    python3 generator/patch_s27_v818.py            # aperçu
    python3 generator/patch_s27_v818.py --apply    # écrit
"""

import argparse
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

GEN = Path(__file__).resolve().parent
MARQUEUR = "PATCH_S27_V818"

# ---------------------------------------------------------------------------
# simuler_et_si.py
# ---------------------------------------------------------------------------

SIM = [
    ('VERSION = "v8.17.1"', 'VERSION = "v8.18"'),

    ('''    acteurs = [s for s, _ in sorted(poids.items(), key=lambda x: -x[1])][:4]
    return {"etapes": E, "avert": donnees["avert"], "sources_ia": sources_ia, "fiches_citant": cites,
            "nouvelles_entites": cons.get("nouvelles_entites") or [], "acteurs": acteurs}
''',
     '''    acteurs = [s for s, _ in sorted(poids.items(), key=lambda x: -x[1])][:4]
    # PATCH_S27_V818 : sort de chaque acteur du récit (et zones changées), transmis à
    # l'injection pour que le texte ne le réinvente pas à chaque tirage.
    annee = f"{hyp['date']:g}"
    sort_final = {t["instance"]: t for t in (cons.get("trajectoires") or []) + p_obl["trajectoires"]}
    faits = []
    for s in acteurs:
        inst = by_inst.get(s) or {}
        nom = inst.get("name") or s
        t = sort_final.get(s)
        if t and t["apres"] == "disparu":
            faits.append({"fait": f"{nom} ({s}) disparaît en {annee} (trajectoire {t['avant']} → disparu) : "
                                  f"après cette date, elle n'agit plus.", "slug": s, "sort": "disparait"})
        elif t:
            faits.append({"fait": f"{nom} ({s}) passe de « {t['avant']} » à « {t['apres']} » après {annee} : "
                                  f"elle existe toujours (elle peut perdre des lieux, des biens ou du pouvoir), "
                                  f"ne la décris pas comme disparue.", "slug": s, "sort": "change"})
        elif inst:
            faits.append({"fait": f"{nom} ({s}) garde sa trajectoire « {inst.get('trajectoire') or '?'} » : "
                                  f"elle survit à l'événement sans changement majeur, ne la décris ni détruite "
                                  f"ni disparue.", "slug": s, "sort": "reste"})
    for z in cons.get("zones_statut") or []:
        faits.append({"fait": f"La zone {z.get('nom') or z['zone']} ({z['zone']}) passe de « {z['avant']} » à "
                              f"« {z['apres']} »" + (" : le lieu disparaît." if z["apres"] == "disparu"
                                                     else " : le lieu subsiste."),
                      "slug": z["zone"], "sort": "zone"})
    return {"etapes": E, "avert": donnees["avert"], "sources_ia": sources_ia, "fiches_citant": cites,
            "nouvelles_entites": cons.get("nouvelles_entites") or [], "acteurs": acteurs, "faits": faits}
'''),

    ('''    # V8.15 : ce qui a été simulé est imposé à l'injection (patch_s27_injection_imposee.py).
''',
     '''    # PATCH_S27_V818 : faits imposés au récit (contraintes de l'hypothèse + sort des acteurs).
    faits = {sc: list((application.get(sc) or {}).get("faits") or []) for sc in scen}
    if hyp.get("contraintes"):
        faits = {sc: [{"fait": c, "sort": "contrainte"} for c in hyp["contraintes"]] + v
                 for sc, v in faits.items()}
    faits = {sc: v for sc, v in faits.items() if v}
    if faits:
        entree["faits_imposes"] = faits
    # V8.15 : ce qui a été simulé est imposé à l'injection (patch_s27_injection_imposee.py).
'''),

    ('''            "```yaml", _yaml_bloc([entree]), "```", ""]''',
     '''            *(["`faits_imposes` : contraintes de l'hypothèse et sort des acteurs du récit (disparaît, "
               "change, reste) ; l'injection les donne à l'IA comme faits non négociables.", ""]
              if entree.get("faits_imposes") else []),
            "```yaml", _yaml_bloc([entree]), "```", ""]'''),
]

# ---------------------------------------------------------------------------
# inject_custom_events.py
# ---------------------------------------------------------------------------

INJ = [
    ('''        lignes.append(f"- Propagation via la matrice : {'oui' if imp['via_matrice'] else 'non'}")''',
     '''        # PATCH_S27_V818 : ne plus donner le mot « matrice » à l'IA (il finissait dans le récit).
        lignes.append(f"- Effet propagé aux autres variables : {'oui' if imp['via_matrice'] else 'non'} "
                      f"(mécanique interne du simulateur : ne nomme jamais ce mécanisme ni le mot "
                      f"« matrice » dans le récit)")'''),

    ('''    impositions_txt = _texte_impositions(idea, scenario)
''',
     '''    impositions_txt = _texte_impositions(idea, scenario)
    faits_txt = _texte_faits(idea, scenario)  # PATCH_S27_V818
'''),

    ('''{actors_hint_txt}{zone_hint_txt}{impositions_txt}''',
     '''{actors_hint_txt}{zone_hint_txt}{impositions_txt}{faits_txt}'''),

    ('''def process_idea(client, idea, dry_run=False):
''',
     '''# PATCH_S27_V818 (13 octobre 2026) -- faits imposés par le simulateur « et si ? »
# (sort des acteurs du récit, contraintes de l'hypothèse). Sans faits_imposes, rien ne change.

def _faits_du_scenario(idea, scenario):
    """faits_imposes : {scénario: [fait]} ou [fait] (tous scénarios) ; un fait est une
    phrase ou {fait, slug, sort}. Retourne une liste de dicts."""
    brut = idea.get("faits_imposes")
    if isinstance(brut, dict):
        liste = brut.get(scenario) or []
    elif isinstance(brut, list):
        liste = brut
    else:
        return []
    out = []
    for f in liste if isinstance(liste, list) else []:
        if isinstance(f, str) and f.strip():
            out.append({"fait": f.strip()})
        elif isinstance(f, dict) and str(f.get("fait") or "").strip():
            out.append(f)
    return out


def _texte_faits(idea, scenario):
    faits = _faits_du_scenario(idea, scenario)
    if not faits:
        return ""
    return ("\\n## FAITS IMPOSÉS (issus de la simulation -- le récit ne doit JAMAIS les contredire)\\n"
            + "\\n".join(f"- {f['fait']}" for f in faits)
            + "\\nSi la description originale semble contredire un de ces faits, les faits priment.\\n")


def _plie_v818(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


MOTS_DESTRUCTION_V818 = re.compile(
    r"detrui|\\brase|\\braye|aneanti|dispar|n'existe plus|effondr|en cendres|englouti|raye de la carte")


def verifier_faits(instance_data, idea, scenario, available_actors):
    """Avertissements (jamais bloquants) : entité censée survivre associée à une
    destruction dans une même phrase ; mot « matrice » dans le récit."""
    avert = []
    textes = " ".join(str(instance_data.get(k) or "")
                      for k in ("realisation", "description_complete", "consequences"))
    if re.search(r"\\bmatrices?\\b", _plie_v818(textes)):
        avert.append("le récit emploie « matrice » (terme interne du simulateur) : à retoucher")
    noms = {a["slug"]: a["name"] for a in available_actors}
    phrases = re.split(r"(?<=[.!?])\\s+", textes)
    for f in _faits_du_scenario(idea, scenario):
        if f.get("sort") != "reste" or not f.get("slug"):
            continue
        nom = str(noms.get(f["slug"]) or f["slug"])
        morceaux = [_plie_v818(m.strip()) for m in re.split(r"\\s+[—–-]\\s+", nom) if len(m.strip()) >= 6]
        for ph in phrases:
            pp = _plie_v818(ph)
            if any(m in pp for m in morceaux) and MOTS_DESTRUCTION_V818.search(pp):
                avert.append(f"{nom} ({f['slug']}) doit survivre, mais une phrase l'associe à une "
                             f"destruction : « {' '.join(ph.split())[:160]} »")
                break
    return avert


def process_idea(client, idea, dry_run=False):
'''),

    ('''            if idea.get("edition_active") and idea.get("date_imposee") is not None:
''',
     '''            for avert in verifier_faits(instance_data, idea, scenario, available_actors):  # PATCH_S27_V818
                print(f"  ⚠ [{scenario}] {avert}")

            if idea.get("edition_active") and idea.get("date_imposee") is not None:
'''),

    ('''#   via_matrice_impose     : optionnel, true/false imposé.
''',
     '''#   via_matrice_impose     : optionnel, true/false imposé.
#   faits_imposes          : optionnel (simulateur, v8.18). Faits que le récit ne
#                            doit pas contredire, par scénario :
#                              breakdown:
#                                - {fait: "X disparaît en 2076", slug: x_breakdown,
#                                   sort: disparait}
#                            (sort : disparait | change | reste | zone | contrainte ;
#                            « reste » déclenche un ⚠ si le texte détruit l'entité).
'''),
]


def appliquer(texte, remplacements, nom):
    if MARQUEUR in texte:
        raise SystemExit(f"✗ {nom} : déjà patché ({MARQUEUR} présent), rien à faire.")
    for i, (avant, apres) in enumerate(remplacements, 1):
        n = texte.count(avant)
        if n != 1:
            raise SystemExit(f"✗ {nom} : ancrage n°{i} trouvé {n} fois (attendu 1) — version inattendue, rien écrit.\n"
                             f"  début de l'ancrage : {avant.strip()[:80]!r}")
        texte = texte.replace(avant, apres)
    return texte


def verifier_syntaxe(texte, nom):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(texte)
    try:
        py_compile.compile(f.name, doraise=True)
    except py_compile.PyCompileError as e:
        raise SystemExit(f"✗ {nom} : erreur de syntaxe après patch, rien écrit :\n{e}")
    finally:
        Path(f.name).unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    cibles = [(GEN / "simuler_et_si.py", SIM), (GEN / "inject_custom_events.py", INJ)]
    nouveaux = []
    for p, remp in cibles:
        if not p.exists():
            sys.exit(f"✗ {p.name} introuvable dans {GEN}")
        nouveau = appliquer(p.read_text(encoding="utf-8"), remp, p.name)
        verifier_syntaxe(nouveau, p.name)
        nouveaux.append((p, nouveau))
        print(f"  {p.name} : {len(remp)} modification(s), syntaxe OK")
    if not a.apply:
        print("APERÇU : tout s'applique proprement. Relancer avec --apply pour écrire (.bak_v818).")
        return
    for p, nouveau in nouveaux:
        shutil.copy2(p, p.with_name(p.name + ".bak_v818"))
        p.write_text(nouveau, encoding="utf-8")
    print("✓ v8.18 appliquée (simuler_et_si.py, inject_custom_events.py ; sauvegardes .bak_v818).")


if __name__ == "__main__":
    main()
