const state = {
  incidents: [],
  selectedId: null,
  activeFilter: "all",
  search: "",
  config: null,
  audits: [],
};

const icons = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  shield: '<path d="M12 22s8-3.6 8-10V5l-8-3-8 3v7c0 6.4 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  pulse: '<path d="M3 12h4l2-7 4 14 2-7h6"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21a2 2 0 1 1-4 0v-.09A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.34-1.88L4.2 6.66a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3a2 2 0 1 1 4 0v.09A1.7 1.7 0 0 0 15.4 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9c.14.36.35.7.6 1 .3.28.69.42 1.1.4h.09a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.7.6Z"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
  chevron: '<path d="m8 10 4 4 4-4"/>',
  filter: '<path d="M4 5h16M7 12h10M10 19h4"/>',
  sort: '<path d="m8 9 3-3 3 3M11 6v12M16 15l3 3 3-3M19 18V6"/>',
  user: '<path d="M20 21a8 8 0 0 0-16 0"/><circle cx="12" cy="7" r="4"/>',
  ticket: '<path d="M3 7a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-3a2 2 0 0 0 0-4V7Z"/><path d="M13 5v2M13 17v2M13 10v4"/>',
  alert: '<path d="M10.3 3.7 2.2 18a2 2 0 0 0 1.7 3h16.2a2 2 0 0 0 1.7-3L13.7 3.7a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>',
  arrow: '<path d="m9 18 6-6-6-6"/>',
  sparkle: '<path d="m12 3-1.1 3.1a7 7 0 0 1-4.3 4.3L3.5 11.5l3.1 1.1a7 7 0 0 1 4.3 4.3L12 20l1.1-3.1a7 7 0 0 1 4.3-4.3l3.1-1.1-3.1-1.1a7 7 0 0 1-4.3-4.3L12 3Z"/>',
  activity: '<path d="M3 12h4l2-6 4 12 2-6h6"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4.5V3h6v1.5M9 10h6M9 14h6"/>',
  wrench: '<path d="M14.7 6.3a4 4 0 0 0-5-5l2.1 2.1-2.8 2.8-2.1-2.1a4 4 0 0 0 5 5L19 16.2a2 2 0 0 0 2.8-2.8l-7.1-7.1Z"/><path d="m5 15-3 3 4 4 3-3"/>',
  external: '<path d="M14 3h7v7M10 14 21 3"/><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"/>',
  message: '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z"/>',
  refresh: '<path d="M20 6v5h-5M4 18v-5h5"/><path d="M6.1 9a7 7 0 0 1 11.7-2.6L20 11M4 13l2.2 4.6A7 7 0 0 0 17.9 15"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  send: '<path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/>',
  audit: '<path d="M9 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4"/><path d="M9 15h3M9 11h5M9 7h3M16 3h5v5M15 9l6-6"/>',
  closeCircle: '<circle cx="12" cy="12" r="9"/><path d="m9 12 2 2 4-4"/>',
};

function icon(name) {
  return `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name] || ""}</svg>`;
}

function hydrateIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((node) => {
    node.innerHTML = icon(node.dataset.icon);
  });
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[char]);
}

function formatDate(value, withTime = true) {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return escapeHtml(value);
  return new Intl.DateTimeFormat("en", {
    month: "short", day: "numeric", year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(date);
}

function timeAgo(value) {
  if (!value) return "";
  const minutes = Math.max(0, Math.floor((Date.now() - new Date(value).valueOf()) / 60000));
  if (minutes < 1) return "now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", "X-Analyst": "Alex Morgan", ...(options.headers || {}) },
  });
  let payload = null;
  try { payload = await response.json(); } catch { payload = {}; }
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
  return payload;
}

async function boot() {
  hydrateIcons();
  bindStaticEvents();
  try {
    const [health, incidentPayload] = await Promise.all([api("/api/health"), api("/api/incidents")]);
    state.config = health.servicenow;
    state.incidents = incidentPayload.items;
    state.selectedId = state.incidents[0]?.id || null;
    renderMode();
    renderQueue();
    if (state.selectedId) await selectIncident(state.selectedId, false);
  } catch (error) {
    toast("Could not load workspace", error.message, "error");
    document.getElementById("incident-list").innerHTML = '<p class="audit-empty">The incident queue is unavailable.</p>';
  }
}

function bindStaticEvents() {
  document.getElementById("global-search").addEventListener("input", (event) => {
    state.search = event.target.value.toLowerCase().trim();
    renderQueue();
  });
  document.querySelectorAll(".stat").forEach((button) => button.addEventListener("click", () => {
    state.activeFilter = button.dataset.filter;
    document.querySelectorAll(".stat").forEach((item) => item.classList.toggle("selected", item === button));
    renderQueue();
  }));
  document.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => closeModal(button.dataset.close)));
  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => backdrop.addEventListener("mousedown", (event) => {
    if (event.target === backdrop) closeModal(backdrop.id);
  }));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") document.querySelectorAll(".modal-backdrop:not([hidden])").forEach((modal) => closeModal(modal.id));
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault(); document.getElementById("global-search").focus();
    }
  });
  document.getElementById("confirm-create-ticket").addEventListener("click", createTicket);
  document.getElementById("confirm-comment").addEventListener("click", addComment);
  document.getElementById("comment-text").addEventListener("input", (event) => {
    document.getElementById("comment-count").textContent = `${event.target.value.length.toLocaleString()} / 8,000`;
  });
}

function renderMode() {
  const chip = document.getElementById("mode-chip");
  const label = !state.config.enabled ? "SERVICENOW OFF" : state.config.mode === "mock" ? "MOCK MODE" : "SERVICENOW LIVE";
  chip.innerHTML = `<span class="status-dot"></span>${label}`;
}

function filteredIncidents() {
  return state.incidents.filter((incident) => {
    const filterMatch = state.activeFilter === "all"
      || incident.severity === state.activeFilter
      || (state.activeFilter === "ticketed" && incident.service_now_sys_id);
    const haystack = `${incident.id} ${incident.title} ${incident.identity_name} ${incident.identity_email}`.toLowerCase();
    return filterMatch && (!state.search || haystack.includes(state.search));
  });
}

function renderQueue() {
  document.getElementById("stat-all").textContent = state.incidents.filter((item) => !["Resolved", "Closed"].includes(item.status)).length;
  document.getElementById("stat-critical").textContent = state.incidents.filter((item) => item.severity === "Critical").length;
  document.getElementById("stat-ticketed").textContent = state.incidents.filter((item) => item.service_now_sys_id).length;
  const filtered = filteredIncidents();
  document.getElementById("queue-count").textContent = `${filtered.length} incident${filtered.length === 1 ? "" : "s"}`;
  document.getElementById("incident-list").innerHTML = filtered.length ? filtered.map((incident) => `
    <button class="incident-card ${incident.id === state.selectedId ? "selected" : ""}" data-incident-id="${escapeHtml(incident.id)}">
      <div class="incident-meta"><span class="incident-id">${escapeHtml(incident.id)}</span><span class="severity ${incident.severity.toLowerCase()}">${escapeHtml(incident.severity)}</span></div>
      <h3>${escapeHtml(incident.title)}</h3>
      <div class="incident-person">${icon("user")}<span>${escapeHtml(incident.identity_email)}</span></div>
      <div class="incident-footer">
        <span class="risk-mini"><strong>${incident.risk_score}</strong> risk</span>
        ${incident.service_now_incident_number ? `<span class="ticket-mini">${icon("ticket")}${escapeHtml(incident.service_now_incident_number)}</span>` : `<span class="time-ago">${timeAgo(incident.detected_at)}</span>`}
      </div>
    </button>`).join("") : '<p class="audit-empty">No incidents match this view.</p>';
  document.querySelectorAll(".incident-card").forEach((card) => card.addEventListener("click", () => selectIncident(card.dataset.incidentId)));
}

async function selectIncident(incidentId, showLoading = true) {
  state.selectedId = incidentId;
  renderQueue();
  if (showLoading) document.getElementById("incident-detail").innerHTML = '<div class="detail-loading"><div class="spinner"></div><p>Loading investigation…</p></div>';
  try {
    const [incident, auditPayload] = await Promise.all([
      api(`/api/incidents/${encodeURIComponent(incidentId)}`),
      api(`/api/incidents/${encodeURIComponent(incidentId)}/audit`),
    ]);
    state.audits = auditPayload.items;
    replaceIncident(incident);
    renderDetail(incident);
  } catch (error) {
    toast("Incident unavailable", error.message, "error");
  }
}

function replaceIncident(incident) {
  const index = state.incidents.findIndex((item) => item.id === incident.id);
  if (index >= 0) state.incidents[index] = incident;
  else state.incidents.push(incident);
}

function renderDetail(incident) {
  const isCritical = incident.severity === "Critical";
  const hasTicket = Boolean(incident.service_now_sys_id);
  const detail = document.getElementById("incident-detail");
  detail.innerHTML = `
    <header class="detail-header">
      <div class="breadcrumbs"><span>Incidents</span>${icon("arrow")}<span>${escapeHtml(incident.id)}</span></div>
      <div class="header-main">
        <div class="title-block">
          <div class="card-status-row"><span class="severity ${incident.severity.toLowerCase()}">${escapeHtml(incident.severity)}</span></div>
          <h2>${escapeHtml(incident.title)}</h2>
          <p>Detected ${formatDate(incident.detected_at)} · ${escapeHtml(incident.id)}</p>
        </div>
        <div class="header-actions">
          ${!hasTicket && !isCritical ? `<button class="button secondary" data-action="open-ticket">${icon("ticket")}Create ServiceNow incident</button>` : ""}
          <select class="status-select" id="incident-status" aria-label="Incident status">
            ${["Open", "Investigating", "Resolved", "Closed"].map((status) => `<option ${incident.status === status ? "selected" : ""}>${status}</option>`).join("")}
          </select>
          <button class="icon-button bordered" aria-label="More actions">•••</button>
        </div>
      </div>
    </header>
    ${isCritical ? `
      <div class="critical-strip">
        <div class="critical-icon">${icon("alert")}</div>
        <div class="critical-copy"><strong>CRITICAL SECURITY INCIDENT</strong><span>Privileged identity activity requires immediate analyst review and containment.</span></div>
        <div class="critical-risk"><b>${incident.risk_score}</b><span>Risk score</span></div>
        ${!hasTicket ? `<button class="button critical-button" data-action="open-ticket">${icon("ticket")}${incident.service_now_last_error ? "Retry ticket creation" : "Raise ServiceNow ticket"}</button>` : `<button class="button secondary" data-action="scroll-investigation">View investigation</button>`}
      </div>` : ""}
    <div class="detail-grid">
      <div class="detail-main">
        <section class="panel" id="investigation-panel">
          <header class="panel-header"><h3>${icon("sparkle")}AI investigation</h3><span>Grounded in ${incident.evidence.filter((item) => item.verified).length} verified signals</span></header>
          <div class="panel-body">
            <div class="ai-label">${icon("sparkle")}AI assessment</div>
            <div class="ai-assessment">${escapeHtml(incident.ai_summary)}</div>
            <div class="evidence-grid">
              ${incident.evidence.map((item) => `<div class="evidence"><span class="evidence-label">${escapeHtml(item.label)}</span><span class="evidence-value">${item.verified ? icon("check") : ""}${escapeHtml(item.value)}</span></div>`).join("")}
            </div>
          </div>
        </section>
        <section class="panel">
          <header class="panel-header"><h3>${icon("activity")}Correlated event timeline</h3><span>${incident.timeline.length} observed events</span></header>
          <div class="panel-body timeline">
            ${incident.timeline.map((item) => `<div class="timeline-item"><span class="timeline-time">${escapeHtml(item.time)}</span><span class="timeline-track"><i class="timeline-dot"></i></span><div class="timeline-copy"><strong>${escapeHtml(item.event)}</strong><span>${escapeHtml(item.source)}</span></div></div>`).join("")}
          </div>
        </section>
        <section class="panel recommendations">
          <div class="recommendation-column"><h4>${icon("clipboard")}Recommended investigation</h4><ol>${incident.investigation.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ol></div>
          <div class="recommendation-column"><h4>${icon("wrench")}Recommended remediation</h4><ol>${incident.remediation.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ol></div>
        </section>
      </div>
      <aside class="detail-side">
        <section class="panel risk-card">
          <header class="panel-header"><h3>${icon("pulse")}Risk analysis</h3><span>${escapeHtml(incident.severity)}</span></header>
          <div class="panel-body">
            <div class="risk-ring" style="--risk-angle:${incident.risk_score * 3.6}deg"><div><strong>${incident.risk_score}</strong><span>out of 100</span></div></div>
            <div class="risk-factors"><p><span>Identity privilege</span><b>${incident.privileged ? "Elevated" : "Standard"}</b></p><p><span>Behavior anomaly</span><b>${incident.risk_score > 85 ? "Extreme" : incident.risk_score > 70 ? "High" : "Moderate"}</b></p><p><span>Confidence</span><b>${incident.evidence.length > 2 ? "High" : "Medium"}</b></p></div>
          </div>
        </section>
        <section class="panel">
          <header class="panel-header"><h3>${icon("user")}Affected identity</h3></header>
          <div class="panel-body identity-grid">
            <div class="identity-item wide"><span>Identity</span><strong>${escapeHtml(incident.identity_name)} · ${escapeHtml(incident.identity_email)}</strong></div>
            <div class="identity-item"><span>Source IP</span><strong>${escapeHtml(incident.ip_address)}</strong></div>
            <div class="identity-item"><span>Country</span><strong>${escapeHtml(incident.country)}</strong></div>
            <div class="identity-item"><span>Device</span><strong>${escapeHtml(incident.device)}</strong></div>
            <div class="identity-item"><span>Application</span><strong>${escapeHtml(incident.application)}</strong></div>
            ${incident.privileged ? '<div class="identity-item wide"><span>Privilege</span><strong class="privileged-badge">Privileged identity</strong></div>' : ""}
          </div>
        </section>
        ${renderServiceNowCard(incident)}
        <section class="panel">
          <header class="panel-header"><h3>${icon("audit")}Audit trail</h3><span>${state.audits.length} actions</span></header>
          <div class="panel-body audit-list">${renderAudit()}</div>
        </section>
      </aside>
    </div>`;
  bindDetailEvents(incident);
}

function renderServiceNowCard(incident) {
  const enabled = state.config?.enabled;
  const hasTicket = Boolean(incident.service_now_sys_id);
  return `<section class="panel sn-card">
    <header class="panel-header"><h3 class="sn-brand"><span class="servicenow-logo"><span></span></span>ServiceNow</h3><span class="integration-state"><span class="status-dot"></span>${enabled ? (state.config.mode === "mock" ? "Mock connected" : "Connected") : "Disabled"}</span></header>
    ${hasTicket ? `<div class="sn-ticket">
      <div class="sn-ticket-number"><a href="${escapeHtml(incident.service_now_url)}" target="_blank" rel="noopener">${escapeHtml(incident.service_now_incident_number)}</a><span class="sn-status">${escapeHtml(incident.service_now_status || "New")}</span></div>
      <div class="sn-fields"><div class="sn-field"><span>Assignment group</span><strong>${escapeHtml(incident.service_now_assignment_group || "Unassigned")}</strong></div><div class="sn-field"><span>Created</span><strong>${formatDate(incident.service_now_created_at)}</strong></div></div>
      <div class="sn-actions"><a class="button secondary" href="${escapeHtml(incident.service_now_url)}" target="_blank" rel="noopener">${icon("external")}Open</a><button class="button primary" data-action="open-comment">${icon("message")}Add update</button></div>
      <div class="sync-note">${icon("refresh")}Last synced ${formatDate(incident.service_now_last_sync_at)}</div>
    </div>` : `<div class="sn-empty">
      ${incident.service_now_last_error ? `<div class="sn-error"><strong>ServiceNow ticket creation failed.</strong><br>${escapeHtml(incident.service_now_last_error)}</div>` : ""}
      <p>${enabled ? "No ServiceNow incident is linked. Analyst approval is required before ticket creation." : "ServiceNow integration is disabled by configuration."}</p>
      <button class="button ${incident.severity === "Critical" ? "critical-button" : "secondary"}" data-action="open-ticket" ${enabled ? "" : "disabled"}>${icon("ticket")}${incident.service_now_last_error ? "Retry ticket creation" : "Create ServiceNow incident"}</button>
    </div>`}
  </section>`;
}

function renderAudit() {
  if (!state.audits.length) return '<p class="audit-empty">No ServiceNow actions recorded yet.</p>';
  return state.audits.map((event) => `<div class="audit-item">
    <span class="audit-icon ${event.result === "failed" ? "failed" : ""}">${icon(event.result === "failed" ? "alert" : "check")}</span>
    <div class="audit-copy"><strong>${escapeHtml(event.action.replaceAll("_", " "))}</strong><p>${escapeHtml(event.detail || event.result)}</p><span>${escapeHtml(event.actor)} · ${formatDate(event.timestamp)}</span></div>
  </div>`).join("");
}

function bindDetailEvents(incident) {
  document.querySelectorAll('[data-action="open-ticket"]').forEach((button) => button.addEventListener("click", openTicketModal));
  document.querySelectorAll('[data-action="open-comment"]').forEach((button) => button.addEventListener("click", openCommentModal));
  document.querySelectorAll('[data-action="scroll-investigation"]').forEach((button) => button.addEventListener("click", () => document.getElementById("investigation-panel")?.scrollIntoView({ behavior: "smooth" })));
  document.getElementById("incident-status")?.addEventListener("change", (event) => updateIncidentStatus(incident.id, event.target.value));
}

async function openTicketModal() {
  if (!state.selectedId) return;
  const modal = document.getElementById("ticket-modal");
  const confirm = document.getElementById("confirm-create-ticket");
  confirm.disabled = true;
  modal.hidden = false;
  document.body.style.overflow = "hidden";
  try {
    const preview = await api(`/api/incidents/${encodeURIComponent(state.selectedId)}/servicenow/preview`);
    document.getElementById("ticket-short-description").value = preview.short_description;
    document.getElementById("ticket-description").value = preview.description;
    document.getElementById("ticket-category").value = `${preview.category} · ${preview.subcategory}`;
    const groups = state.config.assignment_groups || [preview.assignment_group];
    document.getElementById("ticket-assignment-group").innerHTML = groups.map((group) => `<option ${group === preview.assignment_group ? "selected" : ""}>${escapeHtml(group)}</option>`).join("");
    confirm.disabled = false;
  } catch (error) {
    closeModal("ticket-modal"); toast("Could not prepare ticket", error.message, "error");
  }
}

async function createTicket() {
  const button = document.getElementById("confirm-create-ticket");
  button.disabled = true;
  button.innerHTML = '<span class="spinner" style="width:14px;height:14px"></span>Creating…';
  try {
    const result = await api(`/api/incidents/${encodeURIComponent(state.selectedId)}/servicenow`, {
      method: "POST",
      body: JSON.stringify({
        assignment_group: document.getElementById("ticket-assignment-group").value,
        short_description: document.getElementById("ticket-short-description").value,
        description: document.getElementById("ticket-description").value,
      }),
    });
    closeModal("ticket-modal");
    toast(result.duplicate_prevented ? "Existing ticket returned" : "ServiceNow incident created", `${result.service_now.number} is assigned to ${result.service_now.assignment_group}.`);
    await refreshSelected();
  } catch (error) {
    toast("Ticket creation failed", `${error.message} You can retry safely.`, "error");
    closeModal("ticket-modal");
    await refreshSelected();
  } finally {
    button.disabled = false;
    button.innerHTML = `${icon("ticket")}Create incident`;
  }
}

function openCommentModal() {
  document.getElementById("comment-text").value = "";
  document.getElementById("comment-count").textContent = "0 / 8,000";
  document.getElementById("comment-modal").hidden = false;
  document.body.style.overflow = "hidden";
  setTimeout(() => document.getElementById("comment-text").focus(), 30);
}

async function addComment() {
  const comment = document.getElementById("comment-text").value.trim();
  if (!comment) { toast("Add a note", "Enter an investigation update before sending.", "error"); return; }
  const button = document.getElementById("confirm-comment");
  button.disabled = true;
  try {
    const result = await api(`/api/incidents/${encodeURIComponent(state.selectedId)}/servicenow/comment`, { method: "POST", body: JSON.stringify({ comment }) });
    closeModal("comment-modal");
    toast("Investigation update sent", `Work note added to ${result.service_now.number}.`);
    await refreshSelected();
  } catch (error) {
    toast("Update failed", error.message, "error");
  } finally { button.disabled = false; }
}

async function updateIncidentStatus(incidentId, status) {
  try {
    await api(`/api/incidents/${encodeURIComponent(incidentId)}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
    toast("Status updated", `EntraGuard is now ${status}${state.incidents.find((item) => item.id === incidentId)?.service_now_sys_id ? " and ServiceNow was synchronized" : ""}.`);
    await refreshSelected();
  } catch (error) {
    toast("Status update failed", error.message, "error");
    await refreshSelected();
  }
}

async function refreshSelected() {
  const [incident, auditPayload] = await Promise.all([
    api(`/api/incidents/${encodeURIComponent(state.selectedId)}`),
    api(`/api/incidents/${encodeURIComponent(state.selectedId)}/audit`),
  ]);
  state.audits = auditPayload.items;
  replaceIncident(incident);
  renderQueue();
  renderDetail(incident);
}

function closeModal(id) {
  document.getElementById(id).hidden = true;
  if (!document.querySelector(".modal-backdrop:not([hidden])")) document.body.style.overflow = "";
}

function toast(title, message, type = "success") {
  const node = document.createElement("div");
  node.className = `toast ${type}`;
  node.innerHTML = `${icon(type === "error" ? "alert" : "check")}<div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(message)}</p></div><button aria-label="Dismiss">${icon("x")}</button>`;
  node.querySelector("button").addEventListener("click", () => node.remove());
  document.getElementById("toast-region").appendChild(node);
  setTimeout(() => node.remove(), 5200);
}

boot();

