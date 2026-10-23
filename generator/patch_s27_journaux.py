#!/usr/bin/env python3
"""
patch_s27_journaux.py -- étape ⑤, partie « Carte » : journaux d'une zone vidée (19 octobre 2026)
================================================================================================
  gui/app.py         routes /api/et_si/main/journal/{garder,apercu,retirer}.
  gui/static/app.js  sous chaque zone vidée, ses journaux : « Le garder (en exil) » (décision
                     notée, rien écrit), « Aperçu du retrait », « Le retirer » (retiré de
                     generator/journaux.yaml, sauvegarde .bak_et_si_main ; les articles déjà
                     signés ne sont pas modifiés).

À placer avec la nouvelle version de generator/et_si_main.py (--journal-retirer) ; demande
patch_s27_carte_main.py déjà appliqué. Tout ou rien, sauvegardes .bak_journaux, refuse un
second passage. Usage, depuis la racine du coffre :
    python3 generator/patch_s27_journaux.py            (aperçu)
    python3 generator/patch_s27_journaux.py --apply
Puis redémarrer le GUI.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "PATCH_S27_JOURNAUX"
VAULT = Path.cwd()
R = {}

R["gui/app.py"] = [
    (
        '''                 "carte": 120}   # PATCH_S27_CARTE_MAIN''',
        '''                 "carte": 120,   # PATCH_S27_CARTE_MAIN
                 "journal": 300}   # PATCH_S27_JOURNAUX''',
    ),
    (
        '''    elif quoi == "articles" and action == "verifier":   # PATCH_S27_ARTICLES (appels IA, lecture seule)''',
        '''    elif (quoi == "journal" and action in ("garder", "apercu", "retirer")   # PATCH_S27_JOURNAUX
          and re.match(r"^[a-z_]+:[a-z0-9_]+:[a-z_]+$", str(data.get("cle") or ""))):
        cle = str(data["cle"])
        cmd += ["--journal-garder", cle] if action == "garder" else (
            ["--journal-retirer", cle] + (["--apply"] if action == "retirer" else []))
    elif quoi == "articles" and action == "verifier":   # PATCH_S27_ARTICLES (appels IA, lecture seule)''',
    ),
]

R["gui/static/app.js"] = [
    (
        r'''        territoire: ['✓ a de nouveau un territoire', '#1e8449'], supprimee: ['· supprimée', '#888'],''',
        r'''        territoire: ['✓ a de nouveau un territoire', '#1e8449'], supprimee: ['· supprimée', '#888'],
        garde: ['✓ gardé (en exil)', '#1e8449'], retire: ['✓ retiré de journaux.yaml', '#1e8449'],   // PATCH_S27_JOURNAUX''',
    ),
    (
        r'''             ['La supprimer : onglet Carte ↗', () => ouvrirCarte(c.sc)]]));
        });''',
        r'''             ['La supprimer : onglet Carte ↗', () => ouvrirCarte(c.sc)]]));
          // PATCH_S27_JOURNAUX : journaux de la zone vidée (garder en exil, ou retirer).
          (z.journaux || []).forEach(j => {
            const lj = ligneZone(j, `Journal ${j.nom} (${j.orientation}`
              + (j.etat === 'retire' ? ')' : `, ${j.journalistes} journaliste(s))`) + ' de cette zone.',
              [['Le garder (en exil)', () => appeler('main/journal', 'garder', { cle: j.cle })],
               ['Aperçu du retrait', () => appeler('main/journal', 'apercu', { cle: j.cle })],
               ['Le retirer', () => {
                 if (!confirm(`Retirer « ${j.nom} » de journaux.yaml ? Les articles déjà signés ne changent pas `
                              + '(sauvegarde journaux.yaml.bak_et_si_main).')) return;
                 appeler('main/journal', 'retirer', { cle: j.cle });
               }, 'yaml-btn yaml-btn-save']]);
            lj.style.marginLeft = '24px';
            bloc.appendChild(lj);
          });
        });''',
    ),
    (
        r'''      'une portion par un tracé dans l\'onglet Carte (l\'état se met à jour à l\'actualisation).\n' +''',
        r'''      'une portion par un tracé dans l\'onglet Carte (l\'état se met à jour à l\'actualisation).\n' +
      'Journaux d\'une zone vidée : les garder (en exil, rien n\'est écrit) ou les retirer de ' +
      'journaux.yaml (aperçu d\'abord ; les articles déjà signés ne changent pas).\n' +''',
    ),
]
PREREQUIS = {"gui/app.py": ["PATCH_S27_CARTE_MAIN"], "gui/static/app.js": ["PATCH_S27_CARTE_MAIN"]}
DEBUT_PANNEAU = "// PATCH_S27_GUI_PARCOURS — PANNEAU"
FIN_PANNEAU = "// PATCH_GUI_OBSIDIAN_PANNEAUX"


def controle_js(js):
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
    main_py = VAULT / "generator" / "et_si_main.py"
    if not main_py.exists() or "def journal_retirer" not in main_py.read_text(encoding="utf-8"):
        sys.exit("✗ placer d'abord la nouvelle version de generator/et_si_main.py (journaux). Rien fait.")
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
        print("✗ Rien n'a été écrit :\n" + "\n".join(f"  - {e}" for e in erreurs))
        sys.exit(1)
    for nom in R:
        print(f"  ✓ {nom} : {len(R[nom])} remplacement(s) prêt(s)")
    if not apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return
    for nom, texte in nouveaux.items():
        chemin = VAULT / nom
        shutil.copy2(chemin, chemin.with_name(chemin.name + ".bak_journaux"))
        chemin.write_text(texte, encoding="utf-8")
    print("\n✓ Journaux des zones vidées dans l'étape ⑤ (sauvegardes .bak_journaux). Redémarrer le GUI.")


if __name__ == "__main__":
    main()
