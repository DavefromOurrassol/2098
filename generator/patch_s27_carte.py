#!/usr/bin/env python3
"""
patch_s27_carte.py -- la carte dans « Appliquer » (étape ④) (18 octobre 2026)
=============================================================================
  generator/simuler_et_si.py (v8.22)
    - enregistre la carte de chaque scénario pour appliquer_et_si.py : changements
      déclarés (ou proposés par l'IA), sous-zones qui ne portent que ce pays (elles
      suivent), sous-zones à plusieurs pays (à répartir à la main), zones vidées ;
    - lecture IA : quand l'hypothèse fixe la carte d'un scénario, les propositions de
      carte de l'IA sont écartées (« carte fixée par l'hypothèse ») ;
    - liste d'application : « Créer la zone / Rattacher » et le rattachement des
      sous-zones renvoient à ④ « Appliquer » ; les sous-zones à plusieurs pays
      indiquent les trois choix.
  generator/appliquer_et_si.py
    - nouvelle opération « carte » (absorber / nouvelle_zone), exécutée par la Carte
      (ZoneRepository.assign_pays) APRÈS les autres écritures ; les sous-zones qui ne
      portent que ce pays gardent le pays et sont rattachées à la zone cible
      (ZoneRepository.reparent). Proposition IA absente de l'hypothèse : ⚠ (--inclure).
      En cas d'échec, geographie/<sc>.md et gui/zones_pays.json sont remis en l'état.
    - check-list : section « Carte » (sous-zones à répartir avec les trois choix, zone
      vidée, relations, rédactions, continent, contrôle de la géographie).
  Partition et région (tracés) restent à la main, comme avant.

Tout ou rien, sauvegardes .bak_carte, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s27_carte.py            (aperçu)
    python3 generator/patch_s27_carte.py --apply
Puis resimuler l'hypothèse (la lecture IA et la passe viennent du cache).
"""
import shutil
import sys
from pathlib import Path

MARQUEUR = "PATCH_S27_CARTE"
VAULT = Path.cwd()
R = {}

# ---------------------------------------------------------------------------
# simuler_et_si.py
# ---------------------------------------------------------------------------
R["generator/simuler_et_si.py"] = [
    ('VERSION = "v8.21"', 'VERSION = "v8.22"'),
    (
        '''        if out[sc].get("geographie") and sc not in hyp["geographie"]:
            hyp["geographie"][sc] = [dict(g, source="ia") for g in out[sc]["geographie"]]''',
        '''        # PATCH_S27_CARTE (v8.22) : l'hypothèse fixe la carte de ce scénario -> les
        # propositions de carte de l'IA sont écartées (elles la contrediraient).
        if out[sc].get("geographie") and any(g.get("source") != "ia"
                                              for g in hyp["geographie"].get(sc) or []):
            out[sc]["ecartees"] = (out[sc].get("ecartees") or []) + [
                f"carte : {g['pays']} ({g['action']}) écartée, carte de ce scénario fixée par l'hypothèse"
                for g in out[sc]["geographie"]]
            out[sc]["geographie"] = []
        if out[sc].get("geographie") and sc not in hyp["geographie"]:
            hyp["geographie"][sc] = [dict(g, source="ia") for g in out[sc]["geographie"]]''',
    ),
    (
        '''        if g["action"] == "absorber":
            _etape(E, "Carte", f"Rattacher {pays} à `{g['cible']}`",
                   f"Carte → clic sur {pays} → affecter à `{g['cible']}`",
                   "le pays change de mains")''',
        '''        auto = op.get("source") != "ia"   # PATCH_S27_CARTE : fait par ④ « Appliquer »
        if g["action"] == "absorber":
            _etape(E, "Carte", f"Rattacher {pays} à `{g['cible']}`",
                   "④ « Appliquer » le fait" if auto else f"Carte → clic sur {pays} → affecter à `{g['cible']}`",
                   "le pays change de mains")''',
    ),
    (
        '''                   f"Carte → clic sur {pays} → créer une zone (slug `{g['cible']}`, type {nz.get('type') or 'autre'}, "
                   f"statut {nz.get('statut') or 'emergent'})", "nouvelle zone de niveau 1")''',
        '''                   "④ « Appliquer » le fait" if auto else
                   f"Carte → clic sur {pays} → créer une zone (slug `{g['cible']}`, type {nz.get('type') or 'autre'}, "
                   f"statut {nz.get('statut') or 'emergent'})", "nouvelle zone de niveau 1")''',
    ),
    (
        '''                       "Carte → arbre → ↗️ déplacer, ou nouvelle sous-zone pour la part de " + pays,''',
        '''                       (f"au choix (étape ⑤) : la laisser sans {pays} ; la déplacer entière sous `{g['cible']}` "
                        f"(Carte → arbre → ↗️ déplacer) ; ou lui garder une portion de {pays} par un tracé"
                        if g["action"] in ("absorber", "nouvelle_zone") else
                        "Carte → arbre → ↗️ déplacer, ou nouvelle sous-zone pour la part de " + pays),''',
    ),
    (
        '''            _etape(E, "Carte", f"{len(simples)} sous-zone(s) de {pays} à rattacher à `{g['cible']}`",
                   f"python3 generator/reparenter_sous_zones_orphelines.py --scenario {sc} --zone-cible {g['cible']}",''',
        '''            _etape(E, "Carte", f"{len(simples)} sous-zone(s) de {pays} à rattacher à `{g['cible']}`"
                   + (f" (en gardant {pays})" if auto else ""),
                   ("④ « Appliquer » le fait (pas le bouton de la Carte : il leur retire le pays)" if auto else
                    f"python3 generator/reparenter_sous_zones_orphelines.py --scenario {sc} --zone-cible {g['cible']}"),''',
    ),
    (
        '''def _ecrire_operations(brut, hyp, portee, consequences, passe):''',
        '''def _carte_operations(hyp, sc, geo):
    """PATCH_S27_CARTE : changements de carte du scénario pour appliquer_et_si.py."""
    carte, zones_sc = [], None
    for op_h, g in zip((hyp.get("geographie") or {}).get(sc) or [], (geo or {}).get(sc) or []):
        entree = {"pays": g["pays"], "action": g["action"], "cible": g.get("cible"),
                  "source": op_h.get("source") or "hypothese",
                  "nouvelle_zone": dict(op_h.get("nouvelle_zone") or {}) if g["action"] == "nouvelle_zone" else None,
                  "erreurs": list(g.get("erreurs") or []), "alertes": list(g.get("alertes") or []),
                  "simples": [], "a_repartir": [],
                  "videes": [q["slug"] for q in g.get("quittees") or [] if q.get("videe")]}
        if g["action"] in ("absorber", "nouvelle_zone") and not entree["erreurs"]:
            if zones_sc is None:
                repo, _m = charger_zone_repository()
                zones_sc = {z.get("slug"): z for z in repo.load_all_zones(sc)}
            for o in (g.get("impact") or {}).get("sous_zones_orphelines") or []:
                if not o.get("slug") or o["slug"] == g.get("cible"):
                    continue
                autres = sorted({p for x in (zones_sc.get(o["slug"]) or {}).get("origine_reelle") or []
                                 if isinstance(x, dict) and x.get("entite")
                                 for p in _autres_pays(str(x["entite"]), g["pays"])})
                if autres:
                    entree["a_repartir"].append({"slug": o["slug"], "nom": o.get("nom"), "autres": autres})
                else:
                    entree["simples"].append(o["slug"])
        carte.append(entree)
    return carte


def _ecrire_operations(brut, hyp, portee, consequences, passe, geo=None):''',
    ),
    (
        '''            "erreurs": erreurs,
        }
    data = {''',
        '''            "erreurs": erreurs,
        }
        try:   # PATCH_S27_CARTE
            par_sc[sc]["carte"] = _carte_operations(hyp, sc, geo)
        except Exception as e:  # la carte ne doit jamais empêcher le reste
            par_sc[sc]["carte"] = []
            par_sc[sc]["erreurs"].append(f"carte : {type(e).__name__}: {e}")
    data = {''',
    ),
    (
        '''        _ecrire_operations(brut, hyp, portee, consequences, passe)''',
        '''        _ecrire_operations(brut, hyp, portee, consequences, passe, geo)   # PATCH_S27_CARTE''',
    ),
]

# ---------------------------------------------------------------------------
# appliquer_et_si.py
# ---------------------------------------------------------------------------
FONCTIONS_CARTE = r'''# ---------------------------------------------------------------------------
# Carte (PATCH_S27_CARTE, 18 oct 2026) : absorber / nouvelle_zone par la Carte
# ---------------------------------------------------------------------------

def zones_geo(sc):
    p = VAULT / "geographie" / f"{sc}.md"
    if not p.exists():
        return []
    d = decoupe(p.read_text(encoding="utf-8"))
    fm = lire_fm(d[1]) if d else None
    return [z for z in (fm or {}).get("zones") or [] if isinstance(z, dict)]


def porte_pays(zone, pays):
    return any(isinstance(o, dict) and plie(o.get("entite")) == plie(pays)
               for o in (zone or {}).get("origine_reelle") or [])


def note_carte(o):
    parts = []
    if o.get("simples"):
        parts.append(f"puis sous-zone(s) rattachée(s) à `{o['cible']}` en gardant {o['pays']} : "
                     + ", ".join(o["simples"]))
    if o.get("a_repartir"):
        parts.append("à répartir à la main (étape ⑤) : "
                     + ", ".join(f"{s['slug']} (aussi {', '.join(s['autres'])})" for s in o["a_repartir"]))
    if o.get("videes"):
        parts.append("zone(s) vidée(s) de tout territoire : " + ", ".join(o["videes"]))
    return "\n         → ".join(parts)


def _repo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("zone_repository", VAULT / "gui" / "zone_repository.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ZoneRepository(VAULT, VAULT / "gui")


def appliquer_carte(repo, o):
    """Un changement de carte ; lève une exception si le résultat n'est pas celui attendu."""
    import copy
    sc, pays, cible = o["sc"], o["pays"], o["cible"]
    by = {z.get("slug"): z for z in repo.load_all_zones(sc)}
    simples = [s for s in o.get("simples") or [] if s in by]
    gardees = {s: copy.deepcopy(by[s].get("origine_reelle") or []) for s in simples}
    hautes = [s for s in simples if by[s].get("parent") not in simples]   # le sous-arbre suit
    if o["action"] == "nouvelle_zone":
        repo.assign_pays(sc, pays, "creer", nouvelle_zone=dict(o.get("nouvelle_zone") or {}))
    else:
        repo.assign_pays(sc, pays, "absorber", zone_slug=cible)
    if gardees:
        gf = repo._load_geo(sc)
        for z in gf.zones:
            if z.get("slug") in gardees:
                z["origine_reelle"] = gardees[z["slug"]]
        repo._save_geo(gf)
        for s in hautes:
            if by[s].get("parent") != cible:
                repo.reparent(sc, s, cible, dry_run=False)
    apres = {z.get("slug"): z for z in repo.load_all_zones(sc)}
    if not porte_pays(apres.get(cible), pays):
        raise ValueError(f"{pays} absent de `{cible}` après l'opération")
    for s in hautes:
        if (apres.get(s) or {}).get("parent") != cible or not porte_pays(apres.get(s), pays):
            raise ValueError(f"sous-zone `{s}` mal rattachée après l'opération")
    return (f"✓ {o['n']}. {o['texte']}"
            + (f" ; {len(hautes)} sous-zone(s) rattachée(s) : {', '.join(hautes)}" if hautes else ""))


def appliquer_cartes(cartes):
    """Toutes les opérations de carte retenues, après les autres écritures. Échec : géographie et
    zones_pays.json remis en l'état d'avant la carte. Retourne (nombre fait, messages)."""
    repo = _repo()
    fichiers = [repo._zones_pays_path()] + sorted({VAULT / "geographie" / f"{o['sc']}.md" for o in cartes})
    avant = {p: p.read_text(encoding="utf-8") for p in fichiers if p.exists()}
    for p in avant:
        bak = p.with_name(p.name + ".bak_appliquer")
        if not bak.exists():
            shutil.copy2(p, bak)
    msgs = []
    try:
        for o in cartes:
            msgs.append(appliquer_carte(repo, o))
    except Exception as e:
        for p, t in avant.items():
            p.write_text(t, encoding="utf-8")
        for o in cartes:
            o["retenue"], o["alerte"] = False, f"échec à l'écriture : {type(e).__name__}: {e}"
        return 0, [f"✗ carte non appliquée ({type(e).__name__}: {e}) : géographie et zones_pays.json "
                   "remis en l'état ; le reste est écrit."]
    return len(cartes), msgs


'''

SECTION_RESTE = r'''        # PATCH_S27_CARTE : suites de la carte
        cartes = [o for o in mes_ops if o["genre"] == "carte" and faites(o)]
        if cartes:
            L += ["### Carte", ""]
            for o in cartes:
                for s in o.get("a_repartir") or []:
                    case(f"Sous-zone `{s['slug']}` ({s.get('nom') or s['slug']}) : elle porte aussi "
                         f"{', '.join(s['autres'])} et a perdu {o['pays']}. Au choix : la laisser ainsi ; la "
                         f"déplacer entière sous `{o['cible']}` (Carte → arbre → ↗️ déplacer) ; ou lui rendre une "
                         f"portion de {o['pays']} par un tracé (Carte → ✏️ éditer → ✏️ dessiner).")
                for v in o.get("videes") or []:
                    case(f"`{v}` n'a plus aucun territoire : la garder (vestige, exil) ou la supprimer "
                         "(Carte → ✏️ éditer → Zone dangereuse).")
                if o["action"] == "nouvelle_zone":
                    case(f"Description, relations (alliés / rivaux) de `{o['cible']}` : `geographie/{sc}.md` "
                         "(la création n'en écrit aucune)")
                    case(f"Rédactions de `{o['cible']}` : `python3 generator/generate_journaux.py --scenario {sc} "
                         "--update`, puis `python3 generator/audit_couverture_journalistes.py --report`")
                    case("Continent de la nouvelle zone sur le site : `python3 generator/export_revues.py --continents`")
            case(f"Contrôle de la géographie : `python3 generator/scan_geographie_complet.py --scenario {sc}`")
            L.append("")

'''

R["generator/appliquer_et_si.py"] = [
    (
        '''  - contrôle final : validate.py.''',
        '''  - carte (18 oct 2026) : absorber / nouvelle_zone de l'hypothèse, par la Carte (zone_repository),
    après les autres écritures ; les sous-zones qui ne portent que ce pays le gardent et suivent ;
    partition, région et sous-zones à plusieurs pays restent à la main ;
  - contrôle final : validate.py.''',
    ),
    (
        '''        # Trajectoires (lecture puis passe ; même instance, sorts différents : ⚠ sur les deux)''',
        '''        # Carte (PATCH_S27_CARTE) : absorber / nouvelle_zone ; partition et région à la main.
        by_z = {z.get("slug"): z for z in zones_geo(sc)}
        for c in ps.get("carte") or []:
            if c["action"] not in ("absorber", "nouvelle_zone"):
                a_main.append(f"[{sc}] carte : {c['action']} de {c['pays']} (tracés) : voir la liste "
                              "d'application du rapport")
                continue
            cible, z = c["cible"], by_z.get(c["cible"])
            alerte = None
            if c.get("erreurs"):
                alerte = "refusé au contrôle de la simulation : " + "; ".join(c["erreurs"][:2])
            elif porte_pays(z, c["pays"]):
                alerte = "déjà appliqué"
            elif c["action"] == "nouvelle_zone" and z:
                alerte = "slug déjà pris"
            elif c["action"] == "absorber" and not z:
                alerte = "zone introuvable dans la géographie"
            elif c.get("source") == "ia":
                alerte = "proposé par la lecture IA, absent de l'hypothèse"
            elif c.get("alertes"):
                alerte = "; ".join(c["alertes"][:2])
            texte = (f"Créer la zone `{cible}` ({(c.get('nouvelle_zone') or {}).get('nom')}) avec {c['pays']}"
                     if c["action"] == "nouvelle_zone" else f"Rattacher {c['pays']} à `{cible}`")
            op(sc, "carte", texte, alerte, pays=c["pays"], action=c["action"], cible=cible,
               nouvelle_zone=c.get("nouvelle_zone"), simples=c.get("simples") or [],
               a_repartir=c.get("a_repartir") or [], videes=c.get("videes") or [])

        # Trajectoires (lecture puis passe ; même instance, sorts différents : ⚠ sur les deux)''',
    ),
    (
        '''        # Phrases à corriger
        textes = pas.get("textes") or []''',
        SECTION_RESTE + '''        # Phrases à corriger
        textes = pas.get("textes") or []''',
    ),
    (
        '''          f"Les « possibles » de la passe exhaustive, la carte et les fiches trouvées par mots-clés restent "''',
        '''          f"Les « possibles » de la passe exhaustive, les tracés de carte et les fiches trouvées par mots-clés restent "''',
    ),
    (
        '''def lancer(cmd):''',
        FONCTIONS_CARTE + '''def lancer(cmd):''',
    ),
    (
        '''            and o["alerte"] not in ("déjà appliqué", "déjà absente", "déjà présente", "fiche introuvable",
                                    "zone introuvable dans la géographie", "trajectoire inconnue")''',
        '''            and o["alerte"] not in ("déjà appliqué", "déjà absente", "déjà présente", "fiche introuvable",
                                    "zone introuvable dans la géographie", "trajectoire inconnue",
                                    "slug déjà pris") \\
            and not str(o["alerte"] or "").startswith("refusé")   # PATCH_S27_CARTE''',
    ),
    (
        '''                notes[o["n"]] = f"{n} modification(s)"''',
        '''                notes[o["n"]] = f"{n} modification(s)"
            elif o["genre"] == "carte":   # PATCH_S27_CARTE : écrite après les autres (--apply)
                notes[o["n"]] = note_carte(o)''',
    ),
    (
        '''    n = W.ecrire()
    print(f"\\n✓ {n} fichier(s) écrit(s).")
    retenues = [o for o in ops if o["retenue"]]''',
        '''    n = W.ecrire()
    print(f"\\n✓ {n} fichier(s) écrit(s).")
    cartes = [o for o in ops if o["retenue"] and o["genre"] == "carte"]   # PATCH_S27_CARTE
    if cartes:
        print("Carte :")
        faits, msgs = appliquer_cartes(cartes)
        for m in msgs:
            print(f"  {m}")
        n += faits
    retenues = [o for o in ops if o["retenue"]]''',
    ),
    (
        '''        if any(o["sc"] == sc and o["genre"] == "zone" for o in retenues):''',
        '''        if any(o["sc"] == sc and o["genre"] in ("zone", "carte") for o in retenues):''',
    ),
]

PREREQUIS = {"generator/simuler_et_si.py": ["PATCH_S27_CATEGORIES", 'VERSION = "v8.21"'],
             "generator/appliquer_et_si.py": ["PATCH_S27_CATEGORIES"]}


def main():
    apply = "--apply" in sys.argv
    if not (VAULT / "gui" / "zone_repository.py").exists():
        sys.exit("✗ gui/zone_repository.py introuvable (lancer depuis la racine du coffre). Rien fait.")
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
                erreurs.append(f"{nom} : « {p} » absent (version inattendue)")
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
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_carte"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Carte dans « Appliquer » en place (sauvegardes .bak_carte). Resimuler l'hypothèse.")


if __name__ == "__main__":
    main()
