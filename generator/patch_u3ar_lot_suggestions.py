#!/usr/bin/env python3
"""
patch_u3ar_lot_suggestions.py — Ourrassol 2098 (14 novembre 2026)

Traitement en lot des suggestions (suite de U3aq). Sous les idées proposées, un
bouton « Traiter les N en lot » fait, pour chaque idée et à la suite : Proposer
(un appel IA) puis, SI le bloc n'a ni erreur ni avertissement, Ajouter à
hypotheses.yaml (le contrôle d'ajout habituel s'applique). Les idées à problème
ne sont PAS ajoutées : elles restent dans la liste avec le motif, et
« Ouvrir pour corriger » charge l'idée et le bloc dans l'éditeur habituel
(Vérifier, puis Ajouter). Aucune adoption, aucune injection : le monde n'est pas touché.

  gui/static/app.js seulement (aucune route nouvelle).
Prérequis : U3aq. Après application : Cmd+Maj+R dans le navigateur.

Usage (depuis la racine du vault) :
    python3 generator/patch_u3ar_lot_suggestions.py            # aperçu
    python3 generator/patch_u3ar_lot_suggestions.py --apply    # écrit
Sauvegarde .bak_u3ar ; refuse un second passage ; contrôle de syntaxe avec restauration.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARQUEUR = "U3ar"
APP_JS = Path("gui/static/app.js")

JS_REMPL = [
    (
        "liste des cartes",
        "    (data.suggestions || []).forEach(s => {\n      const carte = mk('div');\n",
        "    const cartes = [];   // U3ar\n"
        "    (data.suggestions || []).forEach(s => {\n      const carte = mk('div');\n",
    ),
    (
        "bouton de lot",
        "      carte.appendChild(b);\n      listeSugg.appendChild(carte);\n    });\n  });\n",
        r"""      const etat = mk('div', 'option-desc');
      etat.style.whiteSpace = 'pre-wrap';
      carte.appendChild(b);
      carte.appendChild(etat);
      listeSugg.appendChild(carte);
      cartes.push({ s, carte, etat, b, fait: false, bloc: '' });   // U3ar
    });
    if (!cartes.length) return;

    // U3ar : traitement en lot -- Proposer puis, si propre, Ajouter ; sinon « à voir avec toi »
    const appelLot = async (action, texte) => {
      try {
        const res = await fetch(`/api/et_si/${action}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ texte, type: action === 'proposer' ? (data.type === 'entite' ? 'entite' : 'evenement') : '' }),
        });
        return await res.json();
      } catch (e) {
        return { error: `Erreur réseau : ${e.message}` };
      }
    };
    const motifs = (d) => {
      const l = [];
      if (d.error) l.push(`✗ ${d.error}`);
      (d.erreurs || []).forEach(e => l.push(`✗ ${e}`));
      (d.avertissements || []).forEach(a => l.push(`⚠ ${a}`));
      return l;
    };
    const btnLot = mk('button', 'yaml-btn yaml-btn-save', `Traiter les ${cartes.length} en lot (proposer, puis ajouter si propre)`);
    btnLot.type = 'button';
    btnLot.style.marginTop = '8px';
    const resume = mk('div', 'option-desc');
    resume.style.whiteSpace = 'pre-wrap';
    resume.style.marginTop = '6px';
    listeSugg.appendChild(btnLot);
    listeSugg.appendChild(resume);

    btnLot.addEventListener('click', async () => {
      if (!confirm(`Traiter ${cartes.filter(c => !c.fait).length} idée(s) : un appel IA chacune. Les blocs sans problème seront ajoutés à hypotheses.yaml. Continuer ?`)) return;
      [btnLot, btnSugg, btnProposer, btnVerifier, btnAjouter].forEach(x => { x.disabled = true; });
      let ajoutes = 0, aVoir = 0;
      for (const it of cartes) {
        if (it.fait) continue;
        it.etat.style.color = '';
        it.etat.textContent = '⏳ proposition en cours…';
        const p = await appelLot('proposer', it.s.texte);
        let msgs = motifs(p);
        it.bloc = p.bloc || '';
        if (p.bloc && !msgs.length) {
          it.etat.textContent = '⏳ ajout…';
          const a = await appelLot('ajouter', p.bloc);
          if (a.ok) {
            it.fait = true; ajoutes++;
            it.b.disabled = true;
            it.etat.style.color = '#1e8449';
            it.etat.textContent = `✓ ${a.message || 'ajoutée'}`;
            continue;
          }
          msgs = motifs(a);
        }
        aVoir++;
        it.etat.style.color = '#b9770e';
        it.etat.textContent = (msgs.length ? msgs : ['✗ aucun bloc proposé']).join('\n');
        if (!it.ouvrir) {
          it.ouvrir = mk('button', 'yaml-btn', 'Ouvrir pour corriger');
          it.ouvrir.type = 'button';
          it.ouvrir.addEventListener('click', () => {
            idee.value = it.s.texte;
            selType.value = (data.type === 'entite') ? 'entite' : '';
            bloc.value = it.bloc;
            delete btnAjouter.dataset.verrou;
            btnAjouter.disabled = false;
            retour.style.color = '';
            retour.textContent = it.etat.textContent;
            statut.textContent = '';
            (it.bloc ? bloc : idee).scrollIntoView({ behavior: 'smooth', block: 'center' });
          });
          it.carte.appendChild(it.ouvrir);
        }
      }
      resume.textContent = `Lot terminé : ${ajoutes} ajoutée(s) à hypotheses.yaml, ${aVoir} à voir avec toi (ci-dessus).`;
      [btnLot, btnSugg, btnProposer, btnVerifier, btnAjouter].forEach(x => { x.disabled = false; });
      btnAjouter.disabled = !!btnAjouter.dataset.verrou;
      if (ajoutes) {
        const sel = document.querySelector('#form-body [data-slug-type="hypotheses_et_si"]');
        if (sel) await rafraichirChampDynamique(sel);
        const panneau = document.querySelector('#form-body .yaml-panel[data-yaml-path="et_si/hypotheses.yaml"]');
        if (panneau) await loadYamlContent(panneau, 'et_si/hypotheses.yaml');
      }
    });
  });
""",
    ),
]


def _node_check(chemin):
    try:
        r = subprocess.run(["node", "--check", str(chemin)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None, "node absent"
    return r.returncode == 0, r.stderr.strip()


def _premiere_erreur(msg):
    lignes = [l for l in msg.splitlines() if l.strip()]
    return " | ".join(l.strip() for l in lignes[:4] if "SyntaxError" in l or l.strip().startswith("("))[:300]


def verifier_js(chemin, original):
    """Ne bloque que sur une erreur NOUVELLE (un vieux node refuse déjà « ||= » dans l'original)."""
    ok, msg = _node_check(chemin)
    if ok:
        return True, "node --check OK"
    if ok is False:
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "original.js"
            copie.write_text(Path(original).read_text(encoding="utf-8"), encoding="utf-8")
            ok0, msg0 = _node_check(copie)
        if ok0 is False and _premiere_erreur(msg) == _premiere_erreur(msg0):
            return True, "node --check refuse une syntaxe déjà présente dans l'original : aucune erreur nouvelle"
        return False, msg[:400]
    t = chemin.read_text(encoding="utf-8")
    ok2 = t.count("{") == t.count("}") and t.count("(") == t.count(")")
    return ok2, "accolades/parenthèses équilibrées (node absent)" if ok2 else "accolades/parenthèses déséquilibrées"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--js", default=str(APP_JS))
    a = ap.parse_args()
    chemin = Path(a.js)
    if not chemin.exists():
        print(f"✗ Fichier introuvable : {chemin} (lancer depuis la racine du vault)")
        return 2
    texte = chemin.read_text(encoding="utf-8")
    if "U3aq" not in texte:
        print("✗ Prérequis U3aq absent de app.js : appliquer d'abord patch_u3aq_suggestions_lacunes.py.")
        return 1
    if MARQUEUR in texte:
        print(f"✗ {MARQUEUR} déjà appliqué — refus d'un second passage.")
        return 1
    nouveau = texte
    for libelle, ancre, rempl in JS_REMPL:
        n = nouveau.count(ancre)
        if n != 1:
            print(f"✗ app.js : ancre « {libelle} » : {n} occurrence(s) au lieu de 1 — rien écrit.")
            return 1
        nouveau = nouveau.replace(ancre, rempl, 1)
        print(f"  ✓ app.js : {libelle}")
    if not a.apply:
        print("\nAperçu seulement. Relancer avec --apply pour écrire.")
        return 0
    bak = chemin.with_name(chemin.name + ".bak_u3ar")
    shutil.copy2(chemin, bak)
    chemin.write_text(nouveau, encoding="utf-8")
    ok, msg = verifier_js(chemin, bak)
    if not ok:
        shutil.copy2(bak, chemin)
        print(f"✗ Contrôle de syntaxe app.js échoué, fichier restauré : {msg}")
        return 1
    print(f"  (app.js : {msg})")
    print(f"✓ Écrit : {chemin} (sauvegarde : {bak.name})")
    print("\nÀ faire : Cmd+Maj+R dans le navigateur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
