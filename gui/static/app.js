/* ══════════════════════════════════════════════════
   OURRASSOL 2098 — app.js
   ══════════════════════════════════════════════════ */

// ── État global ───────────────────────────────────

const State = {
  config: null,
  scripts: [],
  activeScriptId: null,
  activeTab: null,       // 'dashboard' | 'review' | 'config' | null (script)
  currentRunId: null,
  sseSource: null,
  sessionRan: new Set(), // script_ids ayant tourné dans cette session
};

// ── Init ──────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  await loadConfig();
  await loadScripts();
  buildNav();
  buildLLMSelector();
  initEventListeners();
  // Vérifier si un run est déjà actif (reload page)
  await checkActiveRun();
  // Afficher le dashboard par défaut
  showTab('dashboard');
});

// ── Chargement données ────────────────────────────

async function loadConfig() {
  try {
    const res = await fetch('/api/config');
    State.config = await res.json();
  } catch (e) {
    console.error('Erreur chargement config', e);
    State.config = {};
  }
}

async function loadScripts() {
  try {
    const res = await fetch('/api/scripts');
    State.scripts = await res.json();
  } catch (e) {
    console.error('Erreur chargement scripts', e);
    State.scripts = [];
  }
}

// ── Construction de la nav ────────────────────────

const SECTIONS = [
  { key: 'articles',           label: 'Articles' },
  { key: 'presse',             label: 'Presse & journaux' },
  { key: 'entites_creation',   label: 'Entités & événements — création' },
  { key: 'entites_nettoyage',  label: 'Entités & événements — nettoyage' },
  { key: 'geo_construction',   label: 'Géographie — construction' },
  { key: 'geo_diagnostic',     label: 'Géographie — diagnostic' },
  { key: 'monde_reel',         label: 'Référence — monde réel' },
  { key: 'validation',         label: 'Validation' },
];

function buildNav() {
  const nav = document.getElementById('nav');
  nav.innerHTML = '';

  // Tableau de bord
  nav.appendChild(makeNavItem('dashboard', '📊', 'Tableau de bord', null, 'tab'));
  nav.appendChild(makeNavItem('carte', '🗺️', 'Carte', null, 'tab'));
  nav.appendChild(makeNavItem('chantiers', '🚧', 'Chantiers', null, 'tab'));
  nav.appendChild(makeNavItem('redaction', '📰', 'Rédaction', null, 'tab'));
  nav.appendChild(makeNavItem('articles', '🗂️', 'Articles', null, 'tab'));
  nav.appendChild(makeNavItem('instances', '🏛️', 'Instances', null, 'tab'));
  nav.appendChild(makeNavItem('event_instances', '⚡', 'Événements', null, 'tab'));
  nav.appendChild(makeNavItem('signaux', '📡', 'Signaux faibles', null, 'tab'));
  nav.appendChild(makeNavItem('resumes', '📝', 'Résumés par scénario', null, 'tab'));
  nav.appendChild(makeDivider());

  // Sections scripts
  SECTIONS.forEach(section => {
    nav.appendChild(makeSectionLabel(section.label));
    State.scripts
      .filter(s => s.section === section.key)
      .forEach(s => {
        const badge = s.badge || null;
        nav.appendChild(makeNavItem(s.id, s.icon, s.label, badge, 'script', false, s.gui_verified));
      });
    // "Audit par sujet" (5 septembre 2026, chantier "Suite narrative des
    // événements", point B) : onglet custom (pas un script
    // scripts_config.json déclaratif) mais rangé visuellement dans cette
    // section à la demande de David -- même famille fonctionnelle que
    // create_entities_and_instances/inject_custom_events. L'ancien onglet
    // "Promouvoir un événement" qui vivait ici (3 septembre) a été retiré
    // le 6 septembre : action équivalente désormais dans l'onglet
    // Articles, sans la limite de mois de parution actif.
    if (section.key === 'entites_creation') {
      nav.appendChild(makeNavItem('sujets', '🧭', 'Audit par sujet', null, 'tab'));
    }
    nav.appendChild(makeDivider());
  });

  // Revue + Config
  nav.appendChild(makeNavItem('review', '🔍', 'Revue', null, 'tab', true));
  nav.appendChild(makeNavItem('config', '⚙️', 'Config', null, 'tab'));
}

function makeNavItem(id, icon, label, badge, type, reviewBadge, guiVerified) {
  const el = document.createElement('div');
  el.className = 'nav-item';
  el.dataset.id = id;
  el.dataset.type = type;

  // Indicateur discret "non testé via GUI" (distinct des badges P7/P22/P26/P27,
  // qui référencent un item de backlog, pas un statut de test) — ajouté le
  // 16 juillet. La fonctionnalité marche (testée en CLI ou historiquement),
  // juste jamais cliquée depuis le sidebar lui-même.
  const untestedDot = (type === 'script' && guiVerified === false)
    ? `<span class="gui-untested-dot" title="Jamais testé via clic GUI (fonctionne, vérifié en CLI ou historiquement)" style="opacity:0.5;font-size:0.85em;margin-left:4px;">🧪</span>`
    : '';

  el.innerHTML = `
    <span class="icon">${icon}</span>
    <span class="label">${label}</span>
    ${badge ? `<span class="badge p7">${badge}</span>` : ''}
    ${untestedDot}
    ${reviewBadge ? `<span class="badge orange" id="review-nav-badge" style="display:none">0</span>` : ''}
  `;

  el.addEventListener('click', () => {
    if (type === 'tab') showTab(id);
    else showScript(id);
  });

  return el;
}

function makeSectionLabel(label) {
  const el = document.createElement('div');
  el.className = 'nav-section-label';
  el.textContent = label;
  return el;
}

function makeDivider() {
  const el = document.createElement('div');
  el.className = 'nav-divider';
  return el;
}

function setActiveNav(id) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === id);
  });
}

// ── Sélecteur LLM ─────────────────────────────────

const COST_MAP = {
  'mistral-small':            { cls: 'cost-eco',  label: '● éco' },
  'mistral-medium':           { cls: 'cost-eco',  label: '● éco' },
  'mistral-large':            { cls: 'cost-std',  label: '● std' },
  'claude-haiku-4-5-20251001':{ cls: 'cost-eco',  label: '● éco' },
  'claude-sonnet-4-6':        { cls: 'cost-std',  label: '● std' },
  'claude-opus-4-6':          { cls: 'cost-heavy',label: '● coût' },
};

function buildLLMSelector() {
  const llm = State.config?.llm || {};
  const provider = llm.provider || 'mistral';

  const providerSel = document.getElementById('llm-provider');
  const modelSel    = document.getElementById('llm-model');
  const badge       = document.getElementById('llm-cost-badge');
  const forceChk    = document.getElementById('llm-force-override');
  const forceRow    = document.getElementById('llm-force-row');

  // Populate provider
  providerSel.innerHTML = (llm.available_providers || ['mistral','claude'])
    .map(p => `<option value="${p}" ${p === provider ? 'selected' : ''}>${p.charAt(0).toUpperCase() + p.slice(1)}</option>`)
    .join('');

  // Populate models
  refreshModelSelect(provider);

  // Events
  providerSel.addEventListener('change', () => {
    refreshModelSelect(providerSel.value);
    saveLLM();
    updateForceBanner();
  });

  modelSel.addEventListener('change', () => {
    saveLLM();
    updateForceBanner();
  });

  // Toggle "forcer ce modèle" — état volontairement non persisté (ni
  // localStorage, ni config.json) : décision de session, pas une préférence
  // permanente. Recharger la page remet le toggle à false et le routing par
  // tier reprend la main.
  //
  // "Sticky" depuis le 11 juillet 2026 : contrairement à la première version
  // (qui se redécochait automatiquement après chaque run — pratique pour un
  // test isolé mais pénible pour enchaîner plusieurs lancements forcés), le
  // toggle reste actif jusqu'à ce que l'utilisateur le décoche lui-même. En
  // contrepartie, un bandeau d'alerte permanent (#llm-force-banner) rappelle
  // que le routing par tier est ignoré tant que ce n'est pas fait — pour ne
  // jamais laisser un forçage oublié passer inaperçu.
  State.forceLlmOverride = false;
  forceChk.checked = false;
  forceRow.classList.remove('active');
  forceChk.addEventListener('change', () => {
    State.forceLlmOverride = forceChk.checked;
    forceRow.classList.toggle('active', forceChk.checked);
    updateForceBanner();
  });

  document.getElementById('llm-force-banner-undo').addEventListener('click', () => {
    State.forceLlmOverride = false;
    forceChk.checked = false;
    forceRow.classList.remove('active');
    updateForceBanner();
  });

  updateForceBanner();
}

/** Affiche/masque le bandeau d'alerte "modèle forcé" et tient son texte à jour. */
function updateForceBanner() {
  const banner = document.getElementById('llm-force-banner');
  const text   = document.getElementById('llm-force-banner-text');
  if (!banner) return;

  if (State.forceLlmOverride) {
    const provider = document.getElementById('llm-provider')?.value || '—';
    const model    = document.getElementById('llm-model')?.value || '—';
    text.textContent = `${provider} / ${model}`;
    banner.style.display = 'flex';
  } else {
    banner.style.display = 'none';
  }
}

function refreshModelSelect(provider) {
  const llm = State.config?.llm || {};
  const modelSel = document.getElementById('llm-model');
  const badge    = document.getElementById('llm-cost-badge');

  // Générique : fonctionne pour n'importe quel provider ajouté à
  // available_providers, sans code spécifique par fournisseur (fix du 5
  // juillet — l'ancienne version ne gérait en dur que mistral/claude, un
  // provider comme "openai" retombait silencieusement sur les modèles Claude).
  const models = llm[`available_models_${provider}`] || [];
  const currentModel = llm[`model_${provider}`] || '';

  modelSel.innerHTML = models
    .map(m => `<option value="${m}" ${m === currentModel ? 'selected' : ''}>${m}</option>`)
    .join('');

  updateCostBadge(currentModel);
}

function updateCostBadge(model) {
  const badge = document.getElementById('llm-cost-badge');
  const info = COST_MAP[model] || { cls: 'cost-eco', label: '●' };
  badge.className = 'cost-badge ' + info.cls;
  badge.textContent = info.label;
}

async function saveLLM() {
  const provider = document.getElementById('llm-provider').value;
  const model    = document.getElementById('llm-model').value;

  updateCostBadge(model);

  // Mettre à jour State.config local — générique, même fix que refreshModelSelect
  if (!State.config.llm) State.config.llm = {};
  State.config.llm.provider = provider;
  State.config.llm[`model_${provider}`] = model;

  try {
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ llm: { provider, [`model_${provider}`]: model } }),
    });
  } catch (e) {
    console.error('Erreur sauvegarde LLM', e);
  }
}

// ── Navigation onglets ────────────────────────────

// ── Bandeau global "Mois de parution" (7 septembre 2026) ──────────────
// Visible sur TOUTE vue (appelé depuis showTab() ET showScript() ci-
// dessous) -- contrairement aux bandeaux locaux déjà existants (écran
// "Générer un article", onglet Sujets), qui ne s'affichent que dans leur
// propre onglet. Un seul fetch léger à chaque navigation : pas de
// mécanisme de mise à jour en temps réel, mais toujours à jour au
// prochain clic (y compris juste après un changement via l'écran
// "Mois de parution du journal", qui est lui-même accessible par
// showScript()).
async function chargerMoisParutionBanner() {
  const banner = document.getElementById('mois-parution-banner');
  if (!banner) return;
  try {
    const res = await fetch('/api/edition/active');
    const data = await res.json();
    const active = data.active || null;
    if (active) {
      const numero = active.numero != null ? ` (n°${active.numero})` : '';
      banner.textContent = `📅 Mois de parution : ${MOIS_FR_JS[active.mois]} ${active.annee}${numero}`;
    } else {
      banner.textContent = '📅 Aucun mois de parution défini pour l\'instant.';
    }
  } catch (e) {
    banner.textContent = '📅 Mois de parution : impossible à charger.';
  }
}

function showTab(tab) {
  chargerMoisParutionBanner();
  State.activeTab = tab;
  State.activeScriptId = null;
  setActiveNav(tab);

  document.getElementById('script-view').style.display = 'none';
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));

  const tabEl = document.getElementById('tab-' + tab);
  if (tabEl) {
    tabEl.classList.add('active');
    if (tab === 'dashboard') loadDashboard();
    if (tab === 'carte')     loadCarte();
    if (tab === 'chantiers') loadChantiers();
    if (tab === 'redaction') loadRedaction();
    if (tab === 'articles') loadArticles();
    if (tab === 'instances') loadInstances();
    if (tab === 'event_instances') loadEventInstances();
    if (tab === 'signaux') loadSignaux();
    if (tab === 'resumes') loadResumes();
    if (tab === 'sujets')    loadSujets();
    if (tab === 'review')    loadReview();
    if (tab === 'config')    loadConfigForm();
  }
}

// ── Vue script ────────────────────────────────────

async function showScript(scriptId) {
  chargerMoisParutionBanner();
  State.activeTab = null;
  State.activeScriptId = scriptId;
  setActiveNav(scriptId);

  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  const sv = document.getElementById('script-view');
  sv.style.display = 'flex';
  sv.style.flexDirection = 'column';
  sv.style.flex = '1';
  sv.style.overflow = 'hidden';

  const script = State.scripts.find(s => s.id === scriptId);
  if (!script) return;

  renderFormHeader(script);
  await renderFormBody(script);
}

function renderFormHeader(script) {
  document.getElementById('form-script-title').textContent = script.label;
  document.getElementById('form-script-desc').textContent  = script.description || '';
}

async function renderFormBody(script) {
  const body = document.getElementById('form-body');
  body.innerHTML = '';

  // Bandeau "Mois de parution" (2 septembre 2026, chantier "Éditions
  // datées") -- sur "Générer un article" (suit toujours le mois de
  // parution actif en lecture seule) ET sur "Mois de parution du
  // journal" (utile pour voir le mois actuel avant de le changer).
  // Informationnel seulement, pas un avertissement -- classe distincte
  // de requires-warning pour ne pas laisser croire à un problème.
  // Terminologie alignée avec David le 2 septembre 2026 ("édition" jugé
  // ambigu, lu comme "modifier" plutôt que "numéro du journal").
  // Étendu à "Générer une série d'articles" le 3 septembre 2026 (demande
  // de David après test réel : seul écran de génération à ne pas montrer
  // le mois avant lancement) -- même lecture seule que "generate", le
  // formulaire série retombe sur config_series.yaml puis sur ce mois actif.
  if (script.id === 'generate' || script.id === 'generate_series' || script.id === 'definir_edition') {
    const infoBanner = document.createElement('div');
    infoBanner.className = 'edition-active-banner';
    infoBanner.style.cssText =
      'margin: 8px 0 16px; padding: 8px 12px; border-radius: 6px; ' +
      'background: #eef4fb; border: 1px solid #cfe0f0; font-size: 0.9em; color: #34495e;';
    infoBanner.textContent = 'Mois de parution : chargement...';
    body.appendChild(infoBanner);

    fetch('/api/edition/active')
      .then(res => res.json())
      .then(data => {
        const MOIS_FR = [null, 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                         'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
        if (data.active) {
          const { annee, mois, numero } = data.active;
          let suffixe;
          if (script.id === 'generate') {
            suffixe = ' — cet article suivra ce mois de parution automatiquement.';
          } else if (script.id === 'generate_series') {
            suffixe = ' — cette série suivra ce mois sauf si annee_edition/mois_edition ' +
              'sont renseignés dans config_series.yaml.';
          } else {
            suffixe = ' — utilisez le formulaire ci-dessous pour le changer.';
          }
          infoBanner.textContent = `📅 Mois de parution : ${MOIS_FR[mois]} ${annee} (n°${numero})${suffixe}`;
        } else {
          if (script.id === 'generate') {
            infoBanner.textContent = '📅 Aucun mois de parution défini pour l\'instant — cet article suivra le ' +
              'comportement historique (année 2098, date tirée sur toute l\'année). Configurez-en un ci-dessous.';
          } else if (script.id === 'generate_series') {
            infoBanner.textContent = '📅 Aucun mois de parution défini pour l\'instant — le lancement échouera ' +
              'sauf si annee_edition/mois_edition sont renseignés dans config_series.yaml. Configurez un mois ' +
              'de parution via l\'écran dédié, ou renseignez ces champs.';
          } else {
            infoBanner.textContent = '📅 Aucun mois de parution défini pour l\'instant — configurez-en un ci-dessous.';
          }
        }
      })
      .catch(() => {
        infoBanner.textContent = '📅 Mois de parution : impossible à charger.';
      });
  }

  // Avertissement requires
  if (script.requires && script.requires.length > 0) {
    const missingRan = script.requires.filter(r => !State.sessionRan.has(r));
    if (missingRan.length > 0) {
      const warn = document.createElement('div');
      warn.className = 'requires-warning visible';
      warn.textContent = script.requires_message || `Prérequis : ${script.requires.join(', ')}`;
      body.appendChild(warn);
    }
  }

  // Mode select (create_entities, inject_events)
  if (script.mode_select) {
    body.appendChild(renderModeSelect(script.mode_select));
  }

  // Steps (generate_manual)
  if (script.mode === 'manual_steps' && script.steps) {
    body.appendChild(renderManualSteps(script.steps));
    return; // pas d'autres options
  }

  // Préréglages (ex. scan_geographie_complet : Léger / À la carte / Maxi) --
  // pré-coche un profil de cases avant que l'utilisateur affine à la main.
  // Ajouté le 25 juillet 2026, distinct de mode_select (qui pilote --mode,
  // un argument argparse) : un préréglage ne fait QUE cocher/décocher des
  // checkboxes déjà déclarées dans `options`, jamais envoyé lui-même comme
  // argument CLI.
  if (script.presets) {
    body.appendChild(renderPresets(script.presets));
  }

  // Options standard, plus un regroupement optionnel "Options avancées"
  // (mécanisme ajouté le 31 juillet 2026 -- 7e mécanisme conditionnel du
  // fichier, après vérification qu'aucun des 6 existants ne couvrait ce
  // besoin : masquer par défaut un champ à cas d'usage marginal (ex.
  // --report sur extract_phantom_slugs), sans le retirer complètement --
  // contrairement à hide_when qui masque selon la VALEUR d'un autre champ,
  // ici c'est une préférence d'affichage fixe, non conditionnelle).
  // opt.advanced = true --> regroupé sous un <details> replié par défaut,
  // affiché après les options normales du même script.
  const optionsNormales = (script.options || []).filter(o => !o.advanced);
  const optionsAvancees = (script.options || []).filter(o => o.advanced);

  for (const opt of optionsNormales) {
    const group = await renderOption(opt, script);
    if (group) body.appendChild(group);
  }

  if (optionsAvancees.length > 0) {
    const details = document.createElement('details');
    details.className = 'advanced-options';
    const summary = document.createElement('summary');
    summary.textContent = 'Options avancées';
    details.appendChild(summary);
    for (const opt of optionsAvancees) {
      const group = await renderOption(opt, script);
      if (group) details.appendChild(group);
    }
    body.appendChild(details);
  }

  // YAML panels
  await renderYamlPanels(script);

  // État initial de la visibilité mode_only (onglet par défaut = premier de
  // la liste, cf. renderModeSelect) — sans ça, le premier rendu affiche tout
  // avant le premier clic sur un onglet Mode.
  if (script.mode_select) updateModeOnlyVisibility();

  // État initial des paires diagnostic/correction (depends_on) -- corrige le
  // 26 juillet 2026 (retour de David) : une correction cochée par un
  // préréglage (ex. Maxi) doit forcer visuellement son diagnostic parent
  // coché, plutôt que l'inverse (griser l'enfant selon le parent, logique
  // initiale abandonnée -- voir syncDependsOnParents()).
  syncDependsOnParents();

  // État initial du masquage conditionnel (hide_when) -- même raison que
  // les deux ci-dessus : sans cet appel, un champ qui devrait être masqué
  // dès le départ (valeur par défaut du champ pilote) resterait visible
  // jusqu'au premier changement.
  updateHideWhenVisibility();
}

function renderModeSelect(modeConfig) {
  const group = document.createElement('div');
  group.className = 'option-group';

  const label = document.createElement('div');
  label.className = 'option-label';
  label.textContent = modeConfig.label;
  group.appendChild(label);

  const tabs = document.createElement('div');
  tabs.className = 'mode-tabs';
  tabs.dataset.optType = 'mode_select';

  const note = document.createElement('div');
  note.className = 'mode-note';
  note.id = 'mode-select-note';

  const updateNote = () => {
    const active = tabs.querySelector('.mode-tab.active');
    const choice = modeConfig.choices.find(c => c.value === active?.dataset.value);
    if (choice?.note) {
      note.textContent = choice.note;
      note.style.display = '';
    } else {
      note.style.display = 'none';
    }
  };

  modeConfig.choices.forEach((c, i) => {
    const tab = document.createElement('button');
    tab.className = 'mode-tab' + (i === 0 ? ' active' : '');
    tab.dataset.value = c.value;
    tab.textContent = c.label;
    tab.addEventListener('click', () => {
      tabs.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      updateModeOnlyVisibility();
      updateNote();
    });
    tabs.appendChild(tab);
  });

  group.appendChild(tabs);
  group.appendChild(note);
  updateNote();  // état initial (premier onglet actif par défaut)
  return group;
}

/**
 * Affiche/masque les blocs marqués data-mode-only selon l'onglet Mode
 * actuellement actif. Un bloc sans data-mode-only reste toujours visible
 * (ex: --dry-run, pertinent quel que soit le mode).
 *
 * Corrige la confusion du 11 juillet 2026 : "Scénario de référence"
 * (config_fields, mode custom uniquement) et "Limiter à un scénario"
 * (--scenario, mode auto uniquement) s'affichaient simultanément, sans
 * lien avec l'onglet Mode sélectionné, laissant croire à un doublon alors
 * que les deux champs ne sont jamais actifs pour le même run.
 */
function updateModeOnlyVisibility() {
  const activeTab = document.querySelector('.mode-tab.active');
  const activeMode = activeTab ? activeTab.dataset.value : null;

  document.querySelectorAll('[data-mode-only]').forEach(el => {
    const allowedModes = el.dataset.modeOnly.split(',');
    el.style.display = (!activeMode || allowedModes.includes(activeMode)) ? '' : 'none';
  });
}

/**
 * Masque un option-group entier selon la valeur courante d'un autre champ
 * du même formulaire (ex. "Étendue de l'annulation" masqué quand
 * --type = "signal" sur undo_custom). Ajouté le 26 juillet 2026 -- David
 * a demandé que le champ disparaisse plutôt que de rester affiché avec
 * une simple note "sans effet". Générique : n'importe quelle option future
 * peut poser `hide_when: {field, values}` dans scripts_config.json sans
 * toucher à ce code.
 */
function updateHideWhenVisibility() {
  document.querySelectorAll('#form-body [data-hide-when-field]').forEach(group => {
    const champPilote = document.querySelector(`#form-body [data-flag="${group.dataset.hideWhenField}"]`);
    const valeurs = JSON.parse(group.dataset.hideWhenValues || '[]');
    const valeurActuelle = champPilote ? champPilote.value : undefined;
    group.style.display = valeurs.includes(valeurActuelle) ? 'none' : '';
  });
}

// Le champ pilote (ex. --type) peut changer sans que le formulaire soit
// re-rendu -- même écouteur global que syncDependsOnParents/mode_only,
// posé une seule fois plutôt qu'à chaque renderOption().
document.addEventListener('change', (e) => {
  if (e.target.closest('#form-body')) updateHideWhenVisibility();
});

/**
 * Corrige le 26 juillet 2026 (retour de David sur un premier essai) : ce
 * n'est PAS une histoire de "niveau" où l'enfant serait gouverné par le
 * parent -- vérifié dans les scripts Python réels (check_zones_coherence.py,
 * check_type_entite_coherence.py, etc.) : le diagnostic (--scenario/--all)
 * est TOUJOURS obligatoire et tourne dans le même appel que son option
 * corrective (--apply, --marquer-resolus...). Donc la correction IMPLIQUE
 * le diagnostic, jamais l'inverse. Modèle retenu : paire diagnostic/
 * correction au même niveau logique --
 *   - cocher la correction force le diagnostic parent coché (ajout d'un
 *     écouteur sur la case enfant, voir renderOption)
 *   - décocher le diagnostic décoche automatiquement sa correction (ajout
 *     d'un écouteur sur la case parente, voir renderOption)
 * Cette fonction ne gère que le cas non couvert par ces deux écouteurs
 * directs : un préréglage (ex. Maxi) qui coche une correction en écrivant
 * directement `.checked = true` (voir applyPreset()), sans déclencher
 * d'évènement 'change' natif -- donc sans passer par les écouteurs.
 * Rattrape uniquement le sens "enfant coché -> parent forcé", jamais
 * l'inverse (un préréglage sait ce qu'il veut cocher, on ne le contredit pas).
 */
function syncDependsOnParents() {
  document.querySelectorAll('#form-body [data-depends-on]').forEach(group => {
    const chk = group.querySelector('input[type="checkbox"]');
    if (!chk || !chk.checked) return;
    const parentEl = document.querySelector(`#form-body [data-flag="${group.dataset.dependsOn}"]`);
    if (parentEl && parentEl.type === 'checkbox' && !parentEl.checked) {
      parentEl.checked = true;
    }
  });
}

/**
 * Préréglages (ex. scan_geographie_complet : Léger / À la carte / Maxi),
 * ajouté le 25 juillet 2026. Bande d'onglets visuellement proche de
 * mode-tabs/mode-tab (mode_select), mais avec ses PROPRES classes
 * (preset-tabs/preset-tab) et un style posé en ligne plutôt que dans
 * style.css (jamais lu par Claude à l'écriture de cette fonction -- éviter
 * toute dépendance sur des classes non vérifiées).
 *
 * IMPORTANT : ne JAMAIS réutiliser la classe mode-tab ici. Bug réel du 25
 * juillet 2026 -- collectArgs() sélectionne `.mode-tab.active` n'importe où
 * dans le formulaire pour pousser `--mode <valeur>` dans les args CLI (ce
 * mécanisme sert mode_select, ex. create_entities_and_instances.py). Un
 * premier essai avait donné la classe mode-tab aux boutons de préréglage
 * pour hériter du style -- collectArgs() les prenait alors pour un vrai
 * mode_select et injectait "--mode None" (aucun script.mode_select actif),
 * faisant planter scan_geographie_complet.py ("unrecognized arguments").
 * Un préréglage n'est PAS un mode_select : il ne doit jamais être visible
 * de collectArgs().
 *
 * Schéma attendu dans scripts_config.json (script.presets) :
 *   {
 *     "label": "Mode",
 *     "choices": [
 *       { "id": "light", "label": "Léger", "description": "...",
 *         "values": {} },                              // toutes les cases décochées
 *       { "id": "a_la_carte", "label": "À la carte", "description": "...",
 *         "default": true },                            // pas de "values" -> no-op, voir applyPreset()
 *       { "id": "maxi", "label": "Maxi", "description": "...",
 *         "values": { "--write-chantiers": true, ... } } // coche exactement ces flags, décoche le reste
 *     ]
 *   }
 */
function renderPresets(presetConfig) {
  const group = document.createElement('div');
  group.className = 'option-group';

  const label = document.createElement('div');
  label.className = 'option-label';
  label.textContent = presetConfig.label || 'Mode';
  group.appendChild(label);

  const tabs = document.createElement('div');
  tabs.className = 'preset-tabs';
  tabs.style.cssText = 'display:flex; gap:6px; flex-wrap:wrap;';

  const note = document.createElement('div');
  note.className = 'preset-note';
  note.style.cssText = 'font-size:11px; color:#5a7a9a; background:#eef4fa; ' +
    'border-left:2px solid #a8c8e8; padding:6px 10px; margin-top:8px; ' +
    'border-radius:0 4px 4px 0; line-height:1.4;';

  const styleTab = (tab, active) => {
    tab.style.cssText = 'font-family:"JetBrains Mono",monospace; font-size:12px; ' +
      'padding:5px 12px; border-radius:4px; cursor:pointer; ' +
      (active
        ? 'border:1px solid #3b6fd4; background:#3b6fd4; color:#fff;'
        : 'border:1px solid #ddd; background:#fff; color:#333;');
  };

  const updateNote = () => {
    const active = tabs.querySelector('.preset-tab.active');
    const choice = presetConfig.choices.find(c => c.id === active?.dataset.presetId);
    if (choice && choice.description) {
      note.textContent = choice.description;
      note.style.display = '';
    } else {
      note.style.display = 'none';
    }
  };

  presetConfig.choices.forEach((c) => {
    const tab = document.createElement('button');
    tab.type = 'button';
    tab.className = 'preset-tab' + (c.default ? ' active' : '');
    tab.dataset.presetId = c.id;
    tab.textContent = c.label;
    styleTab(tab, Boolean(c.default));
    tab.addEventListener('click', () => {
      tabs.querySelectorAll('.preset-tab').forEach(t => { t.classList.remove('active'); styleTab(t, false); });
      tab.classList.add('active');
      styleTab(tab, true);
      applyPreset(c);
      syncDependsOnParents();
      updateNote();
    });
    tabs.appendChild(tab);
  });

  group.appendChild(tabs);
  group.appendChild(note);
  updateNote(); // état initial (préréglage par défaut déjà actif, ex. "À la carte")
  return group;
}

/**
 * Applique un préréglage : coche exactement les flags listés dans
 * choice.values (true), décoche tous les autres. Si choice.values est
 * absent (cas "À la carte") : ne touche à AUCUNE case, volontairement --
 * l'utilisateur garde l'état courant et choisit lui-même à partir de là.
 * Ne pilote que les checkboxes -- un préréglage ne force jamais un select
 * (ex. --scenario), ce champ reste toujours un choix manuel séparé.
 */
function applyPreset(choice) {
  if (!choice.values) return; // "À la carte" -- no-op assumé
  document.querySelectorAll('#form-body [data-flag]').forEach(el => {
    if (el.type !== 'checkbox') return;
    el.checked = Boolean(choice.values[el.dataset.flag]);
  });
}

function renderManualSteps(steps) {
  const group = document.createElement('div');
  group.className = 'option-group';

  const label = document.createElement('div');
  label.className = 'option-label';
  label.textContent = 'Action';
  group.appendChild(label);

  const btns = document.createElement('div');
  btns.className = 'step-buttons';

  steps.forEach(step => {
    const btn = document.createElement('button');
    btn.className = 'step-btn';
    btn.dataset.stepArg = step.arg;
    btn.innerHTML = `<div>${step.label}</div><div class="step-desc">${step.description || ''}</div>`;

    if (step.has_input) {
      const input = document.createElement('input');
      input.type = 'text';
      input.placeholder = step.input_label || 'Fichier de sortie';
      input.dataset.stepInput = step.arg;
      input.style.marginTop = '6px';
      btn.appendChild(input);
    }

    btn.addEventListener('click', (e) => {
      if (e.target.tagName === 'INPUT') return; // ne pas déclencher sur l'input
      let args = [step.arg];
      if (step.has_input) {
        const inp = btn.querySelector('input');
        if (inp && inp.value) args.push(inp.value);
      }
      runScript(State.activeScriptId, args);
    });

    btns.appendChild(btn);
  });

  group.appendChild(btns);
  return group;
}

async function renderOption(opt, script) {
  const group = document.createElement('div');
  group.className = 'option-group';
  if (opt.mode_only) {
    group.dataset.modeOnly = Array.isArray(opt.mode_only) ? opt.mode_only.join(',') : opt.mode_only;
  }
  // Paire diagnostic/correction (backlog du 25 juillet 2026, corrigée le 26
  // juillet suite au retour de David) : depends_on pointe vers UN SEUL flag
  // --run-* parent -- toujours un diagnostic obligatoire, jamais optionnel,
  // donc jamais besoin d'un OU entre plusieurs parents (--write-chantiers
  // n'a plus ce champ, voir sa description dans scripts_config.json).
  // Indentation visuelle pour marquer le lien ; le vrai couplage se fait via
  // les écouteurs 'change' posés plus bas et dans syncDependsOnParents().
  if (opt.depends_on) {
    group.dataset.dependsOn = opt.depends_on;
    group.style.marginLeft = '22px';
    group.style.borderLeft = '2px solid #ddd';
    group.style.paddingLeft = '10px';
  }

  // Masquage conditionnel selon la valeur d'un autre champ -- ajouté le 26
  // juillet 2026 (ex. "Étendue de l'annulation" n'a pas de sens quand
  // undo_custom.py Type = "signal", pas juste "sans effet" en description :
  // David a demandé que ça disparaisse plutôt que de rester affiché avec
  // une note). opt.hide_when = { field: "--type", values: ["signal"] } --
  // masqué si la valeur courante du champ piloté est dans `values`.
  if (opt.hide_when) {
    group.dataset.hideWhenField = opt.hide_when.field;
    group.dataset.hideWhenValues = JSON.stringify(opt.hide_when.values);
  }

  if (opt.type === 'checkbox') {
    const row = document.createElement('label');
    row.className = 'checkbox-row';
    const chk = document.createElement('input');
    chk.type = 'checkbox';
    chk.dataset.flag = opt.flag;
    chk.checked = opt.default || false;
    const lbl = document.createElement('span');
    lbl.className = 'check-label';
    lbl.textContent = opt.label;
    row.appendChild(chk);
    row.appendChild(lbl);
    group.appendChild(row);
    if (opt.description) {
      const desc = document.createElement('div');
      desc.className = 'option-desc';
      desc.textContent = opt.description;
      group.appendChild(desc);
    }
    // Paire diagnostic/correction (depends_on) -- ajouté le 26 juillet 2026.
    // Sens 1 : cocher la correction force son diagnostic parent coché (le
    // parent est déjà dans le DOM à ce stade, car il apparaît toujours avant
    // dans scripts_config.json -- voir l'ordre des options réorganisé le
    // même jour). Sens 2 : décocher le diagnostic décoche automatiquement sa
    // correction, puisqu'une correction sans son diagnostic dans le même
    // appel n'a plus de sens (vérifié dans les scripts Python réels).
    if (opt.depends_on) {
      const parentEl = document.querySelector(`#form-body [data-flag="${opt.depends_on}"]`);
      chk.addEventListener('change', () => {
        if (chk.checked && parentEl && parentEl.type === 'checkbox' && !parentEl.checked) {
          parentEl.checked = true;
        }
      });
      if (parentEl) {
        parentEl.addEventListener('change', () => {
          if (!parentEl.checked) chk.checked = false;
        });
      }
    }
    // Logique mutually_exclusive -- corrigée le 25 juillet 2026 (deux passes) :
    // 1ère correction : cocher --all désactivait le <select> --scenario mais
    // ne le réactivait jamais en décochant --all ensuite.
    // 2e correction (même jour, bug remonté par David) : désactiver le select
    // ne vide pas sa valeur -- si un scénario était déjà choisi avant de
    // cocher --all, le select grisé gardait quand même cette valeur, et
    // collectArgs() ne regarde jamais `.disabled`, seulement `.value` : les
    // deux flags --all ET --scenario partaient donc ensemble, rejetés par le
    // groupe mutuellement exclusif argparse côté script ("not allowed with
    // argument --all"). Vider explicitement other.value en plus de
    // other.disabled = true règle la cause réelle, pas juste le symptôme visuel.
    if (opt.mutually_exclusive_with) {
      chk.addEventListener('change', () => {
        const other = document.querySelector(`[data-flag="--${opt.mutually_exclusive_with}"]`);
        if (!other) return;
        if (chk.checked) {
          if (other.type === 'checkbox') other.checked = false;
          if (other.tagName === 'SELECT') { other.disabled = true; other.value = ''; }
        } else {
          if (other.tagName === 'SELECT') other.disabled = false;
        }
      });
    }
    return group;
  }

  // Label commun pour select, number, text, slug_select, ligne_select
  const lbl = document.createElement('div');
  lbl.className = 'option-label';
  lbl.textContent = opt.label + (opt.optional ? ' (optionnel)' : '') + (opt.required ? ' *' : '');
  group.appendChild(lbl);

  if (opt.type === 'select' || opt.type === 'ligne_select') {
    const sel = document.createElement('select');
    sel.dataset.flag = opt.flag;
    sel.dataset.defaultValue = opt.default || '';

    let choices = opt.choices || [];

    // Source dynamique depuis config
    if (opt.source === 'config_scenarios') {
      const scenarios = State.config?.scenarios || [];
      if (opt.optional) choices = [{ value: '', label: '— Aucun —' }];
      scenarios.forEach(sc => choices.push({ value: sc, label: sc }));
    }

    choices.forEach(c => {
      const option = document.createElement('option');
      option.value = c.value;
      option.textContent = c.label;
      if (c.value === (opt.default || '')) option.selected = true;
      sel.appendChild(option);
    });

    // Réciproque de la logique mutually_exclusive ci-dessus (25 juillet 2026) :
    // choisir une vraie valeur décoche la checkbox opposée (ex. --scenario
    // rempli -> --all décoché), pour ne jamais envoyer les deux à la fois.
    if (opt.mutually_exclusive_with) {
      sel.addEventListener('change', () => {
        if (!sel.value) return; // "— Aucun —" : rien à trancher
        const other = document.querySelector(`[data-flag="--${opt.mutually_exclusive_with}"]`);
        if (other && other.type === 'checkbox') other.checked = false;
      });
    }

    group.appendChild(sel);

  } else if (opt.type === 'multi_select') {
    // Chips cliquables — même pattern que multi_select dans buildYamlFormPanel
    // (config_fields), porté ici pour les options CLI classiques.
    const chips = document.createElement('div');
    chips.className = 'yaml-chips';
    chips.dataset.multiFlag = opt.flag;

    let choices = opt.choices || [];
    if (opt.source === 'config_scenarios') {
      choices = (State.config?.scenarios || []).map(sc => ({ value: sc, label: sc }));
    }

    choices.forEach(c => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'yaml-chip';
      chip.textContent = c.label;
      chip.dataset.value = c.value;
      chip.addEventListener('click', () => chip.classList.toggle('active'));
      chips.appendChild(chip);
    });

    group.appendChild(chips);

    if (opt.description) {
      const desc = document.createElement('div');
      desc.className = 'option-desc';
      desc.textContent = opt.description;
      group.appendChild(desc);
    }

  } else if (opt.type === 'dynamic_multi_select') {
    // Ajouté le 2 août 2026 -- même rendu visuel que multi_select
    // (chips cliquables, collectées par le même code dans collectArgs()
    // grâce à dataset.multiFlag identique), mais liste peuplée de façon
    // asynchrone comme slug_select plutôt que depuis opt.choices statiques.
    // Cas d'usage : --forcer-scenarios, restreint dynamiquement aux
    // scénarios où l'élément forcé choisi existe réellement.
    const chips = document.createElement('div');
    chips.className = 'yaml-chips';
    chips.dataset.multiFlag = opt.flag;
    chips.dataset.slugType = opt.slug_type;
    if (opt.slug_type_field && opt.slug_type_map) {
      chips.dataset.slugTypeField = opt.slug_type_field;
      chips.dataset.slugTypeMap = JSON.stringify(opt.slug_type_map);
    }
    if (opt.slug_extra_params) {
      chips.dataset.slugExtraParams = JSON.stringify(opt.slug_extra_params);
    }
    chips.dataset.needsScenario = 'true';
    chips.innerHTML = '<span class="option-desc">Chargement…</span>';
    group.appendChild(chips);

    loadSlugsForChips(chips, opt.slug_type, opt.slug_extra_params);

    if (opt.description) {
      const desc = document.createElement('div');
      desc.className = 'option-desc';
      desc.textContent = opt.description;
      group.appendChild(desc);
    }

  } else if (opt.type === 'slug_select') {
    const sel = document.createElement('select');
    sel.dataset.flag = opt.flag;
    sel.dataset.slugType = opt.slug_type;
    if (opt.slug_extra_params) {
      sel.dataset.slugExtraParams = JSON.stringify(opt.slug_extra_params);
    }
    const placeholder = document.createElement('option');
    placeholder.value = '';
    sel.dataset.needsScenario = 'true';

    // Source de slugs dynamique selon un autre champ -- ajouté le 26
    // juillet 2026 pour undo_custom (--slug doit lister les entités OU
    // les signaux selon la valeur de --type, pas toujours "entities").
    // opt.slug_type_field : flag du champ pilote (ex. "--type").
    // opt.slug_type_map : { valeur_du_champ_pilote: slug_type_a_utiliser },
    // "*" en clé de secours si la valeur ne matche rien de listé.
    if (opt.slug_type_field && opt.slug_type_map) {
      sel.dataset.slugTypeField = opt.slug_type_field;
      sel.dataset.slugTypeMap = JSON.stringify(opt.slug_type_map);
    }

    // requires_scenario_selected (22 août 2026, trouvé en testant
    // set_priorite_forcee) : opt-in -- certains champs slug_select
    // n'ont de sens qu'une fois un scénario réel choisi (la liste
    // dépend entièrement de lui, pas juste "affinée" par lui). Sans ce
    // flag, le chargement initial se faisait AVANT tout choix de
    // scénario (scenario='' dans la requête /api/slugs) -- si
    // l'utilisateur sélectionnait une valeur à ce moment-là puis
    // choisissait le scénario ensuite, le rechargement déclenché par
    // ce second choix REMPLACE silencieusement la liste (innerHTML) et
    // retombe sur le placeholder vide, perdant la sélection sans aucun
    // signal visuel -- collectArgs() n'envoie alors jamais le flag,
    // argparse échoue côté script avec une erreur qui ne dit rien de
    // la vraie cause. Le champ est ici désactivé et affiche un
    // placeholder explicite tant qu'aucun scénario n'est choisi,
    // empêchant la séquence problématique à la source plutôt que de la
    // réparer après coup. N'affecte aucun champ existant qui ne déclare
    // pas ce flag (undo_custom, fix_annee_debut_placeholder, zone_hint) --
    // comportement strictement inchangé pour eux.
    if (opt.requires_scenario_selected) {
      sel.disabled = true;
      placeholder.textContent = 'Choisis d’abord un scénario';
      sel.appendChild(placeholder);
      group.appendChild(sel);
    } else {
      placeholder.textContent = 'Chargement…';
      sel.appendChild(placeholder);
      group.appendChild(sel);
      // Charger les slugs en async
      loadSlugsForSelect(sel, opt.slug_type, opt.slug_extra_params);
    }

  } else if (opt.type === 'number') {
    const inp = document.createElement('input');
    inp.type = 'number';
    inp.dataset.flag = opt.flag;
    inp.value = opt.default ?? '';
    if (opt.min !== undefined) inp.min = opt.min;
    if (opt.max !== undefined) inp.max = opt.max;
    group.appendChild(inp);

  } else if (opt.type === 'textarea') {
    // Option CLI multi-lignes (24 septembre 2026, --role/--consigne de
    // generate_instances.py) : même collecte que 'text' (el.value lu via
    // data-flag dans buildArgs), seule la saisie change.
    const ta = document.createElement('textarea');
    ta.className = 'yaml-form-textarea';
    ta.dataset.flag = opt.flag;
    ta.rows = opt.rows || 4;
    ta.placeholder = opt.placeholder || opt.label;
    ta.autocomplete = 'off';
    group.appendChild(ta);

  } else if (opt.type === 'text') {
    const inp = document.createElement('input');
    inp.type = 'text';
    inp.dataset.flag = opt.flag;
    inp.dataset.defaultValue = opt.default || '';
    // Corrigé le 11 août 2026 : utilisait opt.label (le libellé du champ,
    // déjà affiché juste au-dessus) au lieu de opt.placeholder (le texte
    // d'exemple prévu, ex. "ex : focus sur les réfugiés climatiques") --
    // ce dernier n'était donc jamais visible.
    inp.placeholder = opt.placeholder || opt.label;
    // autocomplete="off" ajouté le 11 août 2026 : sans attribut `name` ni
    // consigne explicite, le navigateur (Safari en particulier) peut
    // proposer/réinjecter une ancienne saisie faite dans ce même champ des
    // semaines plus tôt, en se basant sur le placeholder plutôt que sur un
    // vrai nom de champ -- cas réel vécu par David sur "Angle spécifique"
    // (generate.py), une valeur de test oubliée réapparue sans lien avec
    // config.yaml ni le code serveur (inp.value n'est jamais fixé ici).
    inp.autocomplete = 'off';
    group.appendChild(inp);

    if (opt.description) {
      const desc = document.createElement('div');
      desc.className = 'option-desc';
      desc.textContent = opt.description;
      group.appendChild(desc);
    }
  }

  return group;
}

// Lit la valeur courante d'un champ du formulaire, quel que soit son type
// de rendu -- un <select>/<input> classique (.value), ou un groupe de
// chips multi_select/dynamic_multi_select (valeurs actives jointes par
// virgule). Ajouté le 2 août 2026 pour slug_extra_params ci-dessous :
// avant, seul --scenario (toujours un <select> simple) était jamais lu
// comme dépendance, donc .value suffisait -- pas le cas pour un champ
// forceur potentiellement multi-valeurs.
function lireValeurChamp(flag) {
  const chips = document.querySelector(`[data-multi-flag="${flag}"]`);
  if (chips) {
    return Array.from(chips.querySelectorAll('.yaml-chip.active')).map(c => c.dataset.value).join(',');
  }
  const el = document.querySelector(`[data-flag="${flag}"]`);
  if (!el) return '';
  // Une checkbox sans attribut value explicite renvoie toujours "on" via
  // .value, coché ou pas -- il faut lire .checked. Bug trouvé le 14 août
  // 2026 en diagnostiquant pourquoi --force ne rafraîchissait pas le menu
  // --slug de extract_localisation (backlog Partie 2) : même une fois
  // slug_extra_params câblé, cette fonction aurait renvoyé "on" en
  // permanence, jamais l'état réel de la case. collectArgs()/isFlagActive()
  // géraient déjà correctement ce cas, pas lireValeurChamp().
  if (el.type === 'checkbox') return el.checked ? 'true' : 'false';
  return el.value;
}

// Calcule la chaîne de paramètres additionnels (&nom=valeur...) à partir
// d'un dict slug_extra_params -- factorisé le 2 août 2026 pour être
// partagé entre loadSlugsForSelect (options) et loadSlugsForChips
// (dynamic_multi_select) ci-dessous.
function construireExtraParams(extraParams) {
  let extra = '';
  if (extraParams) {
    for (const [paramName, sourceFlag] of Object.entries(extraParams)) {
      const val = lireValeurChamp(sourceFlag) || '';
      extra += `&${encodeURIComponent(paramName)}=${encodeURIComponent(val)}`;
    }
  }
  return extra;
}

async function loadSlugsForSelect(sel, slugType, extraParams) {
  const scenarioSel = document.querySelector('[data-flag="--scenario"]');
  const scenario = scenarioSel ? scenarioSel.value : (State.config?.default_scenario || '');
  const extra = construireExtraParams(extraParams);

  try {
    const res = await fetch(`/api/slugs?type=${slugType}&scenario=${scenario}${extra}`);
    const data = await res.json();
    sel.innerHTML = '<option value="">— Aucun —</option>';
    // 24 septembre 2026 : type zones_hier (liste de zones d'un scénario,
    // renvoyée sous "zones" et non "slugs") -- utilisé par
    // renommer_slug_sous_zone. Indentation par niveau, slug entre parenthèses.
    if (!data.slugs && Array.isArray(data.zones)) {
      data.zones.forEach(z => {
        const opt = document.createElement('option');
        opt.value = z.slug;
        opt.textContent = '\u00a0\u00a0'.repeat(Math.max(0, (z.niveau || 1) - 1)) + `${z.nom} (${z.slug})`;
        sel.appendChild(opt);
      });
      return;
    }
    (data.slugs || []).forEach(slug => {
      const opt = document.createElement('option');
      opt.value = slug;
      opt.textContent = (data.labels && data.labels[slug]) || slug;
      sel.appendChild(opt);
    });
  } catch (e) {
    sel.innerHTML = '<option value="">Erreur chargement</option>';
  }
}

// dynamic_multi_select (ajouté le 2 août 2026) : même principe que
// loadSlugsForSelect, mais rend des chips cliquables multi-valeurs
// (comme multi_select) plutôt qu'un <select> à valeur unique -- pour
// --forcer-scenarios (plusieurs scénarios possibles à la fois, liste
// restreinte dynamiquement selon l'élément forcé choisi).
// Exclusivité "tous" vs valeurs précises -- ajouté le 2 août 2026 (retour
// de David : rien n'empêchait techniquement de cocher "tous" ET un
// scénario/une zone précis en même temps, ce qui n'a pas de sens -- "tous"
// et une restriction précise sont mutuellement exclusifs). Cocher "tous"
// décoche tout le reste du groupe ; cocher une valeur précise décoche
// "tous" s'il était actif. Un groupe sans chip "tous" (multi_select
// statique classique) n'est pas concerné -- cette fonction n'est câblée
// que sur les chips dynamiques (dynamic_multi_select).
function activerChipExclusifTous(chip, chipsEl) {
  const activation = !chip.classList.contains('active');
  if (!activation) {
    chip.classList.remove('active');
    return;
  }
  if (chip.dataset.value === 'tous') {
    chipsEl.querySelectorAll('.yaml-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
  } else {
    const chipTous = chipsEl.querySelector('.yaml-chip[data-value="tous"]');
    if (chipTous) chipTous.classList.remove('active');
    chip.classList.add('active');
  }
}

async function loadSlugsForChips(chipsEl, slugType, extraParams) {
  const scenarioSel = document.querySelector('[data-flag="--scenario"]');
  const scenario = scenarioSel ? scenarioSel.value : (State.config?.default_scenario || '');
  const extra = construireExtraParams(extraParams);

  // Conserve les valeurs déjà actives avant rechargement, pour les
  // ré-appliquer si elles existent toujours dans la nouvelle liste --
  // évite de perdre une sélection en cours quand un champ frère change.
  const actives = new Set(Array.from(chipsEl.querySelectorAll('.yaml-chip.active')).map(c => c.dataset.value));
  // Premier chargement (aucune chip encore rendue dans ce groupe) : "tous"
  // actif par défaut si présent -- ajouté le 2 août 2026, cohérent avec le
  // comportement réel de generate.py (aucune sélection explicite = tous
  // les scénarios disponibles). Avant, rien n'était visuellement
  // sélectionné au chargement alors que "tous" s'appliquait déjà en
  // silence côté serveur -- source de confusion.
  const premierChargement = chipsEl.children.length === 0
    || (chipsEl.children.length === 1 && chipsEl.querySelector('.option-desc'));
  if (premierChargement) actives.add('tous');

  try {
    const res = await fetch(`/api/slugs?type=${slugType}&scenario=${scenario}${extra}`);
    const data = await res.json();
    chipsEl.innerHTML = '';
    (data.slugs || []).forEach(slug => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'yaml-chip' + (actives.has(slug) ? ' active' : '');
      chip.textContent = (data.labels && data.labels[slug]) || slug;
      chip.dataset.value = slug;
      chip.addEventListener('click', () => activerChipExclusifTous(chip, chipsEl));
      chipsEl.appendChild(chip);
    });
  } catch (e) {
    chipsEl.innerHTML = '<span class="option-desc">Erreur chargement</span>';
  }
}

// Point d'entrée unique pour rafraîchir un champ dynamique (select OU
// chips), quel que soit ce qui a changé -- ajouté le 2 août 2026.
async function rafraichirChampDynamique(el) {
  const extra = el.dataset.slugExtraParams ? JSON.parse(el.dataset.slugExtraParams) : null;
  if (el.tagName === 'SELECT') {
    await loadSlugsForSelect(el, el.dataset.slugType, extra);
  } else {
    await loadSlugsForChips(el, el.dataset.slugType, extra);
  }
}

// Rechargement des slug_selects quand le scénario change
document.addEventListener('change', async (e) => {
  if (e.target.dataset.flag === '--scenario') {
    const slugSelects = document.querySelectorAll('[data-needs-scenario="true"]');
    for (const sel of slugSelects) {
      await rafraichirChampDynamique(sel);
      // 22 août 2026 : réactive un champ bloqué par
      // requires_scenario_selected une fois qu'un scénario réel est
      // choisi. No-op pour un champ jamais désactivé (undo_custom,
      // fix_annee_debut_placeholder, zone_hint).
      if (e.target.value) sel.disabled = false;
    }
  }
});

// Source de slugs dynamique selon un autre champ (ex. --type pilote la
// source de --slug pour undo_custom : "entities" ou "signals" selon que
// le type choisi est "signal" ou non). Ajouté le 26 juillet 2026.
document.addEventListener('change', async (e) => {
  const piloted = document.querySelectorAll(`[data-slug-type-field="${e.target.dataset.flag}"]`);
  for (const sel of piloted) {
    const map = JSON.parse(sel.dataset.slugTypeMap || '{}');
    const nouveauType = map[e.target.value] || map['*'] || sel.dataset.slugType;
    sel.dataset.slugType = nouveauType;
    await rafraichirChampDynamique(sel);
  }
});

// Rechargement des champs dynamiques (select OU chips) dont un des
// slug_extra_params vient de changer -- ajouté le 2 août 2026. Distinct
// de l'écouteur slug_type_field ci-dessus : ici la LISTE change de
// contenu (nouveau slug/scénarios choisis), pas le TYPE de slug_type
// utilisé. Un champ peut légitimement être écouté ici ET par
// slug_type_field (ex. --forcer-slug pilote le type de --forcer-scenarios
// ET fournit sa valeur en paramètre "slug").
async function notifierChangementChamp(flag) {
  if (!flag) return;
  const cibles = document.querySelectorAll('[data-slug-extra-params]');
  for (const el of cibles) {
    const params = JSON.parse(el.dataset.slugExtraParams || '{}');
    if (Object.values(params).includes(flag)) {
      await rafraichirChampDynamique(el);
    }
  }
}
document.addEventListener('change', (e) => {
  if (e.target.dataset.flag) notifierChangementChamp(e.target.dataset.flag);
});
// multi_select/dynamic_multi_select (chips) ne déclenchent pas d'évènement
// natif 'change' (ce sont des <button>, pas des <input>/<select>) --
// écouteur dédié sur le clic des chips, en plus du toggle visuel déjà posé
// dans renderOption()/loadSlugsForChips.
document.addEventListener('click', (e) => {
  const chip = e.target.closest('.yaml-chip');
  const group = chip && chip.closest('[data-multi-flag]');
  if (group) notifierChangementChamp(group.dataset.multiFlag);
});

// ── Construction des args CLI ─────────────────────

function collectArgs() {
  const args = [];

  // Mode select — envoyé comme --mode <valeur>, pas comme argument brut.
  // Avant le 11 juillet 2026, seule la valeur ("custom") était poussée sans
  // flag, ce que argparse rejetait ("unrecognized arguments: custom") côté
  // create_entities_and_instances.py, faute d'argument --mode reconnu.
  const modeActive = document.querySelector('.mode-tab.active');
  if (modeActive) args.push('--mode', modeActive.dataset.value);

  // Options standard
  document.querySelectorAll('[data-flag]').forEach(el => {
    const flag = el.dataset.flag;
    if (!flag) return;

    // 23 août 2026 : ignorer un champ actuellement masqué par mode_only
    // (mode actif différent) -- même correctif que validateRequiredFields()
    // ci-dessous, évite qu'une valeur laissée dans un champ caché (ex.
    // rempli en mode manuel, formulaire ensuite basculé sur auto) ne
    // fuite dans la commande d'un autre mode.
    const modeOnlyGroup = el.closest('[data-mode-only]');
    if (modeOnlyGroup && modeActive) {
      const allowedModes = modeOnlyGroup.dataset.modeOnly.split(',');
      if (!allowedModes.includes(modeActive.dataset.value)) {
        return;
      }
    }

    if (el.type === 'checkbox') {
      if (el.checked) args.push(flag);
    } else {
      const val = el.value;
      if (val !== '' && val !== null && val !== undefined) {
        args.push(flag, val);
      }
    }
  });

  // Groupes multi_select (chips) — un flag suivi de toutes les valeurs
  // actives (argparse nargs='+' côté script). Rien n'est envoyé si aucune
  // chip n'est sélectionnée (comportement "libre choix par défaut").
  document.querySelectorAll('[data-multi-flag]').forEach(group => {
    const flag = group.dataset.multiFlag;
    const values = Array.from(group.querySelectorAll('.yaml-chip.active')).map(c => c.dataset.value);
    if (values.length > 0) {
      args.push(flag, ...values);
    }
  });

  return args;
}

// ── Exécution script ──────────────────────────────

/**
 * Valide les groupes "au moins un requis" (required_one_of) avant de
 * lancer un script. Ajouté le 26 juillet 2026 -- cas réel remonté par
 * David : scan_geographie_complet.py plante ("error: one of the arguments
 * --scenario --all is required", code 2) si ni "Tous les scénarios" ni un
 * scénario précis n'est sélectionné. Le formulaire ne bloquait rien avant
 * l'envoi -- vérifié, même défaut dans 9 autres entrées du panneau
 * (mutually_exclusive_with gère seulement "jamais les deux ensemble",
 * jamais "au moins un"). Deux variantes trouvées côté Python, mais même
 * symptôme cliente : un vrai argparse mutually_exclusive_group(required=True)
 * dans 8 scripts (check_zones_coherence.py, generate_journaux.py, etc.),
 * un parser.error()/sys.exit() manuel équivalent dans enrich_minimal.py et
 * enrich_geographie_recursive.py.
 *
 * required_one_of : liste de groupes au niveau du script, chaque groupe une
 * liste de flags dont au moins un doit être actif (checkbox cochée ou
 * select/texte non vide) -- generer_zones_topdown.py en a deux distincts
 * (portée scenario/all + mode review/apply).
 */
/**
 * Un flag GUI a-t-il une valeur active : checkbox cochée, ou
 * select/texte/slug_select non vide. Factorisé le 26 juillet 2026 -- utilisé
 * par les 3 validations pré-lancement ci-dessous (required_one_of, required,
 * required_if).
 */
function isFlagActive(flag) {
  const el = document.querySelector(`#form-body [data-flag="${flag}"]`);
  if (!el) return false;
  if (el.type === 'checkbox') return el.checked;
  return el.value !== '' && el.value !== null && el.value !== undefined;
}

function validateRequiredGroups(script) {
  const groups = script.required_one_of || [];
  return groups.filter(group => !group.some(isFlagActive));
}

/**
 * Audit du panneau du 26 juillet 2026 (à la demande de David, en plus des
 * doublons -- aucun trouvé au-delà de ceux déjà tranchés le 25 juillet) :
 * en cherchant si la logique de `scan_geographie_complet` s'appliquait
 * ailleurs, deux AUTRES formes du même bug de fond (rien ne bloque le GUI
 * avant un plantage argparse) sont ressorties, dans des scripts qui
 * n'avaient pas de `mutually_exclusive_with` donc invisibles au grep de la
 * première passe :
 *
 * 1. Champ requis seul, inconditionnel (argparse `required=True`, ou
 *    `sys.exit()` manuel équivalent) -- ex. `--scenario` de
 *    `reparenter_sous_zones_orphelines.py`. Le champ `required: true`
 *    existait déjà dans scripts_config.json (une seule entrée s'en servait,
 *    `build_geographie`) mais n'était QUE cosmétique (ajoute juste " *" au
 *    label dans renderOption(), jamais vérifié avant le clic Lancer).
 *
 * 2. Champ requis conditionnel : requis seulement si un AUTRE champ est
 *    rempli -- ex. `--raison-suspicion` requis avec `--zone-suspecte`
 *    (zoning_topdown.py), `--type` requis avec `--slug` (undo_custom.py).
 *    Nouveau champ `required_if` : nom du flag déclencheur.
 */
function validateRequiredFields(script) {
  const manquants = [];
  // 23 août 2026 : un champ caché par mode_only (mode actif différent) ne
  // doit jamais être exigé au lancement -- updateModeOnlyVisibility() le
  // masque visuellement mais ne touchait jamais à cette validation,
  // laissant un champ invisible bloquer le formulaire (trouvé sur
  // inject_journaliste_custom.py, mode auto, --zone-slug mode_only:
  // "manuel"). Même lecture de l'onglet actif que updateModeOnlyVisibility,
  // pour rester cohérent.
  const activeTab = document.querySelector('.mode-tab.active');
  const activeMode = activeTab ? activeTab.dataset.value : null;

  for (const opt of script.options || []) {
    if (opt.mode_only) {
      const allowedModes = Array.isArray(opt.mode_only) ? opt.mode_only : [opt.mode_only];
      if (activeMode && !allowedModes.includes(activeMode)) {
        continue;
      }
    }
    if (opt.required && !isFlagActive(opt.flag)) {
      manquants.push(opt.label || opt.flag);
    }
    if (opt.required_if && isFlagActive(opt.required_if) && !isFlagActive(opt.flag)) {
      manquants.push(`${opt.label || opt.flag} (requis avec ${opt.required_if})`);
    }
  }
  return manquants;
}

/**
 * Sauvegarde automatique avant Lancer (ajouté le 31 juillet 2026, suite à un
 * cas réel : David a rempli le formulaire config_fields de `generate.py`,
 * cliqué directement sur Lancer sans passer par "Sauvegarder", et le script
 * a lu l'ancien config.yaml sur disque -- le formulaire à l'écran n'était
 * jamais persisté avant l'exécution. Corrigé en sauvegardant automatiquement
 * tout panneau `.yaml-form-panel` ouvert dans #form-body juste avant de
 * lancer, en réutilisant les mêmes fonctions que les boutons "Sauvegarder"
 * manuels (_saveYamlForm pour le formulaire guidé, /api/yaml pour le mode
 * "Édition brute"). Ne concerne que le(s) panneau(x) du script actif --
 * #form-body est reconstruit à chaque changement de script, donc aucun
 * panneau d'un autre script ne peut être capté par erreur.
 *
 * Correctif du 11 août 2026 : un panneau `config_fields_mode` (ex. le
 * formulaire queue.yaml de `create_entities`, réservé au mode Custom)
 * reste dans le DOM même quand un autre mode (auto-suggest, auto) est
 * actif -- updateModeOnlyVisibility() le cache seulement visuellement
 * (display:none), il n'est jamais retiré de #form-body. Sans ce filtre,
 * cliquer sur Lancer en mode auto-suggest sauvegardait quand même le
 * formulaire Custom resté ouvert/vu plus tôt dans la session -- vide s'il
 * n'avait jamais été rempli -- écrasant silencieusement le fichier YAML
 * (cas réel vécu : queue.yaml vidé juste après un run auto-suggest ayant
 * pourtant réussi à y écrire 5 idées). On ignore désormais tout panneau
 * dont le mode déclaré ne correspond pas à l'onglet actif, même mode
 * (case, priorité au check) que updateModeOnlyVisibility().
 */
async function saveOpenConfigForms() {
  const activeTab = document.querySelector('.mode-tab.active');
  const activeMode = activeTab ? activeTab.dataset.value : null;

  const panels = document.querySelectorAll('#form-body .yaml-form-panel');
  for (const wrapper of panels) {
    if (activeMode && wrapper.dataset.modeOnly) {
      const allowedModes = wrapper.dataset.modeOnly.split(',');
      if (!allowedModes.includes(activeMode)) continue;
    }
    const yamlPath  = wrapper.dataset.yamlPath;
    const rawZone   = wrapper.querySelector('.yaml-raw-zone');
    const statusMsg = wrapper.querySelector('.yaml-status-msg');
    const isRawMode = rawZone && rawZone.style.display !== 'none';

    if (isRawMode) {
      const rawTextarea = wrapper.querySelector('.yaml-raw-zone .yaml-edit');
      try {
        const res = await fetch('/api/yaml', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: yamlPath, content: rawTextarea.value }),
        });
        const data = await res.json();
        if (!data.ok) return { ok: false, error: data.error };
      } catch (e) {
        return { ok: false, error: e.message };
      }
    } else {
      await _saveYamlForm(wrapper, yamlPath, statusMsg);
      // _saveYamlForm affiche déjà l'erreur dans statusMsg mais ne renvoie
      // rien -- on relit la classe posée par showYamlStatus() (préfixe
      // yaml-status-, voir sa définition plus haut) pour savoir si Lancer
      // doit être bloqué.
      if (statusMsg && statusMsg.classList.contains('yaml-status-error')) {
        return { ok: false, error: statusMsg.textContent };
      }
    }
  }
  return { ok: true };
}

document.getElementById('btn-run').addEventListener('click', async () => {
  if (!State.activeScriptId) return;

  // Cas spécial : generate_manual utilise ses propres boutons
  const script = State.scripts.find(s => s.id === State.activeScriptId);
  if (script && script.mode === 'manual_steps') return;

  const groupesManquants = validateRequiredGroups(script);
  const champsManquants = validateRequiredFields(script);
  if (groupesManquants.length > 0 || champsManquants.length > 0) {
    const detailGroupes = groupesManquants.map(g => g.join(' ou '));
    const detail = [...detailGroupes, ...champsManquants].join('  --  ');
    appendLog(`✗ Choix requis avant de lancer : ${detail}`, 'error');
    setLogStatus('error', 'Choix requis');
    return;
  }

  const saveResult = await saveOpenConfigForms();
  if (!saveResult.ok) {
    appendLog(`✗ Échec de la sauvegarde automatique avant lancement : ${saveResult.error}`, 'error');
    setLogStatus('error', 'Sauvegarde échouée');
    return;
  }

  const args = collectArgs();
  runScript(State.activeScriptId, args);
});

document.getElementById('btn-stop').addEventListener('click', async () => {
  if (!State.currentRunId) return;
  try {
    await fetch(`/api/stop/${State.currentRunId}`, { method: 'POST' });
  } catch (e) {}
});

async function runScript(scriptId, args) {
  if (!scriptId) return;

  clearLog();
  setRunning(true);

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script_id: scriptId, args, force_llm_override: !!State.forceLlmOverride }),
    });

    if (!res.ok) {
      const err = await res.json();
      appendLog(`[ERROR] ${err.error || 'Erreur inconnue'}`, 'error');
      setRunning(false);
      return;
    }

    const data = await res.json();
    State.currentRunId = data.run_id;
    startSSE(data.run_id, scriptId);

  } catch (e) {
    appendLog(`[ERROR] Impossible de contacter le serveur : ${e.message}`, 'error');
    setRunning(false);
  }
}

async function checkActiveRun() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (data.active) {
      State.currentRunId = data.run_id;
      setRunning(true);
      startSSE(data.run_id, data.script_id);
    }
  } catch (e) {}
}

// ── SSE streaming ─────────────────────────────────

function startSSE(runId, scriptId) {
  if (State.sseSource) State.sseSource.close();

  const es = new EventSource(`/api/stream/${runId}`);
  State.sseSource = es;

  const cursor = document.getElementById('log-cursor');
  if (cursor) cursor.style.display = 'inline-block';

  es.onmessage = (e) => {
    const line = e.data;

    if (line.startsWith('[DONE]')) {
      const codeMatch = line.match(/code=(-?\d+)/);
      const rc = codeMatch ? parseInt(codeMatch[1]) : 0;
      appendLog(rc === 0 ? '✓ Terminé avec succès' : `✗ Terminé avec code ${rc}`, rc === 0 ? 'done' : 'error');
      setRunning(false, rc === 0 ? 'ok' : 'error');
      State.sessionRan.add(scriptId);
      es.close();
      return;
    }

    appendLog(line, classifyLine(line));
  };

  es.onerror = () => {
    appendLog('[ERROR] Connexion SSE perdue', 'error');
    setRunning(false, 'error');
    es.close();
  };
}

function classifyLine(line) {
  if (/\[DONE\]/.test(line))             return 'done';
  if (/\[llm\]/.test(line))              return 'llm';
  if (/\[WARN\]\[journal\]/.test(line))  return 'journal';
  if (/✓|OK\b|success/i.test(line))     return 'ok';
  if (/⚠|WARNING|\[WARN\]/i.test(line)) return 'warn';
  if (/ERROR|✗|\[ERROR\]/i.test(line))  return 'error';
  return 'default';
}

// ── Log panel ─────────────────────────────────────

function appendLog(text, cls = 'default') {
  const out = document.getElementById('log-output');
  const line = document.createElement('span');
  line.className = `log-line ${cls}`;
  line.textContent = text;
  out.appendChild(line);
  out.appendChild(document.createTextNode('\n'));
  out.scrollTop = out.scrollHeight;
}

function clearLog() {
  const out = document.getElementById('log-output');
  out.innerHTML = '<span class="cursor-blink" id="log-cursor"></span>';
}

document.getElementById('log-clear').addEventListener('click', (e) => {
  e.preventDefault();
  clearLog();
  setLogStatus('idle', '—');
});

// Réinitialisation des champs partagés après un lancement -- ajouté le
// 2 août 2026 (retour de David) : Thématique/Ligne éditoriale/Longueur/
// Angle ne se réinitialisaient jamais entre deux clics sur "Lancer" tant
// qu'on restait sur le même panneau -- comportement HTML normal (un champ
// garde sa valeur tant qu'on ne le touche pas), mais qui a fait générer
// un article sur une thématique choisie lors d'un essai précédent, sans
// que David s'en aperçoive. Portée volontairement limitée à ces 4 champs
// partagés (pas --forcer-type/--forcer-slug/--scenario/--zone-slug, que
// David veut au contraire pouvoir garder pour itérer sur le même élément
// sans tout re-choisir à chaque essai).
const CHAMPS_A_REINITIALISER = ['--thematique', '--ligne-editoriale', '--article-longueur', '--article-angle-specifique'];

function reinitialiserChampsPartages() {
  CHAMPS_A_REINITIALISER.forEach(flag => {
    const el = document.querySelector(`[data-flag="${flag}"]`);
    if (!el) return;
    el.value = el.dataset.defaultValue || '';
  });
}

function setRunning(isRunning, result = null) {
  const btnRun  = document.getElementById('btn-run');
  const btnStop = document.getElementById('btn-stop');

  if (isRunning) {
    btnRun.disabled = true;
    btnStop.classList.add('visible');
    setLogStatus('running', 'En cours…');
  } else {
    btnRun.disabled = false;
    btnStop.classList.remove('visible');
    State.currentRunId = null;
    const cursor = document.getElementById('log-cursor');
    if (cursor) cursor.style.display = 'none';
    if (result === 'ok')    setLogStatus('ok',    'Succès');
    else if (result === 'error') setLogStatus('error', 'Erreur');
    else                         setLogStatus('idle',  '—');
    reinitialiserChampsPartages();
  }
}

function setLogStatus(cls, text) {
  const el = document.getElementById('log-status');
  el.className = 'log-status ' + cls;
  el.textContent = text;
}

// ── Tableau de bord ───────────────────────────────

async function loadDashboard() {
  const container = document.getElementById('tab-dashboard');
  container.innerHTML = '<h2>Tableau de bord</h2><div class="dashboard-grid" id="dashboard-grid"><div class="stat-card"><div class="card-title">Chargement…</div></div></div>';

  try {
    const res = await fetch('/api/dashboard');
    const data = await res.json();
    renderDashboard(data);
  } catch (e) {
    document.getElementById('dashboard-grid').innerHTML = '<div class="stat-card"><div class="card-title" style="color:var(--error)">Erreur chargement dashboard</div><div class="card-sub">Vérifiez vault_root dans Config</div></div>';
    return;
  }

  // Charger zones manquantes séparément (n'affecte pas le reste si ça échoue)
  try {
    const res2 = await fetch('/api/zones/manquantes');
    const data2 = await res2.json();
    renderZonesManquantes(data2);
  } catch (e) {
    // Silencieux — section optionnelle
  }
}

function statCard(title, value, sub, extraClass) {
  return '<div class="stat-card ' + (extraClass || '') + '">' +
    '<div class="card-title">' + title + '</div>' +
    '<div class="card-value">' + value + '</div>' +
    '<div class="card-sub">' + (sub || '') + '</div>' +
    '</div>';
}

function renderDashboard(data) {
  const grid = document.getElementById('dashboard-grid');
  if (!data.vault_ok) {
    grid.innerHTML = `<div class="stat-card warn-card" style="grid-column:1/-1">
      <div class="card-title">Configuration requise</div>
      <div class="card-sub">Renseignez vault_root et pipeline_dir dans l'onglet Config.</div>
    </div>`;
    return;
  }

  const cards = [];

  // Modèle par défaut — depuis le 11 juillet 2026, ce n'est plus "le" LLM
  // actif : chaque script résout son propre modèle via le routing par tier
  // (llm_client.TASK_TIER_DEFAULTS), sauf si le toggle "Forcer ce modèle" est
  // coché pour un lancement précis. Ce que data.llm reflète ici est la
  // valeur par défaut de gui/config.json, utilisée uniquement quand le
  // toggle est actif — pas le modèle qui tourne réellement par défaut.
  const llm = data.llm || {};
  cards.push(statCard('Modèle si forcé',
    `${(llm.provider||'—').charAt(0).toUpperCase()+(llm.provider||'').slice(1)}`,
    (llm.model || '—') + ' · sinon : routing par tier'));

  // Instances
  const inst = data.instances || {};
  const instSub = Object.entries(inst.by_scenario || {})
    .sort((a,b) => b[1]-a[1])
    .map(([sc, n]) => `${sc}: ${n}`).join(' · ') || '—';
  cards.push(statCard('Instances', inst.total ?? 0, instSub));

  // Entités
  const ent = data.entites || {};
  cards.push(statCard('Entités (archétypes)', ent.total ?? 0, 'dans _entities_list.json'));

  // Enrichissement
  const enr = data.enrichissement || {};
  const enrichPct = enr.total > 0 ? Math.round((enr.enrichi / enr.total) * 100) : 0;
  cards.push(statCard(
    'Enrichissement',
    `${enr.enrichi ?? 0} / ${enr.total ?? 0}`,
    `${enrichPct}% enrichis · ${enr.minimal ?? 0} minimal restants`,
    enr.minimal > 0 ? 'warn-card' : ''
  ));

  // Articles
  const art = data.articles || {};
  const byLigne = art.by_ligne || {};
  const ligneSub = Object.entries(byLigne)
    .map(([k, v]) => `${k}: ${v}`).join(' · ') || '—';
  cards.push(statCard('Articles générés', art.total ?? 0, ligneSub,
    art.total === 0 ? 'warn-card' : ''));

  // Journaux
  const jour = data.journaux || {};
  const jourSub = jour.missing
    ? '⚠ journaux.yaml absent'
    : Object.entries(jour.by_scenario || {}).map(([sc,n]) => `${sc}: ${n}`).join(' · ') || '—';
  cards.push(statCard('Journaux locaux', jour.total ?? 0, jourSub,
    jour.missing ? 'warn-card' : ''));

  // Zones géographiques N1
  const zones = data.zones || {};
  const zonesSub = Object.entries(zones.by_scenario || {})
    .map(([sc, n]) => `${sc}: ${n}`).join(' · ') || '—';
  cards.push(statCard('Zones géo (Niveau 1)', zones.total ?? 0, zonesSub));

  // Revue
  const rc = data.review_count ?? 0;
  cards.push(statCard('Items en revue', rc,
    rc > 0 ? '→ voir onglet Revue' : 'Aucun item en attente',
    rc > 0 ? 'warn-card' : ''));

  // Zones manquantes — placeholder, peuplé après le fetch séparé
  cards.push('<div class="stat-card" id="zones-manquantes-card"><div class="card-title">Zones manquantes</div><div class="card-value">…</div><div class="card-sub">Chargement</div></div>');

  grid.innerHTML = cards.join('');

  // Thématiques — tableau séparé
  const th = data.thematiques || {};
  const thEntries = Object.entries(th);
  if (thEntries.length > 0) {
    const container = document.getElementById('tab-dashboard');
    // Supprimer l'ancien tableau si présent
    const old = container.querySelector('.thematiques-section');
    if (old) old.remove();

    const section = document.createElement('div');
    section.className = 'thematiques-section';
    section.innerHTML = `
      <div class="tab-page-title" style="margin-top:24px">Thématiques</div>
      <table class="review-table">
        <thead><tr><th>Thématique</th><th style="text-align:right">Articles</th></tr></thead>
        <tbody>
          ${thEntries.slice(0, 20).map(([th, n]) =>
            `<tr><td>${th}</td><td style="text-align:right;color:var(--text)">${n}</td></tr>`
          ).join('')}
        </tbody>
      </table>`;
    container.appendChild(section);
  }

  // Badge nav revue
  const badge = document.getElementById('review-nav-badge');
  if (badge) {
    badge.textContent = rc;
    badge.style.display = rc > 0 ? 'inline-block' : 'none';
  }
}


// ── Onglet Revue ──────────────────────────────────────────────────────────────

async function loadReview() {
  const container = document.getElementById('tab-review');
  container.innerHTML = '<div class="tab-page-title">Revue</div><div style="color:var(--text-muted);font-size:12px">Chargement…</div>';

  try {
    const res = await fetch('/api/review');
    const data = await res.json();
    renderReview(data.items || [], container);

    // Mettre à jour badge nav
    const badge = document.getElementById('review-nav-badge');
    if (badge) {
      const n = data.total || 0;
      badge.textContent = n;
      badge.style.display = n > 0 ? 'inline-block' : 'none';
    }
  } catch (e) {
    container.innerHTML = '<div class="tab-page-title">Revue</div><div style="color:var(--error)">Erreur chargement</div>';
  }
}

function renderReview(items, container) {
  // Header
  const titleHtml = `<div class="tab-page-title">Revue
    ${items.length > 0
      ? `<span style="color:var(--warn);font-size:11px;font-weight:400;margin-left:8px">${items.length} item${items.length > 1 ? 's' : ''}</span>`
      : ''
    }
  </div>`;

  if (!items.length) {
    container.innerHTML = titleHtml + '<div class="review-empty">✓ Aucun item en attente de revue.</div>';
    return;
  }

  // Grouper par source
  const groups = {
    enrich:      { label: 'Enrichissement',   items: [] },
    events:      { label: 'Événements',        items: [] },
    localisation:{ label: 'Localisation',      items: [] },
  };

  items.forEach(item => {
    const g = groups[item.source];
    if (g) g.items.push(item);
    else groups[item.source] = { label: item.source, items: [item] };
  });

  let html = titleHtml;

  for (const [key, group] of Object.entries(groups)) {
    if (!group.items.length) continue;

    html += `<div class="review-group">
      <div class="review-group-title">
        <span class="source-badge source-${key}">${group.label}</span>
        <span class="review-group-count">${group.items.length} item${group.items.length > 1 ? 's' : ''}</span>
      </div>
      <table class="review-table">
        <thead>
          <tr>
            <th>Slug</th>
            <th>Scénario</th>
            <th>Détail</th>
          </tr>
        </thead>
        <tbody>
          ${group.items.map(item => `
            <tr>
              <td style="font-family:var(--font-mono);font-size:11px;color:var(--text)">${item.slug || '—'}</td>
              <td style="color:var(--text-dim)">${item.scenario || '—'}</td>
              <td style="color:var(--text-muted);font-size:11px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${(item.error||'').replace(/"/g,"'")}">${item.error || '—'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>`;
  }

  container.innerHTML = html;
}


// ── Onglet Config ─────────────────────────────────

async function loadConfigForm() {
  const cfg = State.config || {};
  const llm = cfg.llm || {};

  // Remplir les champs
  setVal('cfg-vault-root', cfg.vault_root || '');
  setVal('cfg-pipeline-dir', cfg.pipeline_dir || '');
  setVal('cfg-default-scenario', cfg.default_scenario || '');
  setVal('cfg-llm-provider', llm.provider || 'mistral');
  setVal('cfg-llm-model-mistral', llm.model_mistral || '');
  setVal('cfg-llm-model-claude', llm.model_claude || '');

  // Populer le select scénarios
  const scenSel = document.getElementById('cfg-default-scenario');
  if (scenSel) {
    scenSel.innerHTML = (cfg.scenarios || [])
      .map(s => `<option value="${s}" ${s === cfg.default_scenario ? 'selected' : ''}>${s}</option>`)
      .join('');
  }

  // Cacher les messages
  const msg = document.getElementById('cfg-message');
  if (msg) { msg.className = 'config-msg'; msg.textContent = ''; }
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

document.getElementById('cfg-save')?.addEventListener('click', async () => {
  const updated = {
    vault_root:       document.getElementById('cfg-vault-root')?.value || '',
    pipeline_dir:     document.getElementById('cfg-pipeline-dir')?.value || '',
    default_scenario: document.getElementById('cfg-default-scenario')?.value || '',
    llm: {
      provider:      document.getElementById('cfg-llm-provider')?.value || 'mistral',
      model_mistral: document.getElementById('cfg-llm-model-mistral')?.value || '',
      model_claude:  document.getElementById('cfg-llm-model-claude')?.value || '',
    }
  };

  try {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updated),
    });
    const data = await res.json();

    if (data.ok) {
      // Recharger config locale
      await loadConfig();
      showConfigMsg('ok', '✓ Config sauvegardée');
      // Mettre à jour le sélecteur LLM
      buildLLMSelector();
    } else {
      showConfigMsg('error', `Erreur : ${data.error || 'inconnue'}`);
    }
  } catch (e) {
    showConfigMsg('error', `Erreur réseau : ${e.message}`);
  }
});

document.getElementById('cfg-test-path')?.addEventListener('click', async () => {
  const vaultRoot    = document.getElementById('cfg-vault-root')?.value || '';
  const pipelineDir  = document.getElementById('cfg-pipeline-dir')?.value || '';
  showConfigMsg('ok', `vault_root : ${vaultRoot || '(vide)'} · pipeline_dir : ${pipelineDir || '(vide)'}\nLa validation réelle se fait côté serveur.`);
});

function showConfigMsg(cls, text) {
  const msg = document.getElementById('cfg-message');
  if (!msg) return;
  msg.className = `config-msg ${cls}`;
  msg.textContent = text;
  setTimeout(() => { if (msg) msg.className = 'config-msg'; }, 4000);
}

// ── Initialisation event listeners ───────────────

function initEventListeners() {
  // Pas de listeners supplémentaires nécessaires — tout est dans les fonctions ci-dessus
}

// ══════════════════════════════════════════════════
// YAML VIEWER / EDITOR
// ══════════════════════════════════════════════════

// Point d'entrée : appelé depuis renderFormBody après les options standard
async function renderYamlPanels(script) {
  const yamlFiles = script.yaml_files;
  if (!yamlFiles || yamlFiles.length === 0) return;

  const body = document.getElementById('form-body');

  for (const yf of yamlFiles) {
    // Si ce fichier YAML a des config_fields dans le script → formulaire guidé
    if (script.config_file === yf.path && script.config_fields) {
      const panel = await buildYamlFormPanel(yf, script.config_fields, script);
      if (script.config_fields_mode) panel.dataset.modeOnly = script.config_fields_mode;
      body.appendChild(panel);
    } else {
      const panel = await buildYamlPanel(yf);
      body.appendChild(panel);
    }
  }
}

async function buildYamlPanel(yf) {
  const wrapper = document.createElement('div');
  wrapper.className = 'yaml-panel';
  wrapper.dataset.yamlPath = yf.path;
  wrapper.dataset.readonly = yf.readonly ? 'true' : 'false';

  // Header
  const header = document.createElement('div');
  header.className = 'yaml-panel-header';

  const titleRow = document.createElement('div');
  titleRow.className = 'yaml-panel-title-row';

  const titleEl = document.createElement('span');
  titleEl.className = 'yaml-panel-title';
  titleEl.textContent = yf.label;

  const actions = document.createElement('div');
  actions.className = 'yaml-panel-actions';

  if (!yf.readonly) {
    const btnEdit = document.createElement('button');
    btnEdit.className = 'yaml-btn yaml-btn-edit';
    btnEdit.textContent = 'Éditer';
    btnEdit.addEventListener('click', () => toggleYamlEdit(wrapper, true));

    const btnSave = document.createElement('button');
    btnSave.className = 'yaml-btn yaml-btn-save';
    btnSave.textContent = 'Sauvegarder';
    btnSave.style.display = 'none';
    btnSave.addEventListener('click', () => saveYamlContent(wrapper, yf.path));

    const btnCancel = document.createElement('button');
    btnCancel.className = 'yaml-btn yaml-btn-cancel';
    btnCancel.textContent = 'Annuler';
    btnCancel.style.display = 'none';
    btnCancel.addEventListener('click', () => toggleYamlEdit(wrapper, false));

    actions.appendChild(btnEdit);
    actions.appendChild(btnSave);
    actions.appendChild(btnCancel);
  } else {
    const badge = document.createElement('span');
    badge.className = 'yaml-readonly-badge';
    badge.textContent = 'lecture seule';
    actions.appendChild(badge);
  }

  titleRow.appendChild(titleEl);
  titleRow.appendChild(actions);
  header.appendChild(titleRow);

  // Message statut
  const statusMsg = document.createElement('div');
  statusMsg.className = 'yaml-status-msg';
  statusMsg.style.display = 'none';
  header.appendChild(statusMsg);

  wrapper.appendChild(header);

  // Zone contenu (lecture)
  const viewEl = document.createElement('pre');
  viewEl.className = 'yaml-view';
  viewEl.textContent = 'Chargement…';
  wrapper.appendChild(viewEl);

  // Zone édition (textarea, caché par défaut)
  const editEl = document.createElement('textarea');
  editEl.className = 'yaml-edit';
  editEl.style.display = 'none';
  editEl.spellcheck = false;
  wrapper.appendChild(editEl);

  // Charger le contenu
  await loadYamlContent(wrapper, yf.path);

  return wrapper;
}

async function loadYamlContent(wrapper, yamlPath) {
  const viewEl = wrapper.querySelector('.yaml-view');
  const editEl = wrapper.querySelector('.yaml-edit');

  try {
    const res = await fetch(`/api/yaml?path=${encodeURIComponent(yamlPath)}`);
    const data = await res.json();

    if (data.error) {
      viewEl.textContent = `Erreur : ${data.error}`;
      viewEl.className = 'yaml-view yaml-error';
      return;
    }

    if (!data.exists) {
      viewEl.textContent = '(fichier absent)';
      viewEl.className = 'yaml-view yaml-absent';
      editEl.value = '';
    } else {
      viewEl.textContent = data.content;
      viewEl.className = 'yaml-view';
      editEl.value = data.content;
    }
  } catch (e) {
    viewEl.textContent = `Erreur réseau : ${e.message}`;
    viewEl.className = 'yaml-view yaml-error';
  }
}

function toggleYamlEdit(wrapper, editing) {
  const viewEl   = wrapper.querySelector('.yaml-view');
  const editEl   = wrapper.querySelector('.yaml-edit');
  const btnEdit   = wrapper.querySelector('.yaml-btn-edit');
  const btnSave   = wrapper.querySelector('.yaml-btn-save');
  const btnCancel = wrapper.querySelector('.yaml-btn-cancel');

  if (editing) {
    // Copier le contenu affiché dans le textarea
    editEl.value = viewEl.textContent;
    viewEl.style.display   = 'none';
    editEl.style.display   = 'block';
    if (btnEdit)   btnEdit.style.display   = 'none';
    if (btnSave)   btnSave.style.display   = 'inline-block';
    if (btnCancel) btnCancel.style.display = 'inline-block';
    editEl.focus();
  } else {
    viewEl.style.display   = 'block';
    editEl.style.display   = 'none';
    if (btnEdit)   btnEdit.style.display   = 'inline-block';
    if (btnSave)   btnSave.style.display   = 'none';
    if (btnCancel) btnCancel.style.display = 'none';
  }
}

async function saveYamlContent(wrapper, yamlPath) {
  const editEl   = wrapper.querySelector('.yaml-edit');
  const viewEl   = wrapper.querySelector('.yaml-view');
  const statusEl = wrapper.querySelector('.yaml-status-msg');
  const btnSave  = wrapper.querySelector('.yaml-btn-save');

  const content = editEl.value;

  if (btnSave) btnSave.disabled = true;

  try {
    const res = await fetch('/api/yaml', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: yamlPath, content }),
    });
    const data = await res.json();

    if (data.ok) {
      // Mettre à jour la vue lecture
      viewEl.textContent = content;
      toggleYamlEdit(wrapper, false);
      showYamlStatus(statusEl, 'ok', '✓ Sauvegardé');
    } else {
      showYamlStatus(statusEl, 'error', `Erreur : ${data.error}`);
    }
  } catch (e) {
    showYamlStatus(statusEl, 'error', `Erreur réseau : ${e.message}`);
  } finally {
    if (btnSave) btnSave.disabled = false;
  }
}

function showYamlStatus(el, cls, text) {
  el.className = `yaml-status-msg yaml-status-${cls}`;
  el.textContent = text;
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 3000);
}

// ══════════════════════════════════════════════════
// YAML FORM PANEL — formulaires guidés
// ══════════════════════════════════════════════════

const THEMATIQUES = [
  'actualites_a_la_une','politique','economie_finance',
  'environnement_climat','sciences_technologies','societe',
  'culture','international','musique','sports','faits_divers',
  'opinions_editoriaux','lifestyle_art_de_vivre','sante',
  'education','histoire_patrimoine','medias_communication',
  'religion_spiritualite','petites_annonces_services','meteo'
];

/**
 * Construit un panel formulaire guidé pour un fichier YAML avec config_fields.
 * Remplace le textarea brut par des inputs typés. Un toggle "Édition brute"
 * bascule vers le textarea classique.
 */
async function buildYamlFormPanel(yf, configFields, script) {
  const wrapper = document.createElement('div');
  wrapper.className = 'yaml-panel yaml-form-panel';
  wrapper.dataset.yamlPath = yf.path;

  // ── Header ──
  const header = document.createElement('div');
  header.className = 'yaml-panel-header';

  const titleRow = document.createElement('div');
  titleRow.className = 'yaml-panel-title-row';

  const titleEl = document.createElement('span');
  titleEl.className = 'yaml-panel-title';
  titleEl.textContent = yf.label;

  const actions = document.createElement('div');
  actions.className = 'yaml-panel-actions';

  const isQueueMode = yf.path.includes('queue.yaml');
  const btnSave = document.createElement('button');
  btnSave.className = 'yaml-btn yaml-btn-save';
  btnSave.textContent = isQueueMode ? 'Ajouter à la queue' : 'Sauvegarder';

  const btnRaw = document.createElement('button');
  btnRaw.className = 'yaml-btn';
  btnRaw.textContent = 'Édition brute';
  btnRaw.title = 'Basculer vers le textarea YAML brut';

  actions.appendChild(btnSave);
  actions.appendChild(btnRaw);
  titleRow.appendChild(titleEl);
  titleRow.appendChild(actions);
  header.appendChild(titleRow);

  const statusMsg = document.createElement('div');
  statusMsg.className = 'yaml-status-msg';
  statusMsg.style.display = 'none';
  header.appendChild(statusMsg);

  wrapper.appendChild(header);

  // ── Charger le YAML actuel ──
  let currentValues = {};
  try {
    const res = await fetch(`/api/yaml?path=${encodeURIComponent(yf.path)}`);
    const data = await res.json();
    if (data.exists && data.content) {
      currentValues = _parseYamlSimple(data.content);
    }
    // Stocker le contenu brut pour le textarea de fallback
    wrapper._rawContent = data.content || '';
  } catch (e) {
    wrapper._rawContent = '';
  }

  // ── Zone formulaire guidé ──
  const formZone = document.createElement('div');
  formZone.className = 'yaml-form-zone';

  for (const field of configFields) {
    const group = await _buildFormField(field, currentValues, script);
    formZone.appendChild(group);
  }

  wrapper.appendChild(formZone);

  // ── Zone édition brute (cachée par défaut) ──
  const rawZone = document.createElement('div');
  rawZone.className = 'yaml-raw-zone';
  rawZone.style.display = 'none';

  const rawTextarea = document.createElement('textarea');
  rawTextarea.className = 'yaml-edit';
  rawTextarea.spellcheck = false;
  rawTextarea.value = wrapper._rawContent;
  rawZone.appendChild(rawTextarea);

  const rawSaveBtn = document.createElement('button');
  rawSaveBtn.className = 'yaml-btn yaml-btn-save';
  rawSaveBtn.textContent = 'Sauvegarder (brut)';
  rawSaveBtn.style.marginTop = '8px';
  rawZone.appendChild(rawSaveBtn);

  wrapper.appendChild(rawZone);

  // ── Events ──
  let isRawMode = false;

  btnRaw.addEventListener('click', async () => {
    isRawMode = !isRawMode;
    formZone.style.display = isRawMode ? 'none' : 'block';
    rawZone.style.display   = isRawMode ? 'block' : 'none';
    btnRaw.textContent      = isRawMode ? 'Formulaire guidé' : 'Édition brute';
    btnSave.style.display   = isRawMode ? 'none' : '';

    // Corrige un bug trouvé le 26 juillet 2026 (cas réel : une entrée
    // ajoutée via le formulaire guidé s'est fait écraser) : `wrapper._rawContent`
    // n'était capturé QU'UNE FOIS, au chargement initial du panneau -- si le
    // fichier avait changé depuis (ex. un ajout via le formulaire guidé
    // pendant la même visite du script), "Édition brute" affichait un
    // instantané périmé, et cliquer "Sauvegarder (brut)" écrasait les
    // changements plus récents avec ce vieux contenu. On recharge donc
    // depuis le disque à chaque passage en mode brut.
    if (isRawMode) {
      rawTextarea.value = 'Chargement…';
      try {
        const res = await fetch(`/api/yaml?path=${encodeURIComponent(yf.path)}`);
        const data = await res.json();
        wrapper._rawContent = data.content || '';
      } catch (e) {
        // Garde l'ancien contenu si le rechargement échoue -- mieux qu'un
        // textarea vide, mais on ne masque pas le souci pour autant.
        showYamlStatus(statusMsg, 'error', `Rechargement échoué, contenu peut-être périmé : ${e.message}`);
      }
      rawTextarea.value = wrapper._rawContent;
    }
  });

  btnSave.addEventListener('click', async () => {
    if (btnSave.disabled) return;  // garde-fou anti double-clic
    btnSave.disabled = true;
    const originalLabel = btnSave.textContent;
    try {
      if (isQueueMode) {
        await _appendYamlQueue(wrapper, yf.path, statusMsg);
      } else {
        await _saveYamlForm(wrapper, yf.path, statusMsg);
      }
    } finally {
      btnSave.disabled = false;
      btnSave.textContent = originalLabel;
    }
  });

  // Rafraîchir les slug_select de type zones quand le scénario change
  wrapper.addEventListener('change', async (e) => {
    const el = e.target;
    if (el.dataset.formKey === 'scenario' || el.dataset.formKey === 'scenario_ref') {
      const scenario = el.value;
      const zoneSels = wrapper.querySelectorAll('[data-form-key="zone_slug"]');
      for (const sel of zoneSels) {
        const slugType = sel.dataset.slugType || 'zones_hier';
        const current = sel.value;
        await _loadZoneSelect(sel, slugType, scenario, current);
      }
    }
  });

  rawSaveBtn.addEventListener('click', async () => {
    const content = rawTextarea.value;
    try {
      const res = await fetch('/api/yaml', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: yf.path, content }),
      });
      const data = await res.json();
      showYamlStatus(statusMsg, data.ok ? 'ok' : 'error',
        data.ok ? '✓ Sauvegardé' : `Erreur : ${data.error}`);
    } catch (e) {
      showYamlStatus(statusMsg, 'error', `Erreur réseau : ${e.message}`);
    }
  });

  return wrapper;
}

/** Construit un champ de formulaire selon son type. */
async function _buildFormField(field, currentValues, script) {
  const group = document.createElement('div');
  group.className = 'option-group yaml-form-field';
  group.dataset.yamlKey = field.key;

  const label = document.createElement('div');
  label.className = 'option-label';
  label.textContent = field.label + (field.optional ? ' (optionnel)' : '');
  group.appendChild(label);

  // Valeur courante depuis le YAML parsé
  // Supporte les clés imbriquées (article.longueur)
  const currentVal = _getNestedValue(currentValues, field.key);

  if (field.type === 'select' || field.type === 'ligne_select') {
    const sel = document.createElement('select');
    sel.dataset.formKey = field.key;

    let choices = field.choices || [];
    if (field.source === 'config_scenarios') {
      choices = (State.config?.scenarios || []).map(s => ({ value: s, label: s }));
      if (field.optional) choices = [{ value: '', label: '— Aucun —' }, ...choices];
    }

    choices.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.value;
      opt.textContent = c.label;
      // Priorité : valeur du YAML, sinon default du field
      const effective = currentVal !== undefined ? currentVal : (field.default || '');
      if (c.value === effective) opt.selected = true;
      sel.appendChild(opt);
    });

    group.appendChild(sel);

  } else if (field.type === 'slug_select') {
    const scenario = State.config?.default_scenario || '';

    if (field.slug_type === 'zones_hier' && field.key === 'zone_hint') {
      // Double select Zone 2098 / Pays 2026 — uniquement pour zone_hint
      const doubleSelect = await buildZoneDoubleSelect(field, currentVal, scenario);
      group.appendChild(doubleSelect);
    } else {
      const sel = document.createElement('select');
      sel.dataset.formKey = field.key;
      sel.dataset.slugType = field.slug_type;
      sel.innerHTML = '<option value="">Chargement…</option>';
      group.appendChild(sel);
      await _loadZoneSelect(sel, field.slug_type, scenario, currentVal);
    }

  } else if (field.type === 'multi_select') {
    // Chips cliquables pour les listes
    const chips = document.createElement('div');
    chips.className = 'yaml-chips';
    chips.dataset.formKey = field.key;

    const activeValues = new Set(Array.isArray(currentVal) ? currentVal : []);
    const choices = field.choices || THEMATIQUES;

    choices.forEach(val => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'yaml-chip' + (activeValues.has(val) ? ' active' : '');
      chip.textContent = val;
      chip.dataset.value = val;
      chip.addEventListener('click', () => chip.classList.toggle('active'));
      chips.appendChild(chip);
    });

    group.appendChild(chips);

  } else if (field.type === 'number') {
    const inp = document.createElement('input');
    inp.type = 'number';
    inp.dataset.formKey = field.key;
    inp.value = currentVal !== undefined ? currentVal : (field.default ?? '');
    if (field.min !== undefined) inp.min = field.min;
    if (field.max !== undefined) inp.max = field.max;
    group.appendChild(inp);

  } else if (field.type === 'text') {
    const inp = document.createElement('input');
    inp.type = 'text';
    inp.dataset.formKey = field.key;
    inp.value = currentVal !== undefined ? currentVal : '';
    if (field.placeholder) inp.placeholder = field.placeholder;
    else inp.placeholder = field.label;
    group.appendChild(inp);

  } else if (field.type === 'per_scenario_text') {
    // Type ajouté le 24 septembre 2026 (champ consignes_scenarios de
    // entites_custom/queue.yaml) : une zone de texte par scénario, collectée
    // en dictionnaire {scenario: texte} -- seules les zones remplies sont
    // envoyées. Le conteneur porte data-form-key ; les zones internes n'en
    // ont pas (data-scenario seulement), pour ne pas être collectées deux
    // fois comme des champs texte ordinaires.
    const box = document.createElement('div');
    box.className = 'yaml-per-scenario';
    box.dataset.formKey = field.key;
    const current = (currentVal && typeof currentVal === 'object') ? currentVal : {};
    const scenarios = State.config?.scenarios || [];
    scenarios.forEach(sc => {
      const row = document.createElement('div');
      row.style.cssText = 'margin-bottom:6px;';
      const lab = document.createElement('div');
      lab.style.cssText = 'font-size:11px;color:#888;font-family:"JetBrains Mono",monospace;';
      lab.textContent = sc;
      const ta = document.createElement('textarea');
      ta.className = 'yaml-form-textarea';
      ta.dataset.scenario = sc;
      ta.rows = 2;
      ta.placeholder = field.placeholder || `Consigne pour ${sc} (laisser vide = aucune)`;
      ta.value = current[sc] || '';
      row.appendChild(lab);
      row.appendChild(ta);
      box.appendChild(row);
    });
    group.appendChild(box);

  } else if (field.type === 'textarea') {
    const ta = document.createElement('textarea');
    ta.className = 'yaml-form-textarea';
    ta.dataset.formKey = field.key;
    ta.value = currentVal !== undefined ? currentVal : '';
    if (field.placeholder) ta.placeholder = field.placeholder;
    else ta.placeholder = field.label;
    ta.rows = 3;
    group.appendChild(ta);
  }

  // Corrige un bug trouvé le 26 juillet 2026 : marque réellement les
  // champs optionnels dans le DOM (voir _markOptional ci-dessous) --
  // jusqu'ici cet attribut n'était jamais posé, donc le sélecteur
  // ":not([data-optional])" utilisé par _appendYamlQueue() pour repérer
  // les champs requis ne filtrait jamais rien.
  group.querySelectorAll('[data-form-key]').forEach(el => _markOptional(el, field));

  // Texte d'aide (24 septembre 2026) : les "description" des config_fields
  // de scripts_config.json n'étaient jamais affichées dans ce formulaire
  // guidé (seulement pour les options CLI classiques), alors que plusieurs
  // champs en ont une (priorite_forcee, consignes_scenarios, champs des
  // signaux...). Même style que les options classiques.
  if (field.description) {
    const desc = document.createElement('div');
    desc.className = 'option-desc';
    desc.textContent = field.description;
    group.appendChild(desc);
  }

  return group;
}

/**
 * Pose `data-optional` sur l'élément de saisie d'un champ, si le champ est
 * marqué optionnel dans scripts_config.json. Sans ça, `_appendYamlQueue()`
 * ne peut jamais distinguer un champ requis d'un champ optionnel -- rien
 * n'empêchait d'envoyer une entrée de queue avec la description vide (cas
 * réel : entrée `{variable_hint_count: 2}` sans `description`, qui aurait
 * fait planter inject_custom_signals.py sur `idea["description"]` au
 * premier traitement de la queue).
 */
function _markOptional(el, field) {
  if (field.optional) el.dataset.optional = 'true';
  return el;
}

/** Valeur d'un champ per_scenario_text : {scenario: texte} des zones remplies. */
function _collectPerScenario(el) {
  const out = {};
  el.querySelectorAll('textarea[data-scenario]').forEach(ta => {
    const v = ta.value.trim();
    if (v !== '') out[ta.dataset.scenario] = v;
  });
  return out;
}

/** Collecte les valeurs du formulaire guidé et appelle /api/yaml/form. */
async function _saveYamlForm(wrapper, yamlPath, statusEl) {
  const fields = {};

  // Selects et inputs simples
  wrapper.querySelectorAll('[data-form-key]').forEach(el => {
    const key = el.dataset.formKey;
    if (!key) return;

    if (el.classList.contains('yaml-chips')) {
      // Multi-select : collecter les chips actives
      const active = [...el.querySelectorAll('.yaml-chip.active')].map(c => c.dataset.value);
      fields[key] = active;
    } else if (el.classList.contains('yaml-per-scenario')) {
      fields[key] = _collectPerScenario(el);
    } else if (el.tagName === 'SELECT' || el.tagName === 'INPUT') {
      fields[key] = el.type === 'number' ? (el.value !== '' ? Number(el.value) : '') : el.value;
    }
  });

  try {
    const res = await fetch('/api/yaml/form', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: yamlPath, fields }),
    });
    const data = await res.json();
    showYamlStatus(statusEl, data.ok ? 'ok' : 'error',
      data.ok ? '✓ Sauvegardé' : `Erreur : ${data.error}`);
  } catch (e) {
    showYamlStatus(statusEl, 'error', `Erreur réseau : ${e.message}`);
  }
}

/** Parse naïvement un YAML simple (clés scalaires et listes à tirets). */
function _parseYamlSimple(content) {
  const result = {};
  const lines = content.split('\n');
  let currentKey = null;
  let currentParent = null;

  for (const line of lines) {
    if (line.trim().startsWith('#') || line.trim() === '') continue;

    // Clé imbriquée niveau 2 (  key: value)
    const nested = line.match(/^  (\w[\w_.]*?)\s*:\s*(.*)$/);
    if (nested && currentParent) {
      const subkey = nested[1];
      const val = nested[2].trim().replace(/^["']|["']$/g, '');
      result[`${currentParent}.${subkey}`] = val;
      currentKey = null;
      continue;
    }

    // Clé niveau 1 (key: value ou key:)
    const top = line.match(/^(\w[\w_]*?)\s*:\s*(.*)$/);
    if (top) {
      const key = top[1];
      const val = top[2].trim().replace(/^["']|["']$/g, '');
      if (val === '' || val === '~' || val === 'null') {
        result[key] = '';
        currentParent = key;
        currentKey = key;
      } else {
        result[key] = val;
        currentParent = key;
        currentKey = null;
      }
      continue;
    }

    // Item de liste (  - value)
    const listItem = line.match(/^  - (.+)$/);
    if (listItem && currentParent) {
      const val = listItem[1].trim();
      const parentKey = currentParent;
      if (!Array.isArray(result[parentKey])) {
        result[parentKey] = result[parentKey] === '' ? [] : [result[parentKey]];
      }
      if (!result[parentKey].includes(val)) result[parentKey].push(val);
    }
  }

  return result;
}

/** Accède à une valeur par clé simple ou imbriquée (article.longueur). */
function _getNestedValue(values, key) {
  if (key in values) return values[key];
  return undefined;
}

/** Charge un select de zones (hiérarchique ou plat). */
async function _loadZoneSelect(sel, slugType, scenario, currentVal) {
  try {
    const res = await fetch(`/api/slugs?type=${slugType}&scenario=${encodeURIComponent(scenario)}`);
    const data = await res.json();

    sel.innerHTML = '<option value="">— Aucun —</option>';

    if (slugType === 'zones_hier' && data.zones) {
      // Select hiérarchique : N1 en optgroup, N2/N3 indentés
      let currentGroup = null;
      let currentGroupSlug = null;

      data.zones.forEach(z => {
        if (z.niveau === 1) {
          // Nouveau optgroup N1
          currentGroup = document.createElement('optgroup');
          currentGroup.label = `${z.nom} (${z.slug})`;
          currentGroupSlug = z.slug;
          sel.appendChild(currentGroup);
          // Option N1 elle-même (sélectionnable)
          const opt = document.createElement('option');
          opt.value = z.slug;
          opt.textContent = z.nom;
          if (z.slug === currentVal) opt.selected = true;
          currentGroup.appendChild(opt);
        } else {
          const indent = '  '.repeat(z.niveau - 1);
          const opt = document.createElement('option');
          opt.value = z.slug;
          opt.textContent = indent + z.nom;
          if (z.slug === currentVal) opt.selected = true;
          // Ajouter dans le bon groupe (parent direct ou groupe courant)
          if (currentGroup) {
            currentGroup.appendChild(opt);
          } else {
            sel.appendChild(opt);
          }
        }
      });
    } else {
      // Select plat
      (data.slugs || []).forEach(slug => {
        const opt = document.createElement('option');
        opt.value = slug;
        opt.textContent = slug;
        if (slug === currentVal) opt.selected = true;
        sel.appendChild(opt);
      });
    }
  } catch (e) {
    sel.innerHTML = '<option value="">Erreur chargement</option>';
  }
}

/** Appende une nouvelle entrée dans une queue YAML via /api/yaml/append. */
async function _appendYamlQueue(wrapper, yamlPath, statusEl) {
  const entry = {};

  wrapper.querySelectorAll('[data-form-key]').forEach(el => {
    const key = el.dataset.formKey;
    if (!key) return;

    if (el.classList.contains('yaml-chips')) {
      const active = [...el.querySelectorAll('.yaml-chip.active')].map(c => c.dataset.value);
      if (active.length > 0) entry[key] = active;
      // Si vide → ne pas inclure (null = défaut dans le script)
    } else if (el.classList.contains('yaml-per-scenario')) {
      const obj = _collectPerScenario(el);
      if (Object.keys(obj).length > 0) entry[key] = obj;
    } else if (el.tagName === 'SELECT') {
      if (el.value !== '') entry[key] = el.value;
    } else if (el.tagName === 'INPUT' && el.type === 'number') {
      if (el.value !== '') entry[key] = Number(el.value);
    } else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      if (el.value.trim() !== '') entry[key] = el.value.trim();
    }
  });

  // Validation minimale côté client -- corrigée le 26 juillet 2026 : cette
  // vérification était calculée (`required`) mais jamais utilisée, et le
  // commentaire d'origine ("la validation stricte est faite par le script
  // Python") était faux pour ce chemin précis -- /api/yaml/append écrit
  // l'entrée telle quelle, sans jamais appeler le script Python. Rien ne
  // protégeait donc contre une entrée incomplète (cas réel : description
  // vide, qui aurait fait planter inject_custom_signals.py plus tard sur
  // `idea["description"]`, une KeyError qui interrompt tout le traitement
  // de la queue -- pas seulement l'entrée fautive).
  const manquants = [...wrapper.querySelectorAll('[data-form-key]:not([data-optional])')]
    .filter(el => {
      if (el.classList.contains('yaml-chips')) {
        return el.querySelectorAll('.yaml-chip.active').length === 0;
      }
      if (el.classList.contains('yaml-per-scenario')) {
        return Object.keys(_collectPerScenario(el)).length === 0;
      }
      return (el.value || '').trim() === '';
    })
    .map(el => el.closest('.yaml-form-field')?.querySelector('.option-label')?.textContent || '(champ)');

  if (manquants.length > 0) {
    showYamlStatus(statusEl, 'error', `Champ(s) requis manquant(s) : ${manquants.join(', ')}`);
    return;
  }

  try {
    const res = await fetch('/api/yaml/append', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: yamlPath, entry }),
    });
    const data = await res.json();
    if (data.ok) {
      showYamlStatus(statusEl, 'ok', `✓ Ajouté (${data.queue_length} entrée${data.queue_length > 1 ? 's' : ''} en queue)`);
      // Réinitialiser le formulaire
      wrapper.querySelectorAll('[data-form-key]').forEach(el => {
        if (el.classList.contains('yaml-chips')) {
          el.querySelectorAll('.yaml-chip').forEach(c => c.classList.remove('active'));
        } else if (el.classList.contains('yaml-per-scenario')) {
          el.querySelectorAll('textarea[data-scenario]').forEach(ta => { ta.value = ''; });
        } else if (el.tagName === 'SELECT') {
          el.selectedIndex = 0;
        } else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          el.value = '';
        }
      });
    } else {
      showYamlStatus(statusEl, 'error', `Erreur : ${data.error}`);
    }
  } catch (e) {
    showYamlStatus(statusEl, 'error', `Erreur réseau : ${e.message}`);
  }
}

// ══════════════════════════════════════════════════
// DOUBLE SELECT ZONE 2098 / PAYS 2026
// ══════════════════════════════════════════════════

/**
 * Construit un groupe double select mutuellement exclusif :
 * - Select 1 : Zone 2098 (hiérarchique)
 * - Select 2 : Pays 2026 → lookup zone 2098
 * La valeur finale dans data-form-key est toujours un slug zone 2098.
 */
async function buildZoneDoubleSelect(field, currentVal, scenario) {
  const wrapper = document.createElement('div');
  wrapper.className = 'zone-double-select';

  // ── Onglets de mode ──
  const tabs = document.createElement('div');
  tabs.className = 'zone-tabs';

  const tab2098 = document.createElement('button');
  tab2098.type = 'button';
  tab2098.className = 'zone-tab active';
  tab2098.textContent = 'Zone 2098';

  const tab2026 = document.createElement('button');
  tab2026.type = 'button';
  tab2026.className = 'zone-tab';
  tab2026.textContent = 'Pays 2026';

  tabs.appendChild(tab2098);
  tabs.appendChild(tab2026);
  wrapper.appendChild(tabs);

  // ── Panel Zone 2098 ──
  const panel2098 = document.createElement('div');
  panel2098.className = 'zone-panel';

  const sel2098 = document.createElement('select');
  sel2098.dataset.formKey = field.key;
  sel2098.dataset.slugType = 'zones_hier';
  sel2098.innerHTML = '<option value="">Chargement…</option>';
  panel2098.appendChild(sel2098);
  wrapper.appendChild(panel2098);

  // ── Panel Pays 2026 ──
  const panel2026 = document.createElement('div');
  panel2026.className = 'zone-panel';
  panel2026.style.display = 'none';

  const sel2026 = document.createElement('select');
  sel2026.className = 'zone-pays-select';
  sel2026.innerHTML = '<option value="">— Choisir un pays —</option>';
  panel2026.appendChild(sel2026);

  const zoneResult = document.createElement('div');
  zoneResult.className = 'zone-lookup-result';
  zoneResult.style.display = 'none';
  panel2026.appendChild(zoneResult);

  wrapper.appendChild(panel2026);

  // ── Charger zones 2098 ──
  await _loadZoneSelect(sel2098, 'zones_hier', scenario, currentVal);

  // ── Charger liste pays 2026 depuis zones_pays.json via API ──
  try {
    const res = await fetch('/api/zones/pays-liste');
    const data = await res.json();
    (data.pays || []).forEach(pays => {
      const opt = document.createElement('option');
      opt.value = pays;
      opt.textContent = pays;
      sel2026.appendChild(opt);
    });
  } catch (e) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = 'Erreur chargement';
    sel2026.appendChild(opt);
  }

  // ── Event : sélection pays 2026 → lookup ──
  sel2026.addEventListener('change', async () => {
    const pays = sel2026.value;
    if (!pays) {
      zoneResult.style.display = 'none';
      sel2098.value = '';
      return;
    }

    zoneResult.style.display = 'block';
    zoneResult.className = 'zone-lookup-result loading';
    zoneResult.textContent = 'Recherche…';

    const sc = _getCurrentScenario(wrapper);
    try {
      const res = await fetch(`/api/zones/lookup?pays=${encodeURIComponent(pays)}&scenario=${sc}`);
      const data = await res.json();

      if (data.zone) {
        zoneResult.className = 'zone-lookup-result found';
        zoneResult.textContent = `→ ${data.zone}`;
        // Pré-remplir le select 2098 avec la zone trouvée
        sel2098.value = data.zone;
        // Si la valeur n'existe pas dans le select, l'ajouter temporairement
        if (!sel2098.value) {
          const opt = document.createElement('option');
          opt.value = data.zone;
          opt.textContent = `${data.zone} ✓`;
          sel2098.appendChild(opt);
          sel2098.value = data.zone;
        }
      } else {
        zoneResult.className = 'zone-lookup-result not-found';
        zoneResult.textContent = `⚠ Aucune zone 2098 pour "${pays}" dans ce scénario — zone_hint laissé vide`;
        sel2098.value = '';
      }
    } catch (e) {
      zoneResult.className = 'zone-lookup-result error';
      zoneResult.textContent = `Erreur : ${e.message}`;
    }
  });

  // ── Onglets exclusifs ──
  tab2098.addEventListener('click', () => {
    tab2098.classList.add('active');
    tab2026.classList.remove('active');
    panel2098.style.display = 'block';
    panel2026.style.display = 'none';
  });

  tab2026.addEventListener('click', () => {
    tab2026.classList.add('active');
    tab2098.classList.remove('active');
    panel2098.style.display = 'none';
    panel2026.style.display = 'block';
  });

  return wrapper;
}

/** Trouve le scénario actif depuis le formulaire parent ou la config globale. */
function _getCurrentScenario(wrapper) {
  // Cherche un select scenario dans le même formulaire guidé
  const form = wrapper.closest('.yaml-form-panel, .yaml-form-zone');
  if (form) {
    const scSel = form.querySelector('[data-form-key="scenario"], [data-form-key="scenario_ref"]');
    if (scSel && scSel.value) return scSel.value;
  }
  return State.config?.default_scenario || 'breakdown';
}

// ══════════════════════════════════════════════════
// ZONES MANQUANTES — Dashboard
// ══════════════════════════════════════════════════

function renderZonesManquantes(data) {
  const card = document.getElementById('zones-manquantes-card');
  const parScenario = data.par_scenario || {};
  const entries = data.manquantes || [];

  // Compter seulement les blanc_a_evaluer + a_enrichir (pas les intentionnels, déjà traités)
  const actionable = entries.filter(e => e.statut !== 'blanc_intentionnel');
  const total = actionable.length;

  if (card) {
    card.className = 'stat-card' + (total > 0 ? ' warn-card' : '');
    card.innerHTML = `
      <div class="card-title">Zones manquantes</div>
      <div class="card-value">${total}</div>
      <div class="card-sub">${total > 0 ? '→ voir détail ci-dessous' : 'Toutes couvertes ou traitées'}</div>
    `;
  }

  // Section détaillée sous le dashboard
  const container = document.getElementById('tab-dashboard');
  const old = container.querySelector('.zones-manquantes-section');
  if (old) old.remove();

  if (entries.length === 0) return;

  const section = document.createElement('div');
  section.className = 'zones-manquantes-section';

  const scenarios = Object.keys(parScenario).sort();

  let html = `<div class="tab-page-title" style="margin-top:24px">Zones manquantes par scénario</div>`;

  scenarios.forEach(sc => {
    const items = parScenario[sc].filter(e => e.statut !== 'blanc_intentionnel');
    if (items.length === 0) return;

    html += `
      <div class="zones-manquantes-scenario">
        <div class="zms-header">
          <span class="zms-scenario-name">${sc}</span>
          <span class="zms-count">${items.length} pays</span>
          <button class="yaml-btn zms-recheck-btn" data-scenario="${sc}">
            Revérifier
          </button>
          <button class="yaml-btn zms-enrich-btn" data-scenario="${sc}">
            Enrichir ce scénario
          </button>
        </div>
        <div class="zms-pays-list">
          ${items.map(e => `
            <div class="zms-pays-item" data-pays="${e.pays}" data-scenario="${sc}">
              <span class="zms-pays-name">${e.pays}</span>
              <span class="zms-statut zms-statut-${e.statut}">${_statutLabel(e.statut)}</span>
              <button class="zms-mark-btn" data-action="blanc_intentionnel"
                      data-pays="${e.pays}" data-scenario="${sc}"
                      title="Marquer comme blanc intentionnel">Intentionnel</button>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  });

  section.innerHTML = html;
  container.appendChild(section);

  // ── Events ──
  section.querySelectorAll('.zms-enrich-btn').forEach(btn => {
    btn.addEventListener('click', () => _launchEnrichGeographie(btn.dataset.scenario, btn));
  });

  section.querySelectorAll('.zms-recheck-btn').forEach(btn => {
    btn.addEventListener('click', () => _recheckScenario(btn.dataset.scenario, btn));
  });

  section.querySelectorAll('.zms-mark-btn').forEach(btn => {
    btn.addEventListener('click', () => _markZoneStatut(
      btn.dataset.pays, btn.dataset.scenario, btn.dataset.action, btn
    ));
  });
}

function _statutLabel(statut) {
  const labels = {
    'blanc_a_evaluer': 'À évaluer',
    'a_enrichir': 'À enrichir',
    'blanc_intentionnel': 'Intentionnel',
  };
  return labels[statut] || statut;
}

/** Lance enrich_geographie_recursive.py --scenario X via /api/run */
async function _launchEnrichGeographie(scenario, btn) {
  if (!confirm(`Lancer enrich_geographie_recursive.py --scenario ${scenario} ?\n\nCela va appeler l'API LLM pour enrichir la fiche géographique.`)) {
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Lancement…';

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        script_id: 'enrich_geographie',
        args: ['--scenario', scenario],
        force_llm_override: !!State.forceLlmOverride,
      }),
    });
    const data = await res.json();

    if (data.run_id) {
      btn.textContent = 'Lancé ✓';
      // Naviguer vers la vue du script et connecter au streaming déjà en cours
      await showScript('enrich_geographie');
      State.currentRunId = data.run_id;
      setRunning(true);
      startSSE(data.run_id, 'enrich_geographie');
    } else {
      btn.textContent = data.error || 'Erreur';
      btn.disabled = false;
    }
  } catch (e) {
    btn.textContent = 'Erreur réseau';
    btn.disabled = false;
  }
}

/** Marque une entrée zones_manquantes avec un nouveau statut */
async function _markZoneStatut(pays, scenario, statut, btn) {
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = '…';

  try {
    const res = await fetch('/api/zones/manquantes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pays, scenario, statut }),
    });
    const data = await res.json();

    if (data.ok) {
      // Retirer visuellement l'item de la liste
      const item = btn.closest('.zms-pays-item');
      if (item) {
        item.style.opacity = '0.4';
        item.style.textDecoration = 'line-through';
      }
      btn.textContent = '✓';
    } else {
      btn.textContent = original;
      btn.disabled = false;
      alert(`Erreur : ${data.error}`);
    }
  } catch (e) {
    btn.textContent = original;
    btn.disabled = false;
  }
}

/** Revérifie tous les pays manquants d'un scénario contre les fiches géographie à jour. */
async function _recheckScenario(scenario, btn) {
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = 'Vérification…';

  try {
    const res = await fetch('/api/zones/recheck', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario }),
    });
    const data = await res.json();

    if (data.error) {
      btn.textContent = 'Erreur';
      btn.disabled = false;
      alert(`Erreur : ${data.error}`);
      return;
    }

    const nbResolved = (data.resolved || []).length;

    if (nbResolved > 0) {
      btn.textContent = `✓ ${nbResolved} résolus`;
      // Recharger la section complète pour refléter les changements
      const res2 = await fetch('/api/zones/manquantes');
      const data2 = await res2.json();
      renderZonesManquantes(data2);
    } else {
      btn.textContent = 'Aucun changement';
      btn.disabled = false;
      setTimeout(() => { btn.textContent = original; btn.disabled = false; }, 2000);
    }
  } catch (e) {
    btn.textContent = 'Erreur réseau';
    btn.disabled = false;
  }
}

// ══════════════════════════════════════════════════
// CARTE — Onglet géographie interactive (P1)
// ══════════════════════════════════════════════════

const CarteState = {
  map: null,
  geojsonLayer: null,
  rawGeojson: null,
  overlays: null,        // FeatureCollection custom (zones qui coupent un pays), ou null si pas encore chargé
  overlaysLayer: null,
  drawControl: null,       // instance L.Control.Draw
  drawPolygonHandler: null, // instance L.Draw.Polygon, démarrée/arrêtée directement (sans passer par l'icône du contrôle)
  drawnItemsLayer: null,   // L.FeatureGroup où Leaflet.Draw dépose le tracé en cours
  modeDessin: false,       // true = outils de dessin visibles
  modeDessinZoneComplete: false,  // true = mode "dessiner une zone complète" (S11, 9 sept)
  zoneCompleteProposition: null,  // dernière proposition reçue (classification + textes portion), pour l'application après review
  faToEn: null,        // mapping FR -> EN name (gui/static/pays_mapping.json)
  affectations: {},    // pays FR -> zone slug|null
  zonesN1: [],          // [{slug,nom,description,color}]
  scenario: null,
  zoneSurlignee: null,  // slug niveau 1 actuellement mis en évidence sur la carte (ou null)
  searchDebounceTimer: null,
  origineReelleParSlug: {},  // slug -> origine_reelle, reconstruit à chaque ouverture d'arbre (split)
  racineParSlug: {},  // slug -> slug de la racine niveau 1, reconstruit à chaque ouverture d'arbre (localiser une sous-zone)
  villes: null,          // [{nom,pays,lat,lon,population,capitale}], chargé une seule fois
  villesLayer: null,
  villesVisibles: false,  // off par défaut
  surligneLayer: null,     // contour unique de la zone sélectionnée (turf.union)
  dessinZonePreselectionnee: null,  // slug pré-choisi pour le prochain overlay dessiné (panneau unique)
  dessinPaysPreselectionne: null,   // pays pré-choisi (dessin depuis une ligne "Pays & portions")
};

function _normEn(s) {
  return (s || '')
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]/g, '');
}

async function loadCarte() {
  const scenarioSel = document.getElementById('carte-scenario');

  if (scenarioSel.options.length === 0) {
    const scenarios = State.config?.scenarios || [];
    scenarioSel.innerHTML = scenarios.map(s => `<option value="${s}">${s}</option>`).join('');
    scenarioSel.value = State.config?.default_scenario || scenarios[0] || '';
    scenarioSel.addEventListener('change', () => refreshCarte());
  }

  if (!CarteState.faToEn) {
    try {
      const res = await fetch('/static/pays_mapping.json');
      CarteState.faToEn = await res.json();
    } catch (e) {
      console.error('Erreur chargement pays_mapping.json', e);
      CarteState.faToEn = {};
    }
  }

  if (!CarteState.villes) {
    try {
      const res = await fetch('/api/carte/villes');
      const data = await res.json();
      CarteState.villes = Array.isArray(data) ? data : [];
    } catch (e) {
      console.error('Erreur chargement villes_principales.json', e);
      CarteState.villes = [];
    }
  }

  if (!CarteState.map) { initLeafletMap(); initCarteDessin(); }
  if (!CarteState.rawGeojson) await loadWorldGeojson();

  initCarteSearch();

  await refreshCarte();
  // Leaflet a besoin d'un recalcul de taille si le conteneur était display:none au moment de l'init
  setTimeout(() => CarteState.map && CarteState.map.invalidateSize(), 50);
}

function initLeafletMap() {
  const mapEl = document.getElementById('carte-map');
  CarteState.map = L.map(mapEl, { worldCopyJump: true, renderer: L.svg() }).setView([20, 10], 2);
  L.svg().addTo(CarteState.map); // force la création immédiate du <svg> (nécessaire pour injecter les motifs)

  // CARTO_API_KEY (30 août 2026) : CARTO exige désormais une clé pour ses
  // tuiles raster gratuites, sinon filigrane "API KEY REQUIRED" sur toute
  // la carte -- changement de leur côté, rien à voir avec ce pipeline.
  // Injectée par app.py/index.html depuis l'environnement (~/.zshrc),
  // jamais en dur ici. Avertissement clair en console si absente, plutôt
  // que de laisser le filigrane silencieux sans piste de correction.
  const cartoKey = window.CARTO_API_KEY || '';
  if (!cartoKey) {
    console.warn(
      "CARTO_API_KEY non définie -- la carte affichera un filigrane " +
      "'API KEY REQUIRED'. Ajoute CARTO_API_KEY à ton environnement " +
      "(clé gratuite sur https://carto.com/basemaps/apikey) et " +
      "redémarre Flask."
    );
  }
  const tileUrlBase = 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png';
  L.tileLayer(cartoKey ? (tileUrlBase + '?key=' + encodeURIComponent(cartoKey)) : tileUrlBase, {
    attribution: '© OpenStreetMap, © CARTO',
    maxZoom: 8,
  }).addTo(CarteState.map);
}

async function loadWorldGeojson() {
  const statusEl = document.getElementById('carte-status');
  try {
    statusEl.textContent = 'Chargement du fond de carte…';
    const res = await fetch('https://cdn.jsdelivr.net/gh/johan/world.geo.json/countries.geo.json');
    const gj = await res.json();
    CarteState.rawGeojson = gj;
    statusEl.textContent = '';
  } catch (e) {
    console.error('Erreur chargement geojson', e);
    statusEl.textContent = 'Impossible de charger le fond de carte (connexion internet requise).';
  }
}

async function refreshCarte() {
  const scenario = document.getElementById('carte-scenario').value;
  if (!scenario) return;
  CarteState.scenario = scenario;

  const statusEl = document.getElementById('carte-status');
  statusEl.textContent = 'Chargement des affectations…';

  try {
    // Refonte Carte (12 sept 2026, étape 1) : un seul appel désormais --
    // /api/carte/affectations renvoie déjà couverture.overlays (les mêmes
    // features qu'avant via /api/carte/overlays, mais avec couleur_effective/
    // motif_effectif déjà résolus par héritage N1 côté serveur). Plus besoin
    // du fetch séparé ni de deviner la couleur d'un overlay côté client.
    const res = await fetch(`/api/carte/affectations?scenario=${encodeURIComponent(scenario)}`);
    const data = await res.json();
    if (data.error) {
      statusEl.textContent = `Erreur : ${data.error}`;
      return;
    }
    CarteState.affectations = data.affectations || {};
    CarteState.zonesN1 = data.zones_n1 || [];
    const couverture = data.couverture || { pays_masques: {}, overlays: [] };
    CarteState.couverture = couverture;
    CarteState.overlays = { type: 'FeatureCollection', features: couverture.overlays || [] };

    statusEl.textContent = '';
    renderCarteLayer();
    renderCarteLegend();
  } catch (e) {
    statusEl.textContent = `Erreur réseau : ${e.message}`;
  }
}

/** Index EN normalisé -> [pays FR...] (plusieurs pays FR peuvent pointer vers un seul polygone, ex UK) */
function _buildEnToFrIndex() {
  const idx = {};
  Object.entries(CarteState.faToEn || {}).forEach(([fr, en]) => {
    if (!en) return;
    const key = _normEn(en);
    idx[key] = idx[key] || [];
    idx[key].push(fr);
  });
  return idx;
}

// ── Motifs de zone (couleur + hachures pour garantir la distinction visuelle) ──

const PATTERN_ANGLES  = [45, 135, 0, 90, 20];
const PATTERN_SPACING = [7, 7, 9, 9, 6];

// Bibliothèque de motifs personnalisés (8 sept 2026) -- distincte des
// hachures génériques automatiques (PATTERN_ANGLES/PATTERN_SPACING) : ici
// chaque zone qui en choisit un affiche ce symbole précis, tuilé. Formes
// simplifiées volontairement (lisibles à petite échelle, ~24px de tuile).
const MOTIFS_ICONES = {
  radiation: (g, fg) => {
    // Trèfle radioactif approximé par 3 secteurs triangulaires à 120°.
    const cx = 12, cy = 12, rInt = 3, rExt = 10;
    for (let k = 0; k < 3; k++) {
      const centre = -90 + k * 120; // premier secteur pointant vers le haut
      const a1 = (centre - 25) * Math.PI / 180, a2 = (centre + 25) * Math.PI / 180;
      const x1 = cx + rExt * Math.cos(a1), y1 = cy + rExt * Math.sin(a1);
      const x2 = cx + rExt * Math.cos(a2), y2 = cy + rExt * Math.sin(a2);
      const xi1 = cx + rInt * Math.cos(a1), yi1 = cy + rInt * Math.sin(a1);
      const xi2 = cx + rInt * Math.cos(a2), yi2 = cy + rInt * Math.sin(a2);
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', `M${xi1},${yi1} L${x1},${y1} A${rExt},${rExt} 0 0 1 ${x2},${y2} L${xi2},${yi2} Z`);
      path.setAttribute('fill', fg);
      g.appendChild(path);
    }
    const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    c.setAttribute('cx', cx); c.setAttribute('cy', cy); c.setAttribute('r', rInt);
    c.setAttribute('fill', fg);
    g.appendChild(c);
  },
  flamme: (g, fg) => {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M12,3 C9,7 7,9 7,13 a5,5 0 1,0 10,0 C17,9 15,7 12,3 Z');
    path.setAttribute('fill', fg);
    g.appendChild(path);
  },
  vague: (g, fg) => {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M2,14 Q6,9 10,14 T18,14 T26,14 L26,20 L2,20 Z');
    path.setAttribute('fill', fg);
    g.appendChild(path);
  },
  crane: (g, fg) => {
    const head = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    head.setAttribute('cx', 12); head.setAttribute('cy', 10); head.setAttribute('r', 6);
    head.setAttribute('fill', fg);
    g.appendChild(head);
    const jaw = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    jaw.setAttribute('x', 9); jaw.setAttribute('y', 15); jaw.setAttribute('width', 6); jaw.setAttribute('height', 4);
    jaw.setAttribute('fill', fg);
    g.appendChild(jaw);
    [9, 15].forEach(ex => {
      const eye = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      eye.setAttribute('cx', ex); eye.setAttribute('cy', 10); eye.setAttribute('r', 1.6);
      eye.setAttribute('fill', 'var(--carte-eye-bg, #fff)');
      g.appendChild(eye);
    });
  },
};

const MOTIFS_LABELS = { radiation: '☢ Radiation', flamme: '🔥 Flamme', vague: '🌊 Vague', crane: '💀 Crâne' };

function _darken(hex, amount) {
  const num = parseInt(hex.replace('#', ''), 16);
  let r = (num >> 16) - amount;
  let g = ((num >> 8) & 0xff) - amount;
  let b = (num & 0xff) - amount;
  r = Math.max(0, r); g = Math.max(0, g); b = Math.max(0, b);
  return '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
}

function _ensureSvgDefs() {
  const svg = document.querySelector('#carte-map svg');
  if (!svg) return null;
  let defs = svg.querySelector('defs#carte-patterns-defs');
  if (defs) defs.remove(); // régénéré à chaque refresh (couleurs/motifs peuvent changer)
  defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.id = 'carte-patterns-defs';
  svg.insertBefore(defs, svg.firstChild);
  return defs;
}

/** Crée (si besoin) le <pattern> SVG d'une zone et retourne l'URL de fill à utiliser. */
function _zoneFill(defs, zone) {
  if (!defs) return zone.color;

  // Motif personnalisé (icône) -- prioritaire sur les hachures génériques.
  if (zone.motif && MOTIFS_ICONES[zone.motif]) {
    const id = `carte-zone-motif-${zone.slug}`;
    const pattern = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
    pattern.setAttribute('id', id);
    pattern.setAttribute('width', 24);
    pattern.setAttribute('height', 24);
    pattern.setAttribute('patternUnits', 'userSpaceOnUse');

    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bg.setAttribute('width', 24);
    bg.setAttribute('height', 24);
    bg.setAttribute('fill', zone.color);
    pattern.appendChild(bg);

    const fg = _darken(zone.color, 70);
    MOTIFS_ICONES[zone.motif](pattern, fg);

    defs.appendChild(pattern);
    return `url(#${id})`;
  }

  if (zone.pattern === null || zone.pattern === undefined) return zone.color;

  const id = `carte-zone-pattern-${zone.slug}`;
  const angle = PATTERN_ANGLES[zone.pattern % PATTERN_ANGLES.length];
  const spacing = PATTERN_SPACING[zone.pattern % PATTERN_SPACING.length];
  const dark = _darken(zone.color, 45);

  const pattern = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
  pattern.setAttribute('id', id);
  pattern.setAttribute('width', spacing);
  pattern.setAttribute('height', spacing);
  pattern.setAttribute('patternUnits', 'userSpaceOnUse');
  pattern.setAttribute('patternTransform', `rotate(${angle})`);

  const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  bg.setAttribute('width', spacing);
  bg.setAttribute('height', spacing);
  bg.setAttribute('fill', zone.color);
  pattern.appendChild(bg);

  const stripe = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  stripe.setAttribute('width', String(spacing / 2));
  stripe.setAttribute('height', spacing);
  stripe.setAttribute('fill', dark);
  pattern.appendChild(stripe);

  defs.appendChild(pattern);
  return `url(#${id})`;
}

function renderCarteLayer() {
  if (!CarteState.rawGeojson) return;
  if (CarteState.geojsonLayer) CarteState.map.removeLayer(CarteState.geojsonLayer);
  if (CarteState.overlaysLayer) CarteState.map.removeLayer(CarteState.overlaysLayer);

  const enToFr = _buildEnToFrIndex();
  const defs = _ensureSvgDefs();
  const zoneFillMap = {};
  CarteState.zonesN1.forEach(z => { zoneFillMap[z.slug] = _zoneFill(defs, z); });

  CarteState.geojsonLayer = L.geoJSON(CarteState.rawGeojson, {
    style: (feature) => {
      const name = feature.properties?.name || feature.properties?.ADMIN || '';
      const frList = enToFr[_normEn(name)];
      if (!frList) return { fillColor: 'transparent', weight: 0.5, color: '#ccc', fillOpacity: 0 };

      // Le calque de base affiche TOUJOURS la couleur de la zone de base du
      // pays, même s'il a par ailleurs un ou plusieurs overlays -- un pays
      // peut être partagé (ex. France : zone_interdite_heysham en base +
      // portion overlay zone_euro_sud). L'overlay, en opacité pleine plus
      // bas, recouvre correctement sa propre portion.
      //
      // La surbrillance ne se fait plus ici (12 sept 2026, étape 2) : un
      // trait orange par pays laissait les frontières internes de la zone
      // visibles. Un contour unique dessiné par renderSurlignageZone(), à la
      // fin de cette fonction, s'en charge désormais -- ce calque garde
      // toujours son style normal, surligné ou non.
      const allNull = frList.every(fr => !CarteState.affectations[fr]);
      if (allNull) return { fillColor: '#999', weight: 1, color: '#666', fillOpacity: 0.5 };

      const zone = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
      const fill = zoneFillMap[zone] || '#3b6fd4';
      return { fillColor: fill, weight: 1, color: '#666', fillOpacity: 1 };
    },
    onEachFeature: (feature, layer) => {
      const name = feature.properties?.name || feature.properties?.ADMIN || '';
      const frList = enToFr[_normEn(name)];
      if (!frList) return;
      // En mode dessin, on laisse le clic filer vers Leaflet.Draw (qui pose
      // un sommet du polygone) au lieu de sélectionner le pays -- sinon les
      // deux se déclenchaient en même temps (bug remonté par David, 8 sept).
      layer.on('click', () => { if (!CarteState.modeDessin && !CarteState.modeDessinZoneComplete) onCartePaysClick(frList, name); });
      layer.on('mouseover', () => layer.setStyle({ weight: 2, color: '#222' }));
      layer.on('mouseout', () => layer.setStyle({ weight: 1, color: '#666' }));
      layer.bindTooltip(frList.join(' / '), { sticky: true });
    },
  }).addTo(CarteState.map);

  // Overlays custom : zones qui coupent un pays en deux ou plus. Ajoutée
  // APRÈS la couche pays -- Leaflet empile dans l'ordre d'ajout des couches,
  // donc ces polygones s'affichent bien par-dessus. fillOpacity TOUJOURS à
  // 1 (opaque) -- 0.85 laissait transparaître le motif hachuré du pays
  // sous-jacent. Couleur et motif viennent de couleur_effective/
  // motif_effectif, déjà résolus par héritage N1 côté serveur.
  if (CarteState.overlays?.features?.length) {
    CarteState.overlaysLayer = L.geoJSON(CarteState.overlays, {
      style: (feature) => {
        const slug = feature.properties?.zone_slug;
        const couleur = feature.properties?.couleur_effective;
        const motif = feature.properties?.motif_effectif;
        const fill = _zoneFill(defs, { slug, color: couleur || '#3b6fd4', motif });
        return { fillColor: fill, weight: 1.5, color: '#333', fillOpacity: 1, dashArray: '4 3' };
      },
      onEachFeature: (feature, layer) => {
        const slug = feature.properties?.zone_slug;
        const zone = CarteState.zonesN1.find(z => z.slug === slug);
        const label = zone ? `${zone.nom} (${feature.properties?.pays || '?'})` : (slug || '?');
        layer.on('click', () => onCarteZoneOverlayClick(feature.properties || {}));
        layer.on('mouseover', () => layer.setStyle({ weight: 3, color: '#111' }));
        layer.on('mouseout', () => layer.setStyle({ weight: 1.5, color: '#333' }));
        layer.bindTooltip(label, { sticky: true });
      },
    }).addTo(CarteState.map);
  }

  // Diagnostic : pays FR sans correspondance trouvée sur le fond de carte
  const matchedFr = new Set(Object.values(enToFr).flat());
  const allFr = Object.keys(CarteState.faToEn || {}).filter(fr => CarteState.faToEn[fr]);
  const missing = allFr.filter(fr => !matchedFr.has(fr));
  const diagEl = document.getElementById('carte-diagnostic');
  if (missing.length) {
    diagEl.style.display = 'block';
    diagEl.innerHTML = `⚠ ${missing.length} pays non localisés sur le fond de carte (noms à corriger dans gui/static/pays_mapping.json) : ${missing.join(', ')}`;
  } else {
    diagEl.style.display = 'none';
  }

  // Étape 2 (12 sept 2026) : contour unique de la zone sélectionnée, et
  // villes toujours redessinées en dernier (donc toujours au-dessus) --
  // les deux dépendent de ce que renderCarteLayer() vient de (re)dessiner.
  renderSurlignageZone();
  renderVillesLayer();
}

// ── Surbrillance : contour extérieur unique de la zone sélectionnée ─────
//
// Avant (12 sept 2026) : chaque pays de la zone recevait individuellement
// un trait orange, laissant les frontières internes de la zone visibles --
// pas ce que David voulait (juste le contour extérieur de la zone entière).
// Fusionne (turf.union) tous les pays "pays entier" + portions overlay
// appartenant à la zone sélectionnée en une seule géométrie, et affiche
// uniquement son contour, sans remplissage, par-dessus tout le reste.
//
// Pour un pays partagé (ex. France, base=Heysham + overlay=Zone Euro Sud),
// la portion overlay d'une AUTRE zone est retirée par turf.difference avant
// le calcul du contour -- surligner Heysham ne montre plus tout le contour
// de la France, seulement sa portion réelle (fix du 12 sept 2026).
// Rassemble les géométries "pays entier + overlays" appartenant à
// `cibleSlugOverlay`, parmi les pays affectés en base à `racineSlug`, filtré
// le cas échéant par `paysFiltre` (Set de noms FR, ou null = pas de filtre).
// Factorisé (12 sept 2026) pour permettre le repli zone parente ci-dessous
// sans dupliquer la boucle turf.difference.
function _gatherZoneGeometries(racineSlug, cibleSlugOverlay, paysFiltre) {
  const enToFr = _buildEnToFrIndex();
  const geometries = [];

  CarteState.rawGeojson.features.forEach(feature => {
    const name = feature.properties?.name || feature.properties?.ADMIN || '';
    const frList = enToFr[_normEn(name)];
    if (!frList) return;
    const zone = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
    if (zone !== racineSlug) return;
    if (paysFiltre && !frList.some(fr => paysFiltre.has(fr))) return;

    // Ce pays est affecté (en base) à la zone surlignée -- mais si une
    // portion de son territoire est découpée par un overlay appartenant à
    // une AUTRE zone (ex. France : base Zone Interdite de Heysham, portion
    // Zone Euro Sud en overlay), il faut l'exclure du contour. Découpe
    // géométrique réelle (turf.difference), pas une approximation.
    let geom = feature;
    const overlaysAutreZone = (CarteState.overlays?.features || []).filter(f =>
      f.properties?.pays && frList.includes(f.properties.pays) && f.properties.zone_slug !== cibleSlugOverlay
    );
    overlaysAutreZone.forEach(ov => {
      try {
        const diff = turf.difference(geom, ov);
        if (diff) geom = diff;
      } catch (e) {
        console.warn('turf.difference a échoué (géométrie non modifiée)', e);
      }
    });
    geometries.push(geom);
  });

  (CarteState.overlays?.features || []).forEach(feature => {
    if (feature.properties?.zone_slug === cibleSlugOverlay) geometries.push(feature);
  });

  return geometries;
}

const _MSG_REPLI_SOUS_ZONE = "Cette sous-zone n'a pas de tracé propre localisable -- zone parente affichée à la place.";

function renderSurlignageZone() {
  if (CarteState.surligneLayer) {
    CarteState.map.removeLayer(CarteState.surligneLayer);
    CarteState.surligneLayer = null;
  }
  const slug = CarteState.zoneSurlignee;
  if (!slug || !CarteState.rawGeojson) return;
  if (typeof turf === 'undefined') {
    console.warn('Turf.js non chargé -- contour de zone non affiché.');
    return;
  }

  // Sous-zone (niveau 2/3) : pas de couleur propre (héritage N1), mais peut
  // quand même être localisée -- on ne garde que SES propres pays (son
  // origine_reelle à elle), parmi ceux affectés en base à sa racine N1.
  // racineParSlug/origineReelleParSlug sont peuplés à l'ouverture de
  // l'arbre (openArbreZonePanel) -- absents tant qu'aucun arbre n'a encore
  // été ouvert pour cette branche, auquel cas la sous-zone reste non
  // localisable pour l'instant (pas d'erreur, juste rien à afficher).
  const estN1 = CarteState.zonesN1.some(z => z.slug === slug);
  const racineSlug = estN1 ? slug : (CarteState.racineParSlug?.[slug] || null);
  if (!racineSlug) return;

  const statusEl = document.getElementById('carte-status');
  let geometries;

  if (estN1) {
    geometries = _gatherZoneGeometries(racineSlug, slug, null);
  } else {
    const paysSousZone = new Set(
      (CarteState.origineReelleParSlug?.[slug] || [])
        .map(o => o && o.entite)
        .filter(Boolean)
    );
    geometries = _gatherZoneGeometries(racineSlug, slug, paysSousZone);

    if (!geometries.length) {
      // Repli (12 sept 2026) : cette sous-zone référence des lieux/régions
      // plutôt que des noms de pays exacts (ex. "Balkans occidentaux"),
      // sans overlay dédié -- rien à dessiner pour elle spécifiquement.
      // Montrer sa zone parente plutôt que rien du tout, avec un message
      // explicite pour que ça ne ressemble jamais à un bug silencieux.
      geometries = _gatherZoneGeometries(racineSlug, racineSlug, null);
      if (statusEl) statusEl.textContent = _MSG_REPLI_SOUS_ZONE;
    } else if (statusEl && statusEl.textContent === _MSG_REPLI_SOUS_ZONE) {
      statusEl.textContent = '';
    }
  }

  if (!geometries.length) return;

  let union = geometries[0];
  for (let i = 1; i < geometries.length; i++) {
    try {
      union = turf.union(union, geometries[i]);
    } catch (e) {
      console.warn('turf.union a échoué sur une géométrie (ignorée pour le contour)', e);
    }
  }
  if (!union) return;

  CarteState.surligneLayer = L.geoJSON(union, {
    style: { fill: false, weight: 4, color: '#ff5500' },
    interactive: false,
  }).addTo(CarteState.map);
}

// ── Villes principales (12 sept 2026) ───────────────────────────────────

function toggleVillesPrincipales() {
  CarteState.villesVisibles = !CarteState.villesVisibles;
  const btn = document.getElementById('carte-toggle-villes');
  if (btn) btn.classList.toggle('active', CarteState.villesVisibles);
  renderVillesLayer();
}

function renderVillesLayer() {
  if (CarteState.villesLayer) {
    CarteState.map.removeLayer(CarteState.villesLayer);
    CarteState.villesLayer = null;
  }
  if (!CarteState.villesVisibles || !CarteState.villes?.length) return;

  // Un seul style de marqueur pour toutes les villes (12 sept 2026, sur
  // demande de David -- avant, distinction capitale/autre ville).
  const markers = CarteState.villes.map(v => {
    const marker = L.circleMarker([v.lat, v.lon], {
      radius: 3.5,
      weight: 1,
      color: '#fff',
      fillColor: '#333',
      fillOpacity: 0.9,
    });
    const pop = v.population ? `${v.population.toLocaleString('fr-FR')} hab.` : '';
    marker.bindTooltip(`${v.nom}${pop ? ' — ' + pop : ''}`, { sticky: true });
    return marker;
  });

  CarteState.villesLayer = L.layerGroup(markers).addTo(CarteState.map);
}


// ── Overlays custom : dessin, création, suppression (26 août 2026) ─────────

function initCarteDessin() {
  CarteState.drawnItemsLayer = new L.FeatureGroup();
  CarteState.map.addLayer(CarteState.drawnItemsLayer);

  CarteState.drawControl = new L.Control.Draw({
    position: 'topright',
    draw: {
      polygon: {
        allowIntersection: false,
        showArea: true,
        shapeOptions: { color: '#ff5500', weight: 2 },
      },
      // Seul le polygone est utile ici -- pas de marqueurs/lignes/rectangles
      // pour cet usage (frontières de zones).
      polyline: false,
      rectangle: false,
      circle: false,
      circlemarker: false,
      marker: false,
    },
    edit: {
      featureGroup: CarteState.drawnItemsLayer,
      remove: false,  // suppression gérée via notre propre bouton (voir _supprimerOverlay),
                       // pas via l'outil d'édition générique de Leaflet.Draw
    },
  });
  // Le contrôle (barre d'icônes) reste ajouté en permanence une fois le mode
  // dessin actif -- mais on ne compte plus sur le clic manuel sur son icône
  // polygone (source de confusion, bug remonté par David le 8 sept : la
  // barre apparaissait mais cliquer sur la carte sélectionnait un pays au
  // lieu de dessiner). L'outil polygone est démarré directement par code
  // dans toggleModeDessin()/onCarteOverlayDrawCreated().
  CarteState.drawPolygonHandler = new L.Draw.Polygon(CarteState.map, CarteState.drawControl.options.draw.polygon);

  CarteState.map.on(L.Draw.Event.CREATED, (e) => {
    if (CarteState.modeDessinZoneComplete) onZoneCompleteDrawCreated(e);
    else onCarteOverlayDrawCreated(e);
  });
}

function toggleModeDessin() {
  CarteState.modeDessin = !CarteState.modeDessin;
  const btn = document.getElementById('carte-toggle-dessin');

  if (CarteState.modeDessin) {
    CarteState.map.addControl(CarteState.drawControl);
    CarteState.drawPolygonHandler.enable();  // démarre directement l'outil, pas besoin de cliquer l'icône
    if (btn) btn.textContent = '✖ Annuler le dessin';
    document.getElementById('carte-status').textContent =
      'Mode dessin actif — clique sur la carte pour poser chaque sommet du polygone, double-clic pour le fermer.';
  } else {
    CarteState.drawPolygonHandler.disable();
    CarteState.map.removeControl(CarteState.drawControl);
    CarteState.drawnItemsLayer.clearLayers();
    if (btn) btn.textContent = '✏️ Dessiner un overlay';
    document.getElementById('carte-status').textContent = '';
  }
}

async function onCarteOverlayDrawCreated(e) {
  const layer = e.layer;
  CarteState.drawnItemsLayer.addLayer(layer);
  const geometry = layer.toGeoJSON().geometry;

  // Leaflet.Draw désactive l'outil une fois un polygone terminé -- on le
  // relance immédiatement si le mode dessin est toujours actif, pour
  // enchaîner plusieurs overlays sans re-cliquer sur le bouton à chaque fois.
  const _relancerSiModeActif = () => {
    if (CarteState.modeDessin) CarteState.drawPolygonHandler.enable();
  };

  const scenario = CarteState.scenario;
  // Panneau unique (12 sept 2026) : si un dessin a été lancé depuis le
  // panneau d'une zone précise, on saute le sélecteur générique -- usage
  // unique, retombe ensuite sur le sélecteur classique pour le prochain
  // polygone si le mode dessin reste actif.
  const zonePreselectionnee = CarteState.dessinZonePreselectionnee;
  CarteState.dessinZonePreselectionnee = null;
  const zoneSlug = zonePreselectionnee || await _promptZoneSlug(scenario);
  if (!zoneSlug) {
    CarteState.drawnItemsLayer.clearLayers();
    _relancerSiModeActif();
    return;
  }

  const paysPreselectionne = CarteState.dessinPaysPreselectionne;
  CarteState.dessinPaysPreselectionne = null;
  const choixPays = paysPreselectionne
    ? { pays: paysPreselectionne, estNouveau: false }
    : await _promptPays(scenario, zoneSlug);
  if (!choixPays) {
    CarteState.drawnItemsLayer.clearLayers();
    _relancerSiModeActif();
    return;
  }
  const { pays, estNouveau } = choixPays;

  let portion = '';
  if (estNouveau) {
    portion = await _promptPortion(pays);
    if (!portion) {
      CarteState.drawnItemsLayer.clearLayers();
      _relancerSiModeActif();
      return;
    }
  }

  const statusEl = document.getElementById('carte-status');
  statusEl.textContent = 'Enregistrement du polygone…';

  try {
    const res = await fetch('/api/carte/overlays/creer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, zone_slug: zoneSlug, pays, geometry, portion }),
    });
    const data = await res.json();
    if (data.error) {
      statusEl.textContent = `Erreur : ${data.error}`;
      _relancerSiModeActif();
      return;
    }
    statusEl.textContent = data.origine_reelle_creee
      ? `Overlay créé, origine_reelle ajoutée à '${zoneSlug}' (${data.total_features} overlay(s) au total).`
      : `Overlay créé (${data.total_features} au total pour ce scénario).`;
    CarteState.drawnItemsLayer.clearLayers();
    await refreshCarte();  // recharge overlays + réaffiche
    if (zonePreselectionnee) openRenommerZonePanel(zonePreselectionnee);  // réaffiche le panneau à jour
    _relancerSiModeActif();
  } catch (err) {
    statusEl.textContent = `Erreur réseau : ${err.message}`;
    _relancerSiModeActif();
  }
}

// ── S11 : "Dessiner une zone complète" (9 sept 2026) ────────────────────────
// Mode de dessin distinct de l'overlay ci-dessus -- ici on dessine le
// contour complet d'une NOUVELLE zone, sans se soucier des frontières de
// pays en dessous, et zone_dessin_complet.py déduit automatiquement quels
// pays sont entièrement couverts (split) vs partiellement (overlay).
// Doctrine génération/application séparée : /proposer ne modifie jamais le
// vault, l'application ci-dessous réutilise /api/carte/assign,
// /api/carte/creer_zone_vide et /api/carte/overlays/creer -- déjà testées,
// pas de nouveau mécanisme d'écriture.

function toggleModeDessinZoneComplete() {
  CarteState.modeDessinZoneComplete = !CarteState.modeDessinZoneComplete;
  const btn = document.getElementById('carte-toggle-dessin-zone-complete');

  if (CarteState.modeDessinZoneComplete) {
    // Mutuellement exclusif avec le mode overlay existant -- pas de sens
    // à avoir les deux modes de dessin actifs en même temps.
    if (CarteState.modeDessin) toggleModeDessin();
    CarteState.map.addControl(CarteState.drawControl);
    CarteState.drawPolygonHandler.enable();
    if (btn) btn.textContent = '✖ Annuler le dessin';
    document.getElementById('carte-status').textContent =
      'Mode "zone complète" actif — dessine le contour complet de la nouvelle zone (peu importe les frontières en dessous), double-clic pour fermer.';
  } else {
    CarteState.drawPolygonHandler.disable();
    CarteState.map.removeControl(CarteState.drawControl);
    CarteState.drawnItemsLayer.clearLayers();
    if (btn) btn.textContent = '🗺️ Dessiner une zone complète';
    document.getElementById('carte-status').textContent = '';
  }
}

// ── S11 : sélecteur de cible (nouvelle zone vs zone existante) ─────────────
// Même leçon que le bug Allemagne/Norvège (8 sept) : l'option "créer" doit
// être visible en tête de liste, pas perdue en bas -- réutilise le même
// sélecteur générique (_pickFromList) que _promptZoneSlug/_promptPays.
async function _promptCibleZoneComplete(scenario) {
  const statusEl = document.getElementById('carte-status');
  let zones = [];
  try {
    const res = await fetch(`/api/carte/zones_toutes?scenario=${encodeURIComponent(scenario)}`);
    const data = await res.json();
    zones = data.zones || [];
  } catch (e) {
    statusEl.textContent = `Erreur réseau (liste des zones) : ${e.message}`;
    return null;
  }

  const items = [
    { label: '➕ Créer une nouvelle zone', value: '__nouvelle__' },
    ...zones
      .slice()
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'))
      .map(z => ({ label: `${z.nom}  —  ${z.slug} (niveau ${z.niveau})`, value: z.slug })),
  ];

  const choix = await _pickFromList('Zone cible pour ce dessin', items);
  if (choix === null) return null;

  if (choix === '__nouvelle__') {
    const nom = (window.prompt('Nom de la nouvelle zone :') || '').trim();
    if (!nom) return null;
    return { mode: 'nouvelle', nom, slug: null };
  }

  const zoneChoisie = zones.find(z => z.slug === choix);
  return { mode: 'existante', nom: zoneChoisie ? zoneChoisie.nom : choix, slug: choix };
}

async function onZoneCompleteDrawCreated(e) {
  const layer = e.layer;
  CarteState.drawnItemsLayer.addLayer(layer);
  const geometry = layer.toGeoJSON().geometry;
  const scenario = CarteState.scenario;

  const cible = await _promptCibleZoneComplete(scenario);
  if (!cible) {
    CarteState.drawnItemsLayer.clearLayers();
    return;
  }

  const statusEl = document.getElementById('carte-status');
  statusEl.textContent = 'Calcul de la classification en cours (chargement Natural Earth + appels LLM par pays overlay, jusqu\'à 30-60s selon le nombre de pays touchés)…';

  try {
    const [resProp, resAff] = await Promise.all([
      fetch('/api/carte/dessiner_zone_complete/proposer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario, zone_nom: cible.nom, geometry }),
      }),
      // Chargé en parallèle -- sert uniquement à afficher "déjà affecté à
      // <zone>" dans le panneau de review pour les pays en split, avant que
      // l'application n'écrase silencieusement cette affectation (voir
      // /api/carte/assign : retire le pays de toute autre zone existante,
      // portion ou pays entier, sans avertissement natif).
      fetch(`/api/carte/affectations?scenario=${encodeURIComponent(scenario)}`),
    ]);
    const data = await resProp.json();
    if (data.error) {
      statusEl.textContent = `Erreur : ${data.error}`;
      return;
    }
    const dataAff = await resAff.json();
    const nomParSlug = {};
    (dataAff.zones_n1 || []).forEach(z => { nomParSlug[z.slug] = z.nom; });

    statusEl.textContent = '';
    CarteState.zoneCompleteProposition = {
      ...data, zone_nom: cible.nom, geometry, cible,
      affectations_actuelles: dataAff.affectations || {},
      noms_zones_existantes: nomParSlug,
    };
    _renderZoneCompletePanel();
  } catch (err) {
    statusEl.textContent = `Erreur réseau : ${err.message}`;
  }
}

function _renderZoneCompletePanel() {
  const prop = CarteState.zoneCompleteProposition;
  const panel = document.getElementById('carte-panel');
  if (!prop) return;
  const cibleExistante = prop.cible?.mode === 'existante';

  const rows = prop.classification
    .map((c, i) => ({ c, i }))
    .filter(({ c }) => c.classification !== 'ignore_bruit')
    .map(({ c, i }) => {
    const badge = c.classification === 'split'
      ? '<span style="color:#2a7d2a;font-weight:bold;">SPLIT (pays entier)</span>'
      : '<span style="color:#b5760a;font-weight:bold;">OVERLAY (portion)</span>';

    // Avertissement "déjà affecté" -- seulement pertinent/fiable pour les
    // splits : /api/carte/affectations ne reflète que les affectations
    // pays-entier (zones_pays.json), pas les portions overlay des AUTRES
    // zones (non détectable sans intersection géométrique -- pas fait ici).
    // Si la cible EST déjà cette même zone (mode existante), ce n'est pas
    // un vol d'un pays à une autre zone -- pas d'avertissement dans ce cas.
    let dejaAffecte = '';
    if (c.classification === 'split') {
      const slugExistant = prop.affectations_actuelles?.[c.pays];
      if (slugExistant && slugExistant !== prop.cible?.slug) {
        const nomExistant = prop.noms_zones_existantes?.[slugExistant] || slugExistant;
        dejaAffecte = `<div style="font-size:11px;color:#b5760a;margin-top:2px;">⚠ déjà affecté (pays entier) à <strong>${nomExistant}</strong> — sera retiré de cette zone si tu appliques</div>`;
      }
    }

    const portionField = c.classification === 'overlay'
      ? `<textarea class="zc-portion" data-idx="${i}" rows="2" style="width:100%;font-size:12px;margin-top:4px;box-sizing:border-box;">${(c.portion_proposee || '').replace(/</g, '&lt;')}</textarea>
         ${c.portion_erreur ? `<div style="color:#b00;font-size:11px;">Erreur LLM (rédaction manuelle nécessaire) : ${c.portion_erreur}</div>` : ''}`
      : '';
    return `
      <div class="enrichissement-item" style="border:1px solid #eee;border-radius:4px;padding:8px;margin-bottom:6px;">
        <label style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;">
          <span><input type="checkbox" class="zc-inclure" data-idx="${i}" checked> <strong>${c.pays}</strong> — ${c.couverture_pct}% ${badge}</span>
        </label>
        ${dejaAffecte}
        ${portionField}
      </div>`;
  }).join('');

  // Portions sous le seuil de bruit (14 sept 2026) -- non cochées par
  // défaut (le seuil reste la présomption raisonnable : imprécision de
  // dessin à main levée), mais listées avec un texte `portion` à rédiger
  // à la main pour le cas où la petite portion est réelle et voulue.
  // Cochées, elles rejoignent exactement le même circuit d'application
  // qu'un overlay normal (voir _appliquerZoneComplete) -- même indices
  // data-idx que dans le tableau `prop.classification` d'origine, pour
  // que la relecture au clic sur "Appliquer" reste cohérente.
  const rowsIgnorees = prop.classification
    .map((c, i) => ({ c, i }))
    .filter(({ c }) => c.classification === 'ignore_bruit')
    .map(({ c, i }) => `
      <div class="enrichissement-item" style="border:1px solid #eee;border-radius:4px;padding:8px;margin-bottom:6px;opacity:0.75;">
        <label style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;">
          <span><input type="checkbox" class="zc-inclure" data-idx="${i}"> <strong>${c.pays}</strong> — ${c.couverture_pct}% <span style="color:#888;">sous le seuil de bruit (${prop.seuil_bruit}%)</span></span>
        </label>
        <textarea class="zc-portion" data-idx="${i}" rows="2" style="width:100%;font-size:12px;margin-top:4px;box-sizing:border-box;" placeholder="Texte portion (à rédiger à la main si tu inclus quand même) -- vide par défaut, pas de génération LLM automatique sur ces cas"></textarea>
      </div>`).join('');

  const sectionIgnorees = rowsIgnorees
    ? `<details style="margin:8px 0;">
         <summary style="cursor:pointer;font-size:12px;color:#888;">Portions sous le seuil de bruit, ignorées par défaut (${prop.classification.filter(c => c.classification === 'ignore_bruit').length}) — coche pour inclure quand même</summary>
         <div style="margin-top:6px;">${rowsIgnorees}</div>
       </details>`
    : '';

  const avertissement = (prop.petits_pays_non_verifiables || []).length
    ? `<div style="font-size:11px;color:#888;margin:6px 0;">${prop.avertissement_petits_pays}</div>`
    : '';

  const avertissementOverlay = prop.classification.some(c => c.classification === 'overlay')
    ? `<div style="font-size:11px;color:#888;margin:6px 0;">Note : les overlays existants d'autres zones ne sont pas vérifiés automatiquement -- si cette zone chevauche géographiquement une portion déjà dessinée ailleurs, rien ne le signalera ici.</div>`
    : '';

  // Zone cible : slug/description saisis seulement pour une NOUVELLE zone --
  // pour une zone existante, ces informations sont déjà connues (slug
  // choisi dans le sélecteur, description déjà en place, jamais écrasée).
  const cibleHtml = cibleExistante
    ? `<div class="carte-panel-sub">Zone cible : <strong>${prop.cible.nom}</strong> (${prop.cible.slug}) — zone existante, pays ajoutés à sa liste actuelle</div>`
    : `
      <label style="display:block;margin:8px 0;">Slug de la nouvelle zone : <input type="text" id="zc-slug" style="width:100%;box-sizing:border-box;" placeholder="ex. zone_test"></label>
      <label style="display:block;margin:8px 0;">Description : <textarea id="zc-description" rows="2" style="width:100%;box-sizing:border-box;"></textarea></label>
    `;

  panel.innerHTML = `
    <div class="carte-panel-title">${cibleExistante ? 'Ajout à' : 'Nouvelle zone'} : ${prop.zone_nom}</div>
    <div class="carte-panel-sub">${prop.classification.filter(c => c.classification !== 'ignore_bruit').length} pays concernés (seuils ${prop.seuil_split}% / ${prop.seuil_bruit}%) — décoche ceux à exclure, ajuste les textes avant d'appliquer</div>
    ${avertissement}
    ${avertissementOverlay}
    <div id="zc-liste">${rows}</div>
    ${sectionIgnorees}
    ${cibleHtml}
    <div style="display:flex;gap:8px;">
      <button class="btn-primary" id="zc-appliquer-btn">✓ Appliquer</button>
      <button class="btn-secondary" id="zc-annuler-btn">✕ Annuler</button>
    </div>
    <div id="zc-resultat" style="margin-top:8px;"></div>
  `;

  document.getElementById('zc-appliquer-btn').addEventListener('click', _appliquerZoneComplete);
  document.getElementById('zc-annuler-btn').addEventListener('click', _annulerZoneComplete);
}

function _annulerZoneComplete() {
  CarteState.zoneCompleteProposition = null;
  CarteState.drawnItemsLayer.clearLayers();
  const panel = document.getElementById('carte-panel');
  panel.innerHTML = '';
  document.getElementById('carte-status').textContent = '';
  // Si le mode dessin est toujours actif, relance directement l'outil
  // polygone pour permettre un nouvel essai sans re-cliquer le bouton.
  if (CarteState.modeDessinZoneComplete) CarteState.drawPolygonHandler.enable();
}

async function _appliquerZoneComplete() {
  const prop = CarteState.zoneCompleteProposition;
  const scenario = CarteState.scenario;
  const cibleExistante = prop.cible?.mode === 'existante';
  const resultatEl = document.getElementById('zc-resultat');

  // Slug/nom/description dépendent du mode -- pour une zone existante, tout
  // vient déjà du sélecteur (_promptCibleZoneComplete), pas de champs à lire.
  const slug = cibleExistante ? prop.cible.slug : (document.getElementById('zc-slug').value || '').trim();
  const description = cibleExistante ? '' : (document.getElementById('zc-description').value || '').trim();

  if (!slug) {
    resultatEl.innerHTML = `<div class="carte-panel-error">Slug requis.</div>`;
    return;
  }

  // Avertissement (pas un blocage) si le nom choisi correspond déjà à une
  // zone existante -- non pertinent en mode "zone existante" (c'est
  // délibérément la même zone). Le slug reste la vraie clé d'identité
  // (vérifié côté serveur), mais deux zones au même nom affiché sont
  // indiscernables dans les listes déroulantes de l'appli.
  if (!cibleExistante) {
    const nomExistantIdentique = Object.values(prop.noms_zones_existantes || {})
      .some(n => n.trim().toLowerCase() === prop.zone_nom.trim().toLowerCase());
    if (nomExistantIdentique) {
      const confirme = window.confirm(
        `Une zone nommée "${prop.zone_nom}" existe déjà (slug différent). ` +
        `Les deux zones porteront le même nom affiché, ce qui peut prêter à confusion ` +
        `dans les listes déroulantes. Continuer quand même ?`
      );
      if (!confirme) return;
    }
  }

  const btn = document.getElementById('zc-appliquer-btn');
  btn.disabled = true;
  btn.textContent = 'Application…';

  // Relit l'état des checkboxes/textarea au moment du clic -- l'utilisateur
  // a pu les modifier après la génération initiale (décocher un pays,
  // retoucher un texte portion).
  const entries = prop.classification.map((c, i) => {
    const inclure = document.querySelector(`.zc-inclure[data-idx="${i}"]`).checked;
    const portionEl = document.querySelector(`.zc-portion[data-idx="${i}"]`);
    return { ...c, inclure, portion_finale: portionEl ? portionEl.value.trim() : null };
  }).filter(en => en.inclure);

  const splits = entries.filter(en => en.classification === 'split');
  // ignore_bruit coché rejoint le même traitement qu'un overlay normal --
  // même route /api/carte/overlays/creer, même champs (geometry toujours
  // présente pour ce type depuis le correctif du 14 sept, portion_finale
  // rédigée à la main par l'utilisateur puisqu'aucune génération LLM
  // automatique n'a lieu sur ces entrées).
  const overlays = entries.filter(en => en.classification === 'overlay' || en.classification === 'ignore_bruit');

  if (!splits.length && !overlays.length) {
    resultatEl.innerHTML = `<div class="carte-panel-error">Aucun pays sélectionné.</div>`;
    btn.disabled = false;
    btn.textContent = '✓ Appliquer';
    return;
  }

  const journal = [];
  try {
    if (cibleExistante) {
      // Zone déjà là -- tous les splits utilisent "absorber", jamais
      // "creer" ; pas besoin de /api/carte/creer_zone_vide non plus.
      for (const s of splits) {
        const r = await fetch('/api/carte/assign', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario, pays: s.pays, action: 'absorber', zone_slug: slug }),
        });
        const d = await r.json();
        if (d.error) throw new Error(`${s.pays} (split) : ${d.error}`);
        journal.push(`✓ ${s.pays} rattaché (pays entier)`);
      }
    } else if (splits.length) {
      // Le premier split crée la zone (associée à un pays entier, même
      // route /api/carte/assign que le flux manuel existant) ; les
      // suivants l'absorbent -- pas de nouveau mécanisme d'écriture.
      const premier = splits[0];
      const resCreer = await fetch('/api/carte/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario, pays: premier.pays, action: 'creer',
          nouvelle_zone: { slug, nom: prop.zone_nom, description },
        }),
      });
      const dataCreer = await resCreer.json();
      if (dataCreer.error) throw new Error(`Création zone (${premier.pays}) : ${dataCreer.error}`);
      journal.push(`✓ Zone créée, ${premier.pays} rattaché (pays entier)`);

      for (const s of splits.slice(1)) {
        const r = await fetch('/api/carte/assign', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario, pays: s.pays, action: 'absorber', zone_slug: slug }),
        });
        const d = await r.json();
        if (d.error) throw new Error(`${s.pays} (split) : ${d.error}`);
        journal.push(`✓ ${s.pays} rattaché (pays entier)`);
      }
    } else {
      // Aucun split -- la zone n'existerait sinon jamais, d'où
      // /api/carte/creer_zone_vide.
      const resVide = await fetch('/api/carte/creer_zone_vide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario, slug, nom: prop.zone_nom, niveau: 1, parent: null, description }),
      });
      const dataVide = await resVide.json();
      if (dataVide.error) throw new Error(`Création zone vide : ${dataVide.error}`);
      journal.push(`✓ Zone créée (sans pays entier)`);
    }

    for (const o of overlays) {
      const r = await fetch('/api/carte/overlays/creer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario, zone_slug: slug, pays: o.pays,
          geometry: o.geometry, portion: o.portion_finale,
        }),
      });
      const d = await r.json();
      if (d.error) throw new Error(`${o.pays} (overlay) : ${d.error}`);
      journal.push(`✓ ${o.pays} rattaché en overlay`);
    }

    resultatEl.innerHTML = `<div style="color:#2a7d2a;font-size:12px;">${journal.join('<br>')}</div>`;
    btn.textContent = '✓ Appliqué';
    CarteState.drawnItemsLayer.clearLayers();
    await refreshCarte();
  } catch (err) {
    // Arrêt en cours de route (ex. 3e overlay échoue après que la zone et
    // 2 overlays ont déjà été écrits) -- volontairement PAS de retry
    // automatique ni de rollback : le journal partiel reste affiché pour
    // que David sache exactement où ça s'est arrêté et vérifie l'état réel
    // (arborescence / gérer les overlays) avant de rejouer le reste à la
    // main si besoin.
    resultatEl.innerHTML = `
      <div style="color:#2a7d2a;font-size:12px;">${journal.join('<br>')}</div>
      <div class="carte-panel-error">Arrêté en cours de route : ${err.message}</div>
      <div style="font-size:11px;color:#888;">La zone a peut-être été partiellement créée — vérifie dans l'arborescence ou dans le panneau "✏️ éditer" de la zone avant de relancer.</div>
    `;
    btn.disabled = false;
    btn.textContent = 'Réessayer';
  }
}

// ── Petit sélecteur générique (liste filtrable cliquable) ──────────────────
// Remplace window.prompt() pour zone_slug et pays : évite les fautes de
// frappe sur un slug tapé à la main (bug remonté par David le 8 sept --
// "zone 'zone Hartlepool' introuvable", nom inventé au lieu du vrai slug).
// Pas de composant modal existant ailleurs dans app.js, donc autonome
// (styles injectés en JS, pas de dépendance à style.css).
function _pickFromList(titre, items) {
  // items : [{label, value}]. Résout `value` au clic, ou null si annulé
  // (bouton Annuler ou touche Échap).
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:9999;display:flex;align-items:center;justify-content:center;';

    const box = document.createElement('div');
    box.style.cssText = 'background:#fff;border-radius:8px;padding:16px;width:360px;max-height:70vh;display:flex;flex-direction:column;box-shadow:0 4px 24px rgba(0,0,0,0.3);';

    const h = document.createElement('div');
    h.textContent = titre;
    h.style.cssText = 'font-weight:600;margin-bottom:8px;font-size:14px;';

    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Filtrer…';
    input.style.cssText = 'padding:6px 8px;border:1px solid #ccc;border-radius:4px;margin-bottom:8px;font-size:13px;';

    const list = document.createElement('div');
    list.style.cssText = 'overflow-y:auto;flex:1;border:1px solid #eee;border-radius:4px;';

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Annuler';
    cancelBtn.className = 'btn-secondary';
    cancelBtn.style.cssText = 'margin-top:10px;align-self:flex-end;';

    function cleanup(result) {
      document.removeEventListener('keydown', onKeydown);
      overlay.remove();
      resolve(result);
    }
    function onKeydown(e) { if (e.key === 'Escape') cleanup(null); }

    function renderList(filter) {
      list.innerHTML = '';
      const f = (filter || '').toLowerCase();
      const filtered = items.filter(it => it.label.toLowerCase().includes(f));
      if (!filtered.length) {
        const empty = document.createElement('div');
        empty.textContent = 'Aucun résultat.';
        empty.style.cssText = 'padding:8px;color:#888;font-size:12px;';
        list.appendChild(empty);
        return;
      }
      filtered.forEach(it => {
        const row = document.createElement('div');
        row.textContent = it.label;
        row.style.cssText = 'padding:6px 8px;cursor:pointer;font-size:13px;border-bottom:1px solid #f0f0f0;';
        row.addEventListener('mouseenter', () => row.style.background = '#f0f4ff');
        row.addEventListener('mouseleave', () => row.style.background = '');
        row.addEventListener('click', () => cleanup(it.value));
        list.appendChild(row);
      });
    }

    input.addEventListener('input', () => renderList(input.value));
    cancelBtn.addEventListener('click', () => cleanup(null));
    overlay.addEventListener('click', (e) => { if (e.target === overlay) cleanup(null); });
    document.addEventListener('keydown', onKeydown);

    box.appendChild(h);
    box.appendChild(input);
    box.appendChild(list);
    box.appendChild(cancelBtn);
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    renderList('');
    input.focus();
  });
}

async function _promptZoneSlug(scenario) {
  const statusEl = document.getElementById('carte-status');
  let zones = [];
  try {
    const res = await fetch(`/api/carte/zones_toutes?scenario=${encodeURIComponent(scenario)}`);
    const data = await res.json();
    zones = data.zones || [];
  } catch (e) {
    statusEl.textContent = `Erreur réseau (liste des zones) : ${e.message}`;
    return null;
  }

  const items = [
    { label: '+ Créer une nouvelle zone niveau 1…', value: '__creer__' },
    ...zones.map(z => ({ label: `${z.nom}  —  ${z.slug} (niveau ${z.niveau})`, value: z.slug })),
  ];

  const choix = await _pickFromList('Zone concernée par ce polygone', items);
  if (!choix) return null;

  if (choix === '__creer__') {
    return await _creerNouvelleZoneN1(scenario);
  }
  return choix;
}

async function _creerNouvelleZoneN1(scenario) {
  const statusEl = document.getElementById('carte-status');
  const slug = (window.prompt('Slug de la nouvelle zone (minuscules_underscores) :') || '').trim();
  if (!slug) return null;
  const nom = (window.prompt('Nom affiché de la nouvelle zone :') || '').trim();
  if (!nom) return null;
  const description = (window.prompt('Description courte (optionnel) :') || '').trim();

  statusEl.textContent = `Création de la zone '${slug}'…`;
  try {
    const res = await fetch('/api/carte/creer_zone_vide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, slug, nom, niveau: 1, parent: null, description }),
    });
    const data = await res.json();
    if (data.error) {
      statusEl.textContent = `Erreur : ${data.error}`;
      return null;
    }
    statusEl.textContent = `Zone '${nom}' créée.`;
    return data.slug;
  } catch (e) {
    statusEl.textContent = `Erreur réseau (création de zone) : ${e.message}`;
    return null;
  }
}

async function _promptPays(scenario, zoneSlug) {
  // Liste complète des ~200 pays réels (pays_liste), avec les pays déjà
  // présents dans origine_reelle de cette zone marqués d'un ✓ -- fusion en
  // UNE liste plutôt que deux étapes séparées ("déjà là" vs "Autre" en
  // saisie libre), corrige deux problèmes remontés par David le 8 sept :
  // le nom "Autre pays" perdu en fin de liste (overlay créé par erreur sur
  // la Norvège au lieu de l'Allemagne), et le risque de faute de frappe
  // sur un nom de pays tapé à la main.
  let paysExistants = new Set();
  let paysListe = [];
  try {
    const [resArbre, resAff] = await Promise.all([
      fetch(`/api/carte/arbre_zone?scenario=${encodeURIComponent(scenario)}&slug=${encodeURIComponent(zoneSlug)}`),
      fetch(`/api/carte/affectations?scenario=${encodeURIComponent(scenario)}`),
    ]);
    const dataArbre = await resArbre.json();
    paysExistants = new Set((dataArbre?.arbre?.origine_reelle || []).map(o => o.entite).filter(Boolean));
    const dataAff = await resAff.json();
    paysListe = dataAff.pays_liste || [];
  } catch (e) {
    document.getElementById('carte-status').textContent = `Erreur réseau (liste des pays) : ${e.message}`;
    return null;
  }

  const items = paysListe
    .slice()
    .sort((a, b) => a.localeCompare(b, 'fr'))
    .map(p => ({
      label: paysExistants.has(p) ? `${p}  ✓ déjà dans la zone` : p,
      value: p,
    }));

  const choix = await _pickFromList(`Pays couvert par ce polygone (zone '${zoneSlug}')`, items);
  if (!choix) return null;
  return { pays: choix, estNouveau: !paysExistants.has(choix) };
}

async function _promptPortion(pays) {
  // Demandée uniquement pour un pays PAS encore dans origine_reelle -- décrit
  // la portion couverte par le polygone qu'on vient de dessiner (ex. "nord",
  // "la moitié sud, au-delà de la zone tampon"). Écrite telle quelle dans
  // origine_reelle côté serveur -- voir /api/carte/overlays/creer.
  const saisie = window.prompt(
    `Description de la portion de ${pays} couverte par ce polygone (ex. "nord", "sud, au-delà des Pyrénées") :`
  );
  return (saisie || '').trim();
}

function onCarteZoneOverlayClick(props) {
  const slug = props?.zone_slug || null;
  if (!slug) return;

  if (CarteState.modeDessin) {
    // En mode dessin, un clic sur un overlay existant propose sa suppression
    // plutôt que de surligner (évite la confusion avec le mode consultation).
    if (window.confirm(`Supprimer cet overlay (${slug} / ${props.pays}) ?`)) {
      _supprimerOverlay(props.id);
    }
    return;
  }

  CarteState.zoneSurlignee = (CarteState.zoneSurlignee === slug) ? null : slug;
  renderCarteLayer();
  renderCarteLegend();
}

async function _supprimerOverlay(id) {
  const statusEl = document.getElementById('carte-status');
  try {
    const res = await fetch('/api/carte/overlays/supprimer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, id }),
    });
    const data = await res.json();
    if (data.error) {
      statusEl.textContent = `Erreur : ${data.error}`;
      return;
    }
    statusEl.textContent = `Overlay supprimé (${data.total_features} restant(s)).`;
    await refreshCarte();
  } catch (e) {
    statusEl.textContent = `Erreur réseau : ${e.message}`;
  }
}

/**
 * Recherche de zone tous niveaux (14 juillet 2026) : la légende et la carte
 * n'affichent que les zones niveau 1 (voir renderCarteLegend / zones_n1 côté
 * backend) -- une zone niveau 2/3 comme delta_rhone_fermes_verticales reste
 * invisible tant qu'on n'a pas ouvert l'arbre de SA racine N1, qui n'est pas
 * forcément son parent immédiat. Ce champ cherche tous niveaux via
 * /api/carte/rechercher_zone et ouvre directement le bon arbre au clic.
 */
function initCarteSearch() {
  const input = document.getElementById('carte-search-input');
  if (!input || input.dataset.bound) return;
  input.dataset.bound = '1';

  input.addEventListener('input', () => {
    clearTimeout(CarteState.searchDebounceTimer);
    const q = input.value.trim();
    const resultsEl = document.getElementById('carte-search-results');
    if (q.length < 2) {
      resultsEl.innerHTML = '';
      resultsEl.style.display = 'none';
      return;
    }
    CarteState.searchDebounceTimer = setTimeout(() => _carteRechercherZone(q), 250);
  });

  document.addEventListener('click', (e) => {
    const resultsEl = document.getElementById('carte-search-results');
    if (resultsEl && !e.target.closest('.carte-search')) {
      resultsEl.style.display = 'none';
    }
  });
}

async function _carteRechercherZone(q) {
  const resultsEl = document.getElementById('carte-search-results');
  try {
    const res = await fetch(
      `/api/carte/rechercher_zone?scenario=${encodeURIComponent(CarteState.scenario)}&q=${encodeURIComponent(q)}`
    );
    const data = await res.json();
    if (data.error) {
      resultsEl.innerHTML = `<div class="carte-search-empty">${data.error}</div>`;
      resultsEl.style.display = 'block';
      return;
    }
    if (!data.resultats.length) {
      resultsEl.innerHTML = `<div class="carte-search-empty">Aucune zone trouvée.</div>`;
      resultsEl.style.display = 'block';
      return;
    }
    resultsEl.innerHTML = data.resultats.map(r => {
      const cheminLabel = r.chemin.map(c => c.nom).join(' › ');
      return `
        <div class="carte-search-result" data-slug="${r.slug}">
          <span class="carte-search-result-nom">${r.nom}</span>
          <span class="carte-search-result-niveau">N${r.niveau}</span>
          <div class="carte-search-result-chemin">${cheminLabel}</div>
        </div>`;
    }).join('');
    resultsEl.style.display = 'block';

    resultsEl.querySelectorAll('.carte-search-result').forEach((el, i) => {
      el.addEventListener('click', () => _carteSelectionnerResultatRecherche(data.resultats[i]));
    });
  } catch (e) {
    resultsEl.innerHTML = `<div class="carte-search-empty">Erreur réseau : ${e.message}</div>`;
    resultsEl.style.display = 'block';
  }
}

/**
 * Ouvre la racine N1 du résultat choisi (seule vue possible, voir
 * openArbreZonePanel) puis surligne et centre la zone recherchée dans
 * l'arbre déplié -- évite d'avoir à deviner/remonter la chaîne à la main
 * (cas réel du 14 juillet : delta_rhone_fermes_verticales, niveau 3, dont
 * le parent immédiat corridor_iberique_energetique n'est lui-même pas la
 * racine attendue).
 */
async function _carteSelectionnerResultatRecherche(resultat) {
  document.getElementById('carte-search-results').style.display = 'none';
  document.getElementById('carte-search-input').value = resultat.nom;

  const racineSlug = (resultat.chemin && resultat.chemin[0] && resultat.chemin[0].slug) || resultat.slug;
  await openArbreZonePanel(racineSlug, { skipHighlight: true });

  const noeud = document.querySelector(`#arbre-zone-tree [data-slug="${CSS.escape(resultat.slug)}"]`);
  if (noeud) {
    noeud.scrollIntoView({ behavior: 'smooth', block: 'center' });
    noeud.classList.add('surlignee-recherche');
    setTimeout(() => noeud.classList.remove('surlignee-recherche'), 2500);
  }

  // Localiser sur la carte (12 sept 2026) : avant, seule la surbrillance
  // texte dans l'arbre existait -- une sous-zone n'apparaissait nulle part
  // sur la carte elle-même. openArbreZonePanel vient de peupler
  // racineParSlug/origineReelleParSlug pour tout l'arbre affiché, donc
  // renderSurlignageZone (appelé via renderCarteLayer) sait maintenant
  // reconstruire l'emprise de n'importe quel nœud, N1 ou sous-zone.
  CarteState.zoneSurlignee = resultat.slug;
  renderCarteLayer();
}

function renderCarteLegend() {
  const legendEl = document.getElementById('carte-legend');
  legendEl.innerHTML = CarteState.zonesN1.map(z => {
    let bg = z.color;
    if (z.pattern !== null && z.pattern !== undefined) {
      const angle = PATTERN_ANGLES[z.pattern % PATTERN_ANGLES.length];
      const dark = _darken(z.color, 45);
      bg = `repeating-linear-gradient(${angle}deg, ${z.color}, ${z.color} 3px, ${dark} 3px, ${dark} 6px)`;
    }
    // Zone niveau 2/3 visible sur la carte via un overlay custom (pas un
    // simple pays colorié) -- bordure en pointillés sur la pastille + badge
    // de niveau, pour rester cohérent avec le style pointillé du polygone
    // lui-même sur la carte (voir renderCarteLayer -- dashArray '4 3') et
    // la rendre "observable" comme une vraie zone (demande de David, 8 sept).
    const estOverlay = z.niveau && z.niveau > 1;
    const swatchStyle = estOverlay
      ? `background:${bg};border:2px dashed #333;`
      : `background:${bg}`;
    const badge = estOverlay ? `<span class="carte-legend-badge" title="Zone niveau ${z.niveau}, affichée via overlay">N${z.niveau}</span>` : '';
    const motifBadge = z.motif ? `<span title="Motif personnalisé : ${MOTIFS_LABELS[z.motif] || z.motif}">${(MOTIFS_LABELS[z.motif] || '').split(' ')[0]}</span>` : '';
    return `
    <div class="carte-legend-item" data-slug="${z.slug}">
      <span class="carte-legend-swatch" style="${swatchStyle}"></span>
      <span class="carte-legend-label">${z.nom}</span>
      ${badge}
      ${motifBadge}
      <button class="carte-legend-rename-btn" data-slug="${z.slug}" title="Renommer cette zone">✏️</button>
    </div>`;
  }).join('') + `
    <div class="carte-legend-item">
      <span class="carte-legend-swatch" style="background:#999"></span>
      <span class="carte-legend-label">Non affecté</span>
    </div>
  `;

  legendEl.querySelectorAll('.carte-legend-rename-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openRenommerZonePanel(btn.dataset.slug);
    });
  });

  legendEl.querySelectorAll('.carte-legend-item[data-slug]').forEach(item => {
    item.addEventListener('click', () => openArbreZonePanel(item.dataset.slug));
    item.style.cursor = 'pointer';
  });
}

/**
 * Arbre hiérarchique en lecture seule des sous-zones (P7 étape 2 phase 1,
 * 12 juillet 2026). Les niveaux 2/3 n'ont pas de coordonnées géographiques,
 * donc pas de vraie carte possible pour eux — on affiche la structure
 * parent/niveau déjà présente dans le YAML.
 */
/**
 * Panneau "Zones à enrichir" (8 sept 2026) -- liste les zones du scénario
 * dont tensions_internes ou periode_transition est vide (typiquement issues
 * d'un split via ✂️ scinder), avec génération + application par zone.
 * Même doctrine que le panneau top-down existant : proposition d'abord
 * (jamais d'écriture), application seulement après relecture humaine.
 */
async function openEnrichissementPanel() {
  const scenario = CarteState.scenario;
  if (!scenario) return;

  const panel = document.getElementById('carte-panel');
  panel.innerHTML = `<div class="carte-panel-title">Zones à enrichir</div><div class="carte-status">Chargement…</div>`;

  try {
    const res = await fetch(`/api/carte/zones_manquantes_enrichissement?scenario=${encodeURIComponent(scenario)}`);
    const data = await res.json();
    if (data.error) {
      panel.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
      return;
    }
    const zones = data.zones || [];
    if (!zones.length) {
      panel.innerHTML = `
        <div class="carte-panel-title">Zones à enrichir</div>
        <div class="carte-panel-empty">Aucune zone incomplète dans ce scénario — tensions_internes et periode_transition sont renseignés partout.</div>`;
      return;
    }

    panel.innerHTML = `
      <div class="carte-panel-title">Zones à enrichir (${zones.length})</div>
      <div class="carte-panel-sub">tensions_internes et/ou periode_transition vide</div>
      <div id="enrichissement-liste"></div>
    `;
    const listeEl = document.getElementById('enrichissement-liste');
    zones.forEach(z => {
      const item = document.createElement('div');
      item.className = 'enrichissement-item';
      item.style.cssText = 'border:1px solid #eee;border-radius:4px;padding:8px;margin-bottom:6px;';
      const manque = [
        z.tensions_internes_vide ? 'tensions_internes' : null,
        z.periode_transition_vide ? 'periode_transition' : null,
      ].filter(Boolean).join(', ');
      item.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span><strong>${z.nom}</strong> <span class="carte-legend-badge">N${z.niveau}</span></span>
          <button class="btn-secondary enrichir-generer-btn" data-slug="${z.slug}">Générer</button>
        </div>
        <div style="font-size:11px;color:#888;margin-top:2px;">manque : ${manque}</div>
        <div class="enrichissement-resultat" data-slug="${z.slug}"></div>
      `;
      listeEl.appendChild(item);
    });

    listeEl.querySelectorAll('.enrichir-generer-btn').forEach(btn => {
      btn.addEventListener('click', () => _genererEnrichissement(scenario, btn.dataset.slug));
    });
  } catch (e) {
    panel.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function _genererEnrichissement(scenario, slug) {
  const resultatEl = document.querySelector(`.enrichissement-resultat[data-slug="${slug}"]`);
  resultatEl.innerHTML = `<div class="carte-status">Génération en cours (appel LLM, peut prendre quelques secondes)…</div>`;

  try {
    const res = await fetch('/api/carte/generer_enrichissement_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, slug }),
    });
    const data = await res.json();
    if (data.error) {
      resultatEl.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
      return;
    }
    const p = data.proposition;
    // Champs éditables (23 sept 2026) : la proposition LLM n'était
    // qu'affichée, "Appliquer" renvoyait le texte brut sans possibilité de
    // le retoucher (cas réel : un ancien nom de zone repris par le LLM).
    // Le backend écrit la proposition reçue telle quelle -- on lui envoie
    // donc les valeurs relues/corrigées. Champ vide = null.
    const _st = 'width:100%;box-sizing:border-box;font-size:12px;font-family:inherit;margin:2px 0 6px;';
    resultatEl.innerHTML = `
      <div style="background:#f7f7f7;border-radius:4px;padding:6px;margin-top:6px;font-size:12px;">
        <label><strong>tensions_internes</strong></label>
        <textarea class="enrichir-champ" data-cle="tensions_internes" rows="4" style="${_st}">${_redactionEsc(p.tensions_internes || '')}</textarea>
        <label><strong>periode_transition</strong></label>
        <input type="text" class="enrichir-champ" data-cle="periode_transition" style="${_st}" value="${_redactionEsc(p.periode_transition || '')}">
        <label><strong>evenement_transition</strong> <span style="color:#999">(vide = null)</span></label>
        <textarea class="enrichir-champ" data-cle="evenement_transition" rows="2" style="${_st}">${_redactionEsc(p.evenement_transition || '')}</textarea>
        <div style="color:#888;font-size:11px;">Modifiable avant application -- rien n'est écrit tant que tu n'as pas cliqué.</div>
        <button class="btn-primary enrichir-appliquer-btn" style="margin-top:6px;">✓ Appliquer</button>
      </div>
    `;
    resultatEl.querySelector('.enrichir-appliquer-btn').addEventListener('click', async (e) => {
      resultatEl.querySelectorAll('.enrichir-champ').forEach(el => {
        const v = el.value.trim();
        p[el.dataset.cle] = v === '' ? null : v;
      });
      e.target.disabled = true;
      e.target.textContent = 'Écriture…';
      try {
        const res2 = await fetch('/api/carte/appliquer_enrichissement_zone', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario, slug, proposition: p }),
        });
        const data2 = await res2.json();
        if (data2.error) {
          resultatEl.innerHTML += `<div class="carte-panel-error">Erreur : ${data2.error}</div>`;
          return;
        }
        resultatEl.innerHTML = `<div style="color:#2a7d2a;font-size:12px;">✓ Appliqué.</div>`;
      } catch (err) {
        resultatEl.innerHTML += `<div class="carte-panel-error">Erreur réseau : ${err.message}</div>`;
      }
    });
  } catch (e) {
    resultatEl.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function openArbreZonePanel(slug, options = {}) {
  const panel = document.getElementById('carte-panel');
  panel.innerHTML = `<div class="carte-panel-title">Arborescence</div><div class="carte-status">Chargement…</div>`;

  // skipHighlight (12 sept 2026) : la sélection d'un résultat de recherche
  // vise en réalité une SOUS-ZONE, pas cette racine -- surligner la racine
  // ici puis basculer juste après créait un flash trompeur (racine visible
  // une seconde, puis rien si la sous-zone n'a pas de géométrie propre).
  if (!options.skipHighlight) {
    CarteState.zoneSurlignee = slug;
    renderCarteLayer();
  }

  try {
    const res = await fetch(
      `/api/carte/arbre_zone?scenario=${encodeURIComponent(CarteState.scenario)}&slug=${encodeURIComponent(slug)}`
    );
    const data = await res.json();
    if (data.error) {
      panel.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
      return;
    }
    panel.innerHTML = `
      <div class="carte-panel-title">${data.arbre.nom}</div>
      <div class="carte-panel-sub">Arborescence des sous-zones</div>
      <div id="arbre-zone-tree"></div>
      <div id="carte-panel-msg"></div>
    `;
    document.getElementById('arbre-zone-tree').innerHTML =
      _renderArbreNode(data.arbre, true);

    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-move-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirReparentPanel(btn.dataset.slug, btn.dataset.nom));
    });
    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-renommer-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirRenommerSousZone(btn.dataset.slug, btn.dataset.nom, data.arbre.slug));
    });

    CarteState.origineReelleParSlug = {};
    CarteState.racineParSlug = {};
    (function indexer(node) {
      CarteState.origineReelleParSlug[node.slug] = node.origine_reelle || [];
      CarteState.racineParSlug[node.slug] = data.arbre.slug;  // racine N1 de tout l'arbre affiché
      (node.enfants || []).forEach(indexer);
    })(data.arbre);

    // Localiser une zone (N1 ou sous-zone) sur la carte en cliquant
    // directement son nom dans l'arbre (12 sept 2026) -- avant, seule la
    // recherche déclenchait le surlignage carte, parcourir l'arbre à la
    // main ne faisait rien.
    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-nom').forEach(el => {
      el.addEventListener('click', () => {
        const ligne = el.closest('.arbre-zone-node-row');
        if (!ligne) return;
        CarteState.zoneSurlignee = ligne.dataset.slug;
        renderCarteLayer();
      });
    });

    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-topdown-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirTopdownRevisionPanel(btn.dataset.slug, btn.dataset.nom));
    });

    // Point d'entrée unique (12 sept 2026) : scinder et personnaliser
    // (couleur/motif/hachures) ont été retirés de l'arbre, fusionnés dans
    // openRenommerZonePanel (même panneau que la légende) -- voir sa
    // section "Pays & portions de cette zone".
    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-editer-btn').forEach(btn => {
      btn.addEventListener('click', () => openRenommerZonePanel(btn.dataset.slug));
    });
  } catch (e) {
    panel.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

function _renderArbreNode(node, estRacine) {
  const typeLabel = node.type ? `<span class="arbre-zone-type">${node.type}</span>` : '';
  const statutLabel = node.statut ? `<span class="arbre-zone-statut">${node.statut}</span>` : '';

  let html = `<div class="arbre-zone-branch">`;
  html += `<div class="arbre-zone-node-row arbre-niveau-${node.niveau}" data-slug="${node.slug}">`;
  html += `<span class="arbre-zone-nom" style="cursor:pointer;text-decoration:underline dotted;" title="Localiser sur la carte">${node.nom}</span>`;
  html += `<span class="arbre-zone-slug">${node.slug}</span>`;
  html += `${typeLabel}${statutLabel}`;
  if (!estRacine) {
    html += `<button class="arbre-zone-move-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Déplacer vers un autre parent">↗️ déplacer</button>`;
    // Renommer une sous-zone (24 sept 2026) : slug et/ou nom, même route
    // serveur que le niveau 1 (ZoneRepository.rename gère tous les niveaux).
    if (node.niveau !== 1) {
      html += `<button class="arbre-zone-renommer-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Renommer cette sous-zone (slug et/ou nom affiché), avec propagation aux instances, relations et liens">✏️ renommer</button>`;
    }
  } else if (node.niveau === 1) {
    // Corrige un trou trouvé le 8 sept 2026 : la racine de l'arbre affiché
    // n'avait jamais ce bouton (masqué par le `!estRacine` ci-dessus), donc
    // une zone niveau 1 ouverte depuis la légende (toujours racine dans ce
    // contexte) ne pouvait JAMAIS être rétrogradée en sous-zone d'une autre
    // zone niveau 1 -- alors que /api/carte/reparent_zone le gère très bien
    // dans les deux sens. Condition sur niveau===1 : une racine de niveau
    // 2/3 affichée ailleurs (ex. panneau dédié) passe déjà par le cas
    // !estRacine normalement, ce cas-ci vise spécifiquement le trou niveau 1.
    html += `<button class="arbre-zone-move-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Déplacer vers un autre parent (rétrograder cette zone niveau 1 en sous-zone)">↗️ déplacer</button>`;
  }
  if (node.niveau === 1) {
    html += `<button class="arbre-zone-topdown-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="P24 étape C — réviser cette zone contre le patron spatial narratif du scénario (ex. suite à un signalement check_patron_spatial_coherence.py)">🧭 réviser (patron spatial)</button>`;
    html += `<button class="arbre-zone-editer-btn" data-slug="${node.slug}" title="Éditer cette zone : renommer, couleur/motif/hachures, pays et overlays">✏️ éditer</button>`;
  }
  html += `</div>`;
  html += `<div id="reparent-panel-${node.slug}"></div>`;
  html += `<div id="renommer-sz-panel-${node.slug}"></div>`;
  html += `<div id="topdown-panel-${node.slug}"></div>`;

  if (node.enfants && node.enfants.length) {
    html += `<div class="arbre-zone-children">`;
    html += node.enfants.map(c => _renderArbreNode(c, false)).join('');
    html += `</div>`;
  }
  html += `</div>`;
  return html;
}

/**
 * Panneau de révision top-down (P24 étape C.4, 25 juillet 2026) : ouvre un
 * mini-formulaire juste sous le nœud N1 concerné, demandant la raison du
 * signalement (à coller depuis la sortie de check_patron_spatial_
 * coherence.py, ou à taper librement). N'écrit jamais rien tant que
 * "✓ Appliquer cette révision" n'est pas cliqué dans le résultat.
 *
 * Limite connue : ce panneau ne lit PAS automatiquement
 * patron_spatial_suspectes.yaml pour lister les zones déjà suivies comme
 * suspectes -- la raison doit être collée à la main pour l'instant. Lister
 * automatiquement les entrées a_traiter/en_attente_c2 directement dans
 * l'arbre serait une extension naturelle, pas construite dans cette
 * session (aucune route ne sert ce fichier au frontend aujourd'hui).
 */
function _ouvrirTopdownRevisionPanel(slug, nom) {
  const container = document.getElementById(`topdown-panel-${slug}`);
  if (!container) return;

  if (container.dataset.open === '1') {
    container.innerHTML = '';
    container.dataset.open = '0';
    return;
  }
  container.dataset.open = '1';

  container.innerHTML = `
    <div class="carte-panel-proposal-box" style="margin:4px 0 8px 16px">
      <div style="font-size:11px;color:#666;margin-bottom:4px">
        Raison du signalement (coller la sortie de check_patron_spatial_coherence.py, ou taper librement) :
      </div>
      <textarea id="topdown-raison-${slug}" rows="3" style="width:100%;box-sizing:border-box;font-family:'JetBrains Mono',monospace;font-size:11px;padding:4px"></textarea>
      <button class="yaml-btn" id="topdown-generer-${slug}" style="margin-top:6px">🧭 Générer une révision</button>
      <div id="topdown-resultat-${slug}"></div>
    </div>
  `;

  document.getElementById(`topdown-generer-${slug}`).addEventListener('click', () =>
    _genererRevisionTopdown(slug, nom));
}

async function _genererRevisionTopdown(slug, nom) {
  const raison = document.getElementById(`topdown-raison-${slug}`).value.trim();
  if (!raison) { alert('La raison du signalement est requise'); return; }

  const btn = document.getElementById(`topdown-generer-${slug}`);
  const out = document.getElementById(`topdown-resultat-${slug}`);
  const texteOriginal = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Génération en cours (peut prendre une minute)…';
  out.innerHTML = '';

  try {
    const res = await fetch('/api/carte/generer_zone_topdown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: CarteState.scenario, raison: 'zone_suspecte',
        slug, raison_suspicion: raison,
      }),
    });
    const data = await res.json();
    btn.disabled = false;
    btn.textContent = texteOriginal;

    if (!data.ok) {
      out.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
      return;
    }
    out.innerHTML = _renderPropositionTopdown(data.proposition, data.issues);
    const creerBtn = out.querySelector('.carte-panel-topdown-creer-btn');
    creerBtn.textContent = '✓ Appliquer cette révision';
    creerBtn.addEventListener('click', () => _appliquerRevisionTopdown(data.proposition, out));
  } catch (e) {
    btn.disabled = false;
    btn.textContent = texteOriginal;
    out.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

/** Écrit réellement la révision EN PLACE (cas zone_suspecte) -- route dédiée,
 * distincte de la création : aucune route existante ne convenait à une révision
 * de zone déjà en place (voir commentaire de la route côté serveur). */
async function _appliquerRevisionTopdown(proposition, container) {
  const statusEl = document.createElement('div');
  statusEl.className = 'carte-status';
  statusEl.textContent = 'Application…';
  container.appendChild(statusEl);

  try {
    const res = await fetch('/api/carte/appliquer_zone_topdown_suspecte', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, proposition }),
    });
    const data = await res.json();
    if (!data.ok) {
      statusEl.className = 'carte-panel-error';
      statusEl.textContent = `Erreur : ${data.error}`;
      return;
    }
    const suiviMsg = data.statut_suivi_maj
      ? ' (statut de suivi mis à jour vers corrige_via_c2)' : '';
    statusEl.textContent = `✓ Révision appliquée : ${data.slug}${suiviMsg}`;
    await refreshCarte();
  } catch (e) {
    statusEl.className = 'carte-panel-error';
    statusEl.textContent = `Erreur réseau : ${e.message}`;
  }
}

/**
 * Panneau de reparent (P7 étape 2 phase 2, 13 juillet 2026) : ouvre un
 * sélecteur de nouveau parent juste sous le nœud concerné dans l'arbre.
 * Le sous-arbre entier suit (décision explicite de l'utilisateur) — le
 * niveau de toute la branche est recalculé si la profondeur change.
 */
/**
 * Renommage d'une sous-zone niveau 2/3 depuis l'arbre (24 sept 2026).
 * Mini-formulaire sous le nœud ; réutilise _carteImpactRenommage /
 * _carteRenommerZone (mêmes routes que le niveau 1), puis rouvre l'arbre
 * de la racine N1 pour afficher le nouveau slug.
 */
function _ouvrirRenommerSousZone(slug, nom, racineSlug) {
  const container = document.getElementById(`renommer-sz-panel-${slug}`);
  if (!container) return;
  if (container.dataset.open === '1') {
    container.innerHTML = '';
    container.dataset.open = '0';
    return;
  }
  container.dataset.open = '1';
  const esc = v => String(v ?? '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
  container.innerHTML = `
    <div class="carte-panel-proposal-box" style="margin:4px 0 8px 16px">
      <label style="font-size:10px">Nouveau slug</label>
      <input type="text" class="rsz-slug" value="${esc(slug)}"
             style="width:100%;font-family:'JetBrains Mono',monospace;font-size:11px;padding:4px;margin-bottom:6px">
      <label style="font-size:10px">Nouveau nom affiché</label>
      <input type="text" class="rsz-nom" value="${esc(nom)}"
             style="width:100%;font-size:11px;padding:4px;margin-bottom:6px">
      <button class="yaml-btn rsz-impact">🔍 Évaluer l'impact</button>
      <div class="rsz-report"></div>
    </div>`;
  container.querySelector('.rsz-impact').addEventListener('click', () => {
    const nouveauSlug = container.querySelector('.rsz-slug').value.trim();
    let nouveauNom = container.querySelector('.rsz-nom').value.trim();
    if (!nouveauSlug) { alert('Le nouveau slug est requis'); return; }
    if (!/^[a-z0-9_]+$/.test(nouveauSlug)) {
      alert('Le slug ne doit contenir que des minuscules, chiffres et underscores');
      return;
    }
    if (nouveauNom === nom) nouveauNom = '';  // nom inchangé : ne pas le réécrire
    if (nouveauSlug === slug && !nouveauNom) { alert('Rien à renommer : slug et nom inchangés'); return; }
    _carteImpactRenommage(slug, nouveauSlug, nouveauNom, container.querySelector('.rsz-report'),
      async (msgTexte) => {
        await openArbreZonePanel(racineSlug);
        const m = document.getElementById('carte-panel-msg');
        if (m) m.textContent = msgTexte;
      });
  });
}

async function _ouvrirReparentPanel(slug, nom) {
  const container = document.getElementById(`reparent-panel-${slug}`);
  if (!container) return;

  if (container.dataset.open === '1') {
    container.innerHTML = '';
    container.dataset.open = '0';
    return;
  }

  container.innerHTML = '<div class="carte-status">Chargement des zones…</div>';
  container.dataset.open = '1';

  try {
    const res = await fetch(`/api/slugs?type=zones_hier&scenario=${encodeURIComponent(CarteState.scenario)}`);
    const data = await res.json();
    const toutesZones = data.zones || [];

    const parEnfants = {};
    toutesZones.forEach(z => {
      if (z.parent) (parEnfants[z.parent] = parEnfants[z.parent] || []).push(z.slug);
    });
    const exclus = new Set([slug]);
    (function collecter(s) {
      (parEnfants[s] || []).forEach(c => { exclus.add(c); collecter(c); });
    })(slug);

    const options = toutesZones
      .filter(z => !exclus.has(z.slug))
      .map(z => `<option value="${z.slug}">${'—'.repeat(z.niveau - 1)} ${z.nom} (${z.slug})</option>`)
      .join('');

    container.innerHTML = `
      <div class="carte-panel-proposal-box" style="margin:4px 0 8px 16px">
        <label style="font-size:10px;color:#666">Nouveau parent pour "${nom}"</label>
        <select id="reparent-select-${slug}" style="width:100%;font-size:11px;padding:4px;margin:4px 0">
          <option value="">— choisir —</option>
          <option value="__racine__">★ Devenir une zone niveau 1 (aucun parent)</option>
          <option value="__creer__">+ Créer une nouvelle zone niveau 1…</option>
          ${options}
        </select>
        <div id="reparent-creer-form-${slug}"></div>
        <button id="reparent-impact-btn-${slug}" class="yaml-btn" style="margin-top:4px">🔍 Évaluer l'impact</button>
        <div id="reparent-impact-report-${slug}"></div>
      </div>
    `;

    const selectEl = document.getElementById(`reparent-select-${slug}`);
    selectEl.addEventListener('change', () => {
      const formEl = document.getElementById(`reparent-creer-form-${slug}`);
      if (selectEl.value === '__creer__') {
        formEl.innerHTML = `
          <div style="border:1px solid #dde3ee;border-radius:4px;padding:8px;margin-top:6px;font-size:10px">
            <input type="text" id="creer-slug-${slug}" placeholder="slug_nouvelle_zone (minuscules_underscores)"
                   style="width:100%;padding:3px;margin-bottom:4px;font-family:'JetBrains Mono',monospace">
            <input type="text" id="creer-nom-${slug}" placeholder="Nom affiché"
                   style="width:100%;padding:3px;margin-bottom:4px">
            <select id="creer-type-${slug}" style="width:100%;padding:3px;margin-bottom:4px">
              ${['bloc_continental','union_regionale','territoire_autonome','territoire_herite','region','ville','infrastructure','site_strategique','zone_sinistree','autre']
                .map(t => `<option value="${t}">${t}</option>`).join('')}
            </select>
            <select id="creer-statut-${slug}" style="width:100%;padding:3px;margin-bottom:4px">
              ${['dominant','stable','fragmenté','en_declin','disparu','emergent']
                .map(t => `<option value="${t}">${t}</option>`).join('')}
            </select>
            <input type="text" id="creer-origine-${slug}" placeholder="Pays réel(s) d'origine, séparés par des virgules (ex: Espagne, Portugal)"
                   style="width:100%;padding:3px;margin-bottom:4px">
            <textarea id="creer-desc-${slug}" placeholder="Description courte (optionnel)"
                      style="width:100%;padding:3px;margin-bottom:4px;font-size:10px" rows="2"></textarea>
            <button id="creer-zone-btn-${slug}" class="yaml-btn">Créer cette zone</button>
          </div>
        `;
        document.getElementById(`creer-zone-btn-${slug}`).addEventListener('click', () => {
          _carteCreerZoneEtReparenter(slug);
        });
      } else {
        formEl.innerHTML = '';
      }
    });

    document.getElementById(`reparent-impact-btn-${slug}`).addEventListener('click', () => {
      const valeur = selectEl.value;
      if (valeur === '__creer__') {
        // L'utilisateur a choisi "créer" mais clique le bouton principal plutôt
        // que le bouton dédié du mini-formulaire — déclencher la création
        // directement plutôt que de bloquer avec un message trompeur (bug
        // signalé le 13 juillet 2026).
        _carteCreerZoneEtReparenter(slug);
        return;
      }
      if (!valeur) { alert('Choisis un nouveau parent, ou "Créer une nouvelle zone niveau 1"'); return; }
      const nouveauParent = valeur === '__racine__' ? '' : valeur;
      _carteImpactReparent(slug, nouveauParent, document.getElementById(`reparent-impact-report-${slug}`));
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

/** Crée la nouvelle zone niveau 1 depuis le mini-formulaire, puis lance directement
 * le rapport d'impact du reparent vers cette zone fraîchement créée. */
async function _carteCreerZoneEtReparenter(slug) {
  const nouveauSlug = document.getElementById(`creer-slug-${slug}`).value.trim();
  const nom = document.getElementById(`creer-nom-${slug}`).value.trim();
  const type = document.getElementById(`creer-type-${slug}`).value;
  const statut = document.getElementById(`creer-statut-${slug}`).value;
  const origineTexte = document.getElementById(`creer-origine-${slug}`).value.trim();
  const description = document.getElementById(`creer-desc-${slug}`).value.trim();

  if (!nouveauSlug || !/^[a-z0-9_]+$/.test(nouveauSlug)) {
    alert('Slug requis : minuscules, chiffres, underscores uniquement'); return;
  }
  if (!nom) { alert('Nom requis'); return; }
  if (!origineTexte) { alert('Au moins un pays réel d\'origine est requis'); return; }

  const origine_reelle = origineTexte.split(',').map(s => s.trim()).filter(Boolean)
    .map(entite => ({ entite, type_entite: 'pays' }));

  const reportEl = document.getElementById(`reparent-impact-report-${slug}`);
  reportEl.innerHTML = '<div class="carte-status">Création de la zone…</div>';

  try {
    const res = await fetch('/api/carte/creer_zone_niveau1', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: CarteState.scenario, slug: nouveauSlug, nom, type, statut, origine_reelle, description,
      }),
    });
    const data = await res.json();
    if (!data.ok) {
      reportEl.innerHTML = `<div class="carte-panel-error">Erreur création : ${data.error}</div>`;
      return;
    }

    // La zone créée n'existait pas dans le <select> au chargement du panneau —
    // sans ça, un second clic sur "🔍 Évaluer l'impact" retomberait sur le
    // garde-fou "Choisis un nouveau parent" puisque le select est resté sur
    // "__creer__" (bug signalé le 13 juillet 2026).
    const selectEl = document.getElementById(`reparent-select-${slug}`);
    if (selectEl) {
      const opt = document.createElement('option');
      opt.value = nouveauSlug;
      opt.textContent = `${nom} (${nouveauSlug})`;
      opt.selected = true;
      selectEl.appendChild(opt);
    }
    document.getElementById(`reparent-creer-form-${slug}`).innerHTML = '';

    _carteImpactReparent(slug, nouveauSlug, reportEl);
  } catch (e) {
    reportEl.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function _carteImpactReparent(slug, nouveauParentSlug, container) {
  container.innerHTML = '<div class="carte-status">Analyse en cours…</div>';
  try {
    const res = await fetch('/api/carte/impact_reparent_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug, nouveau_parent_slug: nouveauParentSlug }),
    });
    const r = await res.json();
    if (r.error) {
      container.innerHTML = `<div class="carte-panel-error">Erreur : ${r.error}</div>`;
      return;
    }

    let html = `<div style="margin-top:6px">`;
    const cible = r.devient_racine ? '★ zone niveau 1 autonome' : r.nouveau_parent.slug;
    html += `<div><strong>${r.zone.nom}</strong> : ${r.zone.ancien_parent || '(racine)'} → ${cible}</div>`;
    html += `<div>Niveau : ${r.zone.niveau} → ${r.nouveau_niveau_zone}` +
      (r.changement_de_profondeur ? ' <span style="color:#c0392b">(changement de profondeur)</span>' : '') +
      `</div>`;
    if (r.descendants_impactes.length) {
      html += `<div style="margin-top:6px"><strong>${r.descendants_impactes.length} descendant(s) suivent</strong> ` +
        `(le sous-arbre se déplace en bloc) :</div>`;
      html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
        r.descendants_impactes.map(d =>
          `<li>${d.nom} : niveau ${d.ancien_niveau} → ${d.nouveau_niveau}</li>`
        ).join('') + '</ul>';
    } else {
      html += `<div style="margin-top:6px;color:#2e7d32">✓ Aucun descendant à recalculer.</div>`;
    }
    html += `<button id="reparent-confirm-btn-${slug}" class="yaml-btn" style="margin-top:8px;font-weight:700">✓ Confirmer le déplacement</button>`;
    html += `</div>`;
    container.innerHTML = html;

    document.getElementById(`reparent-confirm-btn-${slug}`).addEventListener('click', () => {
      _carteReparentZone(slug, nouveauParentSlug);
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function _carteReparentZone(slug, nouveauParentSlug) {
  const reportEl = document.getElementById(`reparent-impact-report-${slug}`);
  if (reportEl) reportEl.innerHTML = '<div class="carte-status">Déplacement en cours…</div>';
  try {
    const res = await fetch('/api/carte/reparent_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug, nouveau_parent_slug: nouveauParentSlug }),
    });
    const data = await res.json();
    const msg = document.getElementById('carte-panel-msg');
    if (data.ok) {
      if (msg) msg.textContent = `✓ "${data.ancien_nom}" déplacée (niveau ${data.nouveau_niveau}, ` +
        `${data.descendants_maj} descendant(s) recalculé(s))`;
      await openArbreZonePanel(CarteState.zoneSurlignee);
    } else if (reportEl) {
      reportEl.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
    }
  } catch (e) {
    if (reportEl) reportEl.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

/**
 * Panneau de renommage de zone (P7 étape 1, 12 juillet 2026).
 * Niveau 1 uniquement (couleur/motif/pays) — les sous-zones niveau 2/3 se
 * renomment depuis l'arbre, bouton « ✏️ renommer » (_ouvrirRenommerSousZone).
 */
async function openRenommerZonePanel(ancienSlug) {
  const z = CarteState.zonesN1.find(zz => zz.slug === ancienSlug);
  const panel = document.getElementById('carte-panel');

  CarteState.zoneSurlignee = ancienSlug;
  renderCarteLayer();

  // Couleur/motif RÉELS (custom ou null) -- distincts de z.color (toujours
  // rempli, calculé automatiquement si rien n'est personnalisé). Récupérés
  // via arbre_zone pour que la case "auto" ci-dessous reflète le vrai état.
  let couleurActuelle = null, motifActuel = null, hachuresActuel = false, origineReelleZone = [];
  try {
    const res = await fetch(`/api/carte/arbre_zone?scenario=${encodeURIComponent(CarteState.scenario)}&slug=${encodeURIComponent(ancienSlug)}`);
    const data = await res.json();
    if (data.arbre) {
      couleurActuelle = data.arbre.couleur || null;
      motifActuel = data.arbre.motif || null;
      hachuresActuel = !!data.arbre.hachures;
      origineReelleZone = data.arbre.origine_reelle || [];
    }
  } catch (e) {
    // Non bloquant : le panneau s'ouvre quand même, juste sans préremplissage.
  }

  const motifOptions = ['', ...Object.keys(MOTIFS_LABELS)].map(m =>
    `<option value="${m}" ${m === motifActuel ? 'selected' : ''}>${m ? MOTIFS_LABELS[m] : '— aucun —'}</option>`
  ).join('');

  const overlaysParPays = {};
  (CarteState.overlays?.features || []).forEach(f => {
    if (f.properties?.zone_slug === ancienSlug && f.properties?.pays) {
      overlaysParPays[f.properties.pays] = f.properties.id;
    }
  });

  const paysRowsHtml = origineReelleZone.length
    ? origineReelleZone.map((o, i) => {
        const overlayId = overlaysParPays[o.entite];
        const entiteAttr = (o.entite || '').replace(/"/g, '&quot;');
        return `
        <div class="pp-row" style="border:1px solid #eee;border-radius:4px;padding:6px;margin-bottom:4px;font-size:11px;">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
            <div>
              <strong>${o.entite}</strong>${overlayId ? ' <span style="color:#2a7d2a;">📍 tracé</span>' : ''}
              ${o.portion ? `<div style="color:#888;">${o.portion}</div>` : ''}
            </div>
            <div style="display:flex;gap:4px;">
              <button class="pp-deplacer-btn" data-i="${i}" data-entite="${entiteAttr}">↗️ déplacer</button>
              ${overlayId
                ? `<button class="pp-retirer-tracer-btn" data-id="${overlayId}" title="Retire le polygone dessiné pour ce pays -- origine_reelle reste inchangé">🗑️ supprimer le masque</button>`
                : `<button class="pp-dessiner-btn" data-entite="${entiteAttr}">✏️ dessiner</button>`}
            </div>
          </div>
          <div id="pp-deplacer-form-${i}"></div>
        </div>`;
      }).join('')
    : '<div style="font-size:11px;color:#888;">Aucune entrée.</div>';

  panel.innerHTML = `
    <div class="carte-panel-title">Éditer : ${z ? z.nom : ancienSlug}</div>
    <div class="carte-panel-sub">Slug actuel : ${ancienSlug}</div>

    <div class="carte-panel-section">
      <label>Nouveau slug</label>
      <input type="text" id="renommer-nouveau-slug" value="${ancienSlug}"
             style="width:100%;font-family:'JetBrains Mono',monospace;font-size:11px;padding:4px;margin-bottom:6px">
      <label>Nouveau nom affiché</label>
      <input type="text" id="renommer-nouveau-nom" value="${z ? z.nom : ''}"
             style="width:100%;font-size:11px;padding:4px;margin-bottom:6px">
      <button id="renommer-impact-btn" class="yaml-btn">🔍 Évaluer l'impact</button>
      <div id="renommer-impact-report"></div>
    </div>

    <div class="carte-panel-section">
      <label>Couleur / motif</label>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:4px;">
        <label>Couleur :
          <input type="color" id="perso-legende-couleur" value="${couleurActuelle || (z ? z.color : '#3b6fd4')}">
        </label>
        <label>
          <input type="checkbox" id="perso-legende-auto" ${couleurActuelle ? '' : 'checked'}> auto
        </label>
        <label>Motif :
          <select id="perso-legende-motif">${motifOptions}</select>
        </label>
        <label title="Hachures génériques en plus de la couleur -- désactivées par défaut">
          <input type="checkbox" id="perso-legende-hachures" ${hachuresActuel ? 'checked' : ''}> hachures
        </label>
        <button class="yaml-btn" id="perso-legende-appliquer">✓ Appliquer</button>
        <span id="perso-legende-msg" style="font-size:10px;"></span>
      </div>
    </div>

    <div class="carte-panel-section">
      <label>Pays &amp; portions de cette zone (${origineReelleZone.length})</label>
      <div id="renommer-pays-liste" style="margin-top:4px;">${paysRowsHtml}</div>
      <button id="renommer-dessiner-overlay-btn" class="yaml-btn" style="margin-top:6px;">✏️ Ajouter un nouveau pays (dessiner un tracé)</button>
    </div>

    <div class="carte-panel-section" style="border-top:1px solid #f0c0c0;padding-top:8px;">
      <label style="color:#a33;">Zone dangereuse</label>
      <button id="renommer-supprimer-btn" class="btn-secondary" style="margin-top:4px;color:#a33;border-color:#e0a0a0;">🗑️ Supprimer cette zone</button>
      <div id="renommer-supprimer-report" style="margin-top:6px;"></div>
    </div>

    <div id="carte-panel-msg"></div>
  `;

  document.getElementById('renommer-impact-btn').addEventListener('click', () => {
    const nouveauSlug = document.getElementById('renommer-nouveau-slug').value.trim();
    const nouveauNom = document.getElementById('renommer-nouveau-nom').value.trim();
    if (!nouveauSlug) { alert('Le nouveau slug est requis'); return; }
    if (!/^[a-z0-9_]+$/.test(nouveauSlug)) {
      alert('Le slug ne doit contenir que des minuscules, chiffres et underscores');
      return;
    }
    _carteImpactRenommage(ancienSlug, nouveauSlug, nouveauNom,
      document.getElementById('renommer-impact-report'));
  });

  const couleurInput = document.getElementById('perso-legende-couleur');
  const autoCheckbox = document.getElementById('perso-legende-auto');
  autoCheckbox.addEventListener('change', () => { couleurInput.disabled = autoCheckbox.checked; });
  couleurInput.disabled = autoCheckbox.checked;

  document.getElementById('perso-legende-appliquer').addEventListener('click', async () => {
    const msgEl = document.getElementById('perso-legende-msg');
    msgEl.textContent = 'Enregistrement…';
    const motifChoisi = document.getElementById('perso-legende-motif').value;
    const body = {
      scenario: CarteState.scenario,
      slug: ancienSlug,
      couleur: autoCheckbox.checked ? null : couleurInput.value,
      motif: motifChoisi || null,
      hachures: document.getElementById('perso-legende-hachures').checked,
    };
    try {
      const res = await fetch('/api/carte/personnaliser_zone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (data.error) { msgEl.textContent = `Erreur : ${data.error}`; return; }
      msgEl.textContent = '✓ Appliqué.';
      await refreshCarte();
    } catch (e) {
      msgEl.textContent = `Erreur réseau : ${e.message}`;
    }
  });

  panel.querySelectorAll('.pp-deplacer-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      _ouvrirDeplacerPaysInline(ancienSlug, btn.dataset.entite, btn.dataset.i);
    });
  });

  panel.querySelectorAll('.pp-dessiner-btn').forEach(btn => {
    btn.addEventListener('click', () => demarrerDessinPourPays(ancienSlug, btn.dataset.entite));
  });

  panel.querySelectorAll('.pp-retirer-tracer-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!window.confirm('Retirer ce masque ? Le texte de portion associé sera aussi effacé.')) return;
      btn.disabled = true;
      btn.textContent = '…';
      await _supprimerOverlay(btn.dataset.id);
      openRenommerZonePanel(ancienSlug);  // réaffiche le panneau à jour
    });
  });

  document.getElementById('renommer-dessiner-overlay-btn').addEventListener('click', () => {
    demarrerDessinPourZone(ancienSlug);
  });

  document.getElementById('renommer-supprimer-btn').addEventListener('click', () => {
    _afficherImpactSuppression(ancienSlug);
  });
}

// ── Suppression de zone (12 sept 2026) : aperçu d'impact avant confirmation,
// même doctrine que rename/reparent/split -- jamais de suppression directe
// sans montrer d'abord ce qui va être touché (pays désaffectés, overlays
// retirés, sous-zones bloquantes le cas échéant).
async function _afficherImpactSuppression(slug) {
  const container = document.getElementById('renommer-supprimer-report');
  container.innerHTML = '<div class="carte-status">Analyse en cours…</div>';
  try {
    const res = await fetch('/api/carte/impact_supprimer_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug }),
    });
    const r = await res.json();
    if (r.error) { container.innerHTML = `<div class="carte-panel-error">Erreur : ${r.error}</div>`; return; }

    if (!r.peut_supprimer) {
      container.innerHTML = `
        <div class="carte-panel-error">
          Impossible : ${r.enfants_bloquants.length} sous-zone(s) encore rattachée(s) --
          déplace-les ou supprime-les d'abord :
          <ul style="margin:4px 0;padding-left:16px;font-size:10px">
            ${r.enfants_bloquants.map(e => `<li>${e.nom}</li>`).join('')}
          </ul>
        </div>`;
      return;
    }

    let html = '<div style="font-size:11px;">';
    if (r.pays_a_desaffecter.length) {
      html += `<div>${r.pays_a_desaffecter.length} pays seront désaffectés : ${r.pays_a_desaffecter.join(', ')}</div>`;
    }
    if (r.overlays_a_supprimer) {
      html += `<div style="margin-top:4px;">${r.overlays_a_supprimer} overlay(s) seront retirés.</div>`;
    }
    if (r.zones_relations_liees.length) {
      html += `<div style="margin-top:4px;">Référencée en allié/rival par : ${r.zones_relations_liees.join(', ')} (nettoyé automatiquement).</div>`;
    }
    html += `<button id="renommer-supprimer-confirm-btn" class="yaml-btn" style="margin-top:8px;color:#a33;font-weight:700;">✓ Confirmer la suppression</button>`;
    html += '</div>';
    container.innerHTML = html;

    document.getElementById('renommer-supprimer-confirm-btn').addEventListener('click', () => {
      _confirmerSuppressionZone(slug);
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function _confirmerSuppressionZone(slug) {
  const container = document.getElementById('renommer-supprimer-report');
  container.innerHTML = '<div class="carte-status">Suppression en cours…</div>';
  try {
    const res = await fetch('/api/carte/supprimer_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug }),
    });
    const data = await res.json();
    if (!data.ok) {
      container.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
      return;
    }
    // La zone n'existe plus -- ferme le panneau plutôt que de le réafficher.
    document.getElementById('carte-panel').innerHTML =
      `<div class="carte-panel-empty">Zone "${slug}" supprimée.</div>`;
    CarteState.zoneSurlignee = null;
    await refreshCarte();
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

// ── Panneau unique (12 sept 2026) : lance le dessin d'overlay directement
// pour la zone dont le panneau est ouvert, sans repasser par le sélecteur
// générique de zone (_promptZoneSlug).
function demarrerDessinPourZone(slug) {
  CarteState.dessinZonePreselectionnee = slug;
  if (!CarteState.modeDessin) toggleModeDessin();
  document.getElementById('carte-status').textContent =
    `Mode dessin actif pour "${slug}" — clique sur la carte pour poser chaque sommet du polygone, double-clic pour le fermer.`;
}

// Variante : le pays est AUSSI déjà connu (ligne "Pays & portions"), saute
// _promptZoneSlug ET _promptPays -- juste le tracé à poser.
function demarrerDessinPourPays(zoneSlug, pays) {
  CarteState.dessinZonePreselectionnee = zoneSlug;
  CarteState.dessinPaysPreselectionne = pays;
  if (!CarteState.modeDessin) toggleModeDessin();
  document.getElementById('carte-status').textContent =
    `Mode dessin actif pour "${pays}" (${zoneSlug}) — clique sur la carte pour poser chaque sommet du polygone, double-clic pour le fermer.`;
}

// ── Fusion scinder/overlay (12 sept 2026) : déplace UNE entrée précise
// d'origine_reelle vers une autre zone, formulaire replié sous sa ligne
// dans "Pays & portions" -- même logique que l'ancien panneau de split (retiré le 23 sept)
// (désormais retiré de l'arbre), mais ciblée sur un seul pays au lieu d'une
// sélection multiple, et affichée en ligne plutôt que dans un panneau à part.
function _ouvrirDeplacerPaysInline(zoneSlug, entite, i) {
  const container = document.getElementById(`pp-deplacer-form-${i}`);
  if (!container) return;
  if (container.dataset.open === '1') { container.innerHTML = ''; container.dataset.open = '0'; return; }
  container.dataset.open = '1';

  // Même règle que l'ancien split : le premier token suffit, le backend
  // retrouve les autres formulations du même pays (voir _entite_references_pays).
  const premierToken = entite.split(/[(,]/)[0].trim().toLowerCase();

  container.innerHTML = `
    <div class="carte-panel-proposal-box" style="margin:6px 0 4px 0">
      <label style="font-size:10px;color:#666">Destination pour "${entite}"</label>
      <select id="pp-cible-select-${i}" style="width:100%;font-size:11px;padding:4px;margin:4px 0">
        <option value="__creer__">+ Créer une nouvelle zone niveau 1…</option>
        <option value="__existante__">→ Ajouter à une zone niveau 1 existante…</option>
      </select>
      <div id="pp-cible-form-${i}"></div>
      <button id="pp-impact-btn-${i}" class="yaml-btn" style="margin-top:4px">🔍 Évaluer l'impact</button>
      <div id="pp-impact-report-${i}"></div>
    </div>
  `;

  const cibleSelect = document.getElementById(`pp-cible-select-${i}`);
  const majFormCible = async () => {
    const formEl = document.getElementById(`pp-cible-form-${i}`);
    if (cibleSelect.value === '__existante__') {
      formEl.innerHTML = `<div class="carte-status">Chargement des zones…</div>`;
      try {
        const res = await fetch(`/api/carte/zones_toutes?scenario=${encodeURIComponent(CarteState.scenario)}`);
        const data = await res.json();
        const options = (data.zones || [])
          .filter(z => z.niveau === 1 && z.slug !== zoneSlug)
          .map(z => `<option value="${z.slug}">${z.nom} (${z.slug})</option>`)
          .join('');
        formEl.innerHTML = `
          <select id="pp-existant-slug-${i}" style="width:100%;padding:3px;font-family:'JetBrains Mono',monospace;margin-top:4px">
            <option value="">— choisir —</option>
            ${options}
          </select>`;
      } catch (e) {
        formEl.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
      }
    } else {
      formEl.innerHTML = `
        <input type="text" id="pp-nouveau-slug-${i}" placeholder="slug_nouvelle_zone (minuscules_underscores)"
               style="width:100%;padding:3px;margin:4px 0;font-family:'JetBrains Mono',monospace">
        <input type="text" id="pp-nouveau-nom-${i}" placeholder="Nom affiché"
               style="width:100%;padding:3px;margin-bottom:4px">
        <select id="pp-nouveau-type-${i}" style="width:100%;padding:3px;margin-bottom:4px">
          ${['bloc_continental','union_regionale','territoire_autonome','territoire_herite','region','ville','infrastructure','site_strategique','zone_sinistree','autre']
            .map(t => `<option value="${t}">${t}</option>`).join('')}
        </select>
        <select id="pp-nouveau-statut-${i}" style="width:100%;padding:3px;margin-bottom:4px">
          ${['dominant','stable','fragmenté','en_declin','disparu','emergent']
            .map(t => `<option value="${t}">${t}</option>`).join('')}
        </select>
        <textarea id="pp-nouveau-desc-${i}" placeholder="Description courte (optionnel)"
                  style="width:100%;padding:3px;font-size:10px" rows="2"></textarea>`;
    }
  };
  cibleSelect.addEventListener('change', majFormCible);
  majFormCible();

  document.getElementById(`pp-impact-btn-${i}`).addEventListener('click', () => {
    let cible;
    if (cibleSelect.value === '__existante__') {
      const slugExistant = document.getElementById(`pp-existant-slug-${i}`).value.trim();
      if (!slugExistant) { alert('Choisis une zone existante.'); return; }
      cible = { mode: 'zone_existante', slug_existant: slugExistant };
    } else {
      const cibleSlug = document.getElementById(`pp-nouveau-slug-${i}`).value.trim();
      const cibleNom = document.getElementById(`pp-nouveau-nom-${i}`).value.trim();
      const cibleType = document.getElementById(`pp-nouveau-type-${i}`).value;
      const cibleStatut = document.getElementById(`pp-nouveau-statut-${i}`).value;
      const cibleDesc = document.getElementById(`pp-nouveau-desc-${i}`).value.trim();
      if (!cibleSlug || !cibleNom) { alert('Slug et nom de la nouvelle zone requis.'); return; }
      cible = { mode: 'nouvelle_zone_n1', slug: cibleSlug, nom: cibleNom, type: cibleType, statut: cibleStatut, description: cibleDesc };
    }
    _ppImpactDeplacer(zoneSlug, premierToken, cible, i);
  });
}

async function _ppImpactDeplacer(zoneSlug, premierToken, cible, i) {
  const container = document.getElementById(`pp-impact-report-${i}`);
  container.innerHTML = '<div class="carte-status">Analyse en cours…</div>';
  try {
    const res = await fetch('/api/carte/impact_split_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug_source: zoneSlug, pays_a_extraire: [premierToken], cible }),
    });
    const r = await res.json();
    if (r.error) { container.innerHTML = `<div class="carte-panel-error">Erreur : ${r.error}</div>`; return; }

    let html = `<div style="margin-top:6px">`;
    html += `<div>Entité(s) extraite(s) : ${r.entites_extraites.map(e => e.entite).join(', ')}</div>`;
    html += `<div style="margin-top:4px">Destination : ${r.cible.nom} ` +
      `(${r.cible.mode === 'nouvelle_zone_n1' ? 'nouvelle zone' : 'zone existante'})</div>`;
    if (r.enfants_qui_suivront.length) {
      html += `<div style="margin-top:6px"><strong>${r.enfants_qui_suivront.length} sous-zone(s) suivent automatiquement</strong> ` +
        `(leur propre origine_reelle référence aussi ce pays) :</div>`;
      html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
        r.enfants_qui_suivront.map(e => `<li>${e.nom}</li>`).join('') + '</ul>';
    }
    html += `<button id="pp-confirm-btn-${i}" class="yaml-btn" style="margin-top:8px;font-weight:700">✓ Confirmer</button>`;
    html += `</div>`;
    container.innerHTML = html;

    document.getElementById(`pp-confirm-btn-${i}`).addEventListener('click', () => {
      _ppConfirmerDeplacer(zoneSlug, premierToken, cible, i);
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function _ppConfirmerDeplacer(zoneSlug, premierToken, cible, i) {
  const container = document.getElementById(`pp-impact-report-${i}`);
  container.innerHTML = '<div class="carte-status">Déplacement en cours…</div>';
  try {
    const res = await fetch('/api/carte/split_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug_source: zoneSlug, pays_a_extraire: [premierToken], cible }),
    });
    const data = await res.json();
    if (data.ok) {
      await refreshCarte();
      openRenommerZonePanel(zoneSlug);  // réaffiche le panneau à jour
    } else {
      container.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
    }
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

function onCartePaysClick(frList, displayName) {
  if (frList.length === 1) {
    openCartePanel(frList[0]);
    return;
  }

  // Fix (12 sept 2026) : cas à entrées multiples (ex. Royaume-Uni/Angleterre/
  // Écosse/Pays de Galles, un seul polygone sur le fond de carte pour
  // plusieurs entrées côté vault) -- le fix précédent ne couvrait que
  // openCartePanel (une seule entrée), donc cliquer ici ne mettait jamais à
  // jour la surbrillance avant qu'un choix soit fait dans le sélecteur.
  const zoneResolue = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
  CarteState.zoneSurlignee = zoneResolue || null;
  renderCarteLayer();

  const panel = document.getElementById('carte-panel');
  panel.innerHTML = `
    <div class="carte-panel-title">${displayName} — plusieurs entrées</div>
    <div class="carte-panel-sub">Quelle entrée veux-tu affecter ?</div>
    ${frList.map(fr => `
      <button class="yaml-btn carte-panel-pays-btn" data-pays="${fr}">
        ${fr} ${CarteState.affectations[fr] ? `(→ ${CarteState.affectations[fr]})` : '(non affecté)'}
      </button>
    `).join('')}
  `;
  panel.querySelectorAll('.carte-panel-pays-btn').forEach(btn => {
    btn.addEventListener('click', () => openCartePanel(btn.dataset.pays));
  });
}

async function openCartePanel(pays) {
  const zone = CarteState.affectations[pays];

  // Fix (12 sept 2026) : cliquer sur un pays ne mettait jamais à jour la
  // zone surlignée -- seuls un clic sur un overlay ou sur la légende le
  // faisaient. Résultat : le contour orange restait bloqué sur la
  // précédente sélection tant qu'on ne cliquait pas spécifiquement sur un
  // overlay de cette même zone. Maintenant : tout clic sur un pays met à
  // jour la surbrillance sur SA zone (ou l'efface si le pays n'est pas
  // affecté).
  CarteState.zoneSurlignee = zone || null;
  renderCarteLayer();

  const panel = document.getElementById('carte-panel');

  // Nouveau (13 sept 2026) : un pays peut être réparti sur plusieurs zones
  // (pays entier + une ou plusieurs portions overlay ailleurs, ex. France).
  // Récupère le détail avant de construire le panneau -- non bloquant si
  // l'appel échoue, le panneau reste utilisable sans cette section.
  let zonesDetail = [];
  try {
    const res = await fetch(`/api/carte/zones_par_pays?scenario=${encodeURIComponent(CarteState.scenario)}&pays=${encodeURIComponent(pays)}`);
    const data = await res.json();
    zonesDetail = data.zones || [];
  } catch (e) {
    zonesDetail = [];
  }

  const zoneOptions = CarteState.zonesN1.map(z =>
    `<option value="${z.slug}" ${z.slug === zone ? 'selected' : ''}>${z.nom} (${z.slug})</option>`
  ).join('');

  const repartitionHtml = zonesDetail.length > 1 ? `
    <div class="carte-panel-section">
      <label>Ce pays est réparti sur ${zonesDetail.length} zones</label>
      <ul style="margin:4px 0 0;padding-left:18px;font-size:13px;">
        ${zonesDetail.map(z => `
          <li style="margin-bottom:4px;">
            <strong>${z.nom}</strong>
            ${z.type === 'overlay'
              ? '<span style="color:#b5760a;">(overlay — portion)</span>'
              : '<span style="color:#2a7d2a;">(pays entier)</span>'}
            ${z.portion ? `<div style="color:#666;font-size:12px;">${z.portion}</div>` : ''}
          </li>
        `).join('')}
      </ul>
    </div>
  ` : '';

  panel.innerHTML = `
    <div class="carte-panel-title">${pays}</div>
    <div class="carte-panel-sub">${zone ? `Actuellement (pays entier) : ${zone}` : 'Non affecté (pays entier)'}</div>
    ${repartitionHtml}

    <div class="carte-panel-section">
      <label>Affecter à une zone existante</label>
      <select id="carte-panel-zone-select">
        <option value="">— choisir —</option>
        ${zoneOptions}
      </select>
      <button id="carte-panel-impact-btn" class="yaml-btn">🔍 Évaluer l'impact</button>
      <div id="carte-panel-impact-report"></div>
    </div>

    <div class="carte-panel-section">
      <button id="carte-panel-propose-btn" class="yaml-btn">💡 Demander une proposition (LLM)</button>
      <div id="carte-panel-proposal"></div>
    </div>

    <div class="carte-panel-section">
      <button id="carte-panel-topdown-btn" class="yaml-btn" title="P24 étape C — génère une zone en s'appuyant explicitement sur le patron spatial narratif du scénario (patrons_spatiaux.py), distinct de la proposition ci-dessus qui ne le consulte pas">🧭 Générer selon le patron spatial (top-down)</button>
      <div id="carte-panel-topdown-proposal"></div>
    </div>

    <div class="carte-panel-section">
      <button id="carte-panel-ignorer-btn" class="yaml-btn">Ignorer (blanc intentionnel)</button>
      ${zone ? `<button id="carte-panel-desaffecter-btn" class="yaml-btn" style="margin-top:4px" title="Remet ce pays à Non affecté">↩️ Désaffecter</button>` : ''}
    </div>

    <div id="carte-panel-msg"></div>
  `;

  document.getElementById('carte-panel-impact-btn').addEventListener('click', () => {
    const zoneSlug = document.getElementById('carte-panel-zone-select').value;
    if (!zoneSlug) { alert('Choisis une zone d\'abord'); return; }
    _carteImpact(pays, 'absorber', { zone_slug: zoneSlug },
      document.getElementById('carte-panel-impact-report'), zone ? 'Changer de zone' : 'Absorber');
  });

  // Ré-évaluation obligatoire si la zone sélectionnée change
  document.getElementById('carte-panel-zone-select').addEventListener('change', () => {
    document.getElementById('carte-panel-impact-report').innerHTML = '';
  });

  document.getElementById('carte-panel-propose-btn').addEventListener('click', () => _carteProposer(pays));
  document.getElementById('carte-panel-topdown-btn').addEventListener('click', () => _carteProposerTopdown(pays));
  document.getElementById('carte-panel-ignorer-btn').addEventListener('click', () => _carteIgnorer(pays));
  const desaffecterBtn = document.getElementById('carte-panel-desaffecter-btn');
  if (desaffecterBtn) desaffecterBtn.addEventListener('click', () => _carteDesaffecter(pays, zone));
}

/** Désaffecte un pays déjà assigné (retour à "Non affecté"), avec confirmation
 * -- trou trouvé le 8 sept 2026, voir /api/carte/desaffecter. */
async function _carteDesaffecter(pays, ancienneZone) {
  if (!window.confirm(`Désaffecter "${pays}" (actuellement : ${ancienneZone}) ? Il repassera à "Non affecté".`)) {
    return;
  }
  const msg = document.getElementById('carte-panel-msg');
  msg.textContent = 'Désaffectation…';
  try {
    const res = await fetch('/api/carte/desaffecter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pays, scenario: CarteState.scenario }),
    });
    const data = await res.json();
    if (data.error) {
      msg.textContent = `Erreur : ${data.error}`;
      return;
    }
    msg.textContent = `✓ ${pays} désaffecté.`;
    await refreshCarte();
    openCartePanel(pays);  // rouvre le panneau, reflète le nouvel état "Non affecté"
  } catch (e) {
    msg.textContent = `Erreur réseau : ${e.message}`;
  }
}

/** P24 étape C.4 — génère une proposition de zone niveau 1 pour un pays sans zone,
 * en s'appuyant sur le patron spatial narratif du scénario (zoning_topdown.py, via
 * /api/carte/generer_zone_topdown, subprocess+JSON côté serveur). N'écrit jamais
 * rien tant que "✓ Créer cette zone" n'est pas cliqué. */
async function _carteProposerTopdown(pays) {
  const btn = document.getElementById('carte-panel-topdown-btn');
  const out = document.getElementById('carte-panel-topdown-proposal');
  const texteOriginal = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Génération en cours (peut prendre une minute)…';
  out.innerHTML = '';

  try {
    const res = await fetch('/api/carte/generer_zone_topdown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, raison: 'pays_sans_zone', pays: [pays] }),
    });
    const data = await res.json();
    btn.disabled = false;
    btn.textContent = texteOriginal;

    if (!data.ok) {
      out.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
      return;
    }
    out.innerHTML = _renderPropositionTopdown(data.proposition, data.issues);
    out.querySelector('.carte-panel-topdown-creer-btn').addEventListener('click', () =>
      _carteCreerZoneTopdown(data.proposition, out));
  } catch (e) {
    btn.disabled = false;
    btn.textContent = texteOriginal;
    out.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

/** Rendu commun d'une proposition top-down (pays_sans_zone ou zone_suspecte) --
 * mêmes champs dans les deux cas (schéma validate_zone(), enrich_geographie_
 * recursive.py), seul le bouton final change de libellé/handler côté appelant. */
function _renderPropositionTopdown(p, issues) {
  const lieux = (p.lieux_emblematiques || [])
    .map(l => `<li>${l.nom} (${l.type})${l.notes ? ' — ' + l.notes : ''}</li>`).join('');
  const allies = ((p.relations && p.relations.allies) || []).join(', ') || '—';
  const rivaux = ((p.relations && p.relations.rivaux) || []).join(', ') || '—';

  let html = `<div class="carte-panel-proposal-box">`;
  html += `<div><strong>${p.nom}</strong> <span class="arbre-zone-slug">${p.slug}</span></div>`;
  html += `<div style="margin-top:4px"><span class="arbre-zone-type">${p.type}</span> <span class="arbre-zone-statut">${p.statut}</span></div>`;
  html += `<div style="margin-top:6px;font-size:11px">${p.description || ''}</div>`;
  if (p.tensions_internes) {
    html += `<div style="margin-top:6px;font-size:11px"><em>Tensions internes :</em> ${p.tensions_internes}</div>`;
  }
  if (lieux) {
    html += `<div style="margin-top:6px;font-size:11px"><em>Lieux emblématiques :</em><ul style="margin:4px 0 0 16px;padding:0">${lieux}</ul></div>`;
  }
  html += `<div style="margin-top:6px;font-size:11px"><em>Alliés :</em> ${allies} — <em>Rivaux :</em> ${rivaux}</div>`;
  if (issues && issues.length) {
    html += `<div class="carte-panel-error" style="margin-top:8px">⚠ ${issues.length} point(s) à relire attentivement :<ul style="margin:4px 0 0 16px;padding:0">${issues.map(i => `<li>${i}</li>`).join('')}</ul></div>`;
  }
  html += `<button class="yaml-btn carte-panel-topdown-creer-btn" style="margin-top:8px;font-weight:700">✓ Créer cette zone</button>`;
  html += `</div>`;
  return html;
}

/** Écrit réellement la zone (cas pays_sans_zone) -- réutilise /api/carte/creer_zone_niveau1,
 * déjà corrigée pour la synchronisation zones_pays.json (25 juillet) et pour accepter
 * les champs enrichis (tensions_internes, lieux_emblematiques, relations...). */
async function _carteCreerZoneTopdown(proposition, container) {
  const statusEl = document.createElement('div');
  statusEl.className = 'carte-status';
  statusEl.textContent = 'Création…';
  container.appendChild(statusEl);

  try {
    const res = await fetch('/api/carte/creer_zone_niveau1', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: CarteState.scenario,
        slug: proposition.slug, nom: proposition.nom, type: proposition.type,
        statut: proposition.statut, origine_reelle: proposition.origine_reelle,
        description: proposition.description,
        tensions_internes: proposition.tensions_internes,
        periode_transition: proposition.periode_transition,
        lieux_emblematiques: proposition.lieux_emblematiques,
        relations: proposition.relations,
        sources_attestees: proposition.sources_attestees,
      }),
    });
    const data = await res.json();
    if (!data.ok) {
      statusEl.className = 'carte-panel-error';
      statusEl.textContent = `Erreur création : ${data.error}`;
      return;
    }
    const syncMsg = (data.pays_zones_pays_json && data.pays_zones_pays_json.length)
      ? ` (zones_pays.json synchronisé : ${data.pays_zones_pays_json.join(', ')})` : '';
    const reparentMsg = (data.sous_zones_reparentees && data.sous_zones_reparentees.length)
      ? ` — sous-zone(s) suivie(s) automatiquement : ${data.sous_zones_reparentees.join(', ')}` : '';
    statusEl.textContent = `✓ Zone créée : ${data.slug}${syncMsg}${reparentMsg}`;
    await refreshCarte();
  } catch (e) {
    statusEl.className = 'carte-panel-error';
    statusEl.textContent = `Erreur réseau : ${e.message}`;
  }
}

async function _carteProposer(pays) {
  const btn = document.getElementById('carte-panel-propose-btn');
  const out = document.getElementById('carte-panel-proposal');
  btn.disabled = true;
  btn.textContent = 'Réflexion…';
  out.innerHTML = '';

  try {
    const res = await fetch('/api/carte/propose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pays, scenario: CarteState.scenario }),
    });
    const data = await res.json();
    btn.disabled = false;
    btn.textContent = '💡 Demander une proposition (LLM)';

    if (!data.ok) {
      out.innerHTML = `<div class="carte-panel-error">Erreur : ${data.error}</div>`;
      return;
    }

    const p = data.proposal;
    let html = `<div class="carte-panel-proposal-box">`;
    if (p.zone_existante_recommandee) {
      html += `<div><strong>Zone recommandée :</strong> ${p.zone_existante_recommandee}</div>
        <button class="yaml-btn" id="carte-panel-accept-existing">🔍 Évaluer l'impact puis appliquer</button>`;
    }
    if (p.nouvelle_zone_proposee) {
      const nz = p.nouvelle_zone_proposee;
      html += `<div style="margin-top:8px"><strong>Nouvelle zone proposée :</strong> ${nz.nom} (${nz.slug})<br>
        <span style="font-size:11px;color:#888">${nz.description}</span></div>
        <button class="yaml-btn" id="carte-panel-accept-new">🔍 Évaluer l'impact puis créer</button>`;
    }
    html += `<div style="margin-top:8px;font-size:11px;font-style:italic">${p.justification || ''}</div>`;
    html += `<div id="carte-panel-llm-impact-report"></div>`;
    html += `</div>`;
    out.innerHTML = html;

    const acceptExisting = document.getElementById('carte-panel-accept-existing');
    if (acceptExisting) {
      acceptExisting.addEventListener('click', () =>
        _carteImpact(pays, 'absorber', { zone_slug: p.zone_existante_recommandee },
          document.getElementById('carte-panel-llm-impact-report'), 'Appliquer cette zone'));
    }
    const acceptNew = document.getElementById('carte-panel-accept-new');
    if (acceptNew) {
      acceptNew.addEventListener('click', () =>
        _carteImpact(pays, 'creer', { nouvelle_zone: p.nouvelle_zone_proposee },
          document.getElementById('carte-panel-llm-impact-report'), 'Créer cette zone'));
    }
  } catch (e) {
    btn.disabled = false;
    btn.textContent = '💡 Demander une proposition (LLM)';
    out.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function _carteAssign(pays, action, extra) {
  const msg = document.getElementById('carte-panel-msg');
  msg.textContent = 'Application…';
  try {
    const res = await fetch('/api/carte/assign', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pays, scenario: CarteState.scenario, action, ...extra }),
    });
    const data = await res.json();
    if (data.ok) {
      msg.textContent = `✓ ${pays} → ${data.zone}`;
      await refreshCarte();
    } else {
      msg.textContent = `Erreur : ${data.error}`;
    }
  } catch (e) {
    msg.textContent = `Erreur réseau : ${e.message}`;
  }
}

async function _carteIgnorer(pays) {
  const msg = document.getElementById('carte-panel-msg');
  msg.textContent = 'Marquage…';
  try {
    const res = await fetch('/api/carte/ignorer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pays, scenario: CarteState.scenario }),
    });
    const data = await res.json();
    msg.textContent = data.ok ? `✓ ${pays} marqué intentionnel` : `Erreur : ${data.error}`;
  } catch (e) {
    msg.textContent = `Erreur réseau : ${e.message}`;
  }
}

/** Évalue l'impact (lecture seule) et affiche le rapport + un bouton de confirmation dans `container`. */
async function _carteImpact(pays, action, extra, container, confirmLabel) {
  container.innerHTML = '<div class="carte-status">Analyse en cours…</div>';

  try {
    const res = await fetch('/api/carte/impact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pays, scenario: CarteState.scenario, action, ...extra }),
    });
    const r = await res.json();

    if (r.error) {
      container.innerHTML = `<div class="carte-panel-error">Erreur : ${r.error}</div>`;
      return;
    }

    let html = `<div class="carte-panel-proposal-box">`;
    html += `<div><strong>${pays}</strong> : ${r.ancienne_zone || '—'} → ${r.nouvelle_zone || '—'}</div>`;

    if (r.rien_detecte) {
      html += `<div style="margin-top:6px;color:#2e7d32">✓ Aucun impact narratif détecté.</div>`;
    } else {
      if (r.sous_zones_orphelines.length) {
        html += `<div style="margin-top:8px;color:#c0392b"><strong>⚠ ${r.sous_zones_orphelines.length} sous-zone(s) potentiellement orphelines</strong></div>`;
        html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px" id="orphelines-list">' +
          r.sous_zones_orphelines.map(sz =>
            `<li data-slug="${sz.slug}">${sz.nom} (${sz.slug}) — origine : ${sz.origine} ` +
            (r.nouvelle_zone
              ? `<button class="orpheline-reparent-btn" data-slug="${sz.slug}" data-nom="${sz.nom.replace(/"/g, '&quot;')}" data-cible="${r.nouvelle_zone}">↗️ rattacher à ${r.nouvelle_zone}</button>`
              : '') +
            `</li>`
          ).join('') +
          '</ul>';
      }
      if (r.instances_liees.length) {
        html += `<div style="margin-top:8px"><strong>${r.instances_liees.length} instance(s)/événement(s) liés à la zone</strong></div>`;
        html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
          r.instances_liees.slice(0, 10).map(it => `<li>${it.slug}</li>`).join('') +
          (r.instances_liees.length > 10 ? `<li>… +${r.instances_liees.length - 10} autres</li>` : '') +
          '</ul>';
      }
      if (r.mentions_texte.length) {
        html += `<div style="margin-top:8px"><strong>${r.mentions_texte.length} mention(s) textuelles de « ${pays} »</strong></div>`;
        html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
          r.mentions_texte.slice(0, 10).map(m => `<li>${m.slug} — ${m.extrait}</li>`).join('') +
          (r.mentions_texte.length > 10 ? `<li>… +${r.mentions_texte.length - 10} autres</li>` : '') +
          '</ul>';
      }
      if (r.registre_hits.length) {
        html += `<div style="margin-top:8px"><strong>${r.registre_hits.length} ligne(s) dans le registre des événements</strong></div>`;
        html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
          r.registre_hits.slice(0, 10).map(h => `<li>${h}</li>`).join('') +
          '</ul>';
      }
      html += `<div style="margin-top:8px;font-size:10px;color:#888">Rapport sauvegardé : ${r.rapport_path || '(non écrit)'}</div>`;
    }

    html += `<button id="carte-panel-confirm-btn" class="yaml-btn" style="margin-top:10px;font-weight:700">✓ ${confirmLabel}</button>`;
    html += `</div>`;
    container.innerHTML = html;

    document.getElementById('carte-panel-confirm-btn').addEventListener('click', () => {
      _carteAssign(pays, action, extra);
    });

    container.querySelectorAll('.orpheline-reparent-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        _carteReparenterOrpheline(btn.dataset.slug, btn.dataset.nom, btn.dataset.cible, btn);
      });
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

/**
 * Corrige directement une sous-zone orpheline détectée par le rapport
 * d'impact de bascule (P7 étape 3, 13 juillet 2026) : reparent en un clic
 * vers la nouvelle zone du pays qui vient de basculer, en réutilisant
 * l'endpoint /api/carte/reparent_zone déjà construit pour l'arbre. Pas de
 * double rapport d'impact imbriqué ici — le contexte (bascule de pays déjà
 * en cours de revue) suffit, une simple confirmation native est demandée.
 */
async function _carteReparenterOrpheline(slug, nom, cibleSlug, btn) {
  if (!confirm(`Rattacher "${nom}" à "${cibleSlug}" ?\n\nSon niveau sera recalculé si besoin, et ses éventuelles sous-zones suivront.`)) {
    return;
  }
  btn.disabled = true;
  btn.textContent = '…';
  try {
    const res = await fetch('/api/carte/reparent_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug, nouveau_parent_slug: cibleSlug }),
    });
    const data = await res.json();
    const li = btn.closest('li');
    if (data.ok) {
      li.innerHTML = `✓ ${nom} (${slug}) — rattachée à ${cibleSlug}`;
      li.style.color = '#2e7d32';
    } else {
      btn.disabled = false;
      btn.textContent = `↗️ rattacher à ${cibleSlug}`;
      alert(`Erreur : ${data.error}`);
    }
  } catch (e) {
    btn.disabled = false;
    btn.textContent = `↗️ rattacher à ${cibleSlug}`;
    alert(`Erreur réseau : ${e.message}`);
  }
}

/** Rapport d'impact (lecture seule) pour un renommage de zone (P7 étape 1). */
async function _carteImpactRenommage(ancienSlug, nouveauSlug, nouveauNom, container, apresSucces = null) {
  container.innerHTML = '<div class="carte-status">Analyse en cours…</div>';

  try {
    const res = await fetch('/api/carte/impact_renommage_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: CarteState.scenario,
        ancien_slug: ancienSlug,
        nouveau_slug: nouveauSlug,
        nouveau_nom: nouveauNom,
      }),
    });
    const r = await res.json();

    if (r.error) {
      container.innerHTML = `<div class="carte-panel-error">Erreur : ${r.error}</div>`;
      return;
    }

    let html = `<div class="carte-panel-proposal-box">`;
    html += `<div><strong>${r.zone.nom}</strong> (${r.zone.slug}) → ${nouveauSlug}</div>`;

    if (r.collision_slug_entite) {
      html += `<div style="margin-top:8px;color:#c0392b">⚠ Une entité porte déjà le slug ` +
        `<code>${r.collision_slug_entite}</code> — collision de nommage possible entre ` +
        `l'archétype et la zone renommée (pas bloquant, mais à vérifier après coup).</div>`;
    }

    if (r.rien_detecte) {
      html += `<div style="margin-top:6px;color:#2e7d32">✓ Aucune propagation au-delà de la zone elle-même.</div>`;
    } else {
      if (r.enfants_directs.length) {
        html += `<div style="margin-top:8px"><strong>${r.enfants_directs.length} sous-zone(s) enfant(s) directe(s)</strong> ` +
          `(champ parent + wikilink "sous [[...]]" mis à jour)</div>`;
        html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
          r.enfants_directs.map(e => `<li>${e.nom} (${e.slug})</li>`).join('') + '</ul>';
      }
      if (r.zones_relations_liees.length) {
        html += `<div style="margin-top:8px"><strong>${r.zones_relations_liees.length} zone(s) la référencent en allié/rival</strong></div>`;
        html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
          r.zones_relations_liees.map(s => `<li>${s}</li>`).join('') + '</ul>';
      }
      if (r.instances_liees.length) {
        html += `<div style="margin-top:8px"><strong>${r.instances_liees.length} instance(s)/événement(s) liés</strong></div>`;
        html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
          r.instances_liees.slice(0, 10).map(it => `<li>${it.slug}</li>`).join('') +
          (r.instances_liees.length > 10 ? `<li>… +${r.instances_liees.length - 10} autres</li>` : '') +
          '</ul>';
      }
      if (r.pays_zones_pays_json.length) {
        html += `<div style="margin-top:8px"><strong>${r.pays_zones_pays_json.length} pays dans zones_pays.json</strong></div>`;
        html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
          r.pays_zones_pays_json.map(p => `<li>${p}</li>`).join('') + '</ul>';
      }
    }

    html += `<button id="renommer-confirm-btn" class="yaml-btn" style="margin-top:10px;font-weight:700">✓ Confirmer le renommage</button>`;
    html += `</div>`;
    container.innerHTML = html;

    // Portée au conteneur : plusieurs rapports peuvent coexister (arbre).
    container.querySelector('#renommer-confirm-btn').addEventListener('click', () => {
      _carteRenommerZone(ancienSlug, nouveauSlug, nouveauNom, apresSucces);
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

/** Applique le renommage confirmé. */
async function _carteRenommerZone(ancienSlug, nouveauSlug, nouveauNom, apresSucces = null) {
  const msg = document.getElementById('carte-panel-msg');
  msg.textContent = 'Renommage en cours…';
  try {
    const res = await fetch('/api/carte/renommer_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: CarteState.scenario,
        ancien_slug: ancienSlug,
        nouveau_slug: nouveauSlug,
        nouveau_nom: nouveauNom,
      }),
    });
    const data = await res.json();
    if (data.ok) {
      const texte = `✓ Zone renommée : ${ancienSlug} → ${data.nouveau_slug} ` +
        `(${data.enfants_maj} enfant(s), ${data.zones_relations_maj} relation(s), ` +
        `${data.instances_maj} instance(s), ${data.pays_maj} pays mis à jour)`;
      msg.textContent = texte;
      await refreshCarte();
      if (apresSucces) await apresSucces(texte);
    } else {
      msg.textContent = `Erreur : ${data.error}`;
    }
  } catch (e) {
    msg.textContent = `Erreur réseau : ${e.message}`;
  }
}

/* ══════════════════════════════════════════════════
   ONGLET CHANTIERS (point 4.5, 26 juillet 2026)
   Cycle complet : lister → générer proposition (IA) →
   approuver/rejeter → appliquer (lot) → ignorer/marquer traité.
   ══════════════════════════════════════════════════ */

const ChantiersState = {
  items: [],
  filtersWired: false,
};

async function loadChantiers() {
  const scenarioSel = document.getElementById('chantiers-scenario');
  if (!ChantiersState.filtersWired) {
    const scenarios = State.config?.scenarios || [];
    scenarioSel.innerHTML = '<option value="">Tous</option>' +
      scenarios.map(s => `<option value="${s}">${s}</option>`).join('');

    document.getElementById('chantiers-scenario').addEventListener('change', refreshChantiers);
    document.getElementById('chantiers-type').addEventListener('change', refreshChantiers);
    document.getElementById('chantiers-statut').addEventListener('change', refreshChantiers);
    document.getElementById('chantiers-appliquer-tout').addEventListener('click', chantiersAppliquerTout);
    ChantiersState.filtersWired = true;
  }
  await refreshChantiers();
}

async function refreshChantiers() {
  const scenario = document.getElementById('chantiers-scenario').value;
  const type_ = document.getElementById('chantiers-type').value;
  const statut = document.getElementById('chantiers-statut').value;

  const applyBtn = document.getElementById('chantiers-appliquer-tout');
  applyBtn.textContent = scenario
    ? `Appliquer les propositions approuvées (${scenario})`
    : 'Appliquer les propositions approuvées (tous les scénarios)';

  const params = new URLSearchParams();
  if (scenario) params.set('scenario', scenario);
  if (type_) params.set('type', type_);
  if (statut) params.set('statut', statut);

  const list = document.getElementById('chantiers-list');
  list.innerHTML = '<div class="chantiers-empty">Chargement…</div>';

  try {
    const res = await fetch(`/api/chantiers?${params.toString()}`);
    const data = await res.json();
    ChantiersState.items = data.chantiers || [];
    renderChantiersList();
  } catch (e) {
    list.innerHTML = `<div class="chantiers-empty">Erreur réseau : ${e.message}</div>`;
  }
}

function renderChantiersList() {
  const list = document.getElementById('chantiers-list');
  const items = ChantiersState.items;
  document.getElementById('chantiers-count').textContent =
    `${items.length} chantier${items.length > 1 ? 's' : ''}`;

  if (items.length === 0) {
    list.innerHTML = '<div class="chantiers-empty">Aucun chantier pour ces filtres.</div>';
    return;
  }

  // Groupés par scénario, comme le dashboard zones-manquantes
  const parScenario = {};
  items.forEach(c => {
    (parScenario[c.scenario] ||= []).push(c);
  });

  list.innerHTML = Object.entries(parScenario).map(([scenario, chantiers]) => `
    <div class="chantiers-scenario-group">
      <div class="chantiers-scenario-header">
        ${scenario}
        <span class="chantiers-scenario-count">${chantiers.length}</span>
      </div>
      ${chantiers.map(renderChantierRow).join('')}
    </div>
  `).join('');
}

const CHANTIERS_TYPE_LABEL = {
  pays_sans_zone: 'Pays sans zone', zone_suspecte: 'Zone suspecte',
  doublon_pays_entier: 'Doublon pays-entier',
};
const CHANTIERS_STATUT_LABEL = { a_traiter: 'À traiter', ignore: 'Ignoré', traite: 'Traité' };

function renderChantierRow(c) {
  const aProposition = c.proposition != null;
  const approuvee = c.proposition_approuvee === true;
  const enAttente = c.statut === 'a_traiter';

  return `
    <div class="chantiers-row" data-chantier-id="${c.id}">
      <div class="chantiers-row-head">
        <span class="chantiers-type-badge">${CHANTIERS_TYPE_LABEL[c.type] || c.type}</span>
        <span class="chantiers-cible">${_redactionEsc(c.cible)}</span>
        <span class="chantiers-statut-badge chantiers-statut-${c.statut}">${CHANTIERS_STATUT_LABEL[c.statut] || c.statut}</span>
        ${aProposition && approuvee ? '<span class="chantiers-approuvee-badge">✓ approuvée</span>' : ''}
      </div>
      <div class="chantiers-probleme">${_redactionEsc(c.probleme)}</div>
      ${aProposition ? `<div class="chantiers-proposal-box">${_redactionEsc(_chantiersFormatProposition(c.proposition))}</div>` : ''}
      <div class="chantiers-actions">
        ${enAttente ? `
          <button class="chantiers-btn" data-action="generer">${aProposition ? 'Régénérer la proposition' : 'Générer une proposition (IA)'}</button>
          ${aProposition ? (approuvee
            ? '<button class="chantiers-btn" data-action="rejeter">Retirer l\'approbation</button>'
            : '<button class="chantiers-btn chantiers-btn-primary" data-action="approuver">Approuver</button>'
          ) : ''}
          ${aProposition && approuvee ? '<button class="chantiers-btn chantiers-btn-primary" data-action="appliquer">✓ Appliquer ce chantier</button>' : ''}
          <button class="chantiers-btn" data-action="ignorer">Ignorer</button>
          <button class="chantiers-btn" data-action="marquer_traite">Marquer traité manuellement</button>
        ` : `
          <button class="chantiers-btn" data-action="rouvrir">Rouvrir (repasser à traiter)</button>
        `}
      </div>
      <div class="chantiers-row-msg" data-role="msg"></div>
    </div>
  `;
}

function _chantiersFormatProposition(p) {
  // Aperçu compact plutôt que le JSON brut complet -- les champs qui
  // comptent pour une relecture humaine rapide, pas le schéma zone entier.

  // doublon_pays_entier (14 sept 2026) : forme différente des deux types
  // existants (pas une zone complète) -- slug conservé + zones retirées,
  // avec un extrait narratif par zone quand le diagnostic l'a fourni. Ce
  // contexte est ce qui permet de repérer un cas comme "Inde-Corée du Sud
  // (nœud eurasiatique du Pacte)" -- rattachement volontaire, pas un vrai
  // doublon -- avant d'approuver plutôt qu'après coup (cf. handoff du 14
  // sept, bug #6). Sans ce champ, l'utilisateur ne verrait qu'un nom de
  // zone, insuffisant pour juger.
  if (p.slug_a_conserver) {
    const lignes = [`conservé sur : ${p.slug_a_conserver}`];
    for (const z of (p.zones_a_retirer || [])) {
      if (typeof z === 'string') {
        lignes.push(`retiré de : ${z}`);
      } else {
        lignes.push(`retiré de : ${z.nom || z.slug}`);
        if (z.contexte_narratif) lignes.push(`  ↳ « ${z.contexte_narratif} »`);
      }
    }
    return lignes.join('\n');
  }

  const lignes = [];
  if (p.nom) lignes.push(`nom: ${p.nom}`);
  if (p.slug) lignes.push(`slug: ${p.slug}`);
  if (p.type) lignes.push(`type: ${p.type}`);
  if (p.description) lignes.push(`description: ${p.description}`);
  return lignes.join('\n') || JSON.stringify(p, null, 2);
}

// Délégation d'événements sur la liste entière -- les lignes sont
// reconstruites à chaque refresh, pas la peine de recâbler un listener par
// bouton individuellement.
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('#chantiers-list [data-action]');
  if (!btn) return;
  const row = btn.closest('.chantiers-row');
  const chantierId = row.dataset.chantierId;
  const action = btn.dataset.action;
  const msgEl = row.querySelector('[data-role="msg"]');

  const actions = {
    generer:        () => chantiersAction('/api/chantiers/generer', { id: chantierId }, msgEl, 'Génération en cours (appel IA, peut prendre jusqu\'à 90s)…'),
    approuver:       () => chantiersAction('/api/chantiers/approuver', { id: chantierId, approuve: true }, msgEl),
    rejeter:         () => chantiersAction('/api/chantiers/approuver', { id: chantierId, approuve: false }, msgEl),
    appliquer:       () => chantiersAppliquerUn(chantierId, row, msgEl),
    ignorer:         () => chantiersAction('/api/chantiers/statut', { id: chantierId, statut: 'ignore' }, msgEl),
    marquer_traite:  () => chantiersAction('/api/chantiers/statut', { id: chantierId, statut: 'traite' }, msgEl),
    rouvrir:         () => chantiersAction('/api/chantiers/statut', { id: chantierId, statut: 'a_traiter' }, msgEl),
  };
  if (actions[action]) await actions[action]();
});

async function chantiersAction(url, body, msgEl, loadingText = 'En cours…') {
  msgEl.className = 'chantiers-row-msg loading';
  msgEl.textContent = loadingText;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.ok) {
      await refreshChantiers();
    } else {
      msgEl.className = 'chantiers-row-msg error';
      msgEl.textContent = `Erreur : ${data.error}`;
    }
  } catch (e) {
    msgEl.className = 'chantiers-row-msg error';
    msgEl.textContent = `Erreur réseau : ${e.message}`;
  }
}

async function chantiersAppliquerUn(chantierId, row, msgEl) {
  // Granularité fine ajoutée le 1er août 2026 (--cible côté
  // generer_zones_topdown.py) : applique CE chantier précis, sans toucher
  // aux autres chantiers prêts du même scénario -- contrairement à
  // chantiersAppliquerTout() ci-dessous, qui reste utile pour un traitement
  // en lot volontaire.
  const cible = row.querySelector('.chantiers-cible')?.textContent?.trim() || chantierId;
  const confirmMsg = `Appliquer ce chantier (${cible}) ? Cette action écrit dans le vault (sauvegarde .bak automatique).`;
  if (!confirm(confirmMsg)) return;
  await chantiersAction('/api/chantiers/appliquer', { id: chantierId }, msgEl, 'Application en cours…');
}

async function chantiersAppliquerTout() {
  const scenario = document.getElementById('chantiers-scenario').value;
  const btn = document.getElementById('chantiers-appliquer-tout');
  const body = scenario ? { scenario } : { all: true };

  const confirmMsg = scenario
    ? `Appliquer toutes les propositions approuvées de ${scenario} ? Cette action écrit dans le vault (sauvegarde .bak automatique).`
    : `Appliquer toutes les propositions approuvées des 6 scénarios ? Cette action écrit dans le vault (sauvegarde .bak automatique).`;
  if (!confirm(confirmMsg)) return;

  btn.disabled = true;
  const originalText = btn.textContent;
  btn.textContent = 'Application en cours…';
  try {
    const res = await fetch('/api/chantiers/appliquer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.ok) {
      await refreshChantiers();
    } else {
      alert(`Erreur : ${data.error}`);
    }
  } catch (e) {
    alert(`Erreur réseau : ${e.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

// ══════════════════════════════════════════════════
// REDIMENSIONNEMENT DU SIDEBAR À LA SOURIS (31 juillet 2026)
// ══════════════════════════════════════════════════
// Certains titres de scripts sont trop longs pour la largeur fixe du
// sidebar (retour de David). Ajout d'une poignée de glissement entre
// #sidebar et #main -- largeur mémorisée dans localStorage pour survivre
// aux rechargements de page (contexte : vraie appli Flask locale dans le
// navigateur de David, pas un artifact claude.ai -- localStorage est donc
// approprié ici, contrairement aux artifacts où il est proscrit).
(function initSidebarResizer() {
  const sidebar  = document.getElementById('sidebar');
  const resizer  = document.getElementById('sidebar-resizer');
  if (!sidebar || !resizer) return;

  const STORAGE_KEY = 'ourrassol_sidebar_width';
  const MIN_WIDTH = 180;
  const MAX_WIDTH = 600;

  // Restaurer la largeur sauvegardée au chargement, si présente
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    const largeur = parseInt(saved, 10);
    if (largeur >= MIN_WIDTH && largeur <= MAX_WIDTH) {
      sidebar.style.width = `${largeur}px`;
    }
  }

  let dragging = false;

  resizer.addEventListener('mousedown', (e) => {
    dragging = true;
    resizer.classList.add('dragging');
    document.body.classList.add('sidebar-resizing');
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const rect = sidebar.getBoundingClientRect();
    let largeur = e.clientX - rect.left;
    largeur = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, largeur));
    sidebar.style.width = `${largeur}px`;
  });

  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    resizer.classList.remove('dragging');
    document.body.classList.remove('sidebar-resizing');
    localStorage.setItem(STORAGE_KEY, parseInt(sidebar.style.width, 10));
  });

  // Double-clic sur la poignée : revenir à la largeur par défaut (retire
  // le style inline, laisse style.css reprendre la main)
  resizer.addEventListener('dblclick', () => {
    sidebar.style.width = '';
    localStorage.removeItem(STORAGE_KEY);
  });
})();

// ── Redimensionnement du panneau de détail Rédaction (7 septembre 2026) ──
// Même mécanisme que initSidebarResizer() ci-dessus, mais le panneau est
// à DROITE de sa poignée (pas à gauche comme #sidebar) -- glisser vers la
// gauche doit donc AGRANDIR le panneau, pas le rétrécir. On calcule la
// largeur à partir du bord droit du panneau (fixe pendant le drag) plutôt
// que du bord gauche (qui bouge), plus simple qu'inverser le signe partout.
(function initRedactionResizer() {
  const panel   = document.querySelector('.redaction-sidebar');
  const resizer = document.getElementById('redaction-resizer');
  if (!panel || !resizer) return;

  const STORAGE_KEY = 'ourrassol_redaction_panel_width';
  const MIN_WIDTH = 280;
  const MAX_WIDTH = 900;

  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    const largeur = parseInt(saved, 10);
    if (largeur >= MIN_WIDTH && largeur <= MAX_WIDTH) {
      panel.style.width = `${largeur}px`;
    }
  }

  let dragging = false;

  resizer.addEventListener('mousedown', (e) => {
    dragging = true;
    resizer.classList.add('dragging');
    document.body.classList.add('redaction-resizing');
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const rect = panel.getBoundingClientRect();
    let largeur = rect.right - e.clientX;
    largeur = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, largeur));
    panel.style.width = `${largeur}px`;
  });

  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    resizer.classList.remove('dragging');
    document.body.classList.remove('redaction-resizing');
    localStorage.setItem(STORAGE_KEY, parseInt(panel.style.width, 10));
  });

  resizer.addEventListener('dblclick', () => {
    panel.style.width = '';
    localStorage.removeItem(STORAGE_KEY);
  });
})();

// ── Redimensionnement des panneaux Articles/Instances/Événements
// (7 septembre 2026) -- fonction générique réutilisée sur les 3 onglets
// qui partagent le gabarit .articles-sidebar (même mécanisme que
// initRedactionResizer ci-dessus : panneau à droite de sa poignée,
// largeur calculée depuis le bord droit fixe, une clé localStorage
// distincte par onglet pour que chacun garde sa propre largeur).
function initPanelResizer(panelSelector, resizerId, storageKey) {
  const panel   = document.querySelector(panelSelector);
  const resizer = document.getElementById(resizerId);
  if (!panel || !resizer) return;

  const MIN_WIDTH = 280;
  const MAX_WIDTH = 900;

  const saved = localStorage.getItem(storageKey);
  if (saved) {
    const largeur = parseInt(saved, 10);
    if (largeur >= MIN_WIDTH && largeur <= MAX_WIDTH) {
      panel.style.width = `${largeur}px`;
    }
  }

  let dragging = false;

  resizer.addEventListener('mousedown', (e) => {
    dragging = true;
    resizer.classList.add('dragging');
    document.body.classList.add('panel-resizing');
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const rect = panel.getBoundingClientRect();
    let largeur = rect.right - e.clientX;
    largeur = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, largeur));
    panel.style.width = `${largeur}px`;
  });

  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    resizer.classList.remove('dragging');
    document.body.classList.remove('panel-resizing');
    localStorage.setItem(storageKey, parseInt(panel.style.width, 10));
  });

  resizer.addEventListener('dblclick', () => {
    panel.style.width = '';
    localStorage.removeItem(storageKey);
  });
}

initPanelResizer('#tab-articles .articles-sidebar', 'articles-resizer', 'ourrassol_articles_panel_width');
initPanelResizer('#tab-instances .articles-sidebar', 'instances-resizer', 'ourrassol_instances_panel_width');
initPanelResizer('#tab-event_instances .articles-sidebar', 'event-instances-resizer', 'ourrassol_event_instances_panel_width');

/* ══════════════════════════════════════════════════
   ONGLET RÉDACTION — journalistes & orateurs
   (point 3, 30 août 2026 — voir BACKLOG_ACTIF.md)
   Table plate filtrable/triable/paginée + panneau de détail
   au clic sur une ligne. Édition de ton_personnel uniquement
   (deux modes : IA / personnalisé), via set_ton_personnel.py
   --json en sous-processus. Les autres champs (thématiques,
   séniorité, communautés desservies) sont affichés en lecture
   seule -- pas de mécanisme d'écriture existant pour eux.
   --all-manquants (rattrapage par zone) reste CLI-only,
   volontairement absent de cet onglet.
   ══════════════════════════════════════════════════ */

const RedactionState = {
  all: [],
  filtered: [],
  page: 0,
  perPage: 50,
  sortKey: 'ton_personnel',
  sortDir: 'asc',   // vide d'abord par défaut -- l'usage principal est le rattrapage
  filtersWired: false,
  selected: null,   // référence directe vers un objet de RedactionState.all
};

function _redactionEsc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function loadRedaction() {
  if (!RedactionState.filtersWired) {
    const scenarioSel = document.getElementById('redaction-scenario');
    const scenarios = State.config?.scenarios || [];
    scenarioSel.innerHTML = '<option value="">Tous</option>' +
      scenarios.map(s => `<option value="${s}">${s}</option>`).join('');

    ['redaction-scenario', 'redaction-ligne', 'redaction-role', 'redaction-ton-status']
      .forEach(id => document.getElementById(id).addEventListener('change', refreshRedaction));
    document.getElementById('redaction-search').addEventListener('input', () => {
      RedactionState.page = 0;
      _redactionApplyLocalFilterSort();
      renderRedactionTable();
    });
    document.getElementById('redaction-prev').addEventListener('click', () => {
      if (RedactionState.page > 0) { RedactionState.page--; renderRedactionTable(); }
    });
    document.getElementById('redaction-next').addEventListener('click', () => {
      const maxPage = Math.max(0, Math.ceil(RedactionState.filtered.length / RedactionState.perPage) - 1);
      if (RedactionState.page < maxPage) { RedactionState.page++; renderRedactionTable(); }
    });
    document.querySelectorAll('.redaction-table th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.sort;
        if (RedactionState.sortKey === key) {
          RedactionState.sortDir = RedactionState.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          RedactionState.sortKey = key;
          RedactionState.sortDir = 'asc';
        }
        _redactionApplyLocalFilterSort();
        renderRedactionTable();
      });
    });
    RedactionState.filtersWired = true;
  }
  await refreshRedaction();
}

function _redactionKey(p) {
  return `${p.scenario}::${p.ligne}::${p.zone_slug}::${p.nom}`;
}

async function refreshRedaction() {
  const scenario = document.getElementById('redaction-scenario').value;
  const ligne = document.getElementById('redaction-ligne').value;
  const role = document.getElementById('redaction-role').value;
  const tonStatus = document.getElementById('redaction-ton-status').value;

  const params = new URLSearchParams();
  if (scenario) params.set('scenario', scenario);
  if (ligne) params.set('ligne', ligne);
  if (role) params.set('role', role);
  if (tonStatus) params.set('ton_status', tonStatus);

  const tbody = document.getElementById('redaction-tbody');
  tbody.innerHTML = '<tr><td colspan="9" class="redaction-empty">Chargement…</td></tr>';

  try {
    const res = await fetch(`/api/redaction/personnes?${params.toString()}`);
    const data = await res.json();
    RedactionState.all = data.personnes || [];
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="9" class="redaction-empty">Erreur réseau : ${e.message}</td></tr>`;
    return;
  }

  // Nombre d'articles par personne (7 septembre 2026, chantier "Rédaction :
  // détail journaliste" -- étendu au tableau pour filtrage/tri). Un seul
  // fetch de tous les articles (réutilise ArticlesState.all si déjà chargé
  // par l'onglet Articles cette session), puis comptage local par
  // journaliste_slug normalisé -- pas un appel réseau par personne.
  await _redactionChargerArticlesSiBesoin();
  const comptes = new Map();
  for (const a of (ArticlesState.all || [])) {
    if (!a.journaliste_slug) continue;
    const cle = _redactionNormaliser(a.journaliste_slug);
    comptes.set(cle, (comptes.get(cle) || 0) + 1);
  }
  for (const p of RedactionState.all) {
    p.nb_articles = comptes.get(_redactionNormaliser(p.nom)) || 0;
  }

  // Chaque fetch remplace RedactionState.all par de NOUVEAUX objets --
  // la sélection en cours (RedactionState.selected) pointe donc vers une
  // référence obsolète après tout changement de filtre. Sans cette
  // réconciliation, le panneau reste figé sur son dernier contenu
  // indéfiniment (bug remonté le 30 août -- refreshRedaction() ne
  // rafraîchissait jamais le panneau, seulement la table).
  if (RedactionState.selected) {
    const key = _redactionKey(RedactionState.selected);
    RedactionState.selected = RedactionState.all.find(p => _redactionKey(p) === key) || null;
  }

  RedactionState.page = 0;
  _redactionApplyLocalFilterSort();
  renderRedactionTable();
  renderRedactionPanel();
}

function _redactionApplyLocalFilterSort() {
  const search = (document.getElementById('redaction-search').value || '').trim().toLowerCase();
  let rows = RedactionState.all;
  if (search) {
    rows = rows.filter(p => (p.nom || '').toLowerCase().includes(search));
  }

  const key = RedactionState.sortKey;
  const dir = RedactionState.sortDir === 'asc' ? 1 : -1;
  rows = [...rows].sort((a, b) => {
    // ton_personnel : vide avant rempli en tri "asc" (le cas d'usage principal
    // est le rattrapage -- voir les vides en premier par défaut)
    let av = a[key], bv = b[key];
    if (key === 'ton_personnel') { av = av ? 1 : 0; bv = bv ? 1 : 0; }
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });

  RedactionState.filtered = rows;
}

function renderRedactionTable() {
  const tbody = document.getElementById('redaction-tbody');
  const { filtered, page, perPage } = RedactionState;

  document.getElementById('redaction-count').textContent = `${filtered.length} personne(s)`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="redaction-empty">Aucun résultat pour ces filtres.</td></tr>';
    document.getElementById('redaction-range').textContent = '';
    document.getElementById('redaction-page-label').textContent = '';
    document.getElementById('redaction-prev').disabled = true;
    document.getElementById('redaction-next').disabled = true;
    return;
  }

  const start = page * perPage;
  const slice = filtered.slice(start, start + perPage);

  tbody.innerHTML = slice.map(p => `
    <tr data-key="${_redactionEsc(p.scenario)}::${_redactionEsc(p.ligne)}::${_redactionEsc(p.zone_slug)}::${_redactionEsc(p.nom)}"
        class="${RedactionState.selected === p ? 'active' : ''}">
      <td title="${_redactionEsc(p.scenario)}">${_redactionEsc(p.scenario)}</td>
      <td title="${_redactionEsc(p.ligne)}">${_redactionEsc(p.ligne)}</td>
      <td title="${_redactionEsc(p.zone_nom)}">${_redactionEsc(p.zone_nom)}</td>
      <td>${p.type_diffusion === 'oral' ? 'Oral' : 'Écrit'}</td>
      <td title="${_redactionEsc(p.nom)}">${_redactionEsc(p.nom)}</td>
      <td>${p.role === 'orateur' ? 'Orateur' : 'Journaliste'}</td>
      <td>${p.seniorite ?? ''}</td>
      <td>${p.nb_articles ?? 0}</td>
      <td class="${p.ton_personnel ? 'redaction-ton-rempli' : 'redaction-ton-vide'}">
        ${p.ton_personnel ? 'Rempli' : 'Vide'}
      </td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr[data-key]').forEach((tr, i) => {
    tr.addEventListener('click', () => {
      selectRedactionRow(slice[i]);
    });
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  document.getElementById('redaction-range').textContent =
    `${start + 1}–${Math.min(start + perPage, filtered.length)} sur ${filtered.length}`;
  document.getElementById('redaction-page-label').textContent = `page ${page + 1} / ${totalPages}`;
  document.getElementById('redaction-prev').disabled = page === 0;
  document.getElementById('redaction-next').disabled = page >= totalPages - 1;
}

function selectRedactionRow(personne) {
  RedactionState.selected = personne;
  renderRedactionTable();
  renderRedactionPanel();
}

// Rapprochement journaliste/orateur <-> articles (7 septembre 2026,
// chantier "Rédaction : détail journaliste"). Plutôt que de répliquer
// côté client la formule exacte de slugification utilisée à la
// génération de l'article (journaliste_slug, écrit côté backend --
// voir prompt_builder.py), on normalise les deux côtés (nom curaté ET
// journaliste_slug de l'article) vers une forme comparable : accents
// retirés, minuscule, tout séparateur (espace/underscore/tiret)
// uniformisé. Plus robuste qu'une dépendance à une formule exacte
// partagée entre deux fichiers différents.
function _redactionNormaliser(s) {
  return (s || '')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

// Charge ArticlesState.all si pas déjà fait cette session (réutilisé par
// le comptage par personne dans refreshRedaction() ET par le détail
// article-par-article du panel ci-dessous -- un seul point de fetch).
async function _redactionChargerArticlesSiBesoin() {
  if (ArticlesState.all && ArticlesState.all.length) return;
  try {
    const res = await fetch('/api/articles/liste');
    const data = await res.json();
    if (res.ok && !data.error) {
      ArticlesState.all = (data.articles || []).map(a => ({
        ...a,
        date_tri: a.annee != null ? (a.annee * 10000 + a.mois * 100 + a.jour) : -1,
      }));
    }
  } catch (e) { /* ArticlesState.all reste [] -- géré par les appelants */ }
}

// Récupère les articles d'une personne. Réutilise ArticlesState.all
// (déjà chargé si l'onglet Articles a été visité cette session, ou par
// refreshRedaction() ci-dessus) -- sinon fetch une fois.
async function _redactionArticlesPourPersonne(p) {
  await _redactionChargerArticlesSiBesoin();
  const cible = _redactionNormaliser(p.nom);
  return (ArticlesState.all || []).filter(
    a => a.journaliste_slug && _redactionNormaliser(a.journaliste_slug) === cible
  );
}

function renderRedactionPanel() {
  const panel = document.getElementById('redaction-panel');
  const p = RedactionState.selected;
  if (!p) {
    panel.innerHTML = '<div class="redaction-panel-empty">Clique sur une ligne pour voir/éditer sa fiche.</div>';
    return;
  }

  const thematiquesSection = p.role === 'journaliste'
    ? `
      <div class="redaction-panel-section">
        <label>Thématiques</label>
        <div id="redaction-thematiques-box" class="redaction-chips-box">Chargement…</div>
      </div>`
    : `
      <div class="redaction-panel-section">
        <label>Communautés desservies</label>
        <div class="redaction-panel-list">${(p.communautes_desservies || []).map(_redactionEsc).join(', ') || '(non renseigné)'}</div>
      </div>
      <div class="redaction-panel-section">
        <label>Réputation orale</label>
        <div class="redaction-panel-list">${_redactionEsc(p.reputation_orale) || '(non renseignée)'}</div>
      </div>`;

  panel.innerHTML = `
    <div class="redaction-panel-title">${_redactionEsc(p.nom)}</div>
    <div class="redaction-panel-sub">${p.role === 'orateur' ? 'Orateur·rice' : 'Journaliste'}</div>

    <div class="redaction-panel-section">
      <label>Journal</label>
      <div class="redaction-panel-list">${_redactionEsc(p.zone_nom)}</div>
    </div>
    <div class="redaction-panel-section">
      <label>Zone</label>
      <div class="redaction-panel-list">${_redactionEsc(p.zone_slug)}</div>
    </div>
    <div class="redaction-panel-section">
      <label>Ligne</label>
      <div class="redaction-panel-list">${_redactionEsc(p.ligne)} — ${_redactionEsc(p.scenario)}</div>
    </div>
    <div class="redaction-panel-section">
      <label>Ton du journal</label>
      <div class="redaction-panel-list">${_redactionEsc(p.zone_ton) || '(non renseigné)'}</div>
    </div>

    <div class="redaction-panel-section">
      <label>Articles</label>
      <div id="redaction-articles-box" class="redaction-panel-list">Chargement…</div>
    </div>

    ${thematiquesSection}

    <div class="redaction-panel-section">
      <label>Séniorité</label>
      <select id="redaction-seniorite-select">
        ${[1, 2, 3, 4, 5].map(n => `<option value="${n}" ${p.seniorite === n ? 'selected' : ''}>${n}</option>`).join('')}
      </select>
      <div id="redaction-seniorite-msg" class="redaction-panel-msg"></div>
    </div>

    <div class="redaction-panel-section">
      <label>ton_personnel</label>
      ${p.ton_personnel
        ? `<div class="redaction-panel-current">${_redactionEsc(p.ton_personnel)}</div>`
        : '<div class="redaction-panel-list" style="margin-bottom:8px">(vide)</div>'}

      <div class="redaction-ton-mode-tabs">
        <div class="redaction-ton-mode-tab active" data-mode="ia">Généré par IA</div>
        <div class="redaction-ton-mode-tab" data-mode="custom">Personnalisé</div>
      </div>

      <textarea id="redaction-ton-custom" rows="3" placeholder="Ton personnalisé…" style="display:none"></textarea>

      ${p.ton_personnel ? '<div class="redaction-panel-warning">Un ton_personnel existe déjà — cette action le remplace.</div>' : ''}

      <button id="redaction-ton-submit" class="redaction-panel-btn">
        ${p.ton_personnel ? 'Régénérer' : 'Générer'}
      </button>
      <div id="redaction-ton-msg" class="redaction-panel-msg"></div>
    </div>
  `;

  if (p.role === 'journaliste') {
    renderRedactionThematiquesBox(p);
  }

  _redactionArticlesPourPersonne(p).then(articles => {
    if (RedactionState.selected !== p) return; // sélection changée entre-temps
    const box = document.getElementById('redaction-articles-box');
    if (!box) return;
    if (!articles.length) {
      box.innerHTML = 'Aucun article trouvé.';
      return;
    }
    box.innerHTML = `<div style="margin-bottom:6px">${articles.length} article(s)</div>` +
      articles.map(a => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid #eee">
          <span title="${_redactionEsc(a.slug)}">${a.annee != null ? `${a.jour} ${MOIS_FR_JS[a.mois]} ${a.annee}` : '(date non reconnue)'} — ${_redactionEsc(a.slug)}</span>
          <button class="redaction-btn-obsidian-article" data-key="${_redactionEsc(_articlesKey(a))}" style="background:#5b4a9e;color:#fff;border:none;border-radius:4px;padding:3px 8px;cursor:pointer;font-size:11px">Obsidian</button>
        </div>
      `).join('');
    box.querySelectorAll('.redaction-btn-obsidian-article').forEach(btn => {
      const key = btn.dataset.key;
      const article = articles.find(a => _articlesKey(a) === key);
      btn.addEventListener('click', () => _articlesOuvrirDansObsidian(article));
    });
  });

  document.getElementById('redaction-seniorite-select').addEventListener('change', (e) => {
    submitRedactionChamps(p, { seniorite: parseInt(e.target.value, 10) }, 'redaction-seniorite-msg');
  });

  let mode = 'ia';
  const tabs = panel.querySelectorAll('.redaction-ton-mode-tab');
  const textarea = document.getElementById('redaction-ton-custom');
  const submitBtn = document.getElementById('redaction-ton-submit');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      mode = tab.dataset.mode;
      tabs.forEach(t => t.classList.toggle('active', t === tab));
      textarea.style.display = mode === 'custom' ? 'block' : 'none';
      submitBtn.textContent = mode === 'custom'
        ? 'Enregistrer'
        : (p.ton_personnel ? 'Régénérer' : 'Générer');
    });
  });

  submitBtn.addEventListener('click', () => submitRedactionTonPersonnel(p, () => mode, textarea));
}

// Cache la liste des thématiques + le plafond (chargée une seule fois par
// session) -- vraie constante THEMATIQUES_CONNUES/MAX_THEMATIQUES_PAR_
// JOURNALISTE depuis le 30 août 2026 (inject_journaliste_custom.py), voir
// app.py.
let _redactionThematiquesCache = null;
let _redactionMaxThematiques = null;

async function renderRedactionThematiquesBox(personne) {
  const box = document.getElementById('redaction-thematiques-box');
  if (!box) return;

  if (!_redactionThematiquesCache) {
    try {
      const res = await fetch('/api/redaction/thematiques');
      const data = await res.json();
      _redactionThematiquesCache = data.thematiques || [];
      _redactionMaxThematiques = data.max_par_journaliste || null;
    } catch (e) {
      box.innerHTML = `<span class="redaction-panel-list">Erreur de chargement : ${e.message}</span>`;
      return;
    }
  }
  // La personne sélectionnée a pu changer pendant le fetch (clic rapide) --
  // on ne rend que si le panneau affiche toujours la même personne.
  if (RedactionState.selected !== personne) return;

  const selected = new Set(personne.thematiques || []);
  box.innerHTML = _redactionThematiquesCache.map(t => `
    <label class="redaction-chip ${selected.has(t) ? 'active' : ''}">
      <input type="checkbox" value="${_redactionEsc(t)}" ${selected.has(t) ? 'checked' : ''}>
      ${_redactionEsc(t)}
    </label>
  `).join('')
    + (_redactionMaxThematiques ? `<div class="redaction-panel-hint">${selected.size} / ${_redactionMaxThematiques} (plafond habituel, pas une limite technique dure)</div>` : '')
    + '<div id="redaction-thematiques-msg" class="redaction-panel-msg"></div>';

  box.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      cb.closest('.redaction-chip').classList.toggle('active', cb.checked);
      const nouvelles = [...box.querySelectorAll('input[type="checkbox"]:checked')].map(c => c.value);
      const hint = box.querySelector('.redaction-panel-hint');
      if (hint && _redactionMaxThematiques) {
        hint.textContent = `${nouvelles.length} / ${_redactionMaxThematiques} (plafond habituel, pas une limite technique dure)`;
        hint.classList.toggle('over', nouvelles.length > _redactionMaxThematiques);
      }
      submitRedactionChamps(personne, { thematiques: nouvelles }, 'redaction-thematiques-msg');
    });
  });
}

async function submitRedactionChamps(personne, champs, msgElId) {
  const msgEl = document.getElementById(msgElId);
  if (msgEl) { msgEl.className = 'redaction-panel-msg loading'; msgEl.textContent = 'Enregistrement…'; }

  try {
    const res = await fetch('/api/redaction/champs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: personne.scenario, ligne: personne.ligne,
        zone_slug: personne.zone_slug, nom: personne.nom, role: personne.role,
        ...champs,
      }),
    });
    const data = await res.json();
    if (data.ok) {
      if ('thematiques' in champs) personne.thematiques = data.thematiques;
      if ('seniorite' in champs) personne.seniorite = data.seniorite;
      if (msgEl) { msgEl.className = 'redaction-panel-msg ok'; msgEl.textContent = '✓ Enregistré.'; }
      renderRedactionTable();
    } else {
      if (msgEl) { msgEl.className = 'redaction-panel-msg error'; msgEl.textContent = `Erreur : ${data.error}`; }
    }
  } catch (e) {
    if (msgEl) { msgEl.className = 'redaction-panel-msg error'; msgEl.textContent = `Erreur réseau : ${e.message}`; }
  }
}

async function submitRedactionTonPersonnel(personne, getMode, textarea) {
  const msgEl = document.getElementById('redaction-ton-msg');
  const submitBtn = document.getElementById('redaction-ton-submit');
  const mode = getMode();
  const texte = (textarea.value || '').trim();

  if (mode === 'custom' && !texte) {
    msgEl.className = 'redaction-panel-msg error';
    msgEl.textContent = 'Entre un texte avant d\'enregistrer.';
    return;
  }

  submitBtn.disabled = true;
  msgEl.className = 'redaction-panel-msg loading';
  msgEl.textContent = mode === 'custom' ? 'Enregistrement…' : 'Génération en cours (appel IA, peut prendre jusqu\'à 90s)…';

  try {
    const res = await fetch('/api/redaction/ton_personnel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario: personne.scenario,
        ligne: personne.ligne,
        zone_slug: personne.zone_slug,
        nom: personne.nom,
        mode: mode === 'custom' ? 'custom' : 'ia',
        texte: mode === 'custom' ? texte : undefined,
        overwrite: !!personne.ton_personnel,
      }),
    });
    const data = await res.json();
    if (data.ok) {
      personne.ton_personnel = data.ton_personnel;
      msgEl.className = 'redaction-panel-msg ok';
      msgEl.textContent = '✓ Enregistré.';
      renderRedactionTable();
      renderRedactionPanel();
    } else {
      msgEl.className = 'redaction-panel-msg error';
      msgEl.textContent = `Erreur : ${data.error}`;
    }
  } catch (e) {
    msgEl.className = 'redaction-panel-msg error';
    msgEl.textContent = `Erreur réseau : ${e.message}`;
  } finally {
    submitBtn.disabled = false;
  }
}

// ═══════════════════════════════════════════════════════════════════════
// Constantes partagées -- ex-écran "Injecter un événement depuis un
// article" (3 septembre 2026), retiré le 6 septembre au profit de
// l'action "Promouvoir en événement" dans l'onglet Articles (couvre le
// même besoin sans la limite de mois : voir plus bas, section Articles).
// Les deux constantes ci-dessous restent utilisées par ce nouveau point
// d'entrée.
// ═══════════════════════════════════════════════════════════════════════

const MOIS_FR_JS = [null, 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                     'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];

// Même liste que VALID_VARS dans inject_custom_events.py -- dupliquée ici
// faute de route dédiée (liste stable, même pattern que les choix de
// scénarios en dur ailleurs dans scripts_config.json).
const INJEV_VALID_VARS = [
  'systeme_economique_redistribution', 'gouvernance_institutions',
  'geopolitique_conflits', 'valeurs_culture_tempo_sociale',
  'organisation_territoires', 'sante_biotechnologies',
  'frontieres_du_systeme', 'technologie_information',
  'climat_environnement_global', 'energie_ressources_critiques',
  'demographie_mobilite_humaine', 'systemes_productifs_travail',
];

// ── Audit & édition de sujets (5 septembre 2026, chantier "Suite
// narrative des événements", point B) ────────────────────────────────
// classes CSS sujets-* dédiées, voir index.html.
//
// Flux : choisir un scénario + type (événement/entité) + sujet ->
// GET /api/sujets/audit liste toutes les occurrences (toutes dates,
// pas seulement le mois de parution actif), avec signal si postérieur
// au mois en cours -> cliquer une occurrence ouvre le panneau avec
// deux actions destructives, TOUJOURS en deux temps : un premier appel
// sans "confirmer" affiche un APERÇU (rien n'est écrit), un second
// appel avec "confirmer": true après clic explicite exécute réellement
// (POST /api/sujets/supprimer_article ou /api/sujets/modifier_date,
// qui appellent editer_sujets.py --json avec/sans --apply selon le cas).
// Jamais de confirmer:true sur le tout premier appel d'une action.

const SujetsState = {
  scenariosWired: false,
  scenario: '',
  type: 'evenement',
  slug: '',
  evenementsCatalogue: [],
  occurrences: [],
  editionActive: null,
  selected: null,       // occurrence actuellement sélectionnée (objet)
  pendingAction: null,  // 'supprimer' | 'modifier_date' | null -- aperçu en attente de confirmation
  pendingApercu: null,  // dernier aperçu reçu du serveur (payload complet)
};

function _sujetsEsc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function loadSujets() {
  if (!SujetsState.scenariosWired) {
    const selScenario = document.getElementById('sujets-scenario');
    const selType = document.getElementById('sujets-type');
    const scenarios = State.config?.scenarios || [];
    selScenario.innerHTML = '<option value="">— choisir —</option>' +
      scenarios.map(s => `<option value="${s}">${s}</option>`).join('');

    selScenario.addEventListener('change', () => {
      SujetsState.scenario = selScenario.value;
      SujetsState.slug = '';
      SujetsState.selected = null;
      refreshSujetsCatalogue();
    });
    selType.addEventListener('change', () => {
      SujetsState.type = selType.value;
      SujetsState.slug = '';
      SujetsState.selected = null;
      refreshSujetsCatalogue();
    });

    document.getElementById('sujets-slug').addEventListener('change', (e) => {
      SujetsState.slug = e.target.value;
      SujetsState.selected = null;
      refreshSujetsOccurrences();
    });
    document.getElementById('sujets-slug-manuel').addEventListener('input', (e) => {
      SujetsState.slug = e.target.value.trim();
    });
    document.getElementById('sujets-slug-manuel').addEventListener('change', () => {
      SujetsState.selected = null;
      refreshSujetsOccurrences();
    });

    SujetsState.scenariosWired = true;
  }
  if (SujetsState.scenario) refreshSujetsCatalogue();
}

// Recharge le sélecteur de sujet quand le scénario ou le type change --
// pour les événements, catalogue réel (audit_sujets.py --list-evenements) ;
// pour les entités, aucun catalogue disponible (pas d'inventaire d'entités
// exposé par ce chantier) -- champ texte libre à la place.
async function refreshSujetsCatalogue() {
  const selSlug = document.getElementById('sujets-slug');
  const inputManuel = document.getElementById('sujets-slug-manuel');

  if (!SujetsState.scenario) {
    selSlug.style.display = '';
    inputManuel.style.display = 'none';
    selSlug.innerHTML = '<option value="">— choisir un scénario d\'abord —</option>';
    document.getElementById('sujets-occurrences').innerHTML =
      '<div class="sujets-panel-empty">Choisis un scénario, un type et un sujet pour voir ses occurrences.</div>';
    renderSujetsPanel(null);
    return;
  }

  if (SujetsState.type === 'entite') {
    selSlug.style.display = 'none';
    inputManuel.style.display = '';
    inputManuel.value = '';
    document.getElementById('sujets-occurrences').innerHTML =
      '<div class="sujets-panel-empty">Tape le slug exact de l\'entité ci-dessus.</div>';
    renderSujetsPanel(null);
    return;
  }

  selSlug.style.display = '';
  inputManuel.style.display = 'none';
  selSlug.innerHTML = '<option value="">Chargement…</option>';

  try {
    const res = await fetch(`/api/sujets/evenements?scenario=${encodeURIComponent(SujetsState.scenario)}`);
    const data = await res.json();
    if (!res.ok || data.error) {
      selSlug.innerHTML = `<option value="">Erreur : ${_sujetsEsc(data.error || res.statusText)}</option>`;
      return;
    }
    SujetsState.evenementsCatalogue = data.evenements || [];
  } catch (e) {
    selSlug.innerHTML = `<option value="">Erreur réseau : ${_sujetsEsc(e.message)}</option>`;
    return;
  }

  if (!SujetsState.evenementsCatalogue.length) {
    selSlug.innerHTML = '<option value="">— aucun événement custom pour ce scénario —</option>';
    document.getElementById('sujets-occurrences').innerHTML = '';
    renderSujetsPanel(null);
    return;
  }

  selSlug.innerHTML = '<option value="">— choisir —</option>' +
    SujetsState.evenementsCatalogue.map(ev =>
      `<option value="${_sujetsEsc(ev.slug)}">${_sujetsEsc(ev.date_label)} — ${_sujetsEsc(ev.nom)}</option>`
    ).join('');
  document.getElementById('sujets-occurrences').innerHTML =
    '<div class="sujets-panel-empty">Choisis un événement ci-dessus.</div>';
  renderSujetsPanel(null);
}

async function refreshSujetsOccurrences() {
  const listEl = document.getElementById('sujets-occurrences');
  const bannerEl = document.getElementById('sujets-banner');

  if (!SujetsState.scenario || !SujetsState.type || !SujetsState.slug) {
    listEl.innerHTML = '<div class="sujets-panel-empty">Choisis un scénario, un type et un sujet pour voir ses occurrences.</div>';
    bannerEl.style.display = 'none';
    renderSujetsPanel(null);
    return;
  }

  listEl.innerHTML = '<div class="sujets-panel-empty">Chargement…</div>';
  bannerEl.style.display = 'none';

  try {
    const url = `/api/sujets/audit?scenario=${encodeURIComponent(SujetsState.scenario)}` +
                `&type=${encodeURIComponent(SujetsState.type)}&slug=${encodeURIComponent(SujetsState.slug)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok || data.error) {
      listEl.innerHTML = `<div class="sujets-panel-empty">Erreur : ${_sujetsEsc(data.error || res.statusText)}</div>`;
      return;
    }
    SujetsState.occurrences = data.occurrences || [];
    SujetsState.editionActive = data.edition_active || null;
  } catch (e) {
    listEl.innerHTML = `<div class="sujets-panel-empty">Erreur réseau : ${_sujetsEsc(e.message)}</div>`;
    return;
  }

  if (SujetsState.editionActive) {
    bannerEl.style.display = 'block';
    bannerEl.textContent = `Mois de parution actif : ${MOIS_FR_JS[SujetsState.editionActive.mois]} ${SujetsState.editionActive.annee}`;
  } else {
    bannerEl.style.display = 'block';
    bannerEl.textContent = 'Aucun mois de parution actif défini -- signal "postérieur" indisponible.';
  }

  renderSujetsOccurrences();
}

function renderSujetsOccurrences() {
  const listEl = document.getElementById('sujets-occurrences');
  if (!SujetsState.occurrences.length) {
    const note = SujetsState.type === 'evenement'
      ? `<div class="sujets-panel-empty">Aucune occurrence -- rappel : seuls les articles générés en mode Forcer sur cet événement depuis le 5 septembre 2026 apparaîtront ici. Un événement jamais forcé n'aura jamais d'entrée, même s'il est mentionné en passant ailleurs.</div>`
      : `<div class="sujets-panel-empty">Aucune occurrence trouvée pour cette entité sur ce scénario.</div>`;
    listEl.innerHTML = note;
    return;
  }

  listEl.innerHTML = SujetsState.occurrences.map((o, i) => `
    <div class="sujets-occurrence ${o.posterieur_edition_active ? 'posterieur' : ''}" data-idx="${i}">
      <div><strong>${o.annee != null ? `${o.jour} ${MOIS_FR_JS[o.mois]} ${o.annee}` : '(date non reconnue)'}</strong>
        — ${_sujetsEsc(o.titre)} <span style="color:#999">(${_sujetsEsc(o.thematique)})</span></div>
      ${o.chapo ? `<div style="font-size:12px;color:#666;margin-top:4px">${_sujetsEsc(o.chapo)}</div>` : ''}
      ${o.posterieur_edition_active ? '<div class="sujets-occurrence-flag">⚠ POSTÉRIEUR AU MOIS DE PARUTION ACTIF -- risque d\'incohérence temporelle</div>' : ''}
      <div style="font-size:11px;color:#aaa;margin-top:4px">${_sujetsEsc(o.fichier)}</div>
    </div>
  `).join('');

  listEl.querySelectorAll('.sujets-occurrence').forEach(card => {
    card.addEventListener('click', () => {
      const idx = parseInt(card.dataset.idx, 10);
      SujetsState.selected = SujetsState.occurrences[idx];
      SujetsState.pendingAction = null;
      SujetsState.pendingApercu = null;
      renderSujetsPanel(SujetsState.selected);
    });
  });
}

function renderSujetsPanel(occurrence) {
  const panel = document.getElementById('sujets-panel');
  if (!occurrence) {
    panel.innerHTML = '<div class="sujets-panel-empty">Clique sur une occurrence pour la supprimer ou modifier sa date.</div>';
    return;
  }

  panel.innerHTML = `
    <div style="font-weight:600;margin-bottom:8px">${_sujetsEsc(occurrence.titre)}</div>
    <div style="font-size:12px;color:#888;margin-bottom:12px">${_sujetsEsc(occurrence.fichier)}</div>
    <button id="sujets-btn-supprimer" class="sujets-action-confirmer" style="background:#c0392b">Supprimer cet article</button>
    <div style="margin-top:12px">
      <label style="font-size:12px;color:#888">Nouvelle date (ex. "23 août 2098")</label><br>
      <input type="text" id="sujets-nouvelle-date" style="width:100%;padding:6px;margin-top:4px" placeholder="23 août 2098">
      <button id="sujets-btn-modifier-date" class="sujets-action-confirmer" style="background:#3b6fd4;margin-top:8px">Prévisualiser le changement de date</button>
    </div>
    <div id="sujets-apercu-zone"></div>
  `;

  document.getElementById('sujets-btn-supprimer').addEventListener('click', () => {
    apercuSupprimerArticle(SujetsState.scenario, occurrence.fichier,
      document.getElementById('sujets-apercu-zone'), refreshSujetsOccurrences);
  });
  document.getElementById('sujets-btn-modifier-date').addEventListener('click', () => {
    const nouvelleDate = document.getElementById('sujets-nouvelle-date').value.trim();
    if (!nouvelleDate) return;
    apercuModifierDateArticle(SujetsState.scenario, occurrence.fichier, nouvelleDate,
      document.getElementById('sujets-apercu-zone'), refreshSujetsOccurrences);
  });
}

// ── Suppression : aperçu (confirmer=false) puis confirmation explicite ──
// Généralisé le 5 septembre 2026 (ajout de l'onglet Articles) : prend le
// scénario/fichier/zone d'affichage/callback en paramètres explicites au
// lieu de lire SujetsState directement, pour être réutilisable depuis
// n'importe quel écran (Sujets, Articles).

async function apercuSupprimerArticle(scenario, fichier, zoneEl, onSuccess) {
  zoneEl.innerHTML = '<div class="sujets-action-apercu">Chargement de l\'aperçu…</div>';
  try {
    const res = await fetch('/api/sujets/supprimer_article', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({scenario, fichier, confirmer: false}),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      zoneEl.innerHTML = `<div class="sujets-action-apercu">Erreur : ${_sujetsEsc(data.error || res.statusText)}</div>`;
      return;
    }
    zoneEl.innerHTML = `
      <div class="sujets-action-apercu">
        Cet article sera déplacé vers :<br><code>${_sujetsEsc(data.chemin_corbeille)}</code><br>
        (réversible -- pas de suppression définitive)
      </div>
      <button class="sujets-action-confirmer sujets-btn-confirmer-suppr">Confirmer la suppression</button>
      <button class="sujets-action-annuler sujets-btn-annuler-suppr">Annuler</button>
    `;
    zoneEl.querySelector('.sujets-btn-annuler-suppr').addEventListener('click', () => { zoneEl.innerHTML = ''; });
    zoneEl.querySelector('.sujets-btn-confirmer-suppr').addEventListener('click', async () => {
      zoneEl.innerHTML = '<div class="sujets-action-apercu">Suppression en cours…</div>';
      const res2 = await fetch('/api/sujets/supprimer_article', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({scenario, fichier, confirmer: true}),
      });
      const data2 = await res2.json();
      if (!res2.ok || data2.error) {
        zoneEl.innerHTML = `<div class="sujets-action-apercu">Erreur : ${_sujetsEsc(data2.error || res2.statusText)}</div>`;
        return;
      }
      zoneEl.innerHTML = '<div class="sujets-action-apercu">✓ Article déplacé vers la corbeille.</div>';
      if (onSuccess) onSuccess();
    });
  } catch (e) {
    zoneEl.innerHTML = `<div class="sujets-action-apercu">Erreur réseau : ${_sujetsEsc(e.message)}</div>`;
  }
}

// ── Modification de date : aperçu (confirmer=false) puis confirmation ──

async function apercuModifierDateArticle(scenario, fichier, nouvelleDate, zoneEl, onSuccess) {
  zoneEl.innerHTML = '<div class="sujets-action-apercu">Chargement de l\'aperçu…</div>';
  try {
    const res = await fetch('/api/sujets/modifier_date', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({scenario, fichier, nouvelle_date: nouvelleDate, confirmer: false}),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      zoneEl.innerHTML = `<div class="sujets-action-apercu">Erreur : ${_sujetsEsc(data.error || res.statusText)}</div>`;
      return;
    }
    zoneEl.innerHTML = `
      <div class="sujets-action-apercu">
        date_evenement : <code>${_sujetsEsc(data.date_evenement_avant)}</code> → <code>${_sujetsEsc(data.date_evenement_apres)}</code><br>
        Fichier : <code>${_sujetsEsc(data.fichier_avant)}</code> → <code>${_sujetsEsc(data.fichier_apres_prevu)}</code>
        ${data.renommage_impossible ? `<br><span style="color:#b5651d">⚠ ${_sujetsEsc(data.renommage_impossible)}</span>` : ''}
        ${data.date_publication_sera_synchronisee ? '<br>date_publication sera synchronisée (était identique)' : ''}
      </div>
      <button class="sujets-action-confirmer sujets-btn-confirmer-date" style="background:#3b6fd4">Confirmer le changement</button>
      <button class="sujets-action-annuler sujets-btn-annuler-date">Annuler</button>
    `;
    zoneEl.querySelector('.sujets-btn-annuler-date').addEventListener('click', () => { zoneEl.innerHTML = ''; });
    zoneEl.querySelector('.sujets-btn-confirmer-date').addEventListener('click', async () => {
      zoneEl.innerHTML = '<div class="sujets-action-apercu">Modification en cours…</div>';
      const res2 = await fetch('/api/sujets/modifier_date', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({scenario, fichier, nouvelle_date: nouvelleDate, confirmer: true}),
      });
      const data2 = await res2.json();
      if (!res2.ok || data2.error) {
        zoneEl.innerHTML = `<div class="sujets-action-apercu">Erreur : ${_sujetsEsc(data2.error || res2.statusText)}</div>`;
        return;
      }
      zoneEl.innerHTML = `<div class="sujets-action-apercu">✓ Date modifiée. Sauvegarde : <code>${_sujetsEsc(data2.sauvegarde)}</code></div>`;
      if (onSuccess) onSuccess();
    });
  } catch (e) {
    zoneEl.innerHTML = `<div class="sujets-action-apercu">Erreur réseau : ${_sujetsEsc(e.message)}</div>`;
  }
}

// ── Articles — inventaire complet (5 septembre 2026, chantier "Suite
// narrative des événements") ──────────────────────────────────────────
// classes CSS articles-* dédiées, voir index.html. Même gabarit que
// RedactionState (table triable + filtres + pagination + panneau), mais
// filtrage ENTIÈREMENT côté client après un seul fetch initial (~200
// articles, volume trop modeste pour justifier un aller-retour réseau
// à chaque changement de filtre -- contrairement à /api/redaction/
// personnes qui filtre côté serveur).

const ArticlesState = {
  all: [],
  filtered: [],
  page: 0,
  perPage: 50,
  sortKey: 'date_tri',
  sortDir: 'desc',   // plus récent d'abord par défaut
  filtersWired: false,
  selected: null,
  editionActive: null,   // {annee, mois} ou null si aucune édition enregistrée -- alimente le filtre "Mois en cours seulement"
  basculements: {},       // fichier -> {scenario, type_bascule, justification} -- candidats en cache (detect_basculements_narratifs.py)
  basculementsGeneresLe: {}, // scenario -> horodatage de génération (par scénario, un scan partiel ne touche pas les autres)
};

function _articlesEsc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function loadArticles() {
  if (!ArticlesState.filtersWired) {
    const scenarioSel = document.getElementById('articles-scenario');
    const scenarios = State.config?.scenarios || [];
    scenarioSel.innerHTML = '<option value="">Tous</option>' +
      scenarios.map(s => `<option value="${s}">${s}</option>`).join('');

    ['articles-scenario', 'articles-thematique', 'articles-ligne'].forEach(id =>
      document.getElementById(id).addEventListener('change', () => {
        _articlesDeselect();
        ArticlesState.page = 0;
        _articlesApplyLocalFilterSort();
        renderArticlesTable();
      })
    );
    document.getElementById('articles-evenement-force').addEventListener('change', () => {
      _articlesDeselect();
      ArticlesState.page = 0;
      _articlesApplyLocalFilterSort();
      renderArticlesTable();
    });
    document.getElementById('articles-mois-actif').addEventListener('change', () => {
      _articlesDeselect();
      ArticlesState.page = 0;
      _articlesApplyLocalFilterSort();
      renderArticlesTable();
    });
    document.getElementById('articles-basculement').addEventListener('change', () => {
      _articlesDeselect();
      ArticlesState.page = 0;
      _articlesApplyLocalFilterSort();
      renderArticlesTable();
    });
    document.getElementById('articles-btn-lancer-basculements').addEventListener('click', lancerDetectionBasculements);
    document.getElementById('articles-search').addEventListener('input', () => {
      _articlesDeselect();
      ArticlesState.page = 0;
      _articlesApplyLocalFilterSort();
      renderArticlesTable();
    });
    document.getElementById('articles-prev').addEventListener('click', () => {
      if (ArticlesState.page > 0) { ArticlesState.page--; renderArticlesTable(); }
    });
    document.getElementById('articles-next').addEventListener('click', () => {
      const maxPage = Math.max(0, Math.ceil(ArticlesState.filtered.length / ArticlesState.perPage) - 1);
      if (ArticlesState.page < maxPage) { ArticlesState.page++; renderArticlesTable(); }
    });
    document.querySelectorAll('.articles-table th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.sort;
        if (ArticlesState.sortKey === key) {
          ArticlesState.sortDir = ArticlesState.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          ArticlesState.sortKey = key;
          ArticlesState.sortDir = 'asc';
        }
        _articlesApplyLocalFilterSort();
        renderArticlesTable();
      });
    });
    document.getElementById('articles-btn-rapport-md').addEventListener('click', genererRapportMdArticles);

    // Fermeture de la fiche au clic en dehors du tableau ET du panneau
    // (6 septembre 2026, demande de David) -- un clic sur une ligne du
    // tableau ou dans le panneau lui-même (boutons Supprimer/Modifier-
    // date/Promouvoir) ne doit jamais fermer la fiche qu'on est en train
    // de consulter ou d'utiliser.
    //
    // Bug corrigé le 6 septembre (même jour) : un clic sur une ligne
    // appelle selectArticleRow() -> renderArticlesTable(), qui redessine
    // le <tbody> et DÉTRUIT le <tr> cliqué avant que cet écouteur ne
    // s'exécute (bulle jusqu'à document après le gestionnaire de la
    // ligne). e.target.closest('.articles-table-wrap') échouait alors
    // car e.target n'avait plus de parent -- la fiche se refermait
    // aussitôt ouverte, quel que soit l'endroit cliqué dans le tableau.
    // Corrigé en utilisant e.composedPath(), qui capture la liste des
    // ancêtres AU MOMENT du clic, avant toute modification du DOM --
    // fiable même si l'élément cliqué est ensuite retiré/recréé.
    document.addEventListener('click', (e) => {
      if (!ArticlesState.selected) return;
      const tabEl = document.getElementById('tab-articles');
      if (!tabEl || !tabEl.classList.contains('active')) return;
      const chemin = e.composedPath();
      const dansTableau = chemin.some(el => el.classList && el.classList.contains('articles-table-wrap'));
      const dansPanneau = chemin.some(el => el.classList && el.classList.contains('articles-sidebar'));
      if (!dansTableau && !dansPanneau) {
        _articlesDeselect();
      }
    });

    ArticlesState.filtersWired = true;
  }
  await refreshArticlesData();
}

function _articlesKey(a) {
  return `${a.scenario}::${a.fichier}`;
}

function _articlesDeselect() {
  if (!ArticlesState.selected) return;
  ArticlesState.selected = null;
  renderArticlesTable();
  renderArticlesPanel();
}

// Ouvrir l'article dans Obsidian (6 septembre 2026, demande de David) --
// utilise le schéma d'URI natif d'Obsidian (obsidian://open?vault=...&
// file=...), pas de plugin tiers requis. vault_root vient de State.config
// (déjà chargé au démarrage de l'app, /api/config -- même champ que celui
// lu côté serveur via cfg.get("vault_root") dans toutes les routes
// existantes) : aucune nouvelle route backend nécessaire. Le nom du
// vault est le dernier segment du chemin ; le chemin du fichier est
// relatif au vault (articles/{scenario}/{fichier}), sans l'extension
// .md -- convention du paramètre "file" d'Obsidian. Ouvre dans un nouvel
// onglet/fenêtre : le navigateur délègue alors au système, qui lance
// Obsidian via le schéma d'URI enregistré (aucun effet si Obsidian n'est
// pas installé -- pas de détection possible côté web, échec silencieux
// normal du navigateur dans ce cas).
function _articlesOuvrirDansObsidian(article) {
  const vaultRoot = (State.config?.vault_root || '').replace(/[/\\]+$/, '');
  if (!vaultRoot) {
    alert('vault_root introuvable dans la configuration -- impossible de construire le lien Obsidian.');
    return;
  }
  const vaultName = vaultRoot.split(/[/\\]/).pop();
  const cheminRelatif = `articles/${article.scenario}/${article.fichier.replace(/\.md$/i, '')}`;
  const uri = `obsidian://open?vault=${encodeURIComponent(vaultName)}&file=${encodeURIComponent(cheminRelatif)}`;
  window.open(uri, '_blank');
}

async function refreshArticlesData() {
  const tbody = document.getElementById('articles-tbody');
  tbody.innerHTML = '<tr><td colspan="6" class="articles-empty">Chargement…</td></tr>';

  try {
    const res = await fetch('/api/articles/liste');
    const data = await res.json();
    if (!res.ok || data.error) {
      tbody.innerHTML = `<tr><td colspan="6" class="articles-empty">Erreur : ${_articlesEsc(data.error || res.statusText)}</td></tr>`;
      return;
    }
    ArticlesState.all = (data.articles || []).map(a => ({
      ...a,
      date_tri: a.annee != null ? (a.annee * 10000 + a.mois * 100 + a.jour) : -1,
    }));
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" class="articles-empty">Erreur réseau : ${_articlesEsc(e.message)}</td></tr>`;
    return;
  }

  // Mois de parution actif -- pour le filtre "Mois en cours seulement".
  // Lecture seule, échec silencieux (la case reste alors désactivée) :
  // ne doit jamais bloquer l'affichage de l'inventaire lui-même.
  const moisActifCb = document.getElementById('articles-mois-actif');
  try {
    const resEd = await fetch('/api/edition/active');
    const dataEd = await resEd.json();
    ArticlesState.editionActive = dataEd.active || null;
  } catch (e) {
    ArticlesState.editionActive = null;
  }
  if (ArticlesState.editionActive) {
    moisActifCb.disabled = false;
    moisActifCb.title = '';
  } else {
    moisActifCb.checked = false;
    moisActifCb.disabled = true;
    moisActifCb.title = 'Aucune édition active enregistrée (state/editions.json)';
  }

  // Basculements narratifs -- cache lu ici (rapide, aucun appel LLM),
  // jamais recalculé au chargement de l'onglet. Échec silencieux (case
  // désactivée) : ne doit jamais bloquer l'affichage de l'inventaire.
  const bascCb = document.getElementById('articles-basculement');
  try {
    const resBasc = await fetch('/api/articles/basculements');
    const dataBasc = await resBasc.json();
    ArticlesState.basculements = {};
    ArticlesState.basculementsGeneresLe = {};
    for (const [scenario, bloc] of Object.entries(dataBasc.resultats_par_scenario || {})) {
      ArticlesState.basculementsGeneresLe[scenario] = bloc.generated_at || null;
      for (const c of (bloc.candidats || [])) {
        ArticlesState.basculements[c.fichier] = { scenario, ...c };
      }
    }
  } catch (e) {
    ArticlesState.basculements = {};
    ArticlesState.basculementsGeneresLe = {};
  }
  const aDesResultats = Object.keys(ArticlesState.basculements).length > 0;
  bascCb.disabled = !aDesResultats;
  if (!aDesResultats) {
    bascCb.checked = false;
    bascCb.title = 'Aucune détection encore lancée -- utilise le bouton "Détecter les basculements narratifs"';
  } else {
    bascCb.title = '';
  }
  _articlesRenderBasculementsStatus();

  if (ArticlesState.selected) {
    const key = _articlesKey(ArticlesState.selected);
    ArticlesState.selected = ArticlesState.all.find(a => _articlesKey(a) === key) || null;
  }

  _articlesPopulateThematiqueFilter();
  ArticlesState.page = 0;
  _articlesApplyLocalFilterSort();
  renderArticlesTable();
  renderArticlesPanel();
}

function _articlesPopulateThematiqueFilter() {
  const sel = document.getElementById('articles-thematique');
  const current = sel.value;
  const distinctes = [...new Set(ArticlesState.all.map(a => a.thematique))].sort();
  sel.innerHTML = '<option value="">Toutes</option>' +
    distinctes.map(th => `<option value="${_articlesEsc(th)}">${_articlesEsc(th)}</option>`).join('');
  if (distinctes.includes(current)) sel.value = current;
}

function _articlesApplyLocalFilterSort() {
  const scenario = document.getElementById('articles-scenario').value;
  const thematique = document.getElementById('articles-thematique').value;
  const ligne = document.getElementById('articles-ligne').value;
  const evenementForce = document.getElementById('articles-evenement-force').checked;
  const moisActif = document.getElementById('articles-mois-actif').checked;
  const basculement = document.getElementById('articles-basculement').checked;
  const search = (document.getElementById('articles-search').value || '').trim().toLowerCase();

  let rows = ArticlesState.all;
  if (scenario) rows = rows.filter(a => a.scenario === scenario);
  if (thematique) rows = rows.filter(a => a.thematique === thematique);
  if (ligne) rows = rows.filter(a => a.ligne_editoriale === ligne);
  if (evenementForce) rows = rows.filter(a => (a.evenements_cites || []).length > 0);
  if (basculement) rows = rows.filter(a => !!ArticlesState.basculements[a.fichier]);
  if (moisActif && ArticlesState.editionActive) {
    const { annee, mois } = ArticlesState.editionActive;
    rows = rows.filter(a => a.annee === annee && a.mois === mois);
  }
  if (search) {
    rows = rows.filter(a =>
      (a.slug || '').toLowerCase().includes(search) ||
      (a.chapo || '').toLowerCase().includes(search)
    );
  }

  const key = ArticlesState.sortKey;
  const dir = ArticlesState.sortDir === 'asc' ? 1 : -1;
  rows = [...rows].sort((a, b) => {
    let av = a[key], bv = b[key];
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });

  ArticlesState.filtered = rows;
}

function renderArticlesTable() {
  const tbody = document.getElementById('articles-tbody');
  const { filtered, page, perPage } = ArticlesState;

  document.getElementById('articles-count').textContent = `${filtered.length} article(s)`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="articles-empty">Aucun résultat pour ces filtres.</td></tr>';
    document.getElementById('articles-range').textContent = '';
    document.getElementById('articles-page-label').textContent = '';
    document.getElementById('articles-prev').disabled = true;
    document.getElementById('articles-next').disabled = true;
    return;
  }

  const start = page * perPage;
  const slice = filtered.slice(start, start + perPage);

  tbody.innerHTML = slice.map(a => `
    <tr data-key="${_articlesEsc(_articlesKey(a))}" class="${ArticlesState.selected === a ? 'active' : ''}">
      <td title="${_articlesEsc(a.scenario)}">${_articlesEsc(a.scenario)}</td>
      <td>${a.annee != null ? `${a.jour} ${MOIS_FR_JS[a.mois]} ${a.annee}` : '(non reconnue)'}</td>
      <td title="${_articlesEsc(a.thematique)}">${_articlesEsc(a.thematique)}</td>
      <td>${_articlesEsc(a.ligne_editoriale)}</td>
      <td title="${_articlesEsc(a.slug)}">${_articlesEsc(a.slug)}</td>
      <td title="${_articlesEsc(a.fichier)}">${_articlesEsc(a.fichier)}</td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr[data-key]').forEach((tr, i) => {
    tr.addEventListener('click', () => selectArticleRow(slice[i]));
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  document.getElementById('articles-range').textContent =
    `${start + 1}–${Math.min(start + perPage, filtered.length)} sur ${filtered.length}`;
  document.getElementById('articles-page-label').textContent = `page ${page + 1} / ${totalPages}`;
  document.getElementById('articles-prev').disabled = page === 0;
  document.getElementById('articles-next').disabled = page >= totalPages - 1;
}

function selectArticleRow(article) {
  ArticlesState.selected = article;
  renderArticlesTable();
  renderArticlesPanel();
}

function renderArticlesPanel() {
  const panel = document.getElementById('articles-panel');
  const a = ArticlesState.selected;
  if (!a) {
    panel.innerHTML = '<div class="articles-panel-empty">Clique sur une ligne pour voir le détail et agir dessus.</div>';
    return;
  }

  panel.innerHTML = `
    <div class="articles-panel-title">${_articlesEsc(a.slug)}</div>
    <div class="articles-panel-sub">${a.annee != null ? `${a.jour} ${MOIS_FR_JS[a.mois]} ${a.annee}` : '(date non reconnue)'} — ${_articlesEsc(a.scenario)}</div>
    ${a.chapo ? `<div class="articles-panel-section">${_articlesEsc(a.chapo)}</div>` : ''}
    <div class="articles-panel-section">
      <label>Entités citées</label>
      ${(a.entites_citees || []).length ? _articlesEsc(a.entites_citees.join(', ')) : '—'}
    </div>
    <div class="articles-panel-section">
      <label>Événements cités</label>
      ${(a.evenements_cites || []).length ? _articlesEsc(a.evenements_cites.join(', ')) : '—'}
    </div>
    ${ArticlesState.basculements[a.fichier] ? `
    <div class="articles-panel-section" style="background:#fdf6e8;border:1px solid #e0a12e;border-radius:6px;padding:8px 10px">
      <label style="color:#b5651d">⚠ Basculement narratif détecté — [${_articlesEsc(ArticlesState.basculements[a.fichier].type_bascule)}]</label>
      ${_articlesEsc(ArticlesState.basculements[a.fichier].justification)}
      <div style="font-size:10px;color:#999;margin-top:4px">Catégorie indicative (chapo seul) — vérifie contre le texte intégral avant de promouvoir.</div>
    </div>
    ` : ''}
    <div class="articles-panel-section" style="font-size:11px;color:#aaa">${_articlesEsc(a.fichier)}</div>
    <button id="articles-btn-ouvrir-obsidian" class="sujets-action-confirmer" style="background:#5b4a9e">Ouvrir dans Obsidian</button>
    <button id="articles-btn-supprimer" class="sujets-action-confirmer" style="background:#c0392b;margin-left:6px">Supprimer cet article</button>
    <div style="margin-top:12px">
      <label style="font-size:12px;color:#888">Nouvelle date (ex. "23 août 2098")</label><br>
      <input type="text" id="articles-nouvelle-date" style="width:100%;padding:6px;margin-top:4px" placeholder="23 août 2098">
      <button id="articles-btn-modifier-date" class="sujets-action-confirmer" style="background:#3b6fd4;margin-top:8px">Prévisualiser le changement de date</button>
    </div>
    <div id="articles-apercu-zone"></div>
    <div style="margin-top:12px">
      <button id="articles-btn-promouvoir" class="sujets-action-confirmer" style="background:#2c8a4b">Promouvoir en événement</button>
    </div>
    <div id="articles-promouvoir-zone"></div>
  `;

  document.getElementById('articles-btn-ouvrir-obsidian').addEventListener('click', () => {
    _articlesOuvrirDansObsidian(a);
  });
  document.getElementById('articles-btn-supprimer').addEventListener('click', () => {
    apercuSupprimerArticle(a.scenario, a.fichier,
      document.getElementById('articles-apercu-zone'), refreshArticlesData);
  });
  document.getElementById('articles-btn-modifier-date').addEventListener('click', () => {
    const nouvelleDate = document.getElementById('articles-nouvelle-date').value.trim();
    if (!nouvelleDate) return;
    apercuModifierDateArticle(a.scenario, a.fichier, nouvelleDate,
      document.getElementById('articles-apercu-zone'), refreshArticlesData);
  });
  document.getElementById('articles-btn-promouvoir').addEventListener('click', () => {
    const zone = document.getElementById('articles-promouvoir-zone');
    if (zone.dataset.open === '1') {
      zone.innerHTML = '';
      zone.dataset.open = '0';
    } else {
      zone.dataset.open = '1';
      renderArticlesPromouvoirForm(a, zone);
    }
  });
}

// Promouvoir un article en événement custom depuis l'onglet Articles (5
// septembre 2026, suite du chantier "Suite narrative des événements" --
// corrige la limite de l'écran "Injecter un événement depuis un article"
// (section Édition), qui ne liste que les articles du mois de parution
// actif et verrouille date_approximative dessus. Ici la liste source
// (ArticlesState.all, /api/articles/liste) couvre tout le corpus, tous
// scénarios, et chaque article porte sa vraie date (annee/mois/jour) --
// donc date_approximative est pré-remplie avec l'année RÉELLE de
// l'article et reste éditable, et edition_active est décochée par
// défaut (comportement inverse de l'écran Édition : ici on veut en
// général garder la vraie date, pas la remplacer par le mois actif).
// Même route backend (/api/edition/injecter_evenement), neutre sur ces
// deux champs -- aucun changement côté app.py/inject_custom_events.py.
function _articlesPromSuggestId(article) {
  // Suggestion de départ, éditable -- inject_custom_events.py normalise
  // de toute façon le slug final depuis idea_id (re.sub non-[a-z0-9_]).
  return (article.slug || '').slice(0, 50);
}

function renderArticlesPromouvoirForm(article, container) {
  const entites = article.entites_citees || [];
  const scenarios = State.config?.scenarios || [];
  const dateReelle = article.annee != null
    ? `${article.jour} ${MOIS_FR_JS[article.mois]} ${article.annee}`
    : '(date non reconnue)';

  container.innerHTML = `
    <div class="injev-panel-section" style="margin-top:4px;border-top:1px solid #444;padding-top:12px">
      <div class="injev-panel-title" style="font-size:13px">Promouvoir "${_articlesEsc(article.slug)}" en événement</div>
    </div>

    <div class="injev-panel-section">
      <label>Identifiant (id)</label>
      <input type="text" id="artprom-id" value="${_articlesEsc(_articlesPromSuggestId(article))}">
    </div>

    <div class="injev-panel-section">
      <label>Description</label>
      <textarea id="artprom-description" rows="3">${_articlesEsc(article.chapo || '')}</textarea>
    </div>

    <div class="injev-panel-section">
      <label>Portée</label>
      <select id="artprom-portee">
        <option value="">— choisir —</option>
        <option value="locale">locale</option>
        <option value="regionale">régionale</option>
        <option value="continentale">continentale</option>
        <option value="globale">globale</option>
      </select>
    </div>

    <div class="injev-panel-section">
      <label>Intensité</label>
      <select id="artprom-intensite">
        <option value="">— choisir —</option>
        <option value="faible">faible</option>
        <option value="modérée">modérée</option>
        <option value="forte">forte</option>
        <option value="majeure">majeure</option>
      </select>
    </div>

    <div class="injev-panel-section">
      <label>Date approximative (année)</label>
      <input type="number" id="artprom-date-approximative" value="${article.annee != null ? article.annee : ''}" style="width:100px">
      <div class="injev-panel-hint">Pré-remplie depuis la date réelle de l'article (${_articlesEsc(dateReelle)}) — modifiable.</div>
    </div>

    <div class="injev-panel-section">
      <div class="injev-checkbox-row">
        <input type="checkbox" id="artprom-edition-active">
        <label for="artprom-edition-active" style="margin:0">edition_active — forcer la date sur le mois de parution en cours (écrase l'année ci-dessus)</label>
      </div>
    </div>

    <div class="injev-panel-section">
      <label>Scénarios à couvrir</label>
      <div class="injev-chips-box" id="artprom-scenarios-box">
        ${scenarios.map(s => `
          <label class="injev-chip ${s === article.scenario ? 'active' : ''}">
            <input type="checkbox" value="${s}" ${s === article.scenario ? 'checked' : ''}>
            ${s}
          </label>
        `).join('')}
      </div>
    </div>

    <div class="injev-panel-section">
      <label>Zone (zone_hint, optionnel)</label>
      <input type="text" id="artprom-zone-hint" value="${_articlesEsc(article.zone_principale || '')}">
    </div>

    <div class="injev-panel-section">
      <label>Acteurs impliqués (acteurs_hint, optionnel — issus de l'article)</label>
      <div class="injev-chips-box" id="artprom-acteurs-box">
        ${entites.length ? entites.map(e => `
          <label class="injev-chip">
            <input type="checkbox" value="${_articlesEsc(e)}">
            ${_articlesEsc(e)}
          </label>
        `).join('') : '<span class="injev-panel-hint">Aucune entité citée sur cet article.</span>'}
      </div>
    </div>

    <div class="injev-panel-section">
      <label>Variables systémiques imposées (variables_hint, optionnel)</label>
      <div class="injev-chips-box" id="artprom-variables-box">
        ${INJEV_VALID_VARS.map(v => `
          <label class="injev-chip">
            <input type="checkbox" value="${v}">
            ${v}
          </label>
        `).join('')}
      </div>
    </div>

    <div class="injev-panel-section">
      <div class="injev-checkbox-row">
        <input type="checkbox" id="artprom-dry-run">
        <label for="artprom-dry-run" style="margin:0">Dry-run (n'écrit rien, affiche juste le résultat)</label>
      </div>
    </div>

    <div class="injev-panel-section" style="border-bottom:none">
      <button id="artprom-submit" class="injev-panel-btn">Injecter</button>
      <div id="artprom-msg" class="injev-panel-msg"></div>
      <div id="artprom-result" style="display:none"></div>
    </div>
  `;

  container.querySelectorAll('.injev-chip').forEach(chip => {
    const cb = chip.querySelector('input');
    chip.addEventListener('click', (e) => {
      if (e.target !== cb) cb.checked = !cb.checked;
      chip.classList.toggle('active', cb.checked);
    });
  });

  document.getElementById('artprom-submit').addEventListener('click', () => submitArticlesPromouvoirInjection(article));
}

async function submitArticlesPromouvoirInjection(article) {
  const msgEl = document.getElementById('artprom-msg');
  const resultEl = document.getElementById('artprom-result');
  const submitBtn = document.getElementById('artprom-submit');

  const id = document.getElementById('artprom-id').value.trim();
  const description = document.getElementById('artprom-description').value.trim();
  const portee = document.getElementById('artprom-portee').value;
  const intensite = document.getElementById('artprom-intensite').value;
  const dateApproximativeRaw = document.getElementById('artprom-date-approximative').value.trim();
  const dateApproximative = parseInt(dateApproximativeRaw, 10);
  const editionActive = document.getElementById('artprom-edition-active').checked;
  const zoneHint = document.getElementById('artprom-zone-hint').value.trim();
  const dryRun = document.getElementById('artprom-dry-run').checked;

  const scenarios = [...document.querySelectorAll('#artprom-scenarios-box input:checked')].map(cb => cb.value);
  const acteursHint = [...document.querySelectorAll('#artprom-acteurs-box input:checked')].map(cb => cb.value);
  const variablesHint = [...document.querySelectorAll('#artprom-variables-box input:checked')].map(cb => cb.value);

  if (!id || !description || !portee || !intensite || !Number.isFinite(dateApproximative)) {
    msgEl.className = 'injev-panel-msg error';
    msgEl.textContent = 'id, description, portée, intensité et date approximative (année) sont requis.';
    return;
  }
  if (scenarios.length === 0) {
    msgEl.className = 'injev-panel-msg error';
    msgEl.textContent = 'Sélectionne au moins un scénario.';
    return;
  }

  // date_precise (6 septembre 2026, correctif incohérence de dates) : la
  // date réelle et complète de l'article source (pas juste l'année du
  // champ éditable ci-dessus) -- permet à inject_custom_events.py de
  // distinguer un article contemporain de l'événement (ancrage serré) d'un
  // article rétrospectif (l'événement réel est plus ancien que l'article
  // qui en parle). Absente si la date de l'article n'a pas été reconnue.
  const datePrecise = article.annee != null
    ? `${article.jour} ${MOIS_FR_JS[article.mois]} ${article.annee}`
    : null;

  const idea = {
    id, description, portee, intensite,
    date_approximative: dateApproximative,
    date_precise: datePrecise,
    scenarios,
    edition_active: editionActive,
    zone_hint: zoneHint || null,
    acteurs_hint: acteursHint.length ? acteursHint : null,
    variables_hint: variablesHint.length ? variablesHint : null,
    source: `article:${article.fichier}`,
    dry_run: dryRun,
  };

  submitBtn.disabled = true;
  resultEl.style.display = 'none';
  msgEl.className = 'injev-panel-msg loading';
  msgEl.textContent = `Injection en cours (appel(s) IA, peut prendre jusqu'à ${scenarios.length > 1 ? '4 min' : '2-3 min'})…`;

  try {
    const res = await fetch('/api/edition/injecter_evenement', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(idea),
    });
    const data = await res.json();

    if (!res.ok || data.error) {
      msgEl.className = 'injev-panel-msg error';
      msgEl.textContent = `Erreur : ${data.error || res.statusText}`;
      return;
    }

    msgEl.className = 'injev-panel-msg ok';
    msgEl.textContent = dryRun ? '✓ Dry-run terminé (rien écrit).' : '✓ Terminé.';

    resultEl.style.display = 'block';
    if (dryRun) {
      resultEl.className = 'injev-result-box ok';
      resultEl.innerHTML = `<pre style="white-space:pre-wrap;margin:0;font-size:10.5px">${_articlesEsc(JSON.stringify(data.outcome, null, 2))}</pre>`;
    } else {
      const injected = data.injected_scenarios || [];
      const failed = data.failed_scenarios || [];
      resultEl.className = `injev-result-box ${failed.length ? 'error' : 'ok'}`;
      resultEl.innerHTML =
        (injected.length ? `Injecté avec succès : ${injected.join(', ')}.` : '') +
        (failed.length ? `<br>À revoir (needs_review.yaml) : ${failed.join(', ')}.` : '');
      if (injected.length) refreshArticlesData();
    }
  } catch (e) {
    msgEl.className = 'injev-panel-msg error';
    msgEl.textContent = `Erreur réseau : ${e.message}`;
  } finally {
    submitBtn.disabled = false;
  }
}

// Génère le rapport Markdown complet (documentation/inventaire_articles.md,
// consultable dans Obsidian) -- réutilise /api/sujets/inventaire (POST),
// même route que l'ancien bouton de l'onglet Sujets, seulement déplacée
// ici. Limité au scénario actuellement filtré si un scénario est
// sélectionné, sinon tous scénarios confondus.
async function genererRapportMdArticles() {
  const zone = document.getElementById('articles-rapport-resultat');
  zone.style.display = 'block';
  zone.innerHTML = 'Génération du rapport en cours…';
  try {
    const res = await fetch('/api/sujets/inventaire', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({scenario: document.getElementById('articles-scenario').value || ''}),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      zone.innerHTML = `Erreur : ${_articlesEsc(data.error || res.statusText)}`;
      return;
    }
    zone.innerHTML = `✓ Rapport écrit dans <code>${_articlesEsc(data.rapport_md)}</code> (consultable dans Obsidian)`;
  } catch (e) {
    zone.innerHTML = `Erreur réseau : ${_articlesEsc(e.message)}`;
  }
}

// Détection de basculements narratifs (6 septembre 2026, intégration GUI) --
// affiche l'état du cache (jamais/déjà généré, par scénario) et permet de
// relancer le script à la demande. Statut affiché dans #articles-basculements-statut.
function _articlesRenderBasculementsStatus() {
  const zone = document.getElementById('articles-basculements-statut');
  if (!zone) return;
  const entries = Object.entries(ArticlesState.basculementsGeneresLe || {});
  if (!entries.length) {
    zone.textContent = 'Détection jamais lancée.';
    return;
  }
  const total = Object.keys(ArticlesState.basculements || {}).length;
  const plusRecent = entries.map(([, d]) => d).filter(Boolean).sort().pop();
  zone.textContent = `${total} candidat(s) en cache — dernière génération : ${plusRecent || '?'} `
    + `(${entries.length} scénario(s) couvert(s))`;
}

// Lance detect_basculements_narratifs.py depuis le GUI -- coûte de vrais
// appels LLM (un par scénario scanné), peut prendre plusieurs minutes sur
// tout le corpus. Limité au scénario actuellement filtré si un scénario
// est sélectionné dans la barre de filtres (plus rapide), sinon tout le
// corpus. Le script fusionne lui-même le résultat avec le cache existant
// (voir detect_basculements_narratifs.py::ecrire_cache) -- un scan partiel
// ne fait jamais disparaître les résultats des autres scénarios.
async function lancerDetectionBasculements() {
  const btn = document.getElementById('articles-btn-lancer-basculements');
  const zone = document.getElementById('articles-basculements-statut');
  const scenario = document.getElementById('articles-scenario').value || '';

  btn.disabled = true;
  zone.textContent = scenario
    ? `Détection en cours sur ${scenario}… (jusqu'à 2 min)`
    : `Détection en cours sur tout le corpus… (jusqu'à plusieurs minutes, un appel LLM par scénario)`;

  try {
    const res = await fetch('/api/articles/lancer_basculements', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(scenario ? {scenario} : {}),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      zone.textContent = `Erreur : ${data.error || res.statusText}`;
      return;
    }
    // Recharge tout depuis le cache fraîchement écrit -- source unique de
    // vérité, plutôt que de fusionner la réponse de la requête à la main.
    await refreshArticlesData();
  } catch (e) {
    zone.textContent = `Erreur réseau : ${e.message}`;
  } finally {
    btn.disabled = false;
  }
}

// ═══════════════════════════════════════════════════════════════════════
// ONGLET INSTANCES (chantier "GUI Entités/Instances/Événements/Signaux",
// 7 septembre 2026) -- calque exact de l'onglet Articles ci-dessus,
// réutilise les mêmes classes CSS .articles-*. Filtrage 100% client
// (~750 instances, même volume/logique qu'Articles).
// ═══════════════════════════════════════════════════════════════════════

const InstancesState = {
  all: [],
  filtered: [],
  page: 0,
  perPage: 50,
  sortKey: 'scenario',
  sortDir: 'asc',
  filtersWired: false,
  selected: null,
};

function _instancesEsc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function loadInstances() {
  if (!InstancesState.filtersWired) {
    const scenarioSel = document.getElementById('instances-scenario');
    const scenarios = State.config?.scenarios || [];
    scenarioSel.innerHTML = '<option value="">Tous</option>' +
      scenarios.map(s => `<option value="${s}">${s}</option>`).join('');

    ['instances-scenario', 'instances-type', 'instances-trajectoire'].forEach(id =>
      document.getElementById(id).addEventListener('change', () => {
        _instancesDeselect();
        InstancesState.page = 0;
        _instancesApplyLocalFilterSort();
        renderInstancesTable();
      })
    );
    ['instances-transnationale', 'instances-clandestine'].forEach(id =>
      document.getElementById(id).addEventListener('change', () => {
        _instancesDeselect();
        InstancesState.page = 0;
        _instancesApplyLocalFilterSort();
        renderInstancesTable();
      })
    );
    document.getElementById('instances-search').addEventListener('input', () => {
      _instancesDeselect();
      InstancesState.page = 0;
      _instancesApplyLocalFilterSort();
      renderInstancesTable();
    });
    document.getElementById('instances-prev').addEventListener('click', () => {
      if (InstancesState.page > 0) { InstancesState.page--; renderInstancesTable(); }
    });
    document.getElementById('instances-next').addEventListener('click', () => {
      const maxPage = Math.max(0, Math.ceil(InstancesState.filtered.length / InstancesState.perPage) - 1);
      if (InstancesState.page < maxPage) { InstancesState.page++; renderInstancesTable(); }
    });
    document.querySelectorAll('#tab-instances .articles-table th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.sort;
        if (InstancesState.sortKey === key) {
          InstancesState.sortDir = InstancesState.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          InstancesState.sortKey = key;
          InstancesState.sortDir = 'asc';
        }
        _instancesApplyLocalFilterSort();
        renderInstancesTable();
      });
    });
    document.getElementById('instances-btn-rapport-md').addEventListener('click', genererRapportMdInstances);

    // Fermeture de la fiche au clic en dehors du tableau/panneau -- même
    // mécanisme (composedPath) qu'Articles, voir le commentaire détaillé
    // là-bas pour le bug corrigé le 6 septembre que ça évite.
    document.addEventListener('click', (e) => {
      if (!InstancesState.selected) return;
      const tabEl = document.getElementById('tab-instances');
      if (!tabEl || !tabEl.classList.contains('active')) return;
      const chemin = e.composedPath();
      const dansTableau = chemin.some(el => el.classList && el.classList.contains('articles-table-wrap'));
      const dansPanneau = chemin.some(el => el.classList && el.classList.contains('articles-sidebar'));
      if (!dansTableau && !dansPanneau) {
        _instancesDeselect();
      }
    });

    InstancesState.filtersWired = true;
  }
  await refreshInstancesData();
}

function _instancesKey(i) {
  return i.fichier;
}

function _instancesDeselect() {
  if (!InstancesState.selected) return;
  InstancesState.selected = null;
  renderInstancesTable();
  renderInstancesPanel();
}

// Ouvrir l'instance dans Obsidian -- même mécanisme que
// _articlesOuvrirDansObsidian(), mais chemin relatif direct (dossier
// plat instances/, pas de sous-dossier par scénario contrairement à
// articles/{scenario}/).
function _instancesOuvrirDansObsidian(instance) {
  const vaultRoot = (State.config?.vault_root || '').replace(/[/\\]+$/, '');
  if (!vaultRoot) {
    alert('vault_root introuvable dans la configuration -- impossible de construire le lien Obsidian.');
    return;
  }
  const vaultName = vaultRoot.split(/[/\\]/).pop();
  const cheminRelatif = `instances/${instance.fichier.replace(/\.md$/i, '')}`;
  const uri = `obsidian://open?vault=${encodeURIComponent(vaultName)}&file=${encodeURIComponent(cheminRelatif)}`;
  window.open(uri, '_blank');
}

async function refreshInstancesData() {
  const tbody = document.getElementById('instances-tbody');
  tbody.innerHTML = '<tr><td colspan="6" class="articles-empty">Chargement…</td></tr>';

  try {
    const res = await fetch('/api/instances/liste');
    const data = await res.json();
    if (!res.ok || data.error) {
      tbody.innerHTML = `<tr><td colspan="6" class="articles-empty">Erreur : ${_instancesEsc(data.error || res.statusText)}</td></tr>`;
      return;
    }
    InstancesState.all = data.instances || [];
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" class="articles-empty">Erreur réseau : ${_instancesEsc(e.message)}</td></tr>`;
    return;
  }

  if (InstancesState.selected) {
    const key = _instancesKey(InstancesState.selected);
    InstancesState.selected = InstancesState.all.find(i => _instancesKey(i) === key) || null;
  }

  _instancesPopulateFilters();
  InstancesState.page = 0;
  _instancesApplyLocalFilterSort();
  renderInstancesTable();
  renderInstancesPanel();
}

function _instancesPopulateFilters() {
  const typeSel = document.getElementById('instances-type');
  const currentType = typeSel.value;
  const types = [...new Set(InstancesState.all.map(i => i.type_dans_scenario))].sort();
  typeSel.innerHTML = '<option value="">Tous</option>' +
    types.map(t => `<option value="${_instancesEsc(t)}">${_instancesEsc(t)}</option>`).join('');
  if (types.includes(currentType)) typeSel.value = currentType;

  const trajSel = document.getElementById('instances-trajectoire');
  const currentTraj = trajSel.value;
  const trajectoires = [...new Set(InstancesState.all.map(i => i.trajectoire))].sort();
  trajSel.innerHTML = '<option value="">Toutes</option>' +
    trajectoires.map(t => `<option value="${_instancesEsc(t)}">${_instancesEsc(t)}</option>`).join('');
  if (trajectoires.includes(currentTraj)) trajSel.value = currentTraj;
}

function _instancesApplyLocalFilterSort() {
  const scenario = document.getElementById('instances-scenario').value;
  const type = document.getElementById('instances-type').value;
  const trajectoire = document.getElementById('instances-trajectoire').value;
  const transnationale = document.getElementById('instances-transnationale').checked;
  const clandestine = document.getElementById('instances-clandestine').checked;
  const search = (document.getElementById('instances-search').value || '').trim().toLowerCase();

  let rows = InstancesState.all;
  if (scenario) rows = rows.filter(i => i.scenario === scenario);
  if (type) rows = rows.filter(i => i.type_dans_scenario === type);
  if (trajectoire) rows = rows.filter(i => i.trajectoire === trajectoire);
  if (transnationale) rows = rows.filter(i => i.transnationale);
  if (clandestine) rows = rows.filter(i => i.est_clandestin);
  if (search) {
    rows = rows.filter(i =>
      (i.name || '').toLowerCase().includes(search) ||
      (i.role_dans_scenario || '').toLowerCase().includes(search)
    );
  }

  const key = InstancesState.sortKey;
  const dir = InstancesState.sortDir === 'asc' ? 1 : -1;
  rows = [...rows].sort((a, b) => {
    let av = a[key], bv = b[key];
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    if (av == null) av = '';
    if (bv == null) bv = '';
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });

  InstancesState.filtered = rows;
}

function renderInstancesTable() {
  const tbody = document.getElementById('instances-tbody');
  const { filtered, page, perPage } = InstancesState;

  document.getElementById('instances-count').textContent = `${filtered.length} instance(s)`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="articles-empty">Aucun résultat pour ces filtres.</td></tr>';
    document.getElementById('instances-range').textContent = '';
    document.getElementById('instances-page-label').textContent = '';
    document.getElementById('instances-prev').disabled = true;
    document.getElementById('instances-next').disabled = true;
    return;
  }

  const start = page * perPage;
  const slice = filtered.slice(start, start + perPage);

  tbody.innerHTML = slice.map(i => `
    <tr data-key="${_instancesEsc(_instancesKey(i))}" class="${InstancesState.selected === i ? 'active' : ''}">
      <td title="${_instancesEsc(i.scenario)}">${_instancesEsc(i.scenario)}</td>
      <td title="${_instancesEsc(i.name)}">${_instancesEsc(i.name)}</td>
      <td title="${_instancesEsc(i.entite_name || i.entite)}">${_instancesEsc(i.entite_name || i.entite || '—')}</td>
      <td title="${_instancesEsc(i.type_dans_scenario)}">${_instancesEsc(i.type_dans_scenario)}</td>
      <td>${_instancesEsc(i.trajectoire)}</td>
      <td>${i.transnationale ? '(transnationale)' : _instancesEsc(i.zone)}</td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr[data-key]').forEach((tr, idx) => {
    tr.addEventListener('click', () => selectInstanceRow(slice[idx]));
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  document.getElementById('instances-range').textContent =
    `${start + 1}–${Math.min(start + perPage, filtered.length)} sur ${filtered.length}`;
  document.getElementById('instances-page-label').textContent = `page ${page + 1} / ${totalPages}`;
  document.getElementById('instances-prev').disabled = page === 0;
  document.getElementById('instances-next').disabled = page >= totalPages - 1;
}

function selectInstanceRow(instance) {
  InstancesState.selected = instance;
  renderInstancesTable();
  renderInstancesPanel();
}

function renderInstancesPanel() {
  const panel = document.getElementById('instances-panel');
  const i = InstancesState.selected;
  if (!i) {
    panel.innerHTML = '<div class="articles-panel-empty">Clique sur une ligne pour voir le détail.</div>';
    return;
  }

  const periode = i.annee_debut != null
    ? `${i.annee_debut}${i.annee_fin ? ' – ' + i.annee_fin : ' – présent'}`
    : '(période inconnue)';

  panel.innerHTML = `
    <div class="articles-panel-title">${_instancesEsc(i.name)}</div>
    <div class="articles-panel-sub">${_instancesEsc(i.scenario)} — ${_instancesEsc(i.type_dans_scenario)}</div>
    <div class="articles-panel-section">
      <label>Entité archétype parente</label>
      ${i.entite_name ? _instancesEsc(i.entite_name) : (i.entite ? `⚠ "${_instancesEsc(i.entite)}" introuvable` : '—')}
    </div>
    ${i.role_dans_scenario ? `
    <div class="articles-panel-section">
      <label>Rôle dans le scénario</label>
      ${_instancesEsc(i.role_dans_scenario)}
    </div>` : ''}
    <div class="articles-panel-section">
      <label>Impact (local / systémique)</label>
      ${i.impact_local != null ? i.impact_local : '?'} / ${i.impact_systemique_global != null ? i.impact_systemique_global : '?'}
    </div>
    <div class="articles-panel-section">
      <label>Trajectoire</label>
      ${_instancesEsc(i.trajectoire)}${i.est_clandestin ? ' — clandestine' : ''}
    </div>
    <div class="articles-panel-section">
      <label>Période</label>
      ${periode}
    </div>
    <div class="articles-panel-section">
      <label>Zone</label>
      ${i.transnationale ? '(transnationale, sans ancrage territorial)' : (_instancesEsc(i.zone) || '—')}
    </div>
    <div class="articles-panel-section" style="font-size:11px;color:#aaa">${_instancesEsc(i.fichier)}</div>
    <button id="instances-btn-ouvrir-obsidian" class="sujets-action-confirmer" style="background:#5b4a9e">Ouvrir dans Obsidian</button>
  `;

  document.getElementById('instances-btn-ouvrir-obsidian').addEventListener('click', () => {
    _instancesOuvrirDansObsidian(i);
  });
}

// Génère le rapport Markdown complet -- même logique que
// genererRapportMdArticles(), limité au scénario filtré si un scénario
// est sélectionné, sinon tous scénarios confondus.
async function genererRapportMdInstances() {
  const zone = document.getElementById('instances-rapport-resultat');
  zone.style.display = 'block';
  zone.innerHTML = 'Génération du rapport en cours…';
  try {
    const res = await fetch('/api/instances/inventaire', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({scenario: document.getElementById('instances-scenario').value || ''}),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      zone.innerHTML = `Erreur : ${_instancesEsc(data.error || res.statusText)}`;
      return;
    }
    zone.innerHTML = `✓ Rapport écrit dans <code>${_instancesEsc(data.rapport_md)}</code> (consultable dans Obsidian)`;
  } catch (e) {
    zone.innerHTML = `Erreur réseau : ${_instancesEsc(e.message)}`;
  }
}

// ═══════════════════════════════════════════════════════════════════════
// ONGLET EVENT_INSTANCES (chantier "GUI Entités/Instances/Événements/
// Signaux", 7 septembre 2026) -- calque exact de l'onglet Instances
// ci-dessus, réutilise les mêmes classes CSS .articles-*.
// ═══════════════════════════════════════════════════════════════════════

const EventInstancesState = {
  all: [],
  filtered: [],
  page: 0,
  perPage: 50,
  sortKey: 'scenario',
  sortDir: 'asc',
  filtersWired: false,
  selected: null,
};

function _eventInstancesEsc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function loadEventInstances() {
  if (!EventInstancesState.filtersWired) {
    const scenarioSel = document.getElementById('event-instances-scenario');
    const scenarios = State.config?.scenarios || [];
    scenarioSel.innerHTML = '<option value="">Tous</option>' +
      scenarios.map(s => `<option value="${s}">${s}</option>`).join('');

    ['event-instances-scenario', 'event-instances-portee', 'event-instances-type'].forEach(id =>
      document.getElementById(id).addEventListener('change', () => {
        _eventInstancesDeselect();
        EventInstancesState.page = 0;
        _eventInstancesApplyLocalFilterSort();
        renderEventInstancesTable();
      })
    );
    document.getElementById('event-instances-impossible').addEventListener('change', () => {
      _eventInstancesDeselect();
      EventInstancesState.page = 0;
      _eventInstancesApplyLocalFilterSort();
      renderEventInstancesTable();
    });
    document.getElementById('event-instances-search').addEventListener('input', () => {
      _eventInstancesDeselect();
      EventInstancesState.page = 0;
      _eventInstancesApplyLocalFilterSort();
      renderEventInstancesTable();
    });
    document.getElementById('event-instances-prev').addEventListener('click', () => {
      if (EventInstancesState.page > 0) { EventInstancesState.page--; renderEventInstancesTable(); }
    });
    document.getElementById('event-instances-next').addEventListener('click', () => {
      const maxPage = Math.max(0, Math.ceil(EventInstancesState.filtered.length / EventInstancesState.perPage) - 1);
      if (EventInstancesState.page < maxPage) { EventInstancesState.page++; renderEventInstancesTable(); }
    });
    document.querySelectorAll('#tab-event_instances .articles-table th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.sort;
        if (EventInstancesState.sortKey === key) {
          EventInstancesState.sortDir = EventInstancesState.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          EventInstancesState.sortKey = key;
          EventInstancesState.sortDir = 'asc';
        }
        _eventInstancesApplyLocalFilterSort();
        renderEventInstancesTable();
      });
    });
    document.getElementById('event-instances-btn-rapport-md').addEventListener('click', genererRapportMdEventInstances);

    document.addEventListener('click', (e) => {
      if (!EventInstancesState.selected) return;
      const tabEl = document.getElementById('tab-event_instances');
      if (!tabEl || !tabEl.classList.contains('active')) return;
      const chemin = e.composedPath();
      const dansTableau = chemin.some(el => el.classList && el.classList.contains('articles-table-wrap'));
      const dansPanneau = chemin.some(el => el.classList && el.classList.contains('articles-sidebar'));
      if (!dansTableau && !dansPanneau) {
        _eventInstancesDeselect();
      }
    });

    EventInstancesState.filtersWired = true;
  }
  await refreshEventInstancesData();
}

function _eventInstancesKey(i) {
  return i.fichier;
}

function _eventInstancesDeselect() {
  if (!EventInstancesState.selected) return;
  EventInstancesState.selected = null;
  renderEventInstancesTable();
  renderEventInstancesPanel();
}

// Ouvrir dans Obsidian -- dossier plat event_instances/, comme instances/.
function _eventInstancesOuvrirDansObsidian(instance) {
  const vaultRoot = (State.config?.vault_root || '').replace(/[/\\]+$/, '');
  if (!vaultRoot) {
    alert('vault_root introuvable dans la configuration -- impossible de construire le lien Obsidian.');
    return;
  }
  const vaultName = vaultRoot.split(/[/\\]/).pop();
  const cheminRelatif = `event_instances/${instance.fichier.replace(/\.md$/i, '')}`;
  const uri = `obsidian://open?vault=${encodeURIComponent(vaultName)}&file=${encodeURIComponent(cheminRelatif)}`;
  window.open(uri, '_blank');
}

async function refreshEventInstancesData() {
  const tbody = document.getElementById('event-instances-tbody');
  tbody.innerHTML = '<tr><td colspan="6" class="articles-empty">Chargement…</td></tr>';

  try {
    const res = await fetch('/api/event_instances/liste');
    const data = await res.json();
    if (!res.ok || data.error) {
      tbody.innerHTML = `<tr><td colspan="6" class="articles-empty">Erreur : ${_eventInstancesEsc(data.error || res.statusText)}</td></tr>`;
      return;
    }
    EventInstancesState.all = data.event_instances || [];
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" class="articles-empty">Erreur réseau : ${_eventInstancesEsc(e.message)}</td></tr>`;
    return;
  }

  if (EventInstancesState.selected) {
    const key = _eventInstancesKey(EventInstancesState.selected);
    EventInstancesState.selected = EventInstancesState.all.find(i => _eventInstancesKey(i) === key) || null;
  }

  _eventInstancesPopulateFilters();
  EventInstancesState.page = 0;
  _eventInstancesApplyLocalFilterSort();
  renderEventInstancesTable();
  renderEventInstancesPanel();
}

function _eventInstancesPopulateFilters() {
  const porteeSel = document.getElementById('event-instances-portee');
  const currentPortee = porteeSel.value;
  const portees = [...new Set(EventInstancesState.all.map(i => i.portee))].sort();
  porteeSel.innerHTML = '<option value="">Toutes</option>' +
    portees.map(p => `<option value="${_eventInstancesEsc(p)}">${_eventInstancesEsc(p)}</option>`).join('');
  if (portees.includes(currentPortee)) porteeSel.value = currentPortee;

  const typeSel = document.getElementById('event-instances-type');
  const currentType = typeSel.value;
  const types = [...new Set(EventInstancesState.all.map(i => i.type_evenement))].sort();
  typeSel.innerHTML = '<option value="">Tous</option>' +
    types.map(t => `<option value="${_eventInstancesEsc(t)}">${_eventInstancesEsc(t)}</option>`).join('');
  if (types.includes(currentType)) typeSel.value = currentType;
}

function _eventInstancesApplyLocalFilterSort() {
  const scenario = document.getElementById('event-instances-scenario').value;
  const portee = document.getElementById('event-instances-portee').value;
  const type = document.getElementById('event-instances-type').value;
  const impossibleSeulement = document.getElementById('event-instances-impossible').checked;
  const search = (document.getElementById('event-instances-search').value || '').trim().toLowerCase();

  let rows = EventInstancesState.all;
  if (scenario) rows = rows.filter(i => i.scenario === scenario);
  if (portee) rows = rows.filter(i => i.portee === portee);
  if (type) rows = rows.filter(i => i.type_evenement === type);
  if (impossibleSeulement) rows = rows.filter(i => i.impossible);
  if (search) {
    rows = rows.filter(i => (i.name || '').toLowerCase().includes(search));
  }

  const key = EventInstancesState.sortKey;
  const dir = EventInstancesState.sortDir === 'asc' ? 1 : -1;
  rows = [...rows].sort((a, b) => {
    let av = a[key], bv = b[key];
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    if (av == null) av = '';
    if (bv == null) bv = '';
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });

  EventInstancesState.filtered = rows;
}

function renderEventInstancesTable() {
  const tbody = document.getElementById('event-instances-tbody');
  const { filtered, page, perPage } = EventInstancesState;

  document.getElementById('event-instances-count').textContent = `${filtered.length} événement(s)`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="articles-empty">Aucun résultat pour ces filtres.</td></tr>';
    document.getElementById('event-instances-range').textContent = '';
    document.getElementById('event-instances-page-label').textContent = '';
    document.getElementById('event-instances-prev').disabled = true;
    document.getElementById('event-instances-next').disabled = true;
    return;
  }

  const start = page * perPage;
  const slice = filtered.slice(start, start + perPage);

  tbody.innerHTML = slice.map(i => `
    <tr data-key="${_eventInstancesEsc(_eventInstancesKey(i))}" class="${EventInstancesState.selected === i ? 'active' : ''}">
      <td title="${_eventInstancesEsc(i.scenario)}">${_eventInstancesEsc(i.scenario)}</td>
      <td title="${_eventInstancesEsc(i.name)}">${_eventInstancesEsc(i.name)}</td>
      <td title="${_eventInstancesEsc(i.archetype_name || i.archetype)}">${_eventInstancesEsc(i.archetype_name || i.archetype || '—')}</td>
      <td>${_eventInstancesEsc(i.portee)}</td>
      <td>${_eventInstancesEsc(i.date_label || i.date)}</td>
      <td>${i.custom ? 'oui' : 'non'}</td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr[data-key]').forEach((tr, idx) => {
    tr.addEventListener('click', () => selectEventInstanceRow(slice[idx]));
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  document.getElementById('event-instances-range').textContent =
    `${start + 1}–${Math.min(start + perPage, filtered.length)} sur ${filtered.length}`;
  document.getElementById('event-instances-page-label').textContent = `page ${page + 1} / ${totalPages}`;
  document.getElementById('event-instances-prev').disabled = page === 0;
  document.getElementById('event-instances-next').disabled = page >= totalPages - 1;
}

function selectEventInstanceRow(instance) {
  EventInstancesState.selected = instance;
  renderEventInstancesTable();
  renderEventInstancesPanel();
}

function renderEventInstancesPanel() {
  const panel = document.getElementById('event-instances-panel');
  const i = EventInstancesState.selected;
  if (!i) {
    panel.innerHTML = '<div class="articles-panel-empty">Clique sur une ligne pour voir le détail.</div>';
    return;
  }

  panel.innerHTML = `
    <div class="articles-panel-title">${_eventInstancesEsc(i.name)}</div>
    <div class="articles-panel-sub">${_eventInstancesEsc(i.scenario)} — ${_eventInstancesEsc(i.type_evenement)}</div>
    ${i.description ? `<div class="articles-panel-section">${_eventInstancesEsc(i.description)}</div>` : ''}
    <div class="articles-panel-section">
      <label>Archétype parent</label>
      ${i.archetype_name ? _eventInstancesEsc(i.archetype_name) : (i.archetype ? `⚠ "${_eventInstancesEsc(i.archetype)}" introuvable` : '—')}
    </div>
    <div class="articles-panel-section">
      <label>Portée</label>
      ${_eventInstancesEsc(i.portee)}${i.impossible ? ' — marqué impossible' : ''}
    </div>
    <div class="articles-panel-section">
      <label>Date</label>
      ${_eventInstancesEsc(i.date_label || i.date || '?')}
    </div>
    <div class="articles-panel-section">
      <label>Origine</label>
      ${i.custom ? 'Custom (injecté manuellement)' : 'Canonique'}
    </div>
    ${i.zone ? `
    <div class="articles-panel-section">
      <label>Localisation</label>
      ${_eventInstancesEsc(i.lieu || i.zone)}${i.type_lieu ? ` (${_eventInstancesEsc(i.type_lieu)})` : ''}
    </div>` : ''}
    <div class="articles-panel-section" style="font-size:11px;color:#aaa">${_eventInstancesEsc(i.fichier)}</div>
    <button id="event-instances-btn-ouvrir-obsidian" class="sujets-action-confirmer" style="background:#5b4a9e">Ouvrir dans Obsidian</button>
  `;

  document.getElementById('event-instances-btn-ouvrir-obsidian').addEventListener('click', () => {
    _eventInstancesOuvrirDansObsidian(i);
  });
}

async function genererRapportMdEventInstances() {
  const zone = document.getElementById('event-instances-rapport-resultat');
  zone.style.display = 'block';
  zone.innerHTML = 'Génération du rapport en cours…';
  try {
    const res = await fetch('/api/event_instances/inventaire', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({scenario: document.getElementById('event-instances-scenario').value || ''}),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      zone.innerHTML = `Erreur : ${_eventInstancesEsc(data.error || res.statusText)}`;
      return;
    }
    zone.innerHTML = `✓ Rapport écrit dans <code>${_eventInstancesEsc(data.rapport_md)}</code> (consultable dans Obsidian)`;
  } catch (e) {
    zone.innerHTML = `Erreur réseau : ${_eventInstancesEsc(e.message)}`;
  }
}

// ═══════════════════════════════════════════════════════════════════════
// ONGLET SIGNAUX FAIBLES (chantier "GUI Entités/Instances/Événements/
// Signaux", 7 septembre 2026, dernier des 3 types) -- calque de
// l'onglet Instances, réutilise .articles-*. Dossier peu peuplé (~3
// signaux) mais même filtrage local que les 2 autres pour cohérence.
// ═══════════════════════════════════════════════════════════════════════

const SignauxState = {
  all: [],
  filtered: [],
  page: 0,
  perPage: 50,
  sortKey: 'slug',
  sortDir: 'asc',
  filtersWired: false,
  selected: null,
};

function _signauxEsc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function loadSignaux() {
  if (!SignauxState.filtersWired) {
    const scenarioSel = document.getElementById('signaux-scenario');
    const scenarios = State.config?.scenarios || [];
    scenarioSel.innerHTML = '<option value="">Tous</option>' +
      scenarios.map(s => `<option value="${s}">${s}</option>`).join('');

    ['signaux-scenario', 'signaux-categorie', 'signaux-statut'].forEach(id =>
      document.getElementById(id).addEventListener('change', () => {
        _signauxDeselect();
        SignauxState.page = 0;
        _signauxApplyLocalFilterSort();
        renderSignauxTable();
      })
    );
    document.getElementById('signaux-impact').addEventListener('change', () => {
      _signauxDeselect();
      SignauxState.page = 0;
      _signauxApplyLocalFilterSort();
      renderSignauxTable();
    });
    document.getElementById('signaux-search').addEventListener('input', () => {
      _signauxDeselect();
      SignauxState.page = 0;
      _signauxApplyLocalFilterSort();
      renderSignauxTable();
    });
    document.getElementById('signaux-prev').addEventListener('click', () => {
      if (SignauxState.page > 0) { SignauxState.page--; renderSignauxTable(); }
    });
    document.getElementById('signaux-next').addEventListener('click', () => {
      const maxPage = Math.max(0, Math.ceil(SignauxState.filtered.length / SignauxState.perPage) - 1);
      if (SignauxState.page < maxPage) { SignauxState.page++; renderSignauxTable(); }
    });
    document.querySelectorAll('#tab-signaux .articles-table th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.sort;
        if (SignauxState.sortKey === key) {
          SignauxState.sortDir = SignauxState.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          SignauxState.sortKey = key;
          SignauxState.sortDir = 'asc';
        }
        _signauxApplyLocalFilterSort();
        renderSignauxTable();
      });
    });
    document.getElementById('signaux-btn-rapport-md').addEventListener('click', genererRapportMdSignaux);

    document.addEventListener('click', (e) => {
      if (!SignauxState.selected) return;
      const tabEl = document.getElementById('tab-signaux');
      if (!tabEl || !tabEl.classList.contains('active')) return;
      const chemin = e.composedPath();
      const dansTableau = chemin.some(el => el.classList && el.classList.contains('articles-table-wrap'));
      const dansPanneau = chemin.some(el => el.classList && el.classList.contains('articles-sidebar'));
      if (!dansTableau && !dansPanneau) {
        _signauxDeselect();
      }
    });

    SignauxState.filtersWired = true;
  }
  await refreshSignauxData();
}

function _signauxKey(s) {
  return s.fichier;
}

function _signauxDeselect() {
  if (!SignauxState.selected) return;
  SignauxState.selected = null;
  renderSignauxTable();
  renderSignauxPanel();
}

// Ouvrir dans Obsidian -- dossier plat signaux_custom/.
function _signauxOuvrirDansObsidian(signal) {
  const vaultRoot = (State.config?.vault_root || '').replace(/[/\\]+$/, '');
  if (!vaultRoot) {
    alert('vault_root introuvable dans la configuration -- impossible de construire le lien Obsidian.');
    return;
  }
  const vaultName = vaultRoot.split(/[/\\]/).pop();
  const cheminRelatif = `signaux_custom/${signal.fichier.replace(/\.md$/i, '')}`;
  const uri = `obsidian://open?vault=${encodeURIComponent(vaultName)}&file=${encodeURIComponent(cheminRelatif)}`;
  window.open(uri, '_blank');
}

async function refreshSignauxData() {
  const tbody = document.getElementById('signaux-tbody');
  tbody.innerHTML = '<tr><td colspan="5" class="articles-empty">Chargement…</td></tr>';

  try {
    const res = await fetch('/api/signaux/liste');
    const data = await res.json();
    if (!res.ok || data.error) {
      tbody.innerHTML = `<tr><td colspan="5" class="articles-empty">Erreur : ${_signauxEsc(data.error || res.statusText)}</td></tr>`;
      return;
    }
    SignauxState.all = (data.signaux || []).map(s => ({
      ...s,
      scenarios_str: (s.scenarios || []).join(', '),
    }));
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" class="articles-empty">Erreur réseau : ${_signauxEsc(e.message)}</td></tr>`;
    return;
  }

  if (SignauxState.selected) {
    const key = _signauxKey(SignauxState.selected);
    SignauxState.selected = SignauxState.all.find(s => _signauxKey(s) === key) || null;
  }

  _signauxPopulateFilters();
  SignauxState.page = 0;
  _signauxApplyLocalFilterSort();
  renderSignauxTable();
  renderSignauxPanel();
}

function _signauxPopulateFilters() {
  const catSel = document.getElementById('signaux-categorie');
  const currentCat = catSel.value;
  const categories = [...new Set(SignauxState.all.map(s => s.categorie))].sort();
  catSel.innerHTML = '<option value="">Toutes</option>' +
    categories.map(c => `<option value="${_signauxEsc(c)}">${_signauxEsc(c)}</option>`).join('');
  if (categories.includes(currentCat)) catSel.value = currentCat;

  const statutSel = document.getElementById('signaux-statut');
  const currentStatut = statutSel.value;
  const statuts = [...new Set(SignauxState.all.map(s => s.statut))].sort();
  statutSel.innerHTML = '<option value="">Tous</option>' +
    statuts.map(s => `<option value="${_signauxEsc(s)}">${_signauxEsc(s)}</option>`).join('');
  if (statuts.includes(currentStatut)) statutSel.value = currentStatut;
}

function _signauxApplyLocalFilterSort() {
  const scenario = document.getElementById('signaux-scenario').value;
  const categorie = document.getElementById('signaux-categorie').value;
  const statut = document.getElementById('signaux-statut').value;
  const impactSeulement = document.getElementById('signaux-impact').checked;
  const search = (document.getElementById('signaux-search').value || '').trim().toLowerCase();

  let rows = SignauxState.all;
  if (scenario) rows = rows.filter(s => (s.scenarios || []).includes(scenario));
  if (categorie) rows = rows.filter(s => s.categorie === categorie);
  if (statut) rows = rows.filter(s => s.statut === statut);
  if (impactSeulement) rows = rows.filter(s => s.a_impact_chiffre);
  if (search) {
    rows = rows.filter(s => (s.slug || '').toLowerCase().includes(search));
  }

  const key = SignauxState.sortKey;
  const dir = SignauxState.sortDir === 'asc' ? 1 : -1;
  rows = [...rows].sort((a, b) => {
    let av = a[key], bv = b[key];
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    if (av == null) av = '';
    if (bv == null) bv = '';
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });

  SignauxState.filtered = rows;
}

function renderSignauxTable() {
  const tbody = document.getElementById('signaux-tbody');
  const { filtered, page, perPage } = SignauxState;

  document.getElementById('signaux-count').textContent = `${filtered.length} signal(aux)`;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="articles-empty">Aucun résultat pour ces filtres.</td></tr>';
    document.getElementById('signaux-range').textContent = '';
    document.getElementById('signaux-page-label').textContent = '';
    document.getElementById('signaux-prev').disabled = true;
    document.getElementById('signaux-next').disabled = true;
    return;
  }

  const start = page * perPage;
  const slice = filtered.slice(start, start + perPage);

  tbody.innerHTML = slice.map(s => `
    <tr data-key="${_signauxEsc(_signauxKey(s))}" class="${SignauxState.selected === s ? 'active' : ''}">
      <td title="${_signauxEsc(s.slug)}">${_signauxEsc(s.slug)}</td>
      <td>${_signauxEsc(s.categorie)}</td>
      <td>${_signauxEsc(s.statut)}</td>
      <td title="${_signauxEsc(s.scenarios_str)}">${_signauxEsc(s.scenarios_str)}</td>
      <td>${s.a_impact_chiffre ? 'oui' : 'non'}</td>
    </tr>
  `).join('');

  tbody.querySelectorAll('tr[data-key]').forEach((tr, idx) => {
    tr.addEventListener('click', () => selectSignalRow(slice[idx]));
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  document.getElementById('signaux-range').textContent =
    `${start + 1}–${Math.min(start + perPage, filtered.length)} sur ${filtered.length}`;
  document.getElementById('signaux-page-label').textContent = `page ${page + 1} / ${totalPages}`;
  document.getElementById('signaux-prev').disabled = page === 0;
  document.getElementById('signaux-next').disabled = page >= totalPages - 1;
}

function selectSignalRow(signal) {
  SignauxState.selected = signal;
  renderSignauxTable();
  renderSignauxPanel();
}

function renderSignauxPanel() {
  const panel = document.getElementById('signaux-panel');
  const s = SignauxState.selected;
  if (!s) {
    panel.innerHTML = '<div class="articles-panel-empty">Clique sur une ligne pour voir le détail.</div>';
    return;
  }

  panel.innerHTML = `
    <div class="articles-panel-title">${_signauxEsc(s.slug)}</div>
    <div class="articles-panel-sub">${_signauxEsc(s.categorie)} — ${_signauxEsc(s.statut)}</div>
    ${s.description ? `<div class="articles-panel-section">${_signauxEsc(s.description)}</div>` : ''}
    <div class="articles-panel-section">
      <label>Variables cibles</label>
      ${(s.variables_cibles || []).length ? _signauxEsc(s.variables_cibles.join(', ')) : '—'}
    </div>
    <div class="articles-panel-section">
      <label>Scénarios rattachés</label>
      ${(s.scenarios || []).length ? _signauxEsc(s.scenarios.join(', ')) : '⚠ aucun (Trajectoire injectée absente/vide)'}
    </div>
    ${(s.trajectoire || []).length ? `
    <div class="articles-panel-section">
      <label>Trajectoire${s.trajectoire.length > 1 ? ` (${s.trajectoire.length} entrées, une par variable cible)` : ''}</label>
      ${s.trajectoire.map((entree, idx) => `
        ${s.trajectoire.length > 1 ? `<div style="font-weight:600;margin-top:${idx > 0 ? '10px' : '0'}">Entrée ${idx + 1}</div>` : ''}
        ${Object.entries(entree).map(([scen, d]) => `
          <div style="margin-top:6px">
            <div style="font-weight:600;color:#555">${_signauxEsc(scen)} <span style="font-weight:400;color:#999">— ${_signauxEsc(d.date_bascule || '')}</span></div>
            <div>${_signauxEsc(d.evolution || '')}</div>
            <div style="font-size:11px;color:#888">${_signauxEsc(d.evenement_cle || '')}</div>
          </div>
        `).join('')}
      `).join('')}
    </div>` : ''}
    <div class="articles-panel-section">
      <label>Source</label>
      ${_signauxEsc(s.source)}
    </div>
    <div class="articles-panel-section">
      <label>Impact chiffré</label>
      ${s.a_impact_chiffre ? 'oui' : 'non'}
    </div>
    <div class="articles-panel-section" style="font-size:11px;color:#aaa">${_signauxEsc(s.fichier)}</div>
    <button id="signaux-btn-ouvrir-obsidian" class="sujets-action-confirmer" style="background:#5b4a9e">Ouvrir dans Obsidian</button>
  `;

  document.getElementById('signaux-btn-ouvrir-obsidian').addEventListener('click', () => {
    _signauxOuvrirDansObsidian(s);
  });
}

async function genererRapportMdSignaux() {
  const zone = document.getElementById('signaux-rapport-resultat');
  zone.style.display = 'block';
  zone.innerHTML = 'Génération du rapport en cours…';
  try {
    const res = await fetch('/api/signaux/inventaire', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({scenario: document.getElementById('signaux-scenario').value || ''}),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      zone.innerHTML = `Erreur : ${_signauxEsc(data.error || res.statusText)}`;
      return;
    }
    zone.innerHTML = `✓ Rapport écrit dans <code>${_signauxEsc(data.rapport_md)}</code> (consultable dans Obsidian)`;
  } catch (e) {
    zone.innerHTML = `Erreur réseau : ${_signauxEsc(e.message)}`;
  }
}

initPanelResizer('#tab-signaux .articles-sidebar', 'signaux-resizer', 'ourrassol_signaux_panel_width');

// ═══════════════════════════════════════════════════════════════════════
// ONGLET RÉSUMÉS PAR SCÉNARIO (demande de David, 7 septembre 2026) --
// gabarit différent des 3 précédents (pas de table+panneau, une grille
// de cartes -- 6 scénarios seulement, pas besoin de filtres/pagination).
// Même mécanique GET (cache)/POST (régénération, coûte de vrais appels
// LLM) que lancerDetectionBasculements() côté onglet Articles.
// ═══════════════════════════════════════════════════════════════════════

const ResumesState = {
  cache: {},       // scenario -> {resume, n_instances, n_evenements, generated_at, erreur?}
  regenerating: new Set(),  // scénarios en cours de régénération (désactive leur bouton)
};

function _resumesEsc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function loadResumes() {
  if (!document.getElementById('resumes-btn-tout-regenerer').dataset.wired) {
    document.getElementById('resumes-btn-tout-regenerer').addEventListener('click', () => {
      regenererResume(null);  // null = tous les scénarios
    });
    document.getElementById('resumes-btn-tout-regenerer').dataset.wired = '1';
  }
  await refreshResumesData();
}

async function refreshResumesData() {
  const grid = document.getElementById('resumes-grid');
  if (!Object.keys(ResumesState.cache).length) {
    grid.innerHTML = '<div class="resumes-card-empty">Chargement…</div>';
  }
  try {
    const res = await fetch('/api/scenarios/resume');
    const data = await res.json();
    if (!res.ok || data.error) {
      grid.innerHTML = `<div class="resumes-card-empty">Erreur : ${_resumesEsc(data.error || res.statusText)}</div>`;
      return;
    }
    ResumesState.cache = data.resumes_par_scenario || {};
  } catch (e) {
    grid.innerHTML = `<div class="resumes-card-empty">Erreur réseau : ${_resumesEsc(e.message)}</div>`;
    return;
  }
  renderResumesGrid();
}

function renderResumesGrid() {
  const grid = document.getElementById('resumes-grid');
  const scenarios = State.config?.scenarios || Object.keys(ResumesState.cache);

  grid.innerHTML = scenarios.map(scenario => {
    const data = ResumesState.cache[scenario];
    const enCours = ResumesState.regenerating.has(scenario);
    let corps;
    if (enCours) {
      corps = '<div class="resumes-card-empty">Génération en cours… (peut prendre jusqu\'à 1-2 min)</div>';
    } else if (data && data.resume) {
      corps = `<div class="resumes-card-text">${_resumesEsc(data.resume)}</div>`;
    } else if (data && data.erreur) {
      corps = `<div class="resumes-card-empty">Échec de la dernière génération : ${_resumesEsc(data.erreur)}</div>`;
    } else {
      corps = '<div class="resumes-card-empty">Jamais généré.</div>';
    }
    const meta = data && data.generated_at
      ? `Généré le ${_resumesEsc(data.generated_at)} — ${data.n_instances ?? '?'} instance(s), ${data.n_evenements ?? '?'} événement(s) considérés`
      : '';
    return `
      <div class="resumes-card" data-scenario="${_resumesEsc(scenario)}">
        <div class="resumes-card-title">${_resumesEsc(scenario)}</div>
        ${meta ? `<div class="resumes-card-meta">${meta}</div>` : ''}
        ${corps}
        <button class="resumes-btn-regenerer" data-scenario="${_resumesEsc(scenario)}" ${enCours ? 'disabled' : ''}>
          ${enCours ? 'Génération…' : (data && data.resume ? 'Régénérer' : 'Générer')}
        </button>
      </div>
    `;
  }).join('');

  grid.querySelectorAll('.resumes-btn-regenerer').forEach(btn => {
    btn.addEventListener('click', () => regenererResume(btn.dataset.scenario));
  });
}

// Régénère un scénario (ou tous si scenario === null). Coûte de vrais
// appels LLM -- jamais déclenché automatiquement, toujours via un clic
// explicite. Désactive le(s) bouton(s) concerné(s) pendant l'appel
// (synchrone côté serveur, peut prendre jusqu'à plusieurs minutes pour
// tous les scénarios).
async function regenererResume(scenario) {
  const toutBtn = document.getElementById('resumes-btn-tout-regenerer');
  const statut = document.getElementById('resumes-statut');

  if (scenario) {
    ResumesState.regenerating.add(scenario);
  } else {
    (State.config?.scenarios || Object.keys(ResumesState.cache)).forEach(s => ResumesState.regenerating.add(s));
    toutBtn.disabled = true;
  }
  renderResumesGrid();
  statut.textContent = scenario
    ? `Génération en cours pour ${scenario}…`
    : `Génération en cours pour tous les scénarios… (jusqu'à plusieurs minutes, 1 appel LLM par scénario)`;

  try {
    const res = await fetch('/api/scenarios/generer_resume', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(scenario ? {scenario} : {}),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      statut.textContent = `Erreur : ${data.error || res.statusText}`;
      return;
    }
    statut.textContent = '';
    // Recharge depuis le cache fraîchement écrit -- source unique de
    // vérité, plutôt que de fusionner la réponse de la requête à la main.
    await refreshResumesData();
  } catch (e) {
    statut.textContent = `Erreur réseau : ${e.message}`;
  } finally {
    if (scenario) {
      ResumesState.regenerating.delete(scenario);
    } else {
      ResumesState.regenerating.clear();
      toutBtn.disabled = false;
    }
    renderResumesGrid();
  }
}
