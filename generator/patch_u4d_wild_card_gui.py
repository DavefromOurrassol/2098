#!/usr/bin/env python3
"""
patch_u4d_wild_card_gui.py — Ourrassol 2098 (U4d, 15 novembre 2026)
===================================================================

Wild cards, troisième morceau : suggestions et saisie dans « Nouvelle hypothèse ».

  1. suggerer_lacunes.py --type wildcard : UN appel IA, 3 idées de wild cards, rien
     n'est écrit. L'IA reçoit les scénarios, les signaux faibles du monde (à ne pas
     reprendre), les règles de lore (intouchables) et les wild cards existantes
     (quota, écart de 10 ans). Chaque idée est contrôlée (fenêtre 2030-2090, quota,
     écart) : un problème s'affiche en ⚠ sur la carte.
  2. Panneau « Nouvelle hypothèse » : bouton « ⚡ Proposer des wild cards » (à part
     des lacunes) ; case « ⚡ wild card » à côté de « ✨ Proposer » (envoie
     --wild-card, U4a). « Utiliser cette idée » d'une wild card coche la case.
  3. Jamais en lot : pas de bouton « Traiter en lot » pour les wild cards ; le lot des
     suggestions et « Ouvrir pour corriger » décochent la case.

Fichiers : generator/suggerer_lacunes.py, gui/app.py, gui/static/app.js.
Après --apply : relancer Flask ENTIÈREMENT (app.py modifié), puis Cmd-Maj-R.

USAGE (depuis la racine du vault)
    python3 generator/patch_u4d_wild_card_gui.py            # dry-run
    python3 generator/patch_u4d_wild_card_gui.py --apply
Sauvegardes : <fichier>.bak_u4d ; contrôles de syntaxe (Python : py_compile ;
app.js : node --check si node est présent, échec toléré s'il échoue aussi sur
l'original), retour arrière automatique. Exige U4a et U4c.
"""

import argparse
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VAULT = Path.cwd()
GEN = VAULT / "generator"
GUI = VAULT / "gui"
TAG = "U4d"

# ---------------------------------------------------------------------------
# suggerer_lacunes.py
# ---------------------------------------------------------------------------

SL = [
    ("fonction _wild_cards",
     '''def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\\n\\n")[0])
''',
     '''def _wild_cards(n, scenario):
    """U4d : idées de WILD CARDS (rupture improbable, impact majeur). Un appel IA ;
    chaque idée est contrôlée (fenêtre, quota, écart) : un problème devient un ⚠."""
    import inject_custom_events as ie
    import simuler_et_si as se
    if scenario and scenario not in se.SCENARIOS:
        raise ValueError(f"scénario inconnu : {scenario!r}")
    hyps = se.charger_hypotheses()
    signaux = []
    try:
        from loader import load_custom_signals
        signaux = [str(s.get("source_fiche") or s.get("name") or "").replace(".md", "").replace("_", " ")
                   for s in load_custom_signals() or [] if isinstance(s, dict)]
    except Exception:  # noqa: BLE001 -- repli : les hypothèses de type signal
        pass
    signaux += [str(h.get("nom") or "") for h in hyps if str(h.get("type") or "") == "signal"]
    signaux = list(dict.fromkeys(s.strip() for s in signaux if s.strip()))[:80]
    regles = []
    for sc in se.SCENARIOS:
        for rid, msg in se.regles_lore_scenario(sc) or []:
            regles.append(f"- [{sc}] {msg}")
    regles = list(dict.fromkeys(regles))
    existantes = [f"- {h.get('id')} : {h.get('nom')} ({h.get('date')}, scénarios : {h.get('scenarios') or 'tous'})"
                  for h in hyps if se.est_wild_card(h)]
    a0, a1 = se.WILD_CARD_DATES
    orientation = f"\\nOrientation : au moins une idée doit toucher le scénario '{scenario}'." if scenario else ""
    prompt = f"""Tu proposes {n} WILD CARDS pour le monde fictif Ourrassol 2098 (6 scénarios d'avenir, 2026-2098).
Une wild card est une rupture à FAIBLE probabilité et à IMPACT MAJEUR, qu'aucun signal faible du monde n'annonce
encore. Elle change le monde pour de bon et a le droit d'aller contre les tendances des scénarios (ruptures
technologiques, géopolitiques, sociales, sanitaires, environnementales, spatiales…).

## SCÉNARIOS
{ie.build_scenarios_summary_for_auto(None)}

## SIGNAUX FAIBLES DÉJÀ DANS LE MONDE (une wild card ne doit PAS être annoncée par l'un d'eux)
{chr(10).join("- " + s for s in signaux) or "(aucun)"}

## RÈGLES DE LORE (choix de l'auteur, INTOUCHABLES : une wild card ne les contredit jamais)
{chr(10).join(regles) or "(aucune)"}

## WILD CARDS DÉJÀ PRÉVUES (au plus {se.WILD_CARD_QUOTA} par scénario, {se.WILD_CARD_ECART} ans d'écart au moins dans un même scénario)
{chr(10).join(existantes) or "(aucune)"}
{orientation}

## CONSIGNE
- "date" : une année entre {a0} et {a1} ; respecte le plafond et l'écart ci-dessus.
- "scenarios" : "tous" ou une liste de scénarios ; une même rupture peut frapper plusieurs mondes, chacun
  l'absorbant à sa façon.
- Varie les domaines d'une idée à l'autre ; aucune ne doit reprendre une wild card déjà prévue.
- "description" : 2 ou 3 phrases concrètes (ce qui arrive, où, quelle ampleur).
- "improbable" : une phrase, pourquoi c'est improbable vu d'aujourd'hui.
- "bouscule" : une phrase, quelles tendances du monde elle contredit.

Réponds UNIQUEMENT en JSON, sans texte autour :
{{"wild_cards": [{{"titre": "...", "description": "...", "date": 2061, "scenarios": "tous",
  "improbable": "...", "bouscule": "..."}}]}}"""
    res = ie.call_claude_json(None, "Tu es un auteur de prospective qui imagine des ruptures crédibles.", prompt)
    idees = res.get("wild_cards", []) if isinstance(res, dict) else []
    sortie = []
    for i in (idees or [])[:n]:
        desc = " ".join(str((i or {}).get("description") or "").split())
        if not desc:
            continue
        avert = []
        try:
            date = int(float(i.get("date")))
        except (TypeError, ValueError):
            date = None
            avert.append("date illisible : à préciser dans l'idée")
        scen = i.get("scenarios") or "tous"
        if isinstance(scen, list):
            scen = [s for s in scen if s in se.SCENARIOS] or "tous"
        elif str(scen).strip() in se.SCENARIOS:
            scen = [str(scen).strip()]
        else:
            scen = "tous"
        if date is not None:
            if not a0 <= date <= a1:
                avert.append(f"date {date} hors de la fenêtre d'une wild card ({a0}-{a1})")
            avert += se.controle_wild_cards({"id": "_suggestion_u4d", "wild_card": True, "date": date,
                                             "scenarios": scen}, hyps)
        texte = desc + (f" En {date}." if date else "")
        texte += " Scénarios : " + (", ".join(scen) if isinstance(scen, list) else "tous") + "."
        raison = " · ".join(x for x in (
            f"Improbable : {' '.join(str(i.get('improbable') or '').split())}" if i.get("improbable") else "",
            f"Bouscule : {' '.join(str(i.get('bouscule') or '').split())}" if i.get("bouscule") else "") if x)
        titre = " ".join(str(i.get("titre") or "wild card").split())
        sortie.append({"titre": f"⚡ {titre}" + (f" ({date})" if date else ""), "texte": texte,
                       "raison": raison, "avertissements": avert})
    return sortie


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\\n\\n")[0])
'''),
    ("option --type wildcard",
     '''    ap.add_argument("--type", required=True, choices=["evenement", "entite"])
''',
     '''    ap.add_argument("--type", required=True, choices=["evenement", "entite", "wildcard"])   # U4d
'''),
    ("aiguillage",
     '''            sugg = (_evenements if a.type == "evenement" else _entites)(n, a.scenario.strip())
''',
     '''            fonction = {"evenement": _evenements, "entite": _entites, "wildcard": _wild_cards}[a.type]   # U4d
            sugg = fonction(n, a.scenario.strip())
'''),
]

# ---------------------------------------------------------------------------
# app.py
# ---------------------------------------------------------------------------

AP = [
    ("suggestions : type wildcard",
     '''    if type_ not in ("evenement", "entite"):
        return jsonify({"error": "type attendu : evenement ou entite"}), 400
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    cmd = [sys.executable, "suggerer_lacunes.py", "--type", type_, "--n", "5", "--json"]
''',
     '''    if type_ not in ("evenement", "entite", "wildcard"):   # U4d
        return jsonify({"error": "type attendu : evenement, entite ou wildcard"}), 400
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    cmd = [sys.executable, "suggerer_lacunes.py", "--type", type_,
           "--n", "3" if type_ == "wildcard" else "5", "--json"]   # U4d
'''),
    ("proposer : --wild-card",
     '''        if data.get("effet_plein") is True:   # U3d
            cmd.append("--effet-plein")
''',
     '''        if data.get("effet_plein") is True:   # U3d
            cmd.append("--effet-plein")
        if data.get("wild_card") is True:   # U4d
            cmd.append("--wild-card")
'''),
]

# ---------------------------------------------------------------------------
# app.js
# ---------------------------------------------------------------------------

JS = [
    ("case à cocher wild card",
     '''  ligneProposer.appendChild(selType);
  corps.appendChild(ligneProposer);
''',
     '''  ligneProposer.appendChild(selType);
  // U4d : case « wild card » (événement, rupture, 2030-2090, 3 à 6 impacts de force 25 à 35)
  const lblWild = document.createElement('label');
  lblWild.style.cssText = 'display:inline-flex;align-items:center;gap:4px;cursor:pointer;';
  const chkWild = document.createElement('input');
  chkWild.type = 'checkbox';
  chkWild.style.setProperty('width', 'auto', 'important');
  lblWild.appendChild(chkWild);
  lblWild.appendChild(document.createTextNode('⚡ wild card'));
  lblWild.title = 'Rupture improbable à impact majeur : événement en mode rupture, 2030-2090, 3 à 6 variables de force 25 à 35. ' +
    'La simulation lancera d\\'office la lecture IA et la Passe exhaustive (payant).';
  ligneProposer.appendChild(lblWild);
  corps.appendChild(ligneProposer);
'''),
    ("bouton ⚡ à part",
     '''  const listeSugg = mk('div');
  blocSugg.appendChild(listeSugg);
  corps.appendChild(blocSugg);
''',
     '''  // U4d : wild cards, à part des lacunes (3 idées, un appel IA, jamais en lot)
  const ligneWild = document.createElement('div');
  ligneWild.style.cssText = 'display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:8px 0 2px;padding-top:6px;border-top:1px dotted #9aa5b1;';
  const btnWild = mk('button', 'yaml-btn', '⚡ Proposer des wild cards');
  btnWild.type = 'button';
  ligneWild.appendChild(btnWild);
  ligneWild.appendChild(mk('span', 'option-desc', 'Ruptures improbables à impact majeur : 3 idées, un appel IA, rien n\\'est écrit. Traitées une par une, jamais en lot.'));
  blocSugg.appendChild(ligneWild);
  const listeSugg = mk('div');
  blocSugg.appendChild(listeSugg);
  corps.appendChild(blocSugg);
'''),
    ("recherche : fonction commune",
     '''  btnSugg.addEventListener('click', async () => {
    const type = selSugg.value;
    btnSugg.disabled = true;
    listeSugg.textContent = '';
    etatSugg.style.color = '';
    etatSugg.textContent = '💡 Analyse en cours… (un appel IA, jusqu\\'à une minute)';
''',
     '''  const chercherSugg = async (type) => {   // U4d : lacunes ou wild cards
    btnSugg.disabled = true;
    btnWild.disabled = true;
    listeSugg.textContent = '';
    etatSugg.style.color = '';
    etatSugg.textContent = type === 'wildcard' ? '⚡ Recherche de wild cards… (un appel IA, jusqu\\'à une minute)'
      : '💡 Analyse en cours… (un appel IA, jusqu\\'à une minute)';
'''),
    ("recherche : boutons réactivés",
     '''    btnSugg.disabled = false;
    if (data.error) { etatSugg.style.color = '#b03a2e'; etatSugg.textContent = `✗ ${data.error}`; return; }
''',
     '''    btnSugg.disabled = false;
    btnWild.disabled = false;   // U4d
    if (data.error) { etatSugg.style.color = '#b03a2e'; etatSugg.textContent = `✗ ${data.error}`; return; }
'''),
    ("utiliser l'idée : case cochée",
     '''        idee.value = s.texte;
        selType.value = (data.type === 'entite') ? 'entite' : '';
        idee.scrollIntoView({ behavior: 'smooth', block: 'center' });
''',
     '''        idee.value = s.texte;
        selType.value = (data.type === 'entite') ? 'entite' : (data.type === 'wildcard' ? 'evenement' : '');
        chkWild.checked = data.type === 'wildcard';   // U4d
        idee.scrollIntoView({ behavior: 'smooth', block: 'center' });
'''),
    ("jamais en lot",
     '''    if (!cartes.length) return;

    // U3ar : traitement en lot''',
     '''    if (!cartes.length) return;
    if (type === 'wildcard') {   // U4d : une wild card passe seule (Proposer, Vérifier, simulation, décision)
      const n = mk('div', 'option-desc', 'Wild cards : pas de traitement en lot. « Utiliser cette idée », puis ✨ Proposer (case ⚡ cochée), Vérifier, Ajouter, et simuler.');
      n.style.marginTop = '6px';
      listeSugg.appendChild(n);
      return;
    }

    // U3ar : traitement en lot'''),
    ("lot : case décochée",
     '''      [btnLot, btnSugg, btnProposer, btnVerifier, btnAjouter].forEach(x => { x.disabled = true; });
      let ajoutes = 0, aVoir = 0;
''',
     '''      [btnLot, btnSugg, btnProposer, btnVerifier, btnAjouter].forEach(x => { x.disabled = true; });
      chkWild.checked = false;   // U4d : jamais de wild card en lot
      let ajoutes = 0, aVoir = 0;
'''),
    ("ouvrir pour corriger : case décochée",
     '''            idee.value = it.s.texte;
            selType.value = (data.type === 'entite') ? 'entite' : '';
            bloc.value = it.bloc;
''',
     '''            idee.value = it.s.texte;
            selType.value = (data.type === 'entite') ? 'entite' : '';
            chkWild.checked = false;   // U4d
            bloc.value = it.bloc;
'''),
    ("recherche : branchement des boutons",
     '''    });
  });

  const retour = mk('div', 'option-desc');
''',
     '''    });
  };
  btnSugg.addEventListener('click', () => chercherSugg(selSugg.value));   // U4d
  btnWild.addEventListener('click', () => chercherSugg('wildcard'));

  const retour = mk('div', 'option-desc');
'''),
    ("proposer : envoi de la case",
     '''        body: JSON.stringify({ texte, type: action === 'proposer' ? selType.value : '' }),
''',
     '''        body: JSON.stringify({ texte, type: action === 'proposer' ? selType.value : '',
          wild_card: action === 'proposer' && chkWild.checked }),   // U4d
'''),
    ("proposer : type incompatible",
     '''    if (!idee.value.trim()) { retour.textContent = '✗ Écris d\\'abord l\\'idée.'; return; }
''',
     '''    if (!idee.value.trim()) { retour.textContent = '✗ Écris d\\'abord l\\'idée.'; return; }
    if (chkWild.checked && ['signal', 'entite'].includes(selType.value)) {   // U4d
      retour.style.color = '#b03a2e';
      retour.textContent = '✗ Une wild card est un événement : choisir « Événement » (ou « l\\'IA décide »), ou décocher ⚡.';
      return;
    }
'''),
]

FICHIERS = [(GEN / "suggerer_lacunes.py", SL), (GUI / "app.py", AP), (GUI / "static" / "app.js", JS)]


def node_ok(chemin_js):
    """True / False selon node --check ; None si node est absent."""
    try:
        r = subprocess.run(["node", "--check", str(chemin_js)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.returncode == 0


def main():
    a = argparse.ArgumentParser(description="U4d : wild cards dans le GUI et les suggestions.")
    a.add_argument("--apply", action="store_true")
    x = a.parse_args()
    if not GEN.is_dir() or not GUI.is_dir():
        sys.exit("✗ lancer depuis la racine du vault (generator/ et gui/ attendus)")
    erreurs, nouveaux = [], {}
    se_txt = (GEN / "simuler_et_si.py").read_text(encoding="utf-8") if (GEN / "simuler_et_si.py").exists() else ""
    if "WILD_CARD_FORCE" not in se_txt or "regles_lore_scenario" not in se_txt:
        erreurs.append("U4a ou U4c absent de simuler_et_si.py : les appliquer d'abord")
    for chemin, remp in FICHIERS:
        if not chemin.exists():
            erreurs.append(f"{chemin.relative_to(VAULT)} introuvable")
            continue
        texte = chemin.read_text(encoding="utf-8")
        if TAG in texte:
            erreurs.append(f"{chemin.name} : {TAG} déjà appliqué")
            continue
        for libelle, avant, apres in remp:
            n = texte.count(avant)
            if n != 1:
                erreurs.append(f"{chemin.name} [{libelle}] : passage trouvé {n} fois (attendu 1)")
                continue
            texte = texte.replace(avant, apres)
        nouveaux[chemin] = texte
    if erreurs:
        print("✗ Rien n'est écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
        sys.exit(1)
    # Contrôles sur copie
    for chemin, neuf in nouveaux.items():
        suffixe = chemin.suffix
        with tempfile.NamedTemporaryFile("w", suffix=suffixe, delete=False, encoding="utf-8") as f:
            f.write(neuf)
        try:
            if suffixe == ".py":
                py_compile.compile(f.name, doraise=True)
            else:
                ok = node_ok(f.name)
                if ok is False and node_ok(chemin) is not False:
                    sys.exit(f"✗ {chemin.name} : node --check échoue après patch (et pas sur l'original), rien n'est écrit")
                print(f"  ({chemin.name} : node --check "
                      + ("absent" if ok is None else "OK" if ok else "en échec aussi sur l'original, toléré") + ")")
        except py_compile.PyCompileError as e:
            sys.exit(f"✗ {chemin.name} : syntaxe invalide après patch, rien n'est écrit\n{e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    for chemin, remp in FICHIERS:
        print(f"{chemin.relative_to(VAULT)} : {len(remp)} modification(s)")
        for libelle, _, _ in remp:
            print(f"  · {libelle}")
    if not x.apply:
        print("\nDRY-RUN : syntaxe vérifiée sur copie, rien n'est écrit. Relancer avec --apply.")
        return
    faits = []
    try:
        for chemin, neuf in nouveaux.items():
            shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_u4d"))
            chemin.write_text(neuf, encoding="utf-8")
            faits.append(chemin)
            if chemin.suffix == ".py":
                py_compile.compile(str(chemin), doraise=True)
    except Exception as e:  # noqa: BLE001 -- retour arrière complet
        for chemin in faits:
            shutil.copy2(chemin.with_name(chemin.name + ".bak_u4d"), chemin)
        sys.exit(f"✗ échec ({type(e).__name__}: {e}) : fichiers restaurés depuis .bak_u4d")
    print("\n✓ U4d appliqué (sauvegardes .bak_u4d). Relancer Flask ENTIÈREMENT (app.py modifié), puis Cmd-Maj-R.")


if __name__ == "__main__":
    main()
