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
  { key: 'generation', label: 'Génération' },
  { key: 'entities',   label: 'Entités' },
  { key: 'maintenance',label: 'Maintenance' },
];

function buildNav() {
  const nav = document.getElementById('nav');
  nav.innerHTML = '';

  // Tableau de bord
  nav.appendChild(makeNavItem('dashboard', '📊', 'Tableau de bord', null, 'tab'));
  nav.appendChild(makeNavItem('carte', '🗺️', 'Carte', null, 'tab'));
  nav.appendChild(makeDivider());

  // Sections scripts
  SECTIONS.forEach(section => {
    nav.appendChild(makeSectionLabel(section.label));
    State.scripts
      .filter(s => s.section === section.key)
      .forEach(s => {
        const badge = s.badge || null;
        nav.appendChild(makeNavItem(s.id, s.icon, s.label, badge, 'script'));
      });
    nav.appendChild(makeDivider());
  });

  // Revue + Config
  nav.appendChild(makeNavItem('review', '🔍', 'Revue', null, 'tab', true));
  nav.appendChild(makeNavItem('config', '⚙️', 'Config', null, 'tab'));
}

function makeNavItem(id, icon, label, badge, type, reviewBadge) {
  const el = document.createElement('div');
  el.className = 'nav-item';
  el.dataset.id = id;
  el.dataset.type = type;

  el.innerHTML = `
    <span class="icon">${icon}</span>
    <span class="label">${label}</span>
    ${badge ? `<span class="badge p7">${badge}</span>` : ''}
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

  // Options standard
  for (const opt of (script.options || [])) {
    const group = await renderOption(opt, script);
    if (group) body.appendChild(group);
  }

  // YAML panels
  await renderYamlPanels(script);

  // État initial de la visibilité mode_only (onglet par défaut = premier de
  // la liste, cf. renderModeSelect) — sans ça, le premier rendu affiche tout
  // avant le premier clic sur un onglet Mode.
  if (script.mode_select) updateModeOnlyVisibility();
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
    // Logique mutually_exclusive
    if (opt.mutually_exclusive_with) {
      chk.addEventListener('change', () => {
        if (chk.checked) {
          const other = document.querySelector(`[data-flag="--${opt.mutually_exclusive_with}"]`);
          if (other && other.type === 'checkbox') other.checked = false;
          const otherSel = document.querySelector(`[data-flag="--${opt.mutually_exclusive_with}"]`);
          if (otherSel && otherSel.tagName === 'SELECT') otherSel.disabled = true;
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

  } else if (opt.type === 'slug_select') {
    const sel = document.createElement('select');
    sel.dataset.flag = opt.flag;
    sel.dataset.slugType = opt.slug_type;
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Chargement…';
    sel.appendChild(placeholder);
    group.appendChild(sel);

    // Charger les slugs en async
    loadSlugsForSelect(sel, opt.slug_type);

    // Si select scénario existe dans le même formulaire, écouter ses changements
    // (délégué après rendu)
    sel.dataset.needsScenario = 'true';

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
    inp.placeholder = opt.label;
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

async function loadSlugsForSelect(sel, slugType) {
  const scenarioSel = document.querySelector('[data-flag="--scenario"]');
  const scenario = scenarioSel ? scenarioSel.value : (State.config?.default_scenario || '');

  try {
    const res = await fetch(`/api/slugs?type=${slugType}&scenario=${scenario}`);
    const data = await res.json();
    sel.innerHTML = '<option value="">— Aucun —</option>';
    (data.slugs || []).forEach(slug => {
      const opt = document.createElement('option');
      opt.value = slug;
      opt.textContent = slug;
      sel.appendChild(opt);
    });
  } catch (e) {
    sel.innerHTML = '<option value="">Erreur chargement</option>';
  }
}

// Rechargement des slug_selects quand le scénario change
document.addEventListener('change', async (e) => {
  if (e.target.dataset.flag === '--scenario') {
    const slugSelects = document.querySelectorAll('[data-needs-scenario="true"]');
    for (const sel of slugSelects) {
      await loadSlugsForSelect(sel, sel.dataset.slugType);
    }
  }
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

document.getElementById('btn-run').addEventListener('click', () => {
  if (!State.activeScriptId) return;

  // Cas spécial : generate_manual utilise ses propres boutons
  const script = State.scripts.find(s => s.id === State.activeScriptId);
  if (script && script.mode === 'manual_steps') return;

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

  btnRaw.addEventListener('click', () => {
    isRawMode = !isRawMode;
    formZone.style.display = isRawMode ? 'none' : 'block';
    rawZone.style.display   = isRawMode ? 'block' : 'none';
    btnRaw.textContent      = isRawMode ? 'Formulaire guidé' : 'Édition brute';
    btnSave.style.display   = isRawMode ? 'none' : '';
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

  return group;
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

  // Validation minimale côté client
  const required = wrapper.querySelectorAll('[data-form-key]:not([data-optional])');
  // (la validation stricte est faite par le script Python)

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

  await refreshCarte();
  // Leaflet a besoin d'un recalcul de taille si le conteneur était display:none au moment de l'init
  setTimeout(() => CarteState.map && CarteState.map.invalidateSize(), 50);
}

function initLeafletMap() {
  const mapEl = document.getElementById('carte-map');
  CarteState.map = L.map(mapEl, { worldCopyJump: true, renderer: L.svg() }).setView([20, 10], 2);
  L.svg().addTo(CarteState.map); // force la création immédiate du <svg> (nécessaire pour injecter les motifs)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
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
      return { fillColor: fill, weight: 1, color: '#666', fillOpacity: 0.85 };
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
    <div class="carte-legend-item">
      <span class="carte-legend-swatch" style="background:${bg}"></span>
      <span class="carte-legend-label">${z.nom}</span>
    </div>`;
  }).join('') + `
    <div class="carte-legend-item">
      <span class="carte-legend-swatch" style="background:#999"></span>
      <span class="carte-legend-label">Non affecté</span>
    </div>
  `;
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
  document.getElementById('carte-panel-ignorer-btn').addEventListener('click', () => _carteIgnorer(pays));
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
        html += '<ul style="margin:4px 0;padding-left:16px;font-size:10px">' +
          r.sous_zones_orphelines.map(sz => `<li>${sz.nom} (${sz.slug}) — origine : ${sz.origine}</li>`).join('') +
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
  } catch (e) {
    container.innerHTML = `<div class="carte-panel-error">Erreur réseau : ${e.message}</div>`;
  }
}
