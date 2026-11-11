#!/usr/bin/env python3
"""
patch_u3f_extraction_evenements.py — Ourrassol 2098 (11 nov. 2026)

U3f : « ✨ Envoyer vers « et si ? » » (onglet Articles), cas ÉVÉNEMENT.
  - nouvelle route Flask /api/articles/extraire_evenements (gui/app.py) ;
  - bouton « 🔎 Détecter les événements de l'article » (gui/static/app.js) : l'IA lit le texte
    complet de l'article et liste ses événements (date, citation exacte, déjà connu ?) ;
  - on choisit UN événement : sa date est reprise de l'article et verrouillée
    (case « forcer la date » pour la changer) ; « Proposer » reçoit cet événement précis ;
  - « Proposer » est refusé tant qu'aucun événement n'est choisi. Un signal garde l'ancien chemin.

Prérequis : U3e appliqué ; generator/extraire_evenements_article.py présent.
Usage (racine du vault) :
  python3 generator/patch_u3f_extraction_evenements.py            # dry-run
  python3 generator/patch_u3f_extraction_evenements.py --apply    # écrit (.bak_u3f)
"""
import argparse
import shutil
import sys
import py_compile
from pathlib import Path

RACINE = Path(".")

B1_ANCIEN = 'TIMEOUT_ET_SI = {"proposer": 180, "verifier": 60, "ajouter": 60}\n'
B1_NOUVEAU = '''# U3f : l'IA lit le texte complet d'un article et liste ses événements (écrit rien)
@app.route("/api/articles/extraire_evenements", methods=["POST"])
def articles_extraire_evenements():
    cfg = load_config()
    pipeline_dir = Path(cfg.get("pipeline_dir", ""))
    data = request.get_json() or {}
    fichier = str(data.get("fichier") or "")
    scenario = str(data.get("scenario") or "")
    if not re.fullmatch(r"[A-Za-z0-9_.\\-]+\\.md", fichier) or not re.fullmatch(r"[a-z_]+", scenario):
        return jsonify({"error": "fichier ou scénario invalide"}), 400
    try:
        annee = int(data.get("annee"))
        mois = int(data.get("mois") or 12)
    except (TypeError, ValueError):
        return jsonify({"error": "date de l'article illisible"}), 400
    cmd = [sys.executable, "extraire_evenements_article.py", "--fichier", fichier, "--scenario", scenario,
           "--annee", str(annee), "--mois", str(mois), "--json"]
    try:
        resultat = subprocess.run(cmd, cwd=pipeline_dir, capture_output=True, text=True,
                                  timeout=180, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Délai dépassé (180 s)"}), 504
    except FileNotFoundError:
        return jsonify({"error": f"extraire_evenements_article.py introuvable dans {pipeline_dir}"}), 500
    sortie = resultat.stdout.strip()
    try:
        payload = json.loads(sortie.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return jsonify({"error": f"Sortie inattendue (code {resultat.returncode}) : "
                                  f"{(resultat.stderr or sortie)[-500:]}"}), 500
    if not payload.get("ok"):
        return jsonify({"error": payload.get("error", "erreur inconnue")}), 500
    return jsonify(payload)


''' + B1_ANCIEN

A1_ANCIEN = "  selType.addEventListener('change', majReglages);\n  majReglages();\n"
A1_NOUVEAU = A1_ANCIEN + r'''  // U3f : pour un événement, l'IA ne devine plus l'événement. On le choisit parmi ceux que
  // l'article raconte (texte complet lu par l'IA) ; sa date est reprise de l'article et verrouillée.
  let evChoisi = null;
  const zoneDetect = mk('div', '', 'margin-bottom:8px;font-size:11px');
  const btnDetect = mk('button', "🔎 Détecter les événements de l'article");
  btnDetect.type = 'button'; btnDetect.className = 'yaml-btn';
  const etatDetect = mk('div', '', 'white-space:pre-wrap;margin-top:4px');
  const listeDetect = mk('div', '', 'margin-top:4px');
  const [lblForcer, cbForcer] = caseOui("forcer la date (sinon : date de l'article, verrouillée)");
  lblForcer.style.display = 'none';
  [btnDetect, etatDetect, listeDetect, lblForcer].forEach(e => zoneDetect.appendChild(e));
  boite.insertBefore(zoneDetect, reglages);
  const appliquerVerrou = () => {
    const sig = selType.value === 'signal';
    const verrou = !sig && !!evChoisi && !cbForcer.checked;
    champDate.disabled = verrou;
    selMois.disabled = sig || verrou;
    lblForcer.style.display = (!sig && evChoisi) ? '' : 'none';
    zoneDetect.style.display = sig ? 'none' : '';
  };
  selType.addEventListener('change', appliquerVerrou);
  cbForcer.addEventListener('change', appliquerVerrou);
  appliquerVerrou();
  const libelleDate = (ev) => `${NOMS_MOIS_U3E[ev.mois - 1]} ${ev.annee}`;
  const texteEvenement = (ev) => [
    ev.description,
    ev.citation ? `Extrait de l'article : « ${ev.citation} »` : '',
    `Date de l'événement : ${ev.mois_connu ? libelleDate(ev) : ev.annee}.`,
    dateReelle ? `Article du ${dateReelle} (scénario ${article.scenario}).`
               : `Article du scénario ${article.scenario}.`,
    article.zone_principale ? `Lieu : ${article.zone_principale}.` : '',
    (article.entites_citees || []).length ? `Entités citées : ${article.entites_citees.join(', ')}.` : '',
    `Source : article ${article.fichier}.`,
  ].filter(Boolean).join(' ');
  btnDetect.addEventListener('click', async () => {
    btnDetect.disabled = true; evChoisi = null; appliquerVerrou();
    listeDetect.innerHTML = ''; etatDetect.style.color = '';
    etatDetect.textContent = "Lecture de l'article par l'IA (un appel, quelques secondes)…";
    let data;
    try {
      const res = await fetch('/api/articles/extraire_evenements', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fichier: article.fichier, scenario: article.scenario,
                               annee: article.annee, mois: article.mois }),
      });
      data = await res.json();
    } catch (e) { data = { error: `Erreur réseau : ${e.message}` }; }
    btnDetect.disabled = false;
    if (data.error || !data.ok) {
      etatDetect.style.color = '#b03a2e';
      etatDetect.textContent = `✗ ${data.error || 'aucune réponse'}`;
      return;
    }
    const evs = data.evenements || [];
    etatDetect.textContent = [
      evs.length ? `${evs.length} événement(s) trouvé(s) : choisis celui à envoyer.`
                 : "Aucun événement exploitable dans l'article.",
      ...(data.avertissements || []).map(a => `⚠ ${a}`),
    ].join('\n');
    evs.forEach((ev) => {
      const l = mk('label', '', 'display:block;margin:6px 0;padding:6px;border:1px solid #444;border-radius:4px;cursor:pointer');
      const r = document.createElement('input');
      r.type = 'radio'; r.name = 'u3f-ev'; r.style.marginRight = '6px';
      r.addEventListener('change', () => {
        evChoisi = ev; cbForcer.checked = false;
        champDate.value = String(ev.annee); selMois.value = String(ev.mois);
        appliquerVerrou();
        etatDetect.style.color = ev.deja_connu ? '#b5651d' : '';
        etatDetect.textContent = ev.deja_connu
          ? `⚠ Cet événement semble déjà dans le vault : ${ev.deja_connu_nom || ev.deja_connu}. L'envoyer créerait un doublon (effets cumulés).`
          : `Événement choisi : ${libelleDate(ev)}${ev.date_explicite ? '' : ' (date déduite)'}.`;
      });
      l.appendChild(r);
      l.appendChild(document.createTextNode(`${ev.description} `));
      l.appendChild(mk('div',
        `📅 ${ev.mois_connu ? libelleDate(ev) : ev.annee}${ev.date_explicite ? '' : ' (déduite)'}` +
        ` · ${ev.nature === 'propre' ? "événement de l'article" : 'événement passé mentionné'}` +
        `${ev.deja_connu ? ' · ⚠ déjà connu' : ''}${ev.citation_ok ? '' : ' · ⚠ citation introuvable'}`,
        'color:#888;margin-top:2px'));
      if (ev.citation) l.appendChild(mk('div', `« ${ev.citation} »`, 'color:#888;font-style:italic;margin-top:2px'));
      listeDetect.appendChild(l);
    });
  });
'''

A2_ANCIEN = ("    btn.disabled = true;\n    etat.style.color = '';\n"
             "    etat.textContent = 'Appel IA en cours (hypothese_depuis_texte.py)…';\n"
             "    const extra = { date: null };\n")
A2_NOUVEAU = ("    if (selType.value !== 'signal' && !evChoisi) {   // U3f\n"
              "      etat.style.color = '#b03a2e';\n"
              "      etat.textContent = \"✗ Clique d'abord sur « Détecter les événements de l'article » et choisis-en un.\";\n"
              "      return;\n"
              "    }\n") + A2_ANCIEN

A3_ANCIEN = "    const data = await appeler('proposer', texte, selType.value, extra);\n"
A3_NOUVEAU = ("    const data = await appeler('proposer',\n"
              "      (selType.value !== 'signal' && evChoisi) ? texteEvenement(evChoisi) : texte,   // U3f\n"
              "      selType.value, extra);\n")

EDITS = {
    "gui/app.py": [(B1_ANCIEN, B1_NOUVEAU, "route /api/articles/extraire_evenements")],
    "gui/static/app.js": [
        (A1_ANCIEN, A1_NOUVEAU, "bouton de détection, choix de l'événement, verrou de date"),
        (A2_ANCIEN, A2_NOUVEAU, "« Proposer » refusé sans événement choisi"),
        (A3_ANCIEN, A3_NOUVEAU, "« Proposer » reçoit l'événement choisi"),
    ],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    print(f"patch_u3f — mode {'APPLY' if args.apply else 'DRY-RUN'}")
    if not (RACINE / "generator" / "extraire_evenements_article.py").exists():
        print("✗ generator/extraire_evenements_article.py absent : le placer d'abord dans generator/.")
        sys.exit(1)
    if "NOMS_MOIS_U3E" not in (RACINE / "gui/static/app.js").read_text(encoding="utf-8"):
        print("✗ U3e n'est pas appliqué (NOMS_MOIS_U3E absent de app.js) : appliquer d'abord patch_u3e.")
        sys.exit(1)
    plan, bloque = [], False
    for fichier, edits in EDITS.items():
        chemin = RACINE / fichier
        texte = chemin.read_text(encoding="utf-8")
        nouveau = texte
        for ancien, neuf, nom in edits:
            n = nouveau.count(ancien)
            if neuf in nouveau:
                print(f"  · {fichier} : {nom} — déjà appliqué")
            elif n == 1:
                nouveau = nouveau.replace(ancien, neuf)
                print(f"  ✓ {fichier} : {nom}")
            else:
                print(f"  ✗ {fichier} : {nom} — {n} occurrence(s) de l'ancien texte (attendu : 1)")
                bloque = True
        if nouveau != texte:
            plan.append((chemin, nouveau))
    if bloque:
        print("✗ Au moins un remplacement n'est pas applicable : rien n'est écrit.")
        sys.exit(1)
    if not plan:
        print("Rien à faire.")
        return
    if not args.apply:
        print(f"[DRY-RUN] {len(plan)} fichier(s) seraient modifiés. Relancer avec --apply.")
        return
    for chemin, nouveau in plan:
        shutil.copy2(chemin, str(chemin) + ".bak_u3f")
        chemin.write_text(nouveau, encoding="utf-8")
        if chemin.suffix == ".py":
            try:
                py_compile.compile(str(chemin), doraise=True)
            except py_compile.PyCompileError as e:
                print(f"✗ py_compile {chemin} : {e}\n  Restaurer : cp {chemin}.bak_u3f {chemin}")
                sys.exit(1)
        print(f"  écrit : {chemin} (sauvegarde .bak_u3f)")
    print("Terminé. Relancer Flask entièrement (app.py / app.js modifiés).")


if __name__ == "__main__":
    main()
