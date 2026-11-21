#!/usr/bin/env python3
"""
patch_u4h_modifier_hypothese.py — Ourrassol 2098 (21 nov 2026)

U4h : MODIFIER une hypothèse existante depuis le panneau ✨ « Nouvelle hypothèse ».

  - generator/hypothese_depuis_texte.py :
      --extraire  (entrée standard = id) : bloc de l'hypothèse tel qu'écrit dans
                  hypotheses.yaml (commentaires internes compris) et son statut ;
      --remplacer (entrée standard = bloc) : contrôles d'« Ajouter » (doublons de nom et de
                  description, wild cards), puis réécriture du bloc À SA PLACE (ordre et
                  commentaires conservés). Refusé si l'hypothèse est adoptée ou injectée
                  (« Annuler la décision » d'abord) ou si l'id du bloc n'existe pas
                  (l'id ne change pas). Sauvegarde .bak_remplacer, relecture complète,
                  retour arrière si la relecture échoue. Une hypothèse déjà simulée devra
                  être resimulée avant d'être adoptée (déjà imposé par et_si_dossiers.py).
  - gui/app.py : actions « extraire » et « remplacer » de la route /api/et_si/<action>.
  - gui/static/app.js : ligne « ✏️ Modifier une hypothèse existante » (liste + Charger) et
                  bouton « Remplacer dans hypotheses.yaml » (confirmation en deux clics ;
                  refus si l'id du bloc n'est plus celui de l'hypothèse chargée).

Usage (depuis la racine du vault) :
    python3 generator/patch_u4h_modifier_hypothese.py           # dry-run
    python3 generator/patch_u4h_modifier_hypothese.py --apply   # écrit (.bak_u4h)
Après --apply : relancer Flask entièrement, puis Cmd-Maj-R.
"""
import argparse
import py_compile
import shutil
import sys
from pathlib import Path

TAG = "U4h"

# --- 1. hypothese_depuis_texte.py ---------------------------------------------
HDT = Path("generator/hypothese_depuis_texte.py")

HDT_AVANT1 = '''# ---------------------------------------------------------------------------

def main():
'''
HDT_APRES1 = '''# ---------------------------------------------------------------------------
# U4h (21 nov 2026) : modifier une hypothèse existante (extraire, remplacer)
# ---------------------------------------------------------------------------

STATUTS_MODIFIABLES = ("non simulé", "simulé", "rejeté", "vérifié")


def _statut_hyp(hid):
    try:
        import et_si_dossiers as ed
        return str(ed.statut(hid))
    except Exception as e:  # noqa: BLE001
        return f"inconnu ({type(e).__name__})"


def _bornes_bloc(lignes, hid):
    """(début, fin) du bloc `hid` : de « - id: hid » à la ligne avant l'hypothèse suivante,
    sans les lignes vides ni les commentaires de niveau 2 qui précèdent celle-ci (ils lui
    appartiennent). None si absent ou présent plusieurs fois."""
    debuts = [i for i, l in enumerate(lignes)
              if re.match(r"^\\s*- id:\\s*['\\"]?" + re.escape(hid) + r"['\\"]?\\s*(#.*)?$", l)]
    if len(debuts) != 1:
        return None
    d = debuts[0]
    retrait = len(lignes[d]) - len(lignes[d].lstrip(" "))
    f = next((i for i in range(d + 1, len(lignes))
              if re.match(r"^\\s*- id:", lignes[i]) and len(lignes[i]) - len(lignes[i].lstrip(" ")) == retrait),
             len(lignes))
    while f > d + 1 and (not lignes[f - 1].strip()
                         or (lignes[f - 1].lstrip().startswith("#")
                             and len(lignes[f - 1]) - len(lignes[f - 1].lstrip(" ")) <= retrait)):
        f -= 1
    return d, f


def extraire_bloc(hid):
    hid = str(hid or "").strip()
    if not re.fullmatch(r"[a-z0-9_]+", hid):
        return {"ok": False, "erreurs": [f"id {hid!r} invalide"], "avertissements": []}
    lignes = se.HYPOTHESES_PATH.read_text(encoding="utf-8").splitlines()
    b = _bornes_bloc(lignes, hid)
    if b is None:
        return {"ok": False, "erreurs": [f"{hid} introuvable (ou en double) dans {se.HYPOTHESES_PATH.name}"],
                "avertissements": []}
    st = _statut_hyp(hid)
    res = {"ok": True, "id": hid, "statut": st, "bloc": "\\n".join(lignes[b[0]:b[1]]) + "\\n",
           "erreurs": [], "avertissements": []}
    if st not in STATUTS_MODIFIABLES:
        res["ok"] = False
        res["erreurs"].append(f"{hid} est « {st} » : non modifiable (« Annuler la décision » d'abord, "
                              f"et seulement tant qu'elle n'est pas injectée)")
    elif st == "simulé":
        res["avertissements"].append("déjà simulée : après modification, la resimuler avant de décider")
    return res


def remplacer_bloc(texte):
    h, erreurs = lire_bloc(texte)
    if h is None:
        return {"ok": False, "erreurs": erreurs, "avertissements": [], "id": None}
    hid = str(h.get("id") or "")
    if hid not in ids_existants():
        return {"ok": False, "id": hid, "avertissements": [],
                "erreurs": [f"id {hid!r} absent de {se.HYPOTHESES_PATH.name} : l'id d'une hypothèse ne change "
                            "pas (pour un nouvel id, « Ajouter »)"]}
    st = _statut_hyp(hid)
    if st not in STATUTS_MODIFIABLES:
        return {"ok": False, "id": hid, "avertissements": [],
                "erreurs": [f"{hid} est « {st} » : non modifiable (« Annuler la décision » d'abord, "
                            f"et seulement tant qu'elle n'est pas injectée)"]}
    res = verifier_bloc(texte, pour_ajout=True)
    res["erreurs"] = [e for e in res["erreurs"] if not e.startswith(f"id {hid!r} déjà présent")]
    res["ok"] = not res["erreurs"]
    if not res["ok"]:
        return res
    chemin = se.HYPOTHESES_PATH
    original = chemin.read_text(encoding="utf-8")
    lignes = original.splitlines()
    b = _bornes_bloc(lignes, hid)
    if b is None:
        res.update(ok=False, erreurs=[f"bloc de {hid} introuvable (ou en double) dans le fichier : à la main"])
        return res
    d, f = b
    neuf = normaliser_texte_bloc(texte)
    retrait = " " * (len(lignes[d]) - len(lignes[d].lstrip(" ")))
    neuf_l = [(retrait + l) if l.strip() else "" for l in neuf.splitlines()]
    if neuf_l == lignes[d:f]:
        res["message"] = f"{hid} : aucun changement, rien n'est écrit"
        return res
    nouveau = "\\n".join(lignes[:d] + neuf_l + lignes[f:]) + "\\n"
    ids_avant = [x.get("id") for x in (yaml.safe_load(original) or {}).get("hypotheses") or [] if isinstance(x, dict)]
    shutil.copy(chemin, chemin.with_name(chemin.name + ".bak_remplacer"))
    chemin.write_text(nouveau, encoding="utf-8")
    try:
        data = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
        hyps = [x for x in data.get("hypotheses") or [] if isinstance(x, dict)]
        if [x.get("id") for x in hyps] != ids_avant:
            raise ValueError("ordre ou liste des hypothèses changé après réécriture")
        relu = next(x for x in hyps if x.get("id") == hid)
        if relu != h:
            raise ValueError("le bloc relu diffère du bloc envoyé")
    except Exception as e:  # noqa: BLE001 -- retour arrière
        chemin.write_text(original, encoding="utf-8")
        res.update(ok=False, erreurs=[f"remplacement annulé, fichier restauré : {e}"])
        return res
    res["message"] = (f"{hid} remplacée dans {chemin.name} (sauvegarde {chemin.name}.bak_remplacer)"
                      + (" ; sa dernière simulation est périmée : la relancer avant de décider"
                         if st == "simulé" else ""))
    return res


# ---------------------------------------------------------------------------

def main():
'''

HDT_AVANT2 = '''    action.add_argument("--ajouter", action="store_true", help="contrôle puis ajout à hypotheses.yaml")
'''
HDT_APRES2 = '''    action.add_argument("--ajouter", action="store_true", help="contrôle puis ajout à hypotheses.yaml")
    action.add_argument("--extraire", action="store_true",   # U4h
                        help="id (entrée standard) -> bloc de l'hypothèse tel qu'écrit, et son statut")
    action.add_argument("--remplacer", action="store_true",   # U4h
                        help="contrôle puis réécriture du bloc d'une hypothèse existante, à sa place")
'''

HDT_AVANT3 = '''        elif args.verifier:
            res = verifier_bloc(texte)
        else:
            res = ajouter_bloc(texte)
'''
HDT_APRES3 = '''        elif args.verifier:
            res = verifier_bloc(texte)
        elif args.extraire:   # U4h
            res = extraire_bloc(texte.strip())
        elif args.remplacer:   # U4h
            res = remplacer_bloc(texte)
        else:
            res = ajouter_bloc(texte)
'''

# --- 2. gui/app.py ------------------------------------------------------------
APP = Path("gui/app.py")
APP_AVANT = '''TIMEOUT_ET_SI = {"proposer": 180, "verifier": 60, "ajouter": 60}
'''
APP_APRES = '''TIMEOUT_ET_SI = {"proposer": 180, "verifier": 60, "ajouter": 60,
                 "extraire": 60, "remplacer": 60}   # U4h : modifier une hypothèse existante
'''

# --- 3. gui/static/app.js -----------------------------------------------------
JS = Path("gui/static/app.js")

JS_AVANT1 = '''  corps.appendChild(mk('div', 'option-label', 'Bloc de l\\'hypothèse (modifiable)'));
'''
JS_APRES1 = '''  // U4h : modifier une hypothèse existante (Charger -> bloc ; « Remplacer » le réécrit à sa place)
  const ligneModif = mk('div');
  ligneModif.style.cssText = 'display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:4px 0 8px;';
  ligneModif.appendChild(mk('span', 'option-label', '✏️ Modifier une hypothèse existante :'));
  const selModif = document.createElement('select');
  selModif.style.setProperty('width', 'auto', 'important');
  selModif.style.maxWidth = '60%';
  const btnCharger = mk('button', 'yaml-btn', 'Charger');
  btnCharger.type = 'button';
  ligneModif.appendChild(selModif);
  ligneModif.appendChild(btnCharger);
  corps.appendChild(ligneModif);
  const remplirModif = async () => {
    const garde = selModif.value;
    selModif.innerHTML = '<option value="">— choisir —</option>';
    try {
      const r = await fetch('/api/slugs?type=hypotheses_et_si&scenario=');
      const d = await r.json();
      (d.slugs || []).forEach(s => {
        const o = document.createElement('option');
        o.value = s;
        o.textContent = (d.labels && d.labels[s]) || s;
        selModif.appendChild(o);
      });
      if (garde) selModif.value = garde;
    } catch (e) {
      selModif.innerHTML = '<option value="">Erreur chargement</option>';
    }
  };
  remplirModif();

  corps.appendChild(mk('div', 'option-label', 'Bloc de l\\'hypothèse (modifiable)'));
'''

JS_AVANT2 = '''  ligneBoutons.appendChild(btnVerifier);
  ligneBoutons.appendChild(btnAjouter);
  corps.appendChild(ligneBoutons);
'''
JS_APRES2 = '''  ligneBoutons.appendChild(btnVerifier);
  ligneBoutons.appendChild(btnAjouter);
  const btnRemplacer = mk('button', 'yaml-btn yaml-btn-save', 'Remplacer dans hypotheses.yaml');   // U4h
  btnRemplacer.type = 'button';
  btnRemplacer.style.marginLeft = '8px';
  btnRemplacer.disabled = true;
  btnRemplacer.title = 'Actif après « Charger » : réécrit l\\'hypothèse chargée à sa place dans hypotheses.yaml.';
  ligneBoutons.appendChild(btnRemplacer);
  corps.appendChild(ligneBoutons);
'''

JS_AVANT3 = '''  return wrapper;
}


// ══════════════════════════════════════════════════
// PATCH_S27_GUI_PARCOURS'''
JS_APRES3 = '''  // U4h : charger une hypothèse existante, puis la remplacer à sa place
  const rafraichirListes = async () => {
    const sel = document.querySelector('#form-body [data-slug-type="hypotheses_et_si"]');
    if (sel) await rafraichirChampDynamique(sel);
    const panneau = document.querySelector('#form-body .yaml-panel[data-yaml-path="et_si/hypotheses.yaml"]');
    if (panneau) await loadYamlContent(panneau, 'et_si/hypotheses.yaml');
    await remplirModif();
  };
  btnCharger.addEventListener('click', async () => {
    if (!selModif.value) { statut.style.color = '#b03a2e'; statut.textContent = '✗ Choisis d\\'abord une hypothèse.'; return; }
    if (bloc.value.trim() && !armer2(btnCharger, '⚠ Cliquer encore pour remplacer le bloc affiché')) return;
    btnCharger.disabled = true;
    const data = await appeler('extraire', selModif.value);
    btnCharger.disabled = false;
    if (data.bloc) {
      bloc.value = data.bloc;
      btnAjouter.disabled = true;
      btnAjouter.dataset.verrou = '1';
      btnRemplacer.dataset.id = data.id;
      btnRemplacer.disabled = !data.ok;
    }
    afficher(statut, data, data.bloc ? `✓ ${data.id} chargée (${data.statut}) : corrige le bloc, « Vérifier », puis « Remplacer ».` : '');
  });
  btnRemplacer.addEventListener('click', async () => {
    const attendu = btnRemplacer.dataset.id;
    if (!attendu) return;
    const m = bloc.value.match(/^\\s*-?\\s*id:\\s*['"]?([A-Za-z0-9_]+)/m);
    if (!m || m[1] !== attendu) {
      statut.style.color = '#b03a2e';
      statut.textContent = `✗ L'id du bloc doit rester « ${attendu} » (pour un nouvel id : « Ajouter »).`;
      return;
    }
    if (!armer2(btnRemplacer, `⚠ Cliquer encore pour réécrire ${attendu}`)) return;
    btnRemplacer.disabled = true;
    const data = await appeler('remplacer', bloc.value);
    afficher(statut, data, data.message ? `✓ ${data.message}` : '');
    if (data.ok && data.message && !data.message.includes('aucun changement')) {
      bloc.value = '';
      delete btnRemplacer.dataset.id;
      await rafraichirListes();
    } else {
      btnRemplacer.disabled = false;
    }
  });

  return wrapper;
}


// ══════════════════════════════════════════════════
// PATCH_S27_GUI_PARCOURS'''

TRAVAUX = [
    (HDT, [("séparateur avant main()", HDT_AVANT1, HDT_APRES1),
           ("arguments", HDT_AVANT2, HDT_APRES2),
           ("aiguillage des actions", HDT_AVANT3, HDT_APRES3)]),
    (APP, [("TIMEOUT_ET_SI", APP_AVANT, APP_APRES)]),
    (JS, [("titre du bloc", JS_AVANT1, JS_APRES1),
          ("boutons Vérifier / Ajouter", JS_AVANT2, JS_APRES2),
          ("fin de buildAssistantHypothese", JS_AVANT3, JS_APRES3)]),
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
        if "U4h" in texte:
            sys.exit(f"✗ {chemin} contient déjà « U4h » : patch déjà appliqué ? Rien n'est écrit")
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
        shutil.copy(chemin, chemin.with_name(chemin.name + ".bak_u4h"))
        chemin.write_text(neuf, encoding="utf-8")
    for chemin in (HDT, APP):
        try:
            py_compile.compile(str(chemin), doraise=True)
        except py_compile.PyCompileError as e:
            for c, (ancien, _) in nouveaux.items():
                c.write_text(ancien, encoding="utf-8")
            sys.exit(f"✗ syntaxe invalide dans {chemin}, les 3 fichiers sont restaurés : {e}")
    print(f"✓ [{TAG}] appliqué (sauvegardes .bak_u4h). Relancer Flask entièrement, puis Cmd-Maj-R.")


if __name__ == "__main__":
    main()
