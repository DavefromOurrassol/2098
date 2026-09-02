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

function showTab(tab) {
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
    if (tab === 'review')    loadReview();
    if (tab === 'config')    loadConfigForm();
  }
}

// ── Vue script ────────────────────────────────────

async function showScript(scriptId) {
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
  faToEn: null,        // mapping FR -> EN name (gui/static/pays_mapping.json)
  affectations: {},    // pays FR -> zone slug|null
  zonesN1: [],          // [{slug,nom,description,color}]
  scenario: null,
  zoneSurlignee: null,  // slug niveau 1 actuellement mis en évidence sur la carte (ou null)
  searchDebounceTimer: null,
  origineReelleParSlug: {},  // slug -> origine_reelle, reconstruit à chaque ouverture d'arbre (split)
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

  if (!CarteState.map) initLeafletMap();
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
    const res = await fetch(`/api/carte/affectations?scenario=${encodeURIComponent(scenario)}`);
    const data = await res.json();
    if (data.error) {
      statusEl.textContent = `Erreur : ${data.error}`;
      return;
    }
    CarteState.affectations = data.affectations || {};
    CarteState.zonesN1 = data.zones_n1 || [];
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
  if (zone.pattern === null || zone.pattern === undefined || !defs) return zone.color;

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

  const enToFr = _buildEnToFrIndex();
  const defs = _ensureSvgDefs();
  const zoneFillMap = {};
  CarteState.zonesN1.forEach(z => { zoneFillMap[z.slug] = _zoneFill(defs, z); });

  CarteState.geojsonLayer = L.geoJSON(CarteState.rawGeojson, {
    style: (feature) => {
      const name = feature.properties?.name || feature.properties?.ADMIN || '';
      const frList = enToFr[_normEn(name)];
      if (!frList) return { fillColor: 'transparent', weight: 0.5, color: '#ccc', fillOpacity: 0 };

      const allNull = frList.every(fr => !CarteState.affectations[fr]);
      if (allNull) return { fillColor: '#999', weight: 1, color: '#666', fillOpacity: 0.5 };

      const zone = frList.map(fr => CarteState.affectations[fr]).filter(Boolean)[0];
      const fill = zoneFillMap[zone] || '#3b6fd4';
      const estSurlignee = CarteState.zoneSurlignee && zone === CarteState.zoneSurlignee;
      return {
        fillColor: fill,
        weight: estSurlignee ? 4 : 1,
        color: estSurlignee ? '#ff5500' : '#666',
        fillOpacity: estSurlignee ? 1 : 0.85,
      };
    },
    onEachFeature: (feature, layer) => {
      const name = feature.properties?.name || feature.properties?.ADMIN || '';
      const frList = enToFr[_normEn(name)];
      if (!frList) return;
      layer.on('click', () => onCartePaysClick(frList, name));
      layer.on('mouseover', () => layer.setStyle({ weight: 2, color: '#222' }));
      layer.on('mouseout', () => layer.setStyle({ weight: 1, color: '#666' }));
      layer.bindTooltip(frList.join(' / '), { sticky: true });
    },
  }).addTo(CarteState.map);

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
  await openArbreZonePanel(racineSlug);

  const noeud = document.querySelector(`#arbre-zone-tree [data-slug="${CSS.escape(resultat.slug)}"]`);
  if (noeud) {
    noeud.scrollIntoView({ behavior: 'smooth', block: 'center' });
    noeud.classList.add('surlignee-recherche');
    setTimeout(() => noeud.classList.remove('surlignee-recherche'), 2500);
  }
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
    return `
    <div class="carte-legend-item" data-slug="${z.slug}">
      <span class="carte-legend-swatch" style="background:${bg}"></span>
      <span class="carte-legend-label">${z.nom}</span>
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
async function openArbreZonePanel(slug) {
  const panel = document.getElementById('carte-panel');
  panel.innerHTML = `<div class="carte-panel-title">Arborescence</div><div class="carte-status">Chargement…</div>`;

  CarteState.zoneSurlignee = slug;
  renderCarteLayer();

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

    CarteState.origineReelleParSlug = {};
    (function indexer(node) {
      CarteState.origineReelleParSlug[node.slug] = node.origine_reelle || [];
      (node.enfants || []).forEach(indexer);
    })(data.arbre);

    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-split-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirSplitPanel(btn.dataset.slug, btn.dataset.nom));
    });

    document.getElementById('arbre-zone-tree').querySelectorAll('.arbre-zone-topdown-btn').forEach(btn => {
      btn.addEventListener('click', () => _ouvrirTopdownRevisionPanel(btn.dataset.slug, btn.dataset.nom));
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
  html += `<span class="arbre-zone-nom">${node.nom}</span>`;
  html += `<span class="arbre-zone-slug">${node.slug}</span>`;
  html += `${typeLabel}${statutLabel}`;
  if (!estRacine) {
    html += `<button class="arbre-zone-move-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Déplacer vers un autre parent">↗️ déplacer</button>`;
  }
  if ((node.origine_reelle || []).length > 1) {
    html += `<button class="arbre-zone-split-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="Sortir un ou plusieurs pays de cette zone vers une autre">✂️ scinder</button>`;
  }
  if (node.niveau === 1) {
    html += `<button class="arbre-zone-topdown-btn" data-slug="${node.slug}" data-nom="${node.nom.replace(/"/g, '&quot;')}" title="P24 étape C — réviser cette zone contre le patron spatial narratif du scénario (ex. suite à un signalement check_patron_spatial_coherence.py)">🧭 réviser (patron spatial)</button>`;
  }
  html += `</div>`;
  html += `<div id="reparent-panel-${node.slug}"></div>`;
  html += `<div id="split-panel-${node.slug}"></div>`;
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
 * Panneau de split de zone (P7 étape 4, 14 juillet 2026) : sort un ou
 * plusieurs pays de origine_reelle vers une nouvelle zone niveau 1 ou une
 * zone niveau 1 existante. Les sous-zones dont la PROPRE origine_reelle
 * référence aussi ce(s) pays suivent automatiquement côté backend --
 * rien à choisir ici, c'est détecté, pas décidé dans ce panneau (voir
 * _apply_split_zone dans app.py).
 */
function _ouvrirSplitPanel(slug, nom) {
  const container = document.getElementById(`split-panel-${slug}`);
  if (!container) return;

  if (container.dataset.open === '1') {
    container.innerHTML = '';
    container.dataset.open = '0';
    return;
  }

  const origineReelle = CarteState.origineReelleParSlug[slug] || [];
  container.dataset.open = '1';

  // Valeur de chaque case = premier token de l'entité (avant parenthèse/virgule) --
  // suffit de cocher UNE formulation, le backend retrouve les autres variantes du
  // même pays via tokenisation complète (ex. cocher "Groenland" retrouve aussi
  // "Danemark (Groenland)" dans la même zone, voir _entite_references_pays).
  const checkboxes = origineReelle.map(o => {
    const premierToken = (o.entite || '').split(/[(,]/)[0].trim().toLowerCase();
    return `
      <label style="display:block;font-size:11px;margin:2px 0">
        <input type="checkbox" class="split-pays-checkbox-${slug}" value="${premierToken}">
        ${o.entite}
      </label>`;
  }).join('');

  container.innerHTML = `
    <div class="carte-panel-proposal-box" style="margin:4px 0 8px 16px">
      <label style="font-size:10px;color:#666">Pays à sortir de "${nom}"</label>
      <div style="margin:6px 0">${checkboxes}</div>
      <label style="font-size:10px;color:#666">Destination</label>
      <select id="split-cible-select-${slug}" style="width:100%;font-size:11px;padding:4px;margin:4px 0">
        <option value="__creer__">+ Créer une nouvelle zone niveau 1…</option>
        <option value="__existante__">→ Ajouter à une zone niveau 1 existante…</option>
      </select>
      <div id="split-cible-form-${slug}"></div>
      <button id="split-impact-btn-${slug}" class="yaml-btn" style="margin-top:4px">🔍 Évaluer l'impact</button>
      <div id="split-impact-report-${slug}"></div>
    </div>
  `;

  const cibleSelect = document.getElementById(`split-cible-select-${slug}`);
  const majFormCible = () => {
    const formEl = document.getElementById(`split-cible-form-${slug}`);
    if (cibleSelect.value === '__existante__') {
      formEl.innerHTML = `
        <div style="border:1px solid #dde3ee;border-radius:4px;padding:8px;margin-top:6px;font-size:10px">
          <input type="text" id="split-existant-slug-${slug}" placeholder="slug de la zone niveau 1 existante"
                 style="width:100%;padding:3px;font-family:'JetBrains Mono',monospace">
        </div>`;
    } else {
      formEl.innerHTML = `
        <div style="border:1px solid #dde3ee;border-radius:4px;padding:8px;margin-top:6px;font-size:10px">
          <input type="text" id="split-nouveau-slug-${slug}" placeholder="slug_nouvelle_zone (minuscules_underscores)"
                 style="width:100%;padding:3px;margin-bottom:4px;font-family:'JetBrains Mono',monospace">
          <input type="text" id="split-nouveau-nom-${slug}" placeholder="Nom affiché"
                 style="width:100%;padding:3px;margin-bottom:4px">
          <select id="split-nouveau-type-${slug}" style="width:100%;padding:3px;margin-bottom:4px">
            ${['bloc_continental','union_regionale','territoire_autonome','territoire_herite','region','ville','infrastructure','site_strategique','zone_sinistree','autre']
              .map(t => `<option value="${t}">${t}</option>`).join('')}
          </select>
          <select id="split-nouveau-statut-${slug}" style="width:100%;padding:3px;margin-bottom:4px">
            ${['dominant','stable','fragmenté','en_declin','disparu','emergent']
              .map(t => `<option value="${t}">${t}</option>`).join('')}
          </select>
          <textarea id="split-nouveau-desc-${slug}" placeholder="Description courte (optionnel)"
                    style="width:100%;padding:3px;margin-bottom:4px;font-size:10px" rows="2"></textarea>
        </div>`;
    }
  };
  cibleSelect.addEventListener('change', majFormCible);
  majFormCible();

  document.getElementById(`split-impact-btn-${slug}`).addEventListener('click', () => {
    const pays = Array.from(document.querySelectorAll(`.split-pays-checkbox-${slug}:checked`)).map(cb => cb.value);
    if (!pays.length) { alert('Coche au moins un pays à sortir.'); return; }

    let cible;
    if (cibleSelect.value === '__existante__') {
      const slugExistant = document.getElementById(`split-existant-slug-${slug}`).value.trim();
      if (!slugExistant) { alert('Slug de la zone existante requis.'); return; }
      cible = { mode: 'zone_existante', slug_existant: slugExistant };
    } else {
      const cibleSlug = document.getElementById(`split-nouveau-slug-${slug}`).value.trim();
      const cibleNom = document.getElementById(`split-nouveau-nom-${slug}`).value.trim();
      const cibleType = document.getElementById(`split-nouveau-type-${slug}`).value;
      const cibleStatut = document.getElementById(`split-nouveau-statut-${slug}`).value;
      const cibleDesc = document.getElementById(`split-nouveau-desc-${slug}`).value.trim();
      if (!cibleSlug || !cibleNom) { alert('Slug et nom de la nouvelle zone requis.'); return; }
      cible = { mode: 'nouvelle_zone_n1', slug: cibleSlug, nom: cibleNom, type: cibleType, statut: cibleStatut, description: cibleDesc };
    }

    _carteImpactSplit(slug, pays, cible, document.getElementById(`split-impact-report-${slug}`));
  });
}

async function _carteImpactSplit(slug, pays, cible, container) {
  container.innerHTML = '<div class="carte-status">Analyse en cours…</div>';
  try {
    const res = await fetch('/api/carte/impact_split_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug_source: slug, pays_a_extraire: pays, cible }),
    });
    const r = await res.json();
    if (r.error) {
      container.innerHTML = `<div class="carte-panel-error">Erreur : ${r.error}</div>`;
      return;
    }

    let html = `<div style="margin-top:6px">`;
    html += `<div><strong>${r.source.nom}</strong> : ${r.source.origine_reelle_avant.length} → ` +
      `${r.source.origine_reelle_apres.length} entrée(s) dans origine_reelle</div>`;
    html += `<div style="margin-top:4px">Entités extraites : ${r.entites_extraites.map(e => e.entite).join(', ')}</div>`;
    html += `<div style="margin-top:4px">Destination : ${r.cible.nom} ` +
      `(${r.cible.mode === 'nouvelle_zone_n1' ? 'nouvelle zone' : 'zone existante'})</div>`;

    if (r.enfants_qui_suivront.length) {
      html += `<div style="margin-top:6px"><strong>${r.enfants_qui_suivront.length} sous-zone(s) suivent automatiquement</strong> ` +
        `(leur propre origine_reelle référence aussi ce(s) pays) :</div>`;
      html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
        r.enfants_qui_suivront.map(e => `<li>${e.nom}</li>`).join('') + '</ul>';
    }
    if (r.enfants_qui_restent.length) {
      html += `<div style="margin-top:6px;color:#888">${r.enfants_qui_restent.length} autre(s) sous-zone(s) restent en place ` +
        `(non liées au(x) pays extrait(s)).</div>`;
    }

    html += `<button id="split-confirm-btn-${slug}" class="yaml-btn" style="margin-top:8px;font-weight:700">✓ Confirmer le split</button>`;
    html += `</div>`;
    container.innerHTML = html;

    document.getElementById(`split-confirm-btn-${slug}`).addEventListener('click', () => {
      _carteSplitZone(slug, pays, cible);
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

async function _carteSplitZone(slug, pays, cible) {
  const reportEl = document.getElementById(`split-impact-report-${slug}`);
  if (reportEl) reportEl.innerHTML = '<div class="carte-status">Split en cours…</div>';
  try {
    const res = await fetch('/api/carte/split_zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: CarteState.scenario, slug_source: slug, pays_a_extraire: pays, cible }),
    });
    const data = await res.json();
    const msg = document.getElementById('carte-panel-msg');
    if (data.ok) {
      if (msg) msg.textContent = `✓ Split effectué : ${data.entites_deplacees} entité(s) → "${data.cible.nom}"` +
        (data.enfants_reparentes_automatiquement.length
          ? `, ${data.enfants_reparentes_automatiquement.length} sous-zone(s) suivie(s)` : '');
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
 * Niveau 1 uniquement pour l'instant — les zones niveau 2/3 n'ont pas
 * d'entrée cliquable dédiée dans l'UI actuelle, seulement dans la légende
 * (qui ne liste que les zones niveau 1 avec une couleur sur la carte).
 */
function openRenommerZonePanel(ancienSlug) {
  const z = CarteState.zonesN1.find(zz => zz.slug === ancienSlug);
  const panel = document.getElementById('carte-panel');

  CarteState.zoneSurlignee = ancienSlug;
  renderCarteLayer();

  panel.innerHTML = `
    <div class="carte-panel-title">Renommer : ${z ? z.nom : ancienSlug}</div>
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
}

function onCartePaysClick(frList, displayName) {
  if (frList.length === 1) {
    openCartePanel(frList[0]);
    return;
  }
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

function openCartePanel(pays) {
  const zone = CarteState.affectations[pays];
  const panel = document.getElementById('carte-panel');

  const zoneOptions = CarteState.zonesN1.map(z =>
    `<option value="${z.slug}" ${z.slug === zone ? 'selected' : ''}>${z.nom} (${z.slug})</option>`
  ).join('');

  panel.innerHTML = `
    <div class="carte-panel-title">${pays}</div>
    <div class="carte-panel-sub">${zone ? `Actuellement : ${zone}` : 'Non affecté'}</div>

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
async function _carteImpactRenommage(ancienSlug, nouveauSlug, nouveauNom, container) {
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

    document.getElementById('renommer-confirm-btn').addEventListener('click', () => {
      _carteRenommerZone(ancienSlug, nouveauSlug, nouveauNom);
    });
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}

/** Applique le renommage confirmé. */
async function _carteRenommerZone(ancienSlug, nouveauSlug, nouveauNom) {
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
      msg.textContent = `✓ Zone renommée : ${ancienSlug} → ${data.nouveau_slug} ` +
        `(${data.enfants_maj} enfant(s), ${data.zones_relations_maj} relation(s), ` +
        `${data.instances_maj} instance(s), ${data.pays_maj} pays mis à jour)`;
      await refreshCarte();
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

const CHANTIERS_TYPE_LABEL = { pays_sans_zone: 'Pays sans zone', zone_suspecte: 'Zone suspecte' };
const CHANTIERS_STATUT_LABEL = { a_traiter: 'À traiter', ignore: 'Ignoré', traite: 'Traité' };

function renderChantierRow(c) {
  const aProposition = c.proposition != null;
  const approuvee = c.proposition_approuvee === true;
  const enAttente = c.statut === 'a_traiter';

  return `
    <div class="chantiers-row" data-chantier-id="${c.id}">
      <div class="chantiers-row-head">
        <span class="chantiers-type-badge">${CHANTIERS_TYPE_LABEL[c.type] || c.type}</span>
        <span class="chantiers-cible">${c.cible}</span>
        <span class="chantiers-statut-badge chantiers-statut-${c.statut}">${CHANTIERS_STATUT_LABEL[c.statut] || c.statut}</span>
        ${aProposition && approuvee ? '<span class="chantiers-approuvee-badge">✓ approuvée</span>' : ''}
      </div>
      <div class="chantiers-probleme">${c.probleme || ''}</div>
      ${aProposition ? `<div class="chantiers-proposal-box">${_chantiersFormatProposition(c.proposition)}</div>` : ''}
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
  tbody.innerHTML = '<tr><td colspan="8" class="redaction-empty">Chargement…</td></tr>';

  try {
    const res = await fetch(`/api/redaction/personnes?${params.toString()}`);
    const data = await res.json();
    RedactionState.all = data.personnes || [];
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8" class="redaction-empty">Erreur réseau : ${e.message}</td></tr>`;
    return;
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
    tbody.innerHTML = '<tr><td colspan="8" class="redaction-empty">Aucun résultat pour ces filtres.</td></tr>';
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
