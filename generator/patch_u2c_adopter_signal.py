#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unification « et si ? » — étape 2c : « Adopter » sait envoyer un SIGNAL.

  - simuler_et_si.py : l'entrée commune d'un signal (type: signal) est au format de
    signaux_custom/queue.yaml (variable_hint, impacts_imposes, date_imposee, ...),
    sans portée ni intensité ; messages d'adoption adaptés.
  - et_si_dossiers.py : le dossier retient le type ; Adopter écrit dans
    signaux_custom/queue.yaml ; le statut se lit dans signaux_custom/ (processed,
    needs_review, queue) ; Annuler la décision retire l'entrée de la bonne queue.
Rien ne change pour un événement.

    python3 generator/patch_u2c_adopter_signal.py            # dry-run
    python3 generator/patch_u2c_adopter_signal.py --apply    # applique (.bak_u2c)
"""
import py_compile
import shutil
import sys
from pathlib import Path

G = Path("generator")
F_DOS = G / "et_si_dossiers.py"
F_SIM = G / "simuler_et_si.py"

# ------------------------------------------------------------------ et_si_dossiers.py

DOS_CONST = '''EVENT_INSTANCES = VAULT_ROOT / "event_instances"
SIGNAUX_CUSTOM = VAULT_ROOT / "signaux_custom"          # U2c
QUEUE_SIGNAUX = SIGNAUX_CUSTOM / "queue.yaml"
NEEDS_REVIEW_SIGNAUX = SIGNAUX_CUSTOM / "needs_review.yaml"
PROCESSED_SIGNAUX = SIGNAUX_CUSTOM / "processed.yaml"
'''

DOS_HELPERS = '''def type_dossier(dossier):
    """U2c : « evenement » (défaut) ou « signal », retenu à la simulation puis à la décision."""
    d = dossier or {}
    return ((d.get("decision") or {}).get("type") or (d.get("simulation") or {}).get("type")
            or "evenement")


def _chemin_queue(typ):
    return QUEUE_SIGNAUX if typ == "signal" else QUEUE_PATH


def _etat_signal(hid):
    """(injecté, partiellement injecté, présent dans needs_review) d'après signaux_custom/."""
    traites = [x for x in _liste_yaml(PROCESSED_SIGNAUX, "processed") if (x.get("idea") or {}).get("id") == hid]
    revoir = [x for x in _liste_yaml(NEEDS_REVIEW_SIGNAUX, "needs_review") if (x.get("idea") or {}).get("id") == hid]
    partiel = any(r.get("status") == "injected" for x in revoir for r in x.get("results") or [])
    return bool(traites), partiel, bool(revoir)


def _slug_signal(hid):
    for chemin, cle in ((PROCESSED_SIGNAUX, "processed"), (NEEDS_REVIEW_SIGNAUX, "needs_review")):
        for x in _liste_yaml(chemin, cle):
            slug = (x.get("selection") or {}).get("signal_slug")
            if (x.get("idea") or {}).get("id") == hid and slug:
                return slug
    return None


def slug_evenement(hid):'''

DOS_STATUT = '''    if typ_d == "signal":   # U2c
        injecte, partiel, a_revoir = _etat_signal(hid)
        if injecte:
            return "injecté"
        if any(x.get("id") == hid for x in _liste_yaml(QUEUE_SIGNAUX, "queue")):
            return "adopté, en attente d'injection"
        if partiel:
            return "injecté partiellement — à revoir"
        return "à revoir" if a_revoir else "adopté, absent de la queue"
    scen = (dec.get("entree") or {}).get("scenarios") or []
    slug = slug_evenement(hid)
    presents'''

DOS_SEGMENT_QUEUE = '''def _sauver_queue(liste, typ="evenement"):
    """Réécrit la queue du type (sauvegarde .bak_et_si), avec l'en-tête modèle du script
    d'injection correspondant s'il est importable, sinon l'en-tête du fichier."""
    chemin = _chemin_queue(typ)
    if chemin.exists():
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_et_si"))
    try:
        mod = __import__("inject_custom_signals" if typ == "signal" else "inject_custom_events")
        if Path(mod.QUEUE_PATH).resolve() != chemin.resolve():
            raise ImportError("chemin de queue différent")
        mod.save_queue_with_template(liste)
    except Exception:
        entete = []
        try:
            for ligne in chemin.read_text(encoding="utf-8").splitlines():
                if ligne.strip() and not ligne.lstrip().startswith("#"):
                    break
                entete.append(ligne)
        except OSError:
            pass
        chemin.parent.mkdir(parents=True, exist_ok=True)
        corps = yaml.dump({"queue": liste}, allow_unicode=True, sort_keys=False, default_flow_style=False)
        chemin.write_text("\\n".join(entete) + ("\\n" if entete else "") + corps, encoding="utf-8")


def _ecrire_queue(entree, typ="evenement"):
    """Ajoute l'entrée à la queue du type."""
    chemin = _chemin_queue(typ)
    _sauver_queue(_liste_yaml(chemin, "queue") + [entree], typ)
    relue = [x for x in _liste_yaml(chemin, "queue") if x.get("id") == entree.get("id")]
    if len(relue) != 1:
        raise DossierErreur("relecture de queue.yaml impossible après écriture : vérifier le fichier "
                            "(sauvegarde .bak_et_si).")


def _retirer_de_queue(hid, typ="evenement"):
    """Retire l'entrée écrite par « Adopter » (même id ET source et_si_<id>) ;
    une entrée de même id écrite à la main n'est pas touchée. True si retirée."""
    chemin = _chemin_queue(typ)
    existantes = _liste_yaml(chemin, "queue")
    gardees = [x for x in existantes if not (x.get("id") == hid and x.get("source") == f"et_si_{hid}")]
    if len(gardees) == len(existantes):
        return False
    _sauver_queue(gardees, typ)
    if any(x.get("id") == hid and x.get("source") == f"et_si_{hid}" for x in _liste_yaml(chemin, "queue")):
        raise DossierErreur("retrait de queue.yaml non relu : vérifier le fichier (sauvegarde .bak_et_si).")
    return True


def adopter(brut, hid, portee=None, intensite=None, apercu=False):
    entree, sim = preparer_adoption(brut, hid, portee, intensite)
    if apercu:
        return entree
    typ = type_dossier(charger().get(hid))
    _ecrire_queue(entree, typ)
    data = charger()
    data.setdefault(hid, {})["decision"] = {
        "statut": "adopté", "date": _maintenant(), "motif": None, "type": typ,
        "empreinte": sim.get("empreinte"), "simulation_du": sim.get("date"), "entree": entree}
    sauver(data)
    return entree


'''

DOS_ANNULER = '''def annuler_decision(hid):
    """Retire la décision (le dossier revient à « simulé »). Une entrée adoptée encore
    dans la queue (pas encore injectée) en est retirée (sauvegarde .bak_et_si) ; le vault
    n'est jamais touché. Retourne (ancien statut, messages déjà préfixés ✓ ou ⚠)."""
    data = charger()
    d = data.get(hid) or {}
    if not d.get("decision"):
        raise DossierErreur(f"{hid} n'a aucune décision à annuler.")
    st = statut(hid, d)
    typ = type_dossier(d)
    nom_queue = "signaux_custom/queue.yaml" if typ == "signal" else "evenements_custom/queue.yaml"
    messages = []
    if _retirer_de_queue(hid, typ):
        messages.append(f"✓ entrée {hid} retirée de {nom_queue} (sauvegarde queue.yaml.bak_et_si)")
    d.pop("decision")
    data[hid] = d
    sauver(data)
    if any(x.get("id") == hid for x in _liste_yaml(_chemin_queue(typ), "queue")):
        messages.append(f"⚠ une entrée {hid} écrite à la main reste dans {nom_queue}")
    if st.startswith("injecté"):
        if typ == "signal":
            messages.append(f"⚠ le signal reste dans le vault : python3 generator/undo_custom.py "
                            f"--slug {_slug_signal(hid) or '<slug du signal>'} --type signal (aperçu, puis --execute)")
        else:
            messages.append(f"⚠ l'événement reste dans le vault : python3 generator/undo_custom.py "
                            f"--slug {slug_evenement(hid)} --type evenement --generalisation yes (aperçu, puis --execute)")
    return st, messages
'''

PREP_ANCRE = ('    if any(x.get("id") == hid for x in _liste_yaml(QUEUE_PATH, "queue")):\n'
              '        raise DossierErreur(f"une entrée {hid} est déjà dans evenements_custom/queue.yaml.")\n')
PREP_NOUVEAU = ('    if type_dossier(d) == "signal":   # U2c : ni portée ni intensité pour un signal\n'
                '        if any(x.get("id") == hid for x in _liste_yaml(QUEUE_SIGNAUX, "queue")):\n'
                '            raise DossierErreur(f"une entrée {hid} est déjà dans signaux_custom/queue.yaml.")\n'
                '        return entree, sim\n' + PREP_ANCRE)

SIM_FONCTION = '''def _rendre_injection_signal(hyp, out=None):
    """U2c : entrée de signaux_custom/queue.yaml pour une hypothèse `type: signal`."""
    def _nombre(x):
        return int(x) if float(x) == int(x) else x
    entree = {"id": hyp["id"], "description": hyp["description"] or hyp["nom"],
              "source": f"et_si_{hyp['id']}", "persistance": hyp["persistance"],
              "variable_hint": [i["variable"] for i in hyp["impacts"]],
              "variable_hint_count": len(hyp["impacts"]),
              "date_imposee": _nombre(hyp["date"]),
              "impacts_imposes": {
                  sc: [{"variable": i["variable"], "delta_level": _nombre(i["force"]),
                        "duree": _nombre(i["duree"]), "polarite": i["polarites"][sc]}
                       for i in hyp["impacts"] if sc in i["polarites"]]
                  for sc in SCENARIOS},
              "via_matrice_impose": bool(hyp["via_matrice"])}
    if out is not None:
        out["entree"] = entree
    return ["## Liste d'application — injection du signal", "",
            "Entrée pour `signaux_custom/queue.yaml` (une seule pour les 6 scénarios). Forces, sens par "
            "scénario, durées, date et propagation de cette simulation sont imposés (`impacts_imposes`, "
            "`date_imposee`, `via_matrice_impose`) : l'IA de l'injection rédige seulement le récit "
            "(`evolution`, `evenement_cle`). Un signal n'a ni carte, ni portée, ni intensité.", "",
            "```yaml", _yaml_bloc([entree]), "```", ""]


def _rendre_injection_commune(hyp, application, out=None):'''

SIM_ANCRE_BRANCHE = ('    if not hyp.get("impacts"):\n        return []\n'
                     '    scen = [sc for sc in hyp["scenarios"] if sc in application]\n')
SIM_BRANCHE = ('    if not hyp.get("impacts"):\n        return []\n'
               '    if hyp.get("type") == "signal":   # U2c\n'
               '        return _rendre_injection_signal(hyp, out)\n'
               '    scen = [sc for sc in hyp["scenarios"] if sc in application]\n')

SIM_MSG_ANCRE = '''                print("\\nRelancer sans --apercu pour l'écrire dans evenements_custom/queue.yaml.")
            else:
                print(f"✓ {hid} adoptée : entrée ajoutée à evenements_custom/queue.yaml "
                      f"(sauvegarde queue.yaml.bak_et_si).\\n"
                      f"  Injection à lancer à part : python3 generator/inject_custom_events.py --mode custom")
'''
SIM_MSG_NOUVEAU = '''                if ed.type_dossier(ed.charger().get(hid)) == "signal":
                    print("\\nRelancer sans --apercu pour l'écrire dans signaux_custom/queue.yaml.")
                else:
                    print("\\nRelancer sans --apercu pour l'écrire dans evenements_custom/queue.yaml.")
            elif ed.type_dossier(ed.charger().get(hid)) == "signal":
                print(f"✓ {hid} adopté (signal) : entrée ajoutée à signaux_custom/queue.yaml "
                      f"(sauvegarde queue.yaml.bak_et_si).\\n"
                      f"  Injection à lancer à part : python3 generator/inject_custom_signals.py")
            else:
                print(f"✓ {hid} adoptée : entrée ajoutée à evenements_custom/queue.yaml "
                      f"(sauvegarde queue.yaml.bak_et_si).\\n"
                      f"  Injection à lancer à part : python3 generator/inject_custom_events.py --mode custom")
'''

STATUT_ANCRE = ('    scen = (dec.get("entree") or {}).get("scenarios") or []\n'
                '    slug = slug_evenement(hid)\n'
                '    presents')


def edits_dos(src):
    """Retourne le nouveau texte de et_si_dossiers.py ou lève ValueError."""
    def un(ancre):
        if src.count(ancre) != 1:
            raise ValueError("ancre introuvable ou multiple dans et_si_dossiers.py : " + ancre[:60].strip())
    new = src
    simples = [
        ('EVENT_INSTANCES = VAULT_ROOT / "event_instances"\n', DOS_CONST),
        ('def slug_evenement(hid):', DOS_HELPERS),
        ('"passe": bool(passe), "rapport": rapport, "entree": entree,\n',
         '"passe": bool(passe), "rapport": rapport, "entree": entree,\n'
         '        "type": hyp.get("type", "evenement"),\n'),
        ('    if dec.get("statut") != "adopté":\n        return "simulé" if dossier.get("simulation") else "non simulé"\n',
         '    if dec.get("statut") != "adopté":\n        return "simulé" if dossier.get("simulation") else "non simulé"\n'
         '    typ_d = type_dossier(dossier)\n'),
        (STATUT_ANCRE, DOS_STATUT),
        (PREP_ANCRE, PREP_NOUVEAU),
    ]
    for ancre, rempl in simples:
        if new.count(ancre) != 1:
            raise ValueError("ancre introuvable ou multiple dans et_si_dossiers.py : " + ancre[:60].strip())
        new = new.replace(ancre, rempl)
    # segments entiers
    a, b = new.find("def _sauver_queue(liste):"), new.find("def rejeter(hid, motif=None):")
    if a < 0 or b < a or new.count("def _sauver_queue(liste):") != 1:
        raise ValueError("segment _sauver_queue…rejeter introuvable")
    new = new[:a] + DOS_SEGMENT_QUEUE + new[b:]
    c = new.find("def annuler_decision(hid):")
    if c < 0 or new.count("def annuler_decision(hid):") != 1:
        raise ValueError("segment annuler_decision introuvable")
    new = new[:c] + DOS_ANNULER
    return new


def edits_sim(src):
    new = src
    for ancre, rempl in [
        ("def _rendre_injection_commune(hyp, application, out=None):", SIM_FONCTION),
        (SIM_ANCRE_BRANCHE, SIM_BRANCHE),
        (SIM_MSG_ANCRE, SIM_MSG_NOUVEAU),
    ]:
        if new.count(ancre) != 1:
            raise ValueError("ancre introuvable ou multiple dans simuler_et_si.py : " + ancre[:60].strip())
        new = new.replace(ancre, rempl)
    return new


def main():
    for f in (F_DOS, F_SIM):
        if not f.is_file():
            print("ERREUR : {} introuvable (lancer depuis la racine du vault).".format(f))
            return 1
    s_dos, s_sim = F_DOS.read_text(encoding="utf-8"), F_SIM.read_text(encoding="utf-8")
    if "def type_dossier" in s_dos:
        print("Déjà appliqué : rien à faire.")
        return 0
    if "DELTA_MAX_SIGNAL" not in s_sim:
        print("ERREUR : appliquer d'abord patch_u2b_simuler_signal.py.")
        return 1
    try:
        n_dos, n_sim = edits_dos(s_dos), edits_sim(s_sim)
    except ValueError as e:
        print("ERREUR : {}. Rien modifié.".format(e))
        return 1
    print("Modifications prévues dans {} et {}.".format(F_DOS, F_SIM))
    if "--apply" not in sys.argv:
        print("Dry-run : rien écrit. Relancer avec --apply pour appliquer.")
        return 0
    for f, txt in ((F_DOS, n_dos), (F_SIM, n_sim)):
        shutil.copy2(f, str(f) + ".bak_u2c")
        f.write_text(txt, encoding="utf-8")
    try:
        for f in (F_DOS, F_SIM):
            py_compile.compile(str(f), doraise=True)
    except py_compile.PyCompileError as e:
        for f in (F_DOS, F_SIM):
            shutil.copy2(str(f) + ".bak_u2c", f)
        print("ERREUR de syntaxe, fichiers restaurés :\n{}".format(e))
        return 1
    print("Appliqué (sauvegardes .bak_u2c). Syntaxe vérifiée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
