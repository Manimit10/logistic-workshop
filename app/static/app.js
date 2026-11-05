/* Supply Chain Game: plain JS single-page app (no build step).
   Layout: i18n -> helpers -> views (join, player panels, admin) -> polling loop. */
"use strict";

// ----------------------------------------------------------------- i18n
const I18N = {
  en: {
    title: "Supply Chain Game", join_h: "Join the game", name: "Your name", pin: "Class PIN",
    team: "Team name", roles_h: "Your role(s) in the team", join_btn: "Join", staff: "Instructor login",
    password: "Password", login: "Log in", back: "Back",
    planner: "Demand Planner", logistics: "Logistics Manager", finance: "Finance & Customs",
    planner_d: "Reads the forecasts and proposes quantities", logistics_d: "Chooses how each order travels",
    finance_d: "Controls budget and customs cost, approves the order",
    roles_hint: "Teams of 3: one role each. In a team of 2, take two roles.",
    tee: "Basic tee", dress: "Trend dress", coat: "Winter coat", viral: "Viral item",
    sea: "Sea freight", nearshore: "Near-shore", air: "Air parcel",
    round_of: "Round {r} of {n}", lobby: "Waiting for the instructor to start round 1…",
    open: "Decisions are open", closed: "Round {r} closed. Check the results. Waiting for the next round…",
    finished: "Game over. Thank you for playing!",
    ev_port_delay: "⚠ Port congestion: sea shipments still in transit are delayed by one round. Air parcels are not affected.",
    step1: "1 · Quantities", step2: "2 · Shipping", step3: "3 · Approval",
    step1_d: "Planner", step2_d: "Logistics", step3_d: "Finance", waiting: "waiting…", done: "done",
    covering: "Nobody in your team has the role {r}, so you cover it.",
    inv: "In stock", pipe: "On the way", qty: "Order qty", mode: "Mode", save: "Save", saved: "Saved",
    hist: "Sales history (units / round)", fc_h: "Forecast of demand (units)", fc_next: "next", fc_plus: "+{k}",
    fc_hint: "Orders arrive some rounds after you place them, so size each order with the forecast for the round it arrives. Bigger quantile = safer but riskier to overstock.",
    lead_hint: "Arrival if you order now: sea → round {a}, near-shore → round {b}, air → round {c}. The season ends after round {n}.",
    lead: "Lead", freight: "Freight/unit", duty: "Duty/unit", rounds: "rounds",
    arrives: "arrives in round {a}", late: "after the season ends: only 50% salvage value!",
    pipeline_h: "Shipments on the way", sku: "Item", arrival: "Arrival (round)", none: "none",
    modes_h: "Shipping modes", proposed: "Proposed qty",
    cash: "Cash", net: "Net worth", price: "Price", cost: "Unit cost", landed: "Landed cost", cr: "Service level target",
    cr_hint: "Stock enough that demand is covered with probability ≈ this target (newsvendor: lost margin ÷ (lost margin + overstock cost)). Tell the Planner which forecast quantile to use.",
    order_h: "Order to approve", total: "Total", approve: "Approve order", revoke: "Revoke approval",
    approved: "Approved ✓", not_approved: "Not approved yet", over: "Not enough cash for this order",
    pnl_h: "Profit & loss", revenue: "Revenue", holding: "Holding", penalty: "Lost-sale penalty", ordered: "Ordered",
    results_h: "Results", demand: "Demand", sold: "Sold", lost: "Lost", end_stock: "End stock",
    round: "Round", board_h: "Ranking", teams_h: "Teams", team_h: "Team", status: "Status", members: "Members",
    // admin
    start_round: "Start round {r}", close_round: "Close round", reset: "Reset game", reset_sure: "Click again to confirm reset",
    present: "Presenter view", exit_present: "Exit presenter view", players: "players", teams: "teams",
    share_board: "Students can see the ranking", auto_close: "Close rounds automatically when the timer ends",
    secs: "Seconds per round", apply: "Apply", no_order: "no order", ordered_not: "ordered, not approved",
    reveal_h: "What really happened (demand per round)", settings_h: "Settings",
    join_url: "Join at", pin_is: "PIN", ai_note: "AI baseline = forecast-driven bot (quantile + newsvendor rule).",
    // errors
    e_bad_pin: "Wrong class PIN.", e_role_taken: "That role is already taken in this team: {roles}.",
    e_game_started: "The game already started. Join an existing team.", e_forbidden: "Your role cannot do that.",
    e_round_not_open: "The round is not open.", e_over_budget: "Order costs {cost} but you only have {cash}.",
    e_modes_missing: "Logistics must choose a mode for every item with quantity.", e_empty_order: "The order is empty.",
    e_bad_password: "Wrong password.", e_missing_fields: "Please fill in every field.",
    e_reserved_name: "That team name is reserved.", e_unauthorized: "Session expired. Please join again.",
    e_bad_order: "Invalid order values.", e_net: "Connection problem. Retrying…",
    e_round_already_open: "A round is already open.", e_game_finished: "The game is finished.",
  },
  es: {
    title: "Juego de Cadena de Suministro", join_h: "Unirse al juego", name: "Tu nombre", pin: "PIN de clase",
    team: "Nombre del equipo", roles_h: "Tu rol (o roles) en el equipo", join_btn: "Entrar", staff: "Acceso profesor",
    password: "Contraseña", login: "Entrar", back: "Volver",
    planner: "Planificador de demanda", logistics: "Responsable de logística", finance: "Finanzas y aduanas",
    planner_d: "Lee las previsiones y propone cantidades", logistics_d: "Elige cómo viaja cada pedido",
    finance_d: "Controla presupuesto y costes de aduana, aprueba el pedido",
    roles_hint: "Equipos de 3: un rol cada uno. En un equipo de 2, elegid dos roles.",
    tee: "Camiseta básica", dress: "Vestido de tendencia", coat: "Abrigo de invierno", viral: "Artículo viral",
    sea: "Barco", nearshore: "Proximidad (near-shore)", air: "Paquete aéreo",
    round_of: "Ronda {r} de {n}", lobby: "Esperando a que el profesor inicie la ronda 1…",
    open: "Decisiones abiertas", closed: "Ronda {r} cerrada. Revisa los resultados. Esperando la siguiente ronda…",
    finished: "Fin del juego. ¡Gracias por participar!",
    ev_port_delay: "⚠ Congestión portuaria: los envíos marítimos en tránsito se retrasan una ronda. Los paquetes aéreos no se ven afectados.",
    step1: "1 · Cantidades", step2: "2 · Transporte", step3: "3 · Aprobación",
    step1_d: "Planificador", step2_d: "Logística", step3_d: "Finanzas", waiting: "esperando…", done: "hecho",
    covering: "Nadie en tu equipo tiene el rol {r}, así que lo cubres tú.",
    inv: "En stock", pipe: "En camino", qty: "Cantidad", mode: "Modo", save: "Guardar", saved: "Guardado",
    hist: "Historial de ventas (uds / ronda)", fc_h: "Previsión de demanda (uds)", fc_next: "próx.", fc_plus: "+{k}",
    fc_hint: "Los pedidos llegan varias rondas después de hacerlos: dimensiona cada pedido con la previsión de la ronda en que llega. Cuantil más alto = más seguro, pero más riesgo de sobrestock.",
    lead_hint: "Llegada si pides ahora: barco → ronda {a}, near-shore → ronda {b}, aéreo → ronda {c}. La temporada termina tras la ronda {n}.",
    lead: "Plazo", freight: "Flete/ud", duty: "Arancel/ud", rounds: "rondas",
    arrives: "llega en la ronda {a}", late: "después de acabar la temporada: ¡solo 50% de valor residual!",
    pipeline_h: "Envíos en camino", sku: "Artículo", arrival: "Llegada (ronda)", none: "ninguno",
    modes_h: "Modos de transporte", proposed: "Cantidad propuesta",
    cash: "Caja", net: "Patrimonio neto", price: "Precio", cost: "Coste unit.", landed: "Coste puesto en destino", cr: "Nivel de servicio objetivo",
    cr_hint: "Ten stock suficiente para cubrir la demanda con probabilidad ≈ este objetivo (newsvendor: margen perdido ÷ (margen perdido + coste de sobrestock)). Dile al Planificador qué cuantil de previsión usar.",
    order_h: "Pedido a aprobar", total: "Total", approve: "Aprobar pedido", revoke: "Retirar aprobación",
    approved: "Aprobado ✓", not_approved: "Sin aprobar", over: "No hay caja suficiente para este pedido",
    pnl_h: "Pérdidas y ganancias", revenue: "Ingresos", holding: "Almacenaje", penalty: "Penalización venta perdida", ordered: "Pedido",
    results_h: "Resultados", demand: "Demanda", sold: "Vendido", lost: "Perdido", end_stock: "Stock final",
    round: "Ronda", board_h: "Clasificación", teams_h: "Equipos", team_h: "Equipo", status: "Estado", members: "Miembros",
    start_round: "Iniciar ronda {r}", close_round: "Cerrar ronda", reset: "Reiniciar juego", reset_sure: "Pulsa de nuevo para confirmar",
    present: "Vista de proyección", exit_present: "Salir de proyección", players: "jugadores", teams: "equipos",
    share_board: "Los alumnos ven la clasificación", auto_close: "Cerrar rondas automáticamente al acabar el tiempo",
    secs: "Segundos por ronda", apply: "Aplicar", no_order: "sin pedido", ordered_not: "pedido sin aprobar",
    reveal_h: "Lo que pasó realmente (demanda por ronda)", settings_h: "Ajustes",
    join_url: "Entrad en", pin_is: "PIN", ai_note: "IA de referencia = bot guiado por previsión (cuantil + regla newsvendor).",
    e_bad_pin: "PIN de clase incorrecto.", e_role_taken: "Ese rol ya está ocupado en este equipo: {roles}.",
    e_game_started: "El juego ya empezó. Únete a un equipo existente.", e_forbidden: "Tu rol no puede hacer eso.",
    e_round_not_open: "La ronda no está abierta.", e_over_budget: "El pedido cuesta {cost} pero solo tienes {cash}.",
    e_modes_missing: "Logística debe elegir un modo para cada artículo con cantidad.", e_empty_order: "El pedido está vacío.",
    e_bad_password: "Contraseña incorrecta.", e_missing_fields: "Rellena todos los campos.",
    e_reserved_name: "Ese nombre de equipo está reservado.", e_unauthorized: "Sesión caducada. Vuelve a entrar.",
    e_bad_order: "Valores de pedido no válidos.", e_net: "Problema de conexión. Reintentando…",
    e_round_already_open: "Ya hay una ronda abierta.", e_game_finished: "El juego ha terminado.",
  },
};

// ----------------------------------------------------------------- state & helpers
const $ = (s, el = document) => el.querySelector(s);
const app = $("#app");
const S = { lang: "en", token: null, st: null, draft: {}, msg: null, presenter: false, staff: false,
            resetArmed: false, offset: 0, sig: "", busy: false };

const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (e) { /* private mode */ } },
};
S.lang = store.get("eum_lang") || ((navigator.language || "en").startsWith("es") ? "es" : "en");
S.token = store.get("eum_token");

const t = (k, v = {}) => (I18N[S.lang][k] ?? I18N.en[k] ?? k).replace(/\{(\w+)\}/g, (_, n) => v[n] ?? "");
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const eur = (n) => new Intl.NumberFormat(S.lang === "es" ? "es-ES" : "en-GB", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
const num = (n) => new Intl.NumberFormat(S.lang === "es" ? "es-ES" : "en-GB").format(n);
const SKUS = ["tee", "dress", "coat", "viral"];
const LEAD = { sea: 3, nearshore: 2, air: 1 };

function errText(e) {
  if (!e || !e.error) return t("e_net");
  const m = { roles: (e.roles || []).map((r) => t(r)).join(", "), cost: e.cost != null ? eur(e.cost) : "", cash: e.cash != null ? eur(e.cash) : "" };
  return t("e_" + e.error, m);
}

async function api(path, method = "GET", body) {
  const res = await fetch(path, {
    method, headers: { "Content-Type": "application/json", ...(S.token ? { Authorization: "Bearer " + S.token } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw data;
  return data;
}

function spark(values, w = 150, h = 36) {
  const v = values.slice(-14), max = Math.max(...v, 1), min = Math.min(...v, 0);
  const pts = v.map((y, i) => [(i / Math.max(v.length - 1, 1)) * (w - 6) + 3, h - 3 - ((y - min) / (max - min || 1)) * (h - 6)]);
  const last = pts[pts.length - 1] || [0, 0];
  return `<svg class="spark" width="${w}" height="${h}" role="img" aria-label="trend"><polyline fill="none" stroke="var(--accent)" stroke-width="2" points="${pts.map((p) => p.join(",")).join(" ")}"/><circle cx="${last[0]}" cy="${last[1]}" r="3.5" fill="var(--accent-2)"/></svg>`;
}

function say(msg, kind = "err") { S.msg = msg ? { text: msg, kind } : null; const b = $("#msg"); if (b) b.outerHTML = msgHtml(); }
const msgHtml = () => `<div id="msg">${S.msg ? `<div class="banner ${S.msg.kind}" role="alert">${esc(S.msg.text)}</div>` : ""}</div>`;

async function act(path, body, okMsg) {
  if (S.busy) return;
  S.busy = true;
  try { await api(path, "POST", body || {}); say(okMsg || null, "ok"); await refresh(true); }
  catch (e) { say(errText(e)); if (e && e.error === "unauthorized") logout(); }
  finally { S.busy = false; }
}

function logout() { S.token = null; store.set("eum_token", null); S.st = null; S.sig = ""; render(); }

// ----------------------------------------------------------------- join views
function joinView() {
  const roles = ["planner", "logistics", "finance"].map((r) =>
    `<label class="check"><input type="checkbox" name="role" value="${r}" ${(S.draft["role-" + r] ?? false) ? "checked" : ""}>
     <span><b>${t(r)}</b><br><span class="muted">${t(r + "_d")}</span></span></label>`).join("");
  return `<div class="card" style="max-width:520px;margin:0 auto">
    <h2>${t("join_h")}</h2>${msgHtml()}
    <label for="j-name">${t("name")}</label><input type="text" id="j-name" maxlength="30" autocomplete="name" value="${esc(S.draft["j-name"] || "")}">
    <label for="j-pin">${t("pin")}</label><input type="text" id="j-pin" autocapitalize="characters" autocomplete="off" value="${esc(S.draft["j-pin"] || "")}">
    <label for="j-team">${t("team")}</label><input type="text" id="j-team" maxlength="24" value="${esc(S.draft["j-team"] || "")}">
    <label>${t("roles_h")}</label>${roles}<div class="hint">${t("roles_hint")}</div>
    <div class="row spread" style="margin-top:16px"><button id="join-btn" class="big">${t("join_btn")}</button>
    <button id="staff-btn" class="secondary">${t("staff")}</button></div></div>`;
}

function staffView() {
  return `<div class="card" style="max-width:420px;margin:0 auto"><h2>${t("staff")}</h2>${msgHtml()}
    <label for="a-pw">${t("password")}</label><input type="password" id="a-pw" autocomplete="current-password">
    <div class="row spread" style="margin-top:16px"><button id="login-btn" class="big">${t("login")}</button>
    <button id="back-btn" class="secondary">${t("back")}</button></div></div>`;
}

// ----------------------------------------------------------------- player views
function statusBanner(st) {
  const g = st.game;
  let txt = g.phase === "lobby" ? t("lobby") : g.phase === "open" ? `${t("round_of", { r: g.round, n: g.n_rounds })} · ${t("open")}`
    : g.phase === "closed" ? t("closed", { r: g.round }) : t("finished");
  const ev = (g.events || []).map((e) => `<div class="banner warn">${t("ev_" + e.key)}</div>`).join("");
  return `<div class="banner"><b>${esc(st.team.name)}</b> · ${esc(st.me.name)} ${st.me.roles.map((r) => `<span class="badge role">${t(r)}</span>`).join(" ")}
    <div>${txt}</div>${st.me.covering.length ? `<div class="hint">${st.me.covering.map((r) => t("covering", { r: t(r) })).join(" ")}</div>` : ""}</div>${ev}`;
}

function stepsView(st) {
  const o = st.order_status;
  const s = (ok, a, b) => `<div class="step ${ok ? "done" : ""}"><b>${t(a)}</b><span class="muted">${t(b)} · ${ok ? "✓ " + t("done") : t("waiting")}</span></div>`;
  return `<div class="steps">${s(o.has_qty, "step1", "step1_d")}${s(o.has_modes, "step2", "step2_d")}${s(o.approved, "step3", "step3_d")}</div>`;
}

function pipelineTable(st, withMode) {
  if (!st.pipeline.length) return `<p class="muted">${t("none")}</p>`;
  return `<div class="scroll"><table><tr><th>${t("sku")}</th><th>${t("qty")}</th>${withMode ? `<th>${t("mode")}</th>` : ""}<th>${t("arrival")}</th></tr>
    ${st.pipeline.map((p) => `<tr><td>${t(p.sku)}</td><td>${num(p.qty)}</td>${withMode ? `<td>${t(p.mode)}</td>` : ""}<td>${p.arrival}</td></tr>`).join("")}</table></div>`;
}

function plannerPanel(st) {
  const P = st.planner, open = st.game.phase === "open", rnd = st.game.round;
  const cards = SKUS.map((s) => {
    const fc = P.forecast && P.forecast[s];
    const fcT = fc ? `<div class="scroll"><table><tr><th>${t("fc_h")}</th>${[1, 2, 3, 4].map((h) => `<th>${h === 1 ? t("fc_next") : t("fc_plus", { k: h - 1 })}</th>`).join("")}</tr>
      ${["p50", "p80", "p95"].map((q) => `<tr><td>${q.toUpperCase()}</td>${[1, 2, 3, 4].map((h) => `<td>${num(fc[h][q])}</td>`).join("")}</tr>`).join("")}</table></div>` : "";
    const id = "q-" + s, val = S.draft[id] ?? (P.proposal[s] ?? 0);
    return `<div class="card"><div class="row spread"><b>${t(s)}</b><span class="muted">${t("inv")}: <b>${num(st.inventory[s])}</b> · ${t("pipe")}: <b>${num(st.pipeline.filter((p) => p.sku === s).reduce((a, p) => a + p.qty, 0))}</b></span></div>
      <div class="row"><div>${spark(P.history[s])}<div class="hint">${t("hist")}: ${P.history[s].slice(-5).join(" · ")}</div></div></div>${fcT}
      <label for="${id}">${t("qty")}</label><input type="number" min="0" max="5000" step="1" id="${id}" data-draft value="${val}" ${open ? "" : "disabled"}></div>`;
  }).join("");
  const hint = open ? `<div class="banner">${t("lead_hint", { a: rnd + 3, b: rnd + 2, c: rnd + 1, n: st.game.n_rounds })}<div class="hint">${t("fc_hint")}</div></div>` : "";
  return `<section><h2>${t("planner")}</h2>${hint}<div class="grid">${cards}</div>
    <button id="save-qty" ${open ? "" : "disabled"}>${t("save")}</button></section>`;
}

function logisticsPanel(st) {
  const L = st.logistics, open = st.game.phase === "open", rnd = st.game.round;
  const modes = Object.entries(L.modes).map(([m, v]) => `<tr><td>${t(m)}</td><td>${v.lead} ${t("rounds")}</td><td>${eur(v.freight)}</td><td>${eur(v.duty)}</td></tr>`).join("");
  const rows = SKUS.map((s) => {
    const id = "m-" + s, cur = S.draft[id] ?? L.chosen[s] ?? "", q = L.proposal[s] || 0;
    const arr = cur ? rnd + LEAD[cur] : null, late = arr && arr > st.game.n_rounds;
    return `<tr><td>${t(s)}</td><td>${num(q)}</td><td><select id="${id}" data-draft ${open ? "" : "disabled"}><option value="">–</option>
      ${Object.keys(L.modes).map((m) => `<option value="${m}" ${cur === m ? "selected" : ""}>${t(m)}</option>`).join("")}</select></td>
      <td class="${late ? "bad" : ""}">${arr ? t("arrives", { a: arr }) + (late ? " ⚠" : "") : ""}</td></tr>${late ? `<tr><td colspan="4" class="bad hint">${t("late")}</td></tr>` : ""}`;
  }).join("");
  return `<section><h2>${t("logistics")}</h2><div class="grid">
    <div class="card"><h3>${t("modes_h")}</h3><div class="scroll"><table><tr><th>${t("mode")}</th><th>${t("lead")}</th><th>${t("freight")}</th><th>${t("duty")}</th></tr>${modes}</table></div>
      <h3>${t("pipeline_h")}</h3>${pipelineTable(st, true)}</div>
    <div class="card"><h3>${t("order_h")}</h3><div class="scroll"><table><tr><th>${t("sku")}</th><th>${t("proposed")}</th><th>${t("mode")}</th><th></th></tr>${rows}</table></div>
    <button id="save-modes" style="margin-top:10px" ${open ? "" : "disabled"}>${t("save")}</button></div></div></section>`;
}

function financePanel(st) {
  const F = st.finance, o = F.order, open = st.game.phase === "open", g = st.game;
  const qtyRows = SKUS.filter((s) => (o.qty[s] || 0) > 0).map((s) => {
    const m = o.modes[s], unit = m ? F.landed[s][m] : null;
    return `<tr><td>${t(s)}</td><td>${num(o.qty[s])}</td><td>${m ? t(m) : "–"}</td><td>${unit != null ? eur(unit) : "–"}</td><td>${unit != null ? eur(unit * o.qty[s]) : "–"}</td></tr>`;
  }).join("");
  const total = SKUS.reduce((a, s) => a + ((o.qty[s] || 0) > 0 && o.modes[s] ? o.qty[s] * F.landed[s][o.modes[s]] : 0), 0);
  const econ = SKUS.map((s) => `<tr><td>${t(s)}</td><td>${eur(F.prices[s])}</td><td>${eur(F.unit_costs[s])}</td>
    ${["sea", "nearshore", "air"].map((m) => `<td>${eur(F.landed[s][m])}<br><span class="muted">${Math.round(F.critical_ratio[s][m] * 100)}%</span></td>`).join("")}</tr>`).join("");
  const pnl = F.pnl.length ? `<div class="scroll"><table><tr><th>${t("round")}</th><th>${t("revenue")}</th><th>${t("holding")}</th><th>${t("penalty")}</th><th>${t("ordered")}</th><th>${t("cash")}</th></tr>
    ${F.pnl.map((r) => `<tr><td>${r.round}</td><td>${eur(r.revenue)}</td><td>${eur(-r.holding)}</td><td>${eur(-r.penalty)}</td><td>${eur(-r.ordered_cost)}</td><td>${eur(r.cash)}</td></tr>`).join("")}</table></div>` : "";
  const over = total > F.cash;
  return `<section><h2>${t("finance")}</h2><div class="grid">
    <div class="card"><div class="row spread"><div><div class="muted">${t("cash")}</div><div class="kpi">${eur(F.cash)}</div></div>
      <div><div class="muted">${t("net")}</div><div class="kpi">${eur(F.net_worth)}</div></div></div>
      <h3>${t("price")} / ${t("cost")} / ${t("landed")}</h3><div class="scroll"><table><tr><th>${t("sku")}</th><th>${t("price")}</th><th>${t("cost")}</th><th>${t("sea")}</th><th>${t("nearshore")}</th><th>${t("air")}</th></tr>${econ}</table></div>
      <div class="hint"><b>${t("cr")}</b> (%) · ${t("cr_hint")}</div></div>
    <div class="card"><h3>${t("order_h")}</h3>
      ${qtyRows ? `<div class="scroll"><table><tr><th>${t("sku")}</th><th>${t("qty")}</th><th>${t("mode")}</th><th>€/u</th><th>${t("total")}</th></tr>${qtyRows}
      <tr><td colspan="4"><b>${t("total")}</b></td><td><b class="${over ? "bad" : ""}">${eur(total)}</b></td></tr></table></div>` : `<p class="muted">${t("none")}</p>`}
      ${over ? `<p class="bad">${t("over")}</p>` : ""}
      <p>${o.approved ? `<span class="badge ok">${t("approved")}</span>` : `<span class="badge">${t("not_approved")}</span>`}</p>
      <div class="row"><button id="approve" ${open && !o.approved ? "" : "disabled"}>${t("approve")}</button>
      <button id="revoke" class="secondary" ${open && o.approved ? "" : "disabled"}>${t("revoke")}</button></div></div></div>
    ${pnl ? `<div class="card"><h3>${t("pnl_h")}</h3>${pnl}</div>` : ""}</section>`;
}

function resultsPanel(st) {
  if (!st.results.length) return "";
  const last = st.results[st.results.length - 1];
  return `<div class="card"><h2>${t("results_h")} · ${t("round")} ${last.round}</h2><div class="scroll"><table>
    <tr><th>${t("sku")}</th><th>${t("demand")}</th><th>${t("sold")}</th><th>${t("lost")}</th><th>${t("end_stock")}</th></tr>
    ${SKUS.map((s) => { const r = last.rows[s]; return `<tr><td>${t(s)}</td><td>${num(r.demand)}</td><td>${num(r.sold)}</td><td class="${r.lost ? "bad" : ""}">${num(r.lost)}</td><td>${num(r.end_stock)}</td></tr>`; }).join("")}</table></div></div>`;
}

function boardPanel(st) {
  if (!st.board) return "";
  return `<div class="card"><h2>${t("board_h")}</h2>${st.board.map((r) => `<div class="lb"><span>${esc(r.team)}</span><div class="bar" style="width:${barW(r.net_worth, st.board)}%"></div><b>${eur(r.net_worth)}</b></div>`).join("")}</div>`;
}

function playerView(st) {
  const eff = st.me.effective;
  const infoTop = `<div class="card row spread"><span>${t("inv")}: ${SKUS.map((s) => `${t(s)} <b>${num(st.inventory[s])}</b>`).join(" · ")}</span></div>`;
  const noLogi = !eff.includes("logistics") ? `<div class="card"><h3>${t("pipeline_h")}</h3>${pipelineTable(st, false)}</div>` : "";
  return `${statusBanner(st)}${msgHtml()}${st.game.round ? stepsView(st) : ""}${infoTop}
    ${eff.includes("planner") ? plannerPanel(st) : ""}${eff.includes("logistics") ? logisticsPanel(st) : noLogi}
    ${eff.includes("finance") ? financePanel(st) : ""}${resultsPanel(st)}${boardPanel(st)}`;
}

// ----------------------------------------------------------------- admin view
// Bars are scaled to the visible range so small gaps between teams stay readable.
const barW = (v, rows) => { const a = rows.map((r) => r.net_worth), hi = Math.max(...a), lo = Math.min(...a); return hi === lo ? 100 : 18 + 82 * (v - lo) / (hi - lo); };

function leaderboard(A) {
  return A.board.map((r) => `<div class="lb"><span>${r.bot ? "🤖 " : ""}${esc(r.team)}</span><div class="bar ${r.bot ? "bot" : ""}" style="width:${barW(r.net_worth, A.board)}%"></div><b>${eur(r.net_worth)}</b></div>`).join("");
}

function adminView(st) {
  const A = st.admin, g = st.game, open = g.phase === "open", nextR = g.round + 1;
  const canStart = !open && g.round < g.n_rounds;
  if (S.presenter) {
    const ev = (g.events || []).map((e) => `<div class="banner warn">${t("ev_" + e.key)}</div>`).join("");
    return `<div class="presenter"><div class="row spread"><h2>${g.phase === "lobby" ? t("lobby") : t("round_of", { r: g.round, n: g.n_rounds })}</h2>
      <button id="present" class="secondary">${t("exit_present")}</button></div>${ev}
      <div class="card">${leaderboard(A)}</div><p class="muted">${t("ai_note")}</p></div>`;
  }
  const teams = A.teams.map((x) => `<tr><td>${x.bot ? "🤖 " : ""}${esc(x.team)}</td>
    <td style="text-align:left">${x.members.map((m) => esc(m.name) + " <span class='muted'>(" + m.roles.map((r) => r[0].toUpperCase()).join("") + ")</span>").join(", ") || "–"}</td>
    <td>${g.round === 0 ? "" : x.approved ? `<span class="badge ok">✓</span>` : x.ordered ? `<span class="badge">${t("ordered_not")}</span>` : `<span class="badge bad">${t("no_order")}</span>`}</td>
    <td>${eur(x.net_worth)}</td></tr>`).join("");
  const reveal = A.demand.tee.length ? `<div class="card"><h3>${t("reveal_h")}</h3><div class="scroll"><table><tr><th>${t("sku")}</th>${A.demand.tee.map((_, i) => `<th>R${i + 1}</th>`).join("")}</tr>
    ${SKUS.map((s) => `<tr><td>${t(s)}</td>${A.demand[s].map((v) => `<td>${num(v)}</td>`).join("")}</tr>`).join("")}</table></div></div>` : "";
  return `${msgHtml()}<div class="card"><div class="row spread"><div><b>${t("round_of", { r: g.round, n: g.n_rounds })}</b> · ${esc(g.phase)}
      <div class="muted">${A.n_players} ${t("players")} · ${A.teams.filter((x) => !x.bot).length} ${t("teams")} · ${t("join_url")} <b>${esc(location.host)}</b></div></div>
    <div class="row"><button id="start" class="big" ${canStart ? "" : "disabled"}>${t("start_round", { r: nextR })}</button>
    <button id="close" class="big secondary" ${open ? "" : "disabled"}>${t("close_round")}</button>
    <button id="present" class="secondary">${t("present")}</button></div></div>
    <div class="hint">${(g.events || []).map((e) => t("ev_" + e.key)).join(" ")}</div></div>
    <div class="grid"><div class="card"><h2>${t("board_h")}</h2>${leaderboard(A)}<p class="hint">${t("ai_note")}</p></div>
    <div class="card"><h2>${t("teams_h")}</h2><div class="scroll"><table><tr><th>${t("team_h")}</th><th style="text-align:left">${t("members")}</th><th>${t("status")}</th><th>${t("net")}</th></tr>${teams}</table></div></div></div>
    ${reveal}
    <div class="card"><h2>${t("settings_h")}</h2>
      <label class="check"><input type="checkbox" id="s-public" ${A.settings.public_board ? "checked" : ""}> ${t("share_board")}</label>
      <label class="check"><input type="checkbox" id="s-auto" ${A.settings.auto_close ? "checked" : ""}> ${t("auto_close")}</label>
      <div class="row"><label for="s-secs" style="margin:0">${t("secs")}</label><input type="number" id="s-secs" min="0" max="900" step="10" value="${A.settings.round_seconds}">
      <button id="s-apply" class="secondary">${t("apply")}</button></div>
      <hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
      <button id="reset" class="danger">${S.resetArmed ? t("reset_sure") : t("reset")}</button></div>`;
}

// ----------------------------------------------------------------- render & events
function render() {
  $("#title").textContent = t("title"); document.title = t("title") + " · EUM"; $("#lang").textContent = S.lang === "en" ? "ES" : "EN";
  document.documentElement.lang = S.lang;
  if (!S.token) app.innerHTML = S.staff ? staffView() : joinView();
  else if (!S.st) app.innerHTML = `<p class="muted">…</p>`;
  else app.innerHTML = S.st.role === "admin" ? adminView(S.st) : playerView(S.st);
  tick();
}

let timerEl = $("#countdown");
function tick() {
  const g = S.st && S.st.game;
  if (g && g.deadline && g.phase === "open") {
    const left = Math.max(0, Math.round(g.deadline - (Date.now() / 1000 + S.offset)));
    timerEl.hidden = false; timerEl.textContent = `⏱ ${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")}`;
  } else timerEl.hidden = true;
}
setInterval(tick, 1000);

async function refresh(force) {
  if (!S.token) return;
  try {
    const st = await api("/api/state");
    S.offset = st.now - Date.now() / 1000;
    const sig = JSON.stringify({ ...st, now: 0 }) + S.lang + S.presenter + S.resetArmed;
    S.st = st;
    if (force || sig !== S.sig) { S.sig = sig; render(); }
    else tick();
  } catch (e) {
    if (e && e.error === "unauthorized") { logout(); say(t("e_unauthorized")); }
  }
}

document.addEventListener("input", (e) => {
  const el = e.target;
  if (el.id && (el.hasAttribute("data-draft") || el.id.startsWith("j-"))) S.draft[el.id] = el.value;
  if (el.name === "role") S.draft["role-" + el.value] = el.checked;
});
document.addEventListener("change", (e) => { if (e.target.id && e.target.hasAttribute("data-draft")) S.draft[e.target.id] = e.target.value; });

document.addEventListener("click", async (e) => {
  const id = e.target.id; if (!id) return;
  const clear = (p) => Object.keys(S.draft).forEach((k) => k.startsWith(p) && delete S.draft[k]);
  if (id === "lang") { S.lang = S.lang === "en" ? "es" : "en"; store.set("eum_lang", S.lang); render(); }
  else if (id === "staff-btn") { S.staff = true; say(null); render(); }
  else if (id === "back-btn") { S.staff = false; say(null); render(); }
  else if (id === "join-btn") {
    const roles = [...document.querySelectorAll("input[name=role]:checked")].map((x) => x.value);
    try {
      const r = await api("/api/join", "POST", { name: $("#j-name").value, pin: $("#j-pin").value, team: $("#j-team").value, roles });
      S.token = r.token; store.set("eum_token", r.token); S.msg = null; await refresh(true);
    } catch (err) { say(errText(err)); }
  } else if (id === "login-btn") {
    try { const r = await api("/api/admin/login", "POST", { password: $("#a-pw").value }); S.token = r.token; store.set("eum_token", r.token); S.msg = null; await refresh(true); }
    catch (err) { say(errText(err)); }
  } else if (id === "save-qty") {
    const qty = {}; SKUS.forEach((s) => { qty[s] = Math.max(0, Math.round(Number($("#q-" + s).value) || 0)); });
    await act("/api/proposal", { qty }, t("saved")); clear("q-"); await refresh(true);
  } else if (id === "save-modes") {
    const modes = {}; SKUS.forEach((s) => { const v = $("#m-" + s).value; if (v) modes[s] = v; });
    await act("/api/modes", { modes }, t("saved")); clear("m-"); await refresh(true);
  } else if (id === "approve") await act("/api/approve", { approve: true });
  else if (id === "revoke") await act("/api/approve", { approve: false });
  else if (id === "start") await act("/api/admin/start");
  else if (id === "close") await act("/api/admin/close");
  else if (id === "present") { S.presenter = !S.presenter; render(); }
  else if (id === "s-apply") {
    await act("/api/admin/settings", { public_board: $("#s-public").checked, auto_close: $("#s-auto").checked, round_seconds: Number($("#s-secs").value) || 0 }, t("saved"));
  } else if (id === "reset") {
    if (!S.resetArmed) { S.resetArmed = true; render(); setTimeout(() => { S.resetArmed = false; if (S.st) render(); }, 4000); }
    else { S.resetArmed = false; await act("/api/admin/reset", {}); }
  }
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.tagName === "INPUT" && !S.token) $(S.staff ? "#login-btn" : "#join-btn").click();
});

render();
refresh(true);
setInterval(() => { if (!document.hidden) refresh(false); }, 3000);
