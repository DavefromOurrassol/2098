#!/usr/bin/env python3
"""
patch_u3al_entite_decider_injecter.py — Ourrassol 2098 (14 novembre 2026)

Patch 3/4 du type « entité » dans « Et si ? » : étapes ② Décider et ③ Injecter.
Prérequis : U3ah (--idea dans create_entities_and_instances.py) et U3aj.

Parcours d'une entité (option A, sans simulation chiffrée) :
    ① vérifié (dès l'ajout du bloc)  ->  ② adopter / rejeter  ->  ③ injecter
Statuts : vérifié · rejeté · adopté, en attente d'injection · injecté.

  et_si_dossiers.py     statut « vérifié » ; adopter / rejeter / annuler pour une
                        entité (la décision est enregistrée dans le dossier :
                        AUCUNE file n'est remplie) ; contrôle du slug à l'adoption ;
                        empreinte du bloc pour détecter une modification.
  et_si_statut.py       étape en cours (2, 3, puis 6 = terminé) et alerte « modifiée
                        depuis l'adoption ».
  et_si_injecter.py     --id <entité> : create_entities_and_instances.py --idea
                        (une seule entité, sans toucher entites_custom/) ; --dry-run
                        = appels IA réels, rien d'écrit.
  simuler_et_si.py      --adopter <entité> : messages propres (--apercu inclus).
  create_entities_and_instances.py
                        la description de l'idée (champ `description`, facultatif)
                        est transmise à l'IA qui déduit l'archétype ; sans elle,
                        l'IA ne verrait que le nom et la catégorie.

Limite connue : l'annulation d'une entité injectée ne l'enlève pas du vault
(message ⚠ explicite) ; « injecté » = entites/<slug>.md présent.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3al_entite_decider_injecter.py            # aperçu
    python3 generator/patch_u3al_entite_decider_injecter.py --apply    # écrit

Sauvegarde .bak_u3al de chaque fichier ; refuse un second passage ; py_compile de
tous (restauration automatique de TOUS en cas d'échec).
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

MARQUEUR = "U3al"
G = Path("generator")

# --------------------------------------------------------------------------
# et_si_dossiers.py
# --------------------------------------------------------------------------

DOS_HELPERS = '''# ---------------------------------------------------------------------------
# U3al (14 nov 2026) : hypothèses de type « entité » (pas de simulation chiffrée)
# ---------------------------------------------------------------------------

HYPOTHESES_PATH = VAULT_ROOT / "et_si" / "hypotheses.yaml"
ENTITES_DIR = VAULT_ROOT / "entites"


def hypothese_brute(hid):
    """Bloc de l'hypothèse tel qu'écrit dans hypotheses.yaml (None si absent)."""
    try:
        data = yaml.safe_load(HYPOTHESES_PATH.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    for h in data.get("hypotheses") or []:
        if isinstance(h, dict) and str(h.get("id")) == str(hid):
            return h
    return None


def est_entite(hid):
    h = hypothese_brute(hid)
    return bool(h) and str(h.get("type") or "").strip().lower() == "entite"


def slug_entite(nom):
    """Même slug que create_entities_and_instances.py (slugs.slugify)."""
    try:
        from slugs import slugify as _s
        return _s(str(nom or ""))
    except Exception:  # noqa: BLE001 -- repli
        t = re.sub(r"[^a-z0-9]+", "_", _plie(nom)).strip("_")
        return t[:60].rstrip("_")


def entite_existe(slug):
    """entites/<slug>.md présent, ou slug dans le registre entites/_entities_list.json."""
    if not slug:
        return False
    if (ENTITES_DIR / f"{slug}.md").exists():
        return True
    try:
        reg = json.loads((ENTITES_DIR / "_entities_list.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return any(isinstance(e, dict) and e.get("slug") == slug for e in reg)


def entree_entite(brut):
    """Idée au format d'une entrée de entites_custom/queue.yaml, pour
    create_entities_and_instances.py --idea."""
    hid = brut.get("id")
    idee = {"id": hid, "nom": " ".join(str(brut.get("nom") or "").split()),
            "category": brut.get("categorie"), "scenario_ref": brut.get("scenario_ref"),
            "source": f"et_si_{hid}"}
    for cle_h, cle_i in (("description", "description"), ("role", "role"), ("etat", "etat")):
        v = " ".join(str(brut.get(cle_h) or "").split())
        if v:
            idee[cle_i] = v
    scen = brut.get("scenarios")
    if isinstance(scen, list) and scen:
        idee["scenario_hint"] = [str(s) for s in scen]
    return idee


def _statut_entite(hid, dossier):
    dec = dossier.get("decision") or {}
    if dec.get("statut") == "rejeté":
        return "rejeté"
    if dec.get("statut") != "adopté":
        return "vérifié"
    if entite_existe(slug_entite((dec.get("entree") or {}).get("nom"))):
        return "injecté"
    return "adopté, en attente d'injection"


def _adopter_entite(brut, hid, apercu=False):
    d = charger().get(hid) or {}
    st = statut(hid, d)
    if st not in ("vérifié", "rejeté"):
        raise DossierErreur(f"{hid} est déjà « {st} » : --annuler-decision d'abord si tu veux la reprendre.")
    entree = entree_entite(brut)
    slug = slug_entite(entree["nom"])
    if not slug:
        raise DossierErreur(f"{hid} : nom inutilisable (slug vide).")
    if entite_existe(slug):
        raise DossierErreur(f"l'entité {slug!r} existe déjà dans le vault : adopter une entité de même nom "
                            f"réécrirait sa fiche (renommer l'hypothèse, ou la rejeter).")
    if apercu:
        return entree
    data = charger()
    data.setdefault(hid, {})["decision"] = {
        "statut": "adopté", "date": _maintenant(), "motif": None, "type": "entite",
        "empreinte": empreinte_hypothese(brut), "entree": entree}
    sauver(data)
    return entree


'''
DOS_ANCRE_HELPERS = '''# ---------------------------------------------------------------------------
# Enregistrement d'une simulation
# ---------------------------------------------------------------------------
'''

DOS_ANCRE_STATUT = ('def statut(hid, dossier=None):\n'
                    '    dossier = dossier if dossier is not None else charger().get(hid) or {}\n')
DOS_NOUV_STATUT = DOS_ANCRE_STATUT + ('    if est_entite(hid):   # U3al\n'
                                      '        return _statut_entite(hid, dossier)\n')

DOS_ANCRE_ADOPTER = ('def adopter(brut, hid, portee=None, intensite=None, apercu=False):\n'
                     '    entree, sim = preparer_adoption(brut, hid, portee, intensite)\n')
DOS_NOUV_ADOPTER = ('def adopter(brut, hid, portee=None, intensite=None, apercu=False):\n'
                    '    if str(brut.get("type") or "").strip().lower() == "entite":   # U3al\n'
                    '        return _adopter_entite(brut, hid, apercu)\n'
                    '    entree, sim = preparer_adoption(brut, hid, portee, intensite)\n')

DOS_ANCRE_REJ = ('    if not d.get("simulation"):\n'
                 '        raise DossierErreur(f"{hid} n\'a jamais été simulée.")\n'
                 '    st = statut(hid, d)\n'
                 '    if st not in ("simulé", "rejeté"):\n'
                 '        raise DossierErreur(f"{hid} est déjà « {st} » : --annuler-decision d\'abord.")\n')
DOS_NOUV_REJ = ('    if not d.get("simulation") and not est_entite(hid):   # U3al\n'
                '        raise DossierErreur(f"{hid} n\'a jamais été simulée.")\n'
                '    st = statut(hid, d)\n'
                '    if st not in ("simulé", "rejeté", "vérifié"):\n'
                '        raise DossierErreur(f"{hid} est déjà « {st} » : --annuler-decision d\'abord.")\n')

DOS_ANCRE_ANN = '        raise DossierErreur(f"{hid} n\'a aucune décision à annuler.")\n'
DOS_NOUV_ANN = DOS_ANCRE_ANN + '''    if est_entite(hid):   # U3al : pas de file, rien à retirer
        st = statut(hid, d)
        slug = slug_entite(((d.get("decision") or {}).get("entree") or {}).get("nom"))
        d.pop("decision")
        data[hid] = d
        sauver(data)
        msgs = []
        if st == "injecté":
            msgs.append(f"⚠ l'entité {slug} reste dans le vault (entites/{slug}.md) : "
                        f"annuler la décision ne l'enlève pas")
        return st, msgs
'''

DOS_REMPL = [
    ("fonctions entité", DOS_ANCRE_HELPERS, DOS_HELPERS + DOS_ANCRE_HELPERS),
    ("statut d'une entité", DOS_ANCRE_STATUT, DOS_NOUV_STATUT),
    ("adopter une entité", DOS_ANCRE_ADOPTER, DOS_NOUV_ADOPTER),
    ("rejeter une entité", DOS_ANCRE_REJ, DOS_NOUV_REJ),
    ("annuler la décision d'une entité", DOS_ANCRE_ANN, DOS_NOUV_ANN),
]

# --------------------------------------------------------------------------
# et_si_statut.py
# --------------------------------------------------------------------------

STA_ANCRE_TYPE = '    typ = ed.type_dossier(d)   # U2e : evenement | signal\n'
STA_NOUV_TYPE = '    typ = "entite" if ed.est_entite(hid) else ed.type_dossier(d)   # U2e / U3al\n'

STA_ANCRE_ETAPE = '    if not sim:\n        etape = 1\n    elif st in ("simulé", "rejeté"):\n'
STA_NOUV_ETAPE = ('    if typ == "entite":   # U3al : vérifié à l\'ajout, puis ② décider, ③ injecter (6 = terminé)\n'
                  '        etape = 2 if st in ("vérifié", "rejeté") else (3 if st.startswith("adopté") else 6)\n'
                  '    elif not sim:\n        etape = 1\n    elif st in ("simulé", "rejeté"):\n')

STA_ANCRE_RAPPORT = '    rapport = sim.get("rapport")\n'
STA_NOUV_RAPPORT = ('    if typ == "entite" and dec.get("statut") == "adopté" and st != "injecté":   # U3al\n'
                    '        brut = ed.hypothese_brute(hid)\n'
                    '        if brut is not None and dec.get("empreinte") != ed.empreinte_hypothese(brut):\n'
                    '            alertes.append("hypothèse modifiée depuis l\'adoption : annuler la décision, "\n'
                    '                           "puis adopter de nouveau")\n') + STA_ANCRE_RAPPORT

STA_REMPL = [
    ("type entité", STA_ANCRE_TYPE, STA_NOUV_TYPE),
    ("étape en cours d'une entité", STA_ANCRE_ETAPE, STA_NOUV_ETAPE),
    ("alerte hypothèse modifiée", STA_ANCRE_RAPPORT, STA_NOUV_RAPPORT),
]

# --------------------------------------------------------------------------
# et_si_injecter.py
# --------------------------------------------------------------------------

INJ_FONCTION = '''def _injecter_entite(hid, a):
    """U3al : injecte UNE entité adoptée (create_entities_and_instances.py --idea),
    sans lire ni écrire entites_custom/queue.yaml."""
    if a.plan:
        print(f"{hid} est une entité : pas de liste à l'étape ④ (ni carte, ni zones), rien à sauter.")
        return
    st = ed.statut(hid)
    if st != "adopté, en attente d'injection":
        sys.exit(f"✗ {hid} est « {st} » : seule une hypothèse « adopté, en attente d'injection » "
                 f"peut être injectée ici.")
    idee = ((ed.charger().get(hid) or {}).get("decision") or {}).get("entree") or {}
    if not idee.get("nom"):
        sys.exit(f"✗ {hid} : décision sans entrée d'entité (annuler la décision et adopter de nouveau).")
    cmd = [sys.executable, str(GEN / "create_entities_and_instances.py"),
           "--idea", json.dumps(idee, ensure_ascii=False, default=str), "--json"]
    if a.dry_run:
        cmd.append("--dry-run")
    print(("SIMULATION (appels IA réels, rien écrit)" if a.dry_run else "INJECTION")
          + f" — {hid} (entité « {idee.get('nom')} », {idee.get('category')})\\n")
    try:
        r = subprocess.run(cmd, cwd=GEN, capture_output=True, text=True, timeout=TIMEOUT,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        sys.exit(f"✗ délai dépassé ({TIMEOUT} s) : vérifier entites/ avant de relancer.")
    sortie = (r.stdout + ("\\n" + r.stderr if r.stderr.strip() else "")).rstrip()
    lignes = sortie.splitlines()
    print("\\n".join(lignes[-150:]))
    try:
        res = json.loads(lignes[-1])
    except (ValueError, IndexError):
        res = {}
    if a.dry_run:
        print("\\n· simulation : rien n'est écrit, la décision reste « adopté ».")
        sys.exit(r.returncode)
    if r.returncode != 0 or res.get("status") != "injected":
        motif = res.get("reason") or res.get("error") or "; ".join(res.get("issues") or []) or "voir ci-dessus"
        sys.exit(f"\\n✗ entité non injectée ({motif}). La décision reste « adopté » : corriger l'hypothèse, "
                 f"annuler la décision, adopter de nouveau.")
    st_i = res.get("instance_stats") or {}
    print(f"\\n✓ entité {res.get('slug')} injectée — instances : {st_i or 'voir ci-dessus'}")
    print(f"✓ statut : {ed.statut(hid)}")


'''
INJ_ANCRE_MAIN = 'def main():\n    ap = argparse.ArgumentParser(description="Injecte une seule hypothèse adoptée.")\n'

INJ_ANCRE_TYPE = '    typ = ed.type_dossier(ed.charger().get(hid))   # U2d : evenement | signal\n'
INJ_NOUV_TYPE = ('    if ed.est_entite(hid):   # U3al\n'
                 '        return _injecter_entite(hid, a)\n') + INJ_ANCRE_TYPE

INJ_REMPL = [
    ("fonction d'injection d'une entité", INJ_ANCRE_MAIN, INJ_FONCTION + INJ_ANCRE_MAIN),
    ("aiguillage dans main()", INJ_ANCRE_TYPE, INJ_NOUV_TYPE),
]

# --------------------------------------------------------------------------
# simuler_et_si.py
# --------------------------------------------------------------------------

SIM_ANCRE = '            entree = ed.adopter(brut, hid, args.portee, args.intensite, apercu=args.apercu)\n'
SIM_NOUV = '''            if str(brut.get("type") or "").strip().lower() == "entite":   # U3al
                entree = ed.adopter(brut, hid, apercu=args.apercu)
                if args.apercu:
                    print(f"Aperçu de la décision d'adopter l'entité {hid} (rien écrit) :\\n")
                    print(_yaml_bloc([entree]))
                    print("\\nRelancer sans --apercu pour adopter.")
                else:
                    print(f"✓ {hid} adoptée (entité) : aucune file à remplir, l'entité est créée à l'injection.\\n"
                          f"  Injection : python3 generator/et_si_injecter.py --id {hid}")
                return
''' + SIM_ANCRE

SIM_REMPL = [("adopter une entité (CLI)", SIM_ANCRE, SIM_NOUV)]

# --------------------------------------------------------------------------
# create_entities_and_instances.py
# --------------------------------------------------------------------------

CRE_ANCRE_DEF = '    user_content = f"""Tu dois déduire l\'archétype intemporel d\'une entité pour le\n'
CRE_NOUV_DEF = ('    desc_u3al = (f"\\n- Description fournie par l\'auteur (à respecter, sans y ajouter de fait) : "\n'
                '                 f"{idea[\'description\']}" if idea.get("description") else "")   # U3al\n') + CRE_ANCRE_DEF
CRE_ANCRE_ETAT = ('- État dans ce scénario : {idea.get(\'etat\') or "non spécifié par l\'utilisateur — '
                  'à déduire librement"}\n')
CRE_NOUV_ETAT = CRE_ANCRE_ETAT.rstrip("\n") + "{desc_u3al}\n"

CRE_REMPL = [
    ("variable description", CRE_ANCRE_DEF, CRE_NOUV_DEF),
    ("description dans le prompt", CRE_ANCRE_ETAT, CRE_NOUV_ETAT),
]

# nom, prérequis (marqueur attendu ou None), remplacements
CIBLES = [
    ("et_si_dossiers.py", None, DOS_REMPL),
    ("et_si_statut.py", None, STA_REMPL),
    ("et_si_injecter.py", None, INJ_REMPL),
    ("simuler_et_si.py", "U3aj", SIM_REMPL),
    ("create_entities_and_instances.py", "U3ah", CRE_REMPL),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="écrit (sinon aperçu)")
    ap.add_argument("--dossier", default=str(G), help="dossier des scripts (défaut : generator)")
    a = ap.parse_args()
    base = Path(a.dossier)
    prepares = []
    for nom, prereq, remp in CIBLES:
        chemin = base / nom
        if not chemin.exists():
            print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
            return 2
        texte = chemin.read_text(encoding="utf-8")
        if prereq and prereq not in texte:
            print(f"✗ {nom} : prérequis {prereq} absent (appliquer d'abord son patch).")
            return 1
        if MARQUEUR in texte:
            print(f"✗ {MARQUEUR} déjà appliqué dans {nom} — refus d'un second passage.")
            return 1
        nouveau = texte
        for libelle, ancre, rempl in remp:
            n = nouveau.count(ancre)
            if n != 1:
                print(f"✗ {nom} : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
                return 1
            nouveau = nouveau.replace(ancre, rempl, 1)
            print(f"  ✓ {nom} : {libelle}")
        prepares.append((chemin, texte, nouveau))
    if not a.apply:
        for chemin, avant, apres in prepares:
            print(f"  {chemin.name} : {len(avant.splitlines())} -> {len(apres.splitlines())} lignes")
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    baks = []
    for chemin, _, apres in prepares:
        bak = chemin.with_name(chemin.name + ".bak_u3al")
        shutil.copy2(chemin, bak)
        baks.append((chemin, bak))
        chemin.write_text(apres, encoding="utf-8")
    try:
        for chemin, _ in baks:
            py_compile.compile(str(chemin), doraise=True)
    except py_compile.PyCompileError as e:
        for chemin, bak in baks:
            shutil.copy2(bak, chemin)
        print(f"✗ py_compile a échoué, tous les fichiers restaurés : {e}")
        return 1
    for chemin, bak in baks:
        print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
