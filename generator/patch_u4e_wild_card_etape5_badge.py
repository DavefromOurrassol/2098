#!/usr/bin/env python3
"""
patch_u4e_wild_card_etape5_badge.py — Ourrassol 2098 (21 nov 2026)

U4e, deux volets :

1. Étape ⑤ : pour une wild card, le brouillon de règle de lore propose D'OFFICE une
   règle « fait établi » (generator/et_si_main.py, brouillons_regles) :
     - id : <id>_fait_etabli ; gravite : a_relire ;
     - termes : noms propres du nom de l'hypothèse (« Zéro-R »), sinon le nom entier ;
     - message : la wild card est un fait du monde depuis son année ; le nier ou la
       présenter comme hypothétique après cette année est faux ; avant, personne ne la
       connaît.
   Elle vient avant les règles d'entités disparues. Rien n'est écrit sans « Ajouter
   la règle » (le brouillon reste modifiable). Une fois ajoutée, elle entre aussi dans
   le contrôle des règles de lore des wild cards suivantes (U4c).

2. Badge ⚡ :
     - gui/app.py : liste des hypothèses (« ⚡ Nom (2058) ») ; la route /api/et_si/fiche
       transmet `wild_card` ;
     - gui/static/app.js : en-tête de la fiche de l'hypothèse (« · ⚡ wild card · »), lu
       sur la fiche ou sur le libellé de la liste.

Usage (depuis la racine du vault) :
    python3 generator/patch_u4e_wild_card_etape5_badge.py           # dry-run
    python3 generator/patch_u4e_wild_card_etape5_badge.py --apply   # écrit (.bak_u4e)
Après --apply : relancer Flask entièrement (app.py), puis Cmd-Maj-R.
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

TAG = "U4e"

# --- 1. et_si_main.py ---------------------------------------------------------
MAIN = Path("generator/et_si_main.py")

MAIN_AVANT = '''def brouillons_regles(data):
    """Brouillon par scénario : une règle par entité disparue (opération appliquée),
    contraintes de l'hypothèse en commentaires (même contenu que la check-list)."""
    ops, _ = ap.construire_plan(data)
    annee = int(data["annee"]) if data.get("annee") is not None else None
    out = {}
    for sc in data["scenarios"]:
        regles = []
'''

MAIN_APRES = '''# U4e (21 nov 2026) : une wild card devient un fait établi -> règle proposée d'office.
MOTS_NON_PROPRES_U4E = {"Le", "La", "Les", "Un", "Une", "Des", "Du", "De", "Dépôt", "Percée", "Découverte",
                        "Effondrement", "Pandémie", "Signe", "Molécule", "Thérapie", "Gisement"}


def wild_card_de(data):
    """U4e : bloc de l'hypothèse (et_si/hypotheses.yaml) si c'est une wild card, sinon None."""
    try:
        import simuler_et_si as se
        h = next((x for x in se.charger_hypotheses() if x.get("id") == data.get("id")), None)
        return h if h and se.est_wild_card(h) else None
    except (Exception, SystemExit):  # noqa: BLE001 -- sans hypothèse lisible : pas de règle d'office
        return None


def termes_wild_card(h):
    """U4e : noms propres du nom de la wild card (« Le Zéro-R » -> Zéro-R) ; à défaut, le nom entier."""
    nom = " ".join(str(h.get("nom") or "").split())
    termes = []
    for n, mot in enumerate(nom.split(" ")):
        mot = mot.strip("«»\\"'(),.;:")
        if len(mot) < 4 or mot in MOTS_NON_PROPRES_U4E:
            continue
        propre = mot[0].isupper() and n > 0
        marque = any(c.isdigit() for c in mot) or ("-" in mot and any(c.isupper() for c in mot[1:]))
        if (propre or marque) and mot not in termes:
            termes.append(mot)
    return termes or ([nom] if nom else [])


def regle_wild_card(data, h, annee):
    """U4e : règle « fait établi » d'une wild card (gravité a_relire, modifiable avant ajout)."""
    nom = " ".join(str(h.get("nom") or data.get("id")).split())
    desc = " ".join(str(h.get("description") or "").split())
    if len(desc) > 180:
        desc = desc[:180].rsplit(" ", 1)[0] + "…"
    return {"id": f"{data['id']}_fait_etabli", "gravite": "a_relire", "termes": termes_wild_card(h),
            "message": (f"Wild card de {annee} : {nom} est un fait établi du monde depuis {annee}"
                        + (f" ({desc})" if desc else "") + f". Le nier ou le présenter comme hypothétique "
                        f"après {annee} est faux ; avant {annee}, personne ne peut le connaître.")}


def brouillons_regles(data):
    """Brouillon par scénario : une règle par entité disparue (opération appliquée),
    contraintes de l'hypothèse en commentaires (même contenu que la check-list).
    U4e : une wild card ouvre le brouillon par sa règle « fait établi »."""
    ops, _ = ap.construire_plan(data)
    annee = int(data["annee"]) if data.get("annee") is not None else None
    wc = wild_card_de(data)   # U4e
    out = {}
    for sc in data["scenarios"]:
        regles = [regle_wild_card(data, wc, annee)] if wc else []   # U4e
'''

MAIN_AVANT2 = '''        texte = yaml.safe_dump(regles, allow_unicode=True, sort_keys=False, width=1000) if regles else ""
        texte += "".join(f"# contrainte à transformer si besoin : {c}\\n" for c in data.get("contraintes") or [])
'''

MAIN_APRES2 = '''        texte = ("# ⚡ wild card : règle « fait établi » proposée d'office (relire les termes) ; U4e\\n"
                 if wc else "")
        texte += yaml.safe_dump(regles, allow_unicode=True, sort_keys=False, width=1000) if regles else ""
        texte += "".join(f"# contrainte à transformer si besoin : {c}\\n" for c in data.get("contraintes") or [])
'''

# --- 2. gui/app.py ------------------------------------------------------------
APP = Path("gui/app.py")

APP_AVANT = '''                labels[h["id"]] = (f"{h.get('nom')} ({_quand})"
'''
APP_APRES = '''                labels[h["id"]] = (("⚡ " if h.get("wild_card") else "")   # U4e : badge wild card
                                   + f"{h.get('nom')} ({_quand})"
'''

APP_AVANT2 = '''            for k in ("nom", "type", "date", "mode", "categorie", "scenario_ref", "scenarios",
                      "role", "etat", "description"):
'''
APP_APRES2 = '''            for k in ("nom", "type", "date", "mode", "categorie", "scenario_ref", "scenarios",
                      "role", "etat", "description", "wild_card"):   # U4e : wild_card
'''

# --- 3. gui/static/app.js -----------------------------------------------------
JS = Path("gui/static/app.js")

JS_AVANT = '''      const entete = [fi.nom, fi.type === 'entite' ? 'entité' : (fi.type || 'événement'),
'''
JS_APRES = '''      const entete = [fi.nom, fi.type === 'entite' ? 'entité' : (fi.type || 'événement'),
                      estWildU4e(fi) ? '⚡ wild card' : '',   // U4e
'''

JS_AVANT2 = '''    ficheMeta.textContent = [fi.nom, fi.type === 'entite' ? 'entité' : (fi.type || 'événement'),
'''
JS_APRES2 = '''    ficheMeta.textContent = [fi.nom, fi.type === 'entite' ? 'entité' : (fi.type || 'événement'),
                    estWildU4e(fi) ? '⚡ wild card' : '',   // U4e
'''

JS_AVANT3 = '''  // U3av : la fiche s'affiche juste sous la liste « Hypothèse »
  const placerFiche = () => {
'''
JS_APRES3 = '''  // U4e : wild card d'après la fiche, ou d'après le libellé « ⚡ … » de la liste
  const estWildU4e = (fi) => {
    if (fi && (fi.wild_card === true || String(fi.wild_card).toLowerCase() === 'true')) return true;
    const sel = listeHyp();
    const opt = sel && sel.selectedIndex >= 0 ? sel.options[sel.selectedIndex] : null;
    return !!(opt && opt.textContent.trim().startsWith('⚡'));
  };
  // U3av : la fiche s'affiche juste sous la liste « Hypothèse »
  const placerFiche = () => {
'''

TRAVAUX = [
    (MAIN, [("brouillons_regles (début)", MAIN_AVANT, MAIN_APRES),
            ("brouillons_regles (texte)", MAIN_AVANT2, MAIN_APRES2)]),
    (APP, [("libellé de la liste", APP_AVANT, APP_APRES),
           ("route /api/et_si/fiche", APP_AVANT2, APP_APRES2)]),
    (JS, [("en-tête de la fiche (statut)", JS_AVANT, JS_APRES),
          ("en-tête de la fiche (remplirFiche)", JS_AVANT2, JS_APRES2),
          ("fonction estWildU4e", JS_AVANT3, JS_APRES3)]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    nouveaux = {}
    for chemin, remplacements in TRAVAUX:
        if not chemin.is_file():
            sys.exit(f"✗ {chemin} introuvable : lancer depuis la racine du vault")
        texte = chemin.read_text(encoding="utf-8")
        if "U4e" in texte:
            sys.exit(f"✗ {chemin} contient déjà « U4e » : patch déjà appliqué ? Rien n'est écrit")
        neuf = texte
        for nom, avant, apres in remplacements:
            n = neuf.count(avant)
            if n != 1:
                sys.exit(f"✗ {chemin} : ancre « {nom} » trouvée {n} fois (1 attendue) : rien n'est écrit")
            neuf = neuf.replace(avant, apres)
        nouveaux[chemin] = (texte, neuf)
        print(f"[{TAG}] {chemin} : {len(remplacements)} modification(s), "
              f"{len(texte.splitlines())} -> {len(neuf.splitlines())} lignes")
    if not args.apply:
        print(f"[{TAG}] dry-run : relancer avec --apply pour écrire")
        return
    for chemin, (ancien, neuf) in nouveaux.items():
        shutil.copy(chemin, chemin.with_name(chemin.name + ".bak_u4e"))
        chemin.write_text(neuf, encoding="utf-8")
    for chemin in (MAIN, APP):
        try:
            py_compile.compile(str(chemin), doraise=True)
        except py_compile.PyCompileError as e:
            for c, (ancien, _) in nouveaux.items():
                c.write_text(ancien, encoding="utf-8")
            sys.exit(f"✗ syntaxe invalide dans {chemin}, les 3 fichiers sont restaurés : {e}")
    print(f"✓ [{TAG}] appliqué (sauvegardes .bak_u4e). Relancer Flask entièrement, puis Cmd-Maj-R.")


if __name__ == "__main__":
    main()
