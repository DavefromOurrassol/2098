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
  });

  modelSel.addEventListener('change', saveLLM);
}

function refreshModelSelect(provider) {
  const llm = State.config?.llm || {};
  const modelSel = document.getElementById('llm-model');
  const badge    = document.getElementById('llm-cost-badge');

  let models, currentModel;
  if (provider === 'mistral') {
    models = llm.available_models_mistral || [];
    currentModel = llm.model_mistral || '';
  } else {
    models = llm.available_models_claude || [];
    currentModel = llm.model_claude || '';
  }

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

  // Mettre à jour State.config local
  if (!State.config.llm) State.config.llm = {};
  State.config.llm.provider = provider;
  if (provider === 'mistral') State.config.llm.model_mistral = model;
  else                        State.config.llm.model_claude  = model;

  try {
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ llm: { provider, model_mistral: State.config.llm.model_mistral, model_claude: State.config.llm.model_claude } }),
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

  modeConfig.choices.forEach((c, i) => {
    const tab = document.createElement('button');
    tab.className = 'mode-tab' + (i === 0 ? ' active' : '');
    tab.dataset.value = c.value;
    tab.textContent = c.label;
    tab.addEventListener('click', () => {
      tabs.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
    });
    tabs.appendChild(tab);
  });

  group.appendChild(tabs);
  return group;
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

  // Mode select
  const modeActive = document.querySelector('.mode-tab.active');
  if (modeActive) args.push(modeActive.dataset.value);

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
      body: JSON.stringify({ script_id: scriptId, args }),
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

  // LLM actif
  const llm = data.llm || {};
  cards.push(statCard('LLM actif',
    `${(llm.provider||'—').charAt(0).toUpperCase()+(llm.provider||'').slice(1)}`,
    llm.model || '—'));

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
    const panel = await buildYamlPanel(yf);
    body.appendChild(panel);
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
