#!/usr/bin/env python3
"""
patch_s19_retouches.py -- retouches après le premier test réel du mode rupture
(17 octobre 2026, Atlantique 2067)
================================================================================
  gui/static/app.js (panneau « Parcours de l'hypothèse ») :
    1. pendant un appel, « ⏳ … en cours, N s — ne pas recliquer » s'affiche à
       côté du bouton cliqué, boutons grisés ; à la fin, le résultat défile à l'écran ;
    2. aide de ③ : différence avec le bouton « Lancer » général ; durée réaliste.
  generator/trace_injection.py : en rupture, la section 4 le dit (au lieu de
    « l'effet s'atténue avec le temps » seulement).
  generator/simuler_et_si.py :
    - en rupture, l'entrée de queue porte persistance: permanente ;
    - les références déplacées sont regroupées dans l'étape de vérification
      (plus de cases « aucune action »).

Prérequis : patch_s19_chaine_rupture.py et patch_s27_gui_parcours.py appliqués.
Tout ou rien, sauvegardes .bak_s19c, refuse un second passage.
Usage, depuis la racine du coffre :
    python3 generator/patch_s19_retouches.py            (aperçu)
    python3 generator/patch_s19_retouches.py --apply
Puis redémarrer le GUI (Flask) et recharger la page.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S19_RETOUCHES"
VAULT = Path.cwd()
R = {}

# ── gui/static/app.js ──────────────────────────────────────────────────
R["gui/static/app.js"] = [
    (
        '''  const tous = [btnActualiser, btnApercu, btnAdopter, btnRejeter, btnAnnuler, btnInjApercu, btnInjecter,
                btnAppApercu, btnAppliquer, btnReste, btnDossiers];''',
        '''  const tous = [btnActualiser, btnApercu, btnAdopter, btnRejeter, btnAnnuler, btnInjApercu, btnInjecter,
                btnAppApercu, btnAppliquer, btnReste, btnDossiers];
  // PATCH_S19_RETOUCHES : signe d'activité à côté du bouton cliqué (le résultat
  // s'affiche en bas du panneau, hors de vue pendant les longs appels).
  let dernierBouton = null;
  wrapper.addEventListener('click', (ev) => {
    const b = ev.target && ev.target.closest ? ev.target.closest('button') : null;
    if (b) dernierBouton = b;
  }, true);
  const indic = mk('span', 'option-desc');
  indic.style.marginLeft = '8px';
  indic.style.fontWeight = 'bold';''',
    ),
    (
        '''    tous.forEach(b => { b.disabled = true; });
    sortie.style.color = '';
    sortie.textContent = '…';
    let data;''',
        '''    tous.forEach(b => { b.disabled = true; b.style.opacity = '0.5'; });
    sortie.style.color = '';
    const libelle = dernierBouton ? dernierBouton.textContent : 'Appel';
    const debut = Date.now();
    const secondes = () => Math.round((Date.now() - debut) / 1000);
    indic.style.color = '#2e86c1';
    indic.textContent = `⏳ ${libelle} : en cours, 0 s — ne pas recliquer`;
    if (dernierBouton && dernierBouton.parentNode) dernierBouton.parentNode.appendChild(indic);
    sortie.textContent = `⏳ ${libelle} : en cours…`;
    const minuteur = setInterval(() => {
      indic.textContent = `⏳ ${libelle} : en cours, ${secondes()} s — ne pas recliquer`;
    }, 1000);
    let data;''',
    ),
    (
        '''    tous.forEach(b => { b.disabled = false; });
    sortie.textContent = data.error ? `✗ ${data.error}` : (data.sortie || '(aucune sortie)');
    sortie.style.color = (data.error || !data.ok) ? '#b03a2e' : '';''',
        '''    clearInterval(minuteur);
    tous.forEach(b => { b.disabled = false; b.style.opacity = ''; });
    const echec = !!(data.error || !data.ok);
    indic.style.color = echec ? '#b03a2e' : '#1e8449';
    indic.textContent = `${echec ? '✗' : '✓'} ${libelle} : terminé en ${secondes()} s — résultat en bas du panneau`;
    sortie.textContent = data.error ? `✗ ${data.error}` : (data.sortie || '(aucune sortie)');
    sortie.style.color = echec ? '#b03a2e' : '';
    try { sortie.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) { /* ancien navigateur */ }''',
    ),
    (
        '''    '(entité censée survivre décrite comme détruite, mot « matrice »). Le texte final peut différer de la ' +
    'simulation (nouveau tirage). Compte une à deux minutes.'));''',
        '''    '(entité censée survivre décrite comme détruite, mot « matrice »). Le texte final peut différer de la ' +
    'simulation (nouveau tirage). Compte plusieurs minutes (jusqu\\'à une dizaine) : ne reclique pas tant ' +
    'que « ⏳ en cours » est affiché.\\nDifférence avec le bouton « Lancer » de « Injecter des événements » : ' +
    'Lancer traite TOUTE la file d\\'injection ; ce bouton ne prend que l\\'entrée de cette hypothèse, refuse ' +
    'une double injection, la retire de la file et fait passer le parcours à ④.'));''',
    ),
    (
        '''    if (!confirm('Injecter cet événement dans le vault ? (appels IA ; une à deux minutes)')) return;''',
        '''    if (!confirm('Injecter cet événement dans le vault ? (appels IA ; plusieurs minutes)')) return;''',
    ),
]

# ── generator/trace_injection.py ───────────────────────────────────────
R["generator/trace_injection.py"] = [(
    '''                         "et se propage avec retard aux autres variables.")''',
    '''                         "et se propage avec retard aux autres variables.")
            # PATCH_S19_RETOUCHES : la phrase ci-dessus ne vaut pas pour une rupture.
            if any(d.get("rupture") for l in eff["declares"].values() for d in l):
                lines += ["", "**Mode rupture** : cet élément ne s'atténue pas. Il déplace pour de bon la "
                              "référence du scénario, à pleine force (sans la fraction réduite appliquée aux "
                              "chocs) : l'effet net ci-dessous est durable."]''',
)]

# ── generator/simuler_et_si.py ─────────────────────────────────────────
R["generator/simuler_et_si.py"] = [
    (
        '''              "persistance": hyp["persistance"] or "permanente", "scenarios": scen,''',
        '''              # PATCH_S19_RETOUCHES : en rupture, la persistance est sans objet (permanente).
              "persistance": "permanente" if rupture else (hyp["persistance"] or "permanente"), "scenarios": scen,''',
    ),
    (
        '''        for e in (res or {}).get("effets") or []:
            if abs(e.get("reference_apres", e["reference"]) - e["reference"]) >= 0.1:
                # V8.13 : une référence portée au plafond ne laisse plus de marge.
                plafond = e["reference_apres"] >= 99.5
                _etape(E, "Élément", ("⚠ " if plafond else "") + f"{e['variable']} : référence "
                       f"{_virgule(e['reference'], False)} → {_virgule(e['reference_apres'], False)}",
                       "aucune action : déplacée par le moteur dès l'injection",
                       "au plafond : plus aucune marge pour une autre crise sur cette variable" if plafond else None)
        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{i['force']:g}"
                           for i in hyp["impacts"] if sc in i["polarites"])
        _etape(E, "Élément", f"Vérifier que la fiche porte `mode: rupture` et les forces simulées ({cibles})",
               f"event_instances/{hyp['id']}_{sc}.md ; "
               f"python3 generator/trace_injection.py --slug {hyp['id']} --type evenement --scenario {sc}",
               "le Tracer doit finir chaque ligne « Déclaré » par « rupture »")''',
        '''        # PATCH_S19_RETOUCHES : références déplacées regroupées dans la vérification (rien à faire).
        deplacees, plafonnees = [], []
        for e in (res or {}).get("effets") or []:
            if abs(e.get("reference_apres", e["reference"]) - e["reference"]) >= 0.1:
                # V8.13 : une référence portée au plafond ne laisse plus de marge.
                if e["reference_apres"] >= 99.5:
                    plafonnees.append(e["variable"])
                deplacees.append(f"{e['variable']} {_virgule(e['reference'], False)} → "
                                 f"{_virgule(e['reference_apres'], False)}")
        cibles = ", ".join(f"{i['variable']} {'+' if i['polarites'].get(sc, 1) > 0 else '−'}{i['force']:g}"
                           for i in hyp["impacts"] if sc in i["polarites"])
        _etape(E, "Élément", ("⚠ " if plafonnees else "")
               + f"Vérifier que la fiche porte `mode: rupture` et les forces simulées ({cibles})",
               f"event_instances/{hyp['id']}_{sc}.md ; "
               f"python3 generator/trace_injection.py --slug {hyp['id']} --type evenement --scenario {sc}",
               "le Tracer doit finir chaque ligne « Déclaré » par « rupture » et retrouver l'effet simulé"
               + (" ; références déplacées par le moteur (rien à faire) : " + " ; ".join(deplacees) if deplacees else "")
               + (" ; au plafond, plus aucune marge pour une autre crise : " + ", ".join(plafonnees) if plafonnees else ""))''',
    ),
]

PREREQUIS = {
    "gui/static/app.js": ["PATCH_S27_GUI_PARCOURS"],
    "generator/simuler_et_si.py": ["PATCH_S19_CHAINE"],
    "generator/trace_injection.py": ["PATCH_S19_RUPTURE"],
}
DEBUT_PANNEAU = "// PATCH_S27_GUI_PARCOURS — PANNEAU"
FIN_PANNEAU = "// PATCH_GUI_OBSIDIAN_PANNEAUX"


def controle_js(js):
    """node --check sur le seul panneau (node ancien sur l'iMac : pas tout app.js)."""
    i = js.find(DEBUT_PANNEAU)
    j = js.find(FIN_PANNEAU, i)
    if i < 0 or j < 0:
        return "bornes du panneau introuvables"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js[i:j])
    try:
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True, timeout=30)
        return None if r.returncode == 0 else r.stderr.strip()
    except FileNotFoundError:
        print("  (node absent : contrôle JS sauté)")
        return None
    finally:
        Path(f.name).unlink()


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
        if nom.endswith(".py"):
            try:
                compile(texte, str(chemin), "exec")
            except SyntaxError as e:
                erreurs.append(f"{nom} : erreur de syntaxe après patch ({e})")
        else:
            err = controle_js(texte)
            if err:
                erreurs.append(f"{nom} : JavaScript invalide après patch : {err}")
        nouveaux[nom] = texte
    if erreurs:
        print("✗ Rien n'a été écrit :")
        for e in erreurs:
            print("  -", e)
        sys.exit(1)
    for nom in R:
        print(f"  ✓ {nom} : {len(R[nom])} remplacement(s) prêt(s)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    for nom, texte in nouveaux.items():
        chemin = VAULT / nom
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_s19c"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Retouches appliquées (sauvegardes .bak_s19c). Redémarrer le GUI et recharger la page.")


if __name__ == "__main__":
    main()
