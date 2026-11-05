(function () {
"use strict";
const CFG = window.LT_CONFIG || {};
const STATUS = [
  {n:"Pengar avsatta/beslutade", short:"Pengar beslutade", d:"Budget- eller nämndbeslut avsätter pengar uttryckligen kopplade till reformen."},
  {n:"Pengar föreslagna", short:"Pengar föreslagna", d:"Förslag från förvaltning, majoritet eller opposition om pengar kopplade till reformen. Inte bekräftat beslutat."},
  {n:"Kostnad beräknad, inga pengar", short:"Kostnad beräknad", d:"Kommunen har räknat på merkostnad eller lärarbehov, men inga pengar avsatta i det som granskats."},
  {n:"Nämnt utan belopp", short:"Nämnt utan belopp", d:"Reformen nämns i handlingarna, utan kostnad eller pengar."},
  {n:"Ej nämnt i granskade dokument", short:"Ej nämnt", d:"Budgethandlingar för 2027 har granskats men reformen nämns inte."},
  {n:"Inga budgethandlingar 2027 hittade", short:"Ej bedömbart än", d:"Inga budgethandlingar för 2027 kunde hittas eller öppnas. Säger inget om vad kommunen gjort."}
];
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmtPct = p => (p > 0 ? "+" : "") + String(p).replace(".", ",") + " %";
const fmt1 = x => x == null ? "–" : Number(x).toFixed(1).replace(".", ",");
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
};

let DATA = [], byId = {}, RATINGS = {}, currentId = null;
let active = store.get("lt_status", [true, true, true, true, true, true]);
let sortKey = "s", sortDir = 1;

document.querySelectorAll(".asof").forEach(el => el.textContent = CFG.asof || "");
const mailLink = $("#mailLink");
if (mailLink) { mailLink.textContent = CFG.mail; mailLink.href = "mailto:" + CFG.mail; }

function toast(t) { const el = document.createElement("div"); el.className = "toast"; el.textContent = t; document.body.appendChild(el); setTimeout(() => el.remove(), 2600); }
document.addEventListener("click", e => {
  const b = e.target.closest("[data-copy-mail]"); if (!b) return;
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(CFG.mail).then(() => toast("Adressen är kopierad"), () => toast(CFG.mail));
  else toast(CFG.mail);
});

/* ---------- Flikar och adresser ---------- */
const VIEWS = ["oversikt", "kommuner", "analys", "metod", "kontakt"];
function show(v, push) {
  if (!VIEWS.includes(v)) v = "oversikt";
  VIEWS.forEach(x => { $("#view-" + x).hidden = x !== v; $("#tab-" + x).setAttribute("aria-selected", x === v ? "true" : "false"); });
  if (push) setHash(v);
}
function setHash(h) { try { history.replaceState(null, "", "#" + h); } catch (e) { location.hash = h; } }
document.querySelectorAll("nav.tabs button").forEach(b => b.addEventListener("click", () => show(b.dataset.view, true)));
function route() {
  const h = (location.hash || "").slice(1);
  if (h.startsWith("kommun-") && byId[h.slice(7)]) { show("kommuner"); openDetail(h.slice(7), false); return; }
  if (h.startsWith("text-")) { show("analys"); openText(h.slice(5)); return; }
  show(h || "oversikt");
}
window.addEventListener("hashchange", route);

/* ---------- Skolpengsflagga ---------- */
function flagged(k) { return !!(k.sp && typeof k.sp.p === "number" && k.sp.p >= (CFG.skolpengRef + CFG.skolpengMarginal)); }
const flagTitle = () => `Skolpengen höjs med minst ${String(CFG.skolpengRef + CFG.skolpengMarginal).replace(".", ",")} % (normal uppräkning ${String(CFG.skolpengRef).replace(".", ",")} % plus ${String(CFG.skolpengMarginal).replace(".", ",")} procentenheter)`;

/* ---------- Översikt ---------- */
function renderOverview() {
  const c = [0,0,0,0,0,0]; DATA.forEach(k => c[k.s]++);
  $("#stats").innerHTML = [
    [DATA.length, "kommuner i sammanställningen"],
    [DATA.length - c[5], "där underlag har gått att granska"],
    [c[0] + c[1], "har avsatt eller föreslagit pengar kopplade till reformen"],
    [c[2], "har räknat på kostnaden utan att avsätta pengar"]
  ].map(([n, t]) => `<div class="stat"><div class="n">${n}</div><div class="t">${t}</div></div>`).join("");
  const cols = ["--s0","--s1","--s2","--s3","--s4","--s5bg"];
  $("#bar").innerHTML = c.map((v, i) => v ? `<span title="${esc(STATUS[i].short)}: ${v}" style="width:${v / DATA.length * 100}%;background:var(${cols[i]})${i === 5 ? ";background-image:repeating-linear-gradient(45deg,var(--line) 0 2px,transparent 2px 7px)" : ""}"></span>` : "").join("");
  $("#legend").innerHTML = c.map((v, i) => `<span><i style="background:var(${cols[i]})"></i>${esc(STATUS[i].short)} <b style="font-family:var(--f-mono)">${v}</b></span>`).join("");
  const cases = DATA.filter(k => k.s <= 2).sort((a, b) => a.s - b.s || a.k.localeCompare(b.k, "sv"));
  $("#cases").innerHTML = cases.map(k => `<li><div class="top"><button class="linklike" data-open="${k.id}"><b>${esc(k.k)}</b></button><span class="pill s${k.s}">${esc(STATUS[k.s].short)}</span></div><div class="small">${esc(k.m || k.mk || "")}</div><div class="small muted">${esc(k.l)}</div></li>`).join("");
}
document.addEventListener("click", e => { const b = e.target.closest("[data-open]"); if (!b) return; show("kommuner"); openDetail(b.dataset.open, true); });

/* ---------- Kommuntabell ---------- */
function shortKf(s) {
  const d = s.match(/\d{4}-\d{2}-\d{2}/), m = s.match(/(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\s+\d{4}/i);
  const what = /beslutat/i.test(s) && !/ej verifierat|inte verifierat|ej bekräftat|inte bekräftat/i.test(s) ? "beslutat" : "planerat/osäkert";
  return d ? `${d[0]} (${what})` : m ? `${m[0]} (${what})` : (s.length > 40 ? s.slice(0, 40) + "…" : s);
}
function sortVal(k, key) {
  if (key === "sp") return k.sp ? -k.sp.p : 999;
  if (key === "r") { const a = RATINGS[k.id]; return a ? -a.antal : 0; }
  if (key === "s") return k.s;
  return String(k[key] || "zzz");
}
function setupFilters() {
  const lans = [...new Set(DATA.map(k => k.l))].sort((a, b) => a.localeCompare(b, "sv"));
  $("#lan").innerHTML += lans.map(l => `<option>${esc(l)}</option>`).join("");
  $("#chips").innerHTML = STATUS.map((s, i) => `<button type="button" class="pill s${i}" data-i="${i}" aria-pressed="${active[i]}">${esc(s.short)}</button>`).join("");
  $("#chips").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; const i = +b.dataset.i; active[i] = !active[i]; b.setAttribute("aria-pressed", active[i]); store.set("lt_status", active); renderRows(); });
  ["q", "lan"].forEach(id => document.getElementById(id).addEventListener("input", renderRows));
  document.querySelectorAll("th[data-sort]").forEach(th => th.addEventListener("click", () => { const k = th.dataset.sort; if (sortKey === k) sortDir *= -1; else { sortKey = k; sortDir = 1; } renderRows(); }));
  $("#rows").addEventListener("click", e => { const tr = e.target.closest("tr[data-id]"); if (tr) openDetail(tr.dataset.id, true); });
}
function renderRows() {
  const q = $("#q").value.trim().toLowerCase(), lan = $("#lan").value;
  const list = DATA.filter(k => active[k.s] && (!lan || k.l === lan) && (!q || k.k.toLowerCase().includes(q)))
    .sort((a, b) => { const x = sortVal(a, sortKey), y = sortVal(b, sortKey); return (x < y ? -1 : x > y ? 1 : a.k.localeCompare(b.k, "sv")) * sortDir; });
  $("#count").textContent = `${list.length} av ${DATA.length} kommuner visas`;
  $("#rows").innerHTML = list.map(k => {
    const a = RATINGS[k.id];
    const sp = k.sp ? `${fmtPct(k.sp.p)}${flagged(k) ? ` <span class="pill flag" title="${esc(flagTitle())}">Kan ha hanterat</span>` : ""}` : '<span class="muted">–</span>';
    return `<tr data-id="${k.id}" aria-selected="${k.id === currentId}"><td class="k">${esc(k.k)}</td><td class="muted">${esc(k.l.replace(" län", ""))}</td><td><span class="pill s${k.s}">${esc(STATUS[k.s].short)}</span></td><td class="small">${esc(k.m || "") || '<span class="muted">–</span>'}</td><td class="num">${sp}</td><td class="small">${k.kf ? esc(shortKf(k.kf)) : '<span class="muted">–</span>'}</td><td class="num">${a ? `${a.antal} st` : '<span class="muted">–</span>'}</td></tr>`;
  }).join("");
}

/* ---------- Kommundetalj ---------- */
const fact = (t, v, html) => v ? `<div class="fact"><dt>${t}</dt><dd>${html ? v : esc(v)}</dd></div>` : "";
function openDetail(id, push) {
  currentId = id; renderDetail(id); renderRows();
  if (push) setHash("kommun-" + id);
  const el = $("#detail"); if (el && el.scrollIntoView) el.scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start"});
}
function renderDetail(id) {
  const k = byId[id]; if (!k) { $("#detail").innerHTML = ""; return; }
  const a = RATINGS[id], done = store.get("lt_rated", {})[id];
  const spHtml = k.sp ? `${fmtPct(k.sp.p)} (${esc(k.sp.typ)}) ${flagged(k) ? '<span class="pill flag">Kan ha hanterat reformen</span>' : ""}<br><span class="small muted">${esc(k.sp.not)}</span> ${k.sp.u ? `<a class="small" href="${esc(k.sp.u)}" target="_blank" rel="noopener">Källa</a>` : ""}` : '<span class="muted">Ej insamlat ännu</span>';
  const styre = k.styre ? esc(k.styre) : '<span class="muted">Ej insamlat ännu</span>';
  const docs = (k.docs || []).map(d => `<li><div class="meta"><b>${esc(d.t || "Dokument")}</b>${d.d ? `<span class="tag">${esc(d.d)}</span>` : ""}${d.sk ? `<span class="tag">${esc(d.sk)}</span>` : ""}${d.pr ? `<span class="tag">${esc(d.pr)}</span>` : ""}${d.nr === true ? '<span class="pill s3">Nämner reformen</span>' : d.nr === false ? '<span class="tag">Nämner inte reformen</span>' : ""}</div>${d.c ? `<blockquote>${esc(d.c)}</blockquote>` : ""}${d.u ? `<a href="${esc(d.u)}" target="_blank" rel="noopener">${esc(d.u)}</a>` : ""}</li>`).join("") || '<li class="muted">Inga dokument registrerade.</li>';
  const mailto = `mailto:${CFG.mail}?subject=${encodeURIComponent("Lärartiden i budgeten: " + k.k)}`;
  $("#detail").innerHTML = `<article class="detail">
    <header><div><div class="eyebrow">${esc(k.l)}</div><h2>${esc(k.k)}</h2></div><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><span class="pill s${k.s}">${esc(STATUS[k.s].n)}</span><button class="btn ghost" type="button" id="closeDetail">Stäng</button></div></header>
    <p style="margin:0;max-width:80ch">${esc(k.sum || "")}</p>
    <dl class="facts" style="margin:0">
      ${fact("Pengar kopplade till reformen", k.m)}${fact("Egen beräknad merkostnad", k.mk)}
      ${fact("Om statsbidraget", k.sb)}${fact("Om prislista/samverkan", k.pl)}
      ${fact("Fullmäktiges budgetbeslut 2027", k.kf ? esc(k.kf) + (k.kfu ? ` · <a href="${esc(k.kfu)}" target="_blank" rel="noopener">källa</a>` : "") : '<span class="muted">Okänt</span>', true)}
      ${fact("Skolpeng 2027", spHtml, true)}
      ${fact("Styre efter valet 2026", styre, true)}
      ${fact("Luckor i granskningen", k.lu)}
    </dl>
    <div><h3>Granskade dokument</h3><ul class="docs">${docs}</ul></div>
    <form class="box" id="ratebox" novalidate>
      <h3 style="margin:0">Stämmer det här?</h3>
      <p class="small muted" style="margin:0">Känner du till kommunens budget? Bedöm uppgifterna på en skala från 1 (inte alls) till 5 (helt). Bedömningen är anonym.</p>
      <div class="agg">${a ? `<span>Bedömningar: <b>${a.antal}</b></span><span>Citat och data: <b>${fmt1(a.snitt_data)}</b></span><span>Rimliga dokument: <b>${fmt1(a.snitt_dok)}</b></span><span>Tolkning: <b>${fmt1(a.snitt_tolk)}</b></span>` : '<span class="muted">Inga bedömningar ännu.</span>'}</div>
      ${[["data","Stämmer citaten och uppgifterna?"],["dok","Är dokumenten rimliga att granska?"],["tolk","Är slutsatsen (status) rimlig?"]].map(([f, t]) => `<div class="rating-row"><span id="lbl-${f}">${t}</span><div class="scale" role="group" aria-labelledby="lbl-${f}" data-f="${f}">${[1,2,3,4,5].map(n => `<button type="button" aria-pressed="false" data-n="${n}">${n}</button>`).join("")}</div></div>`).join("")}
      <label class="small muted" for="kommentar" style="font-weight:600">Kommentar eller bättre dokument (frivilligt)</label>
      <textarea id="kommentar" rows="3" maxlength="2000" placeholder="Vad stämmer inte? Länka gärna till ett dokument."></textarea>
      <input type="text" id="webbplats" name="webbplats" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px">
      <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center"><button class="btn" type="submit" id="saveRating">Skicka bedömning</button><span class="small muted" id="rateStatus">${done ? "Du har redan bedömt den här kommunen från den här webbläsaren." : ""}</span></div>
    </form>
    <div class="mailrow small"><span>Synpunkter eller ett bättre dokument?</span><a class="mail" href="${esc(mailto)}">${esc(CFG.mail)}</a><button class="btn ghost" type="button" data-copy-mail>Kopiera</button></div>
  </article>`;
  wireRating(k.id);
  $("#closeDetail").addEventListener("click", () => { currentId = null; $("#detail").innerHTML = ""; renderRows(); setHash("kommuner"); });
}

/* ---------- Bedömningar (Supabase) ---------- */
const sbHeaders = () => ({ "apikey": CFG.supabaseKey, "Content-Type": "application/json" });
const sbReady = () => !!(CFG.supabaseUrl && CFG.supabaseKey);
async function loadRatings() {
  if (!sbReady()) return;
  try {
    const r = await fetch(`${CFG.supabaseUrl}/rest/v1/bedomningar_snitt?select=kommun,antal,snitt_data,snitt_dok,snitt_tolk`, { headers: sbHeaders() });
    if (!r.ok) return;
    const rows = await r.json(); const m = {};
    rows.forEach(x => m[x.kommun] = x); RATINGS = m;
    renderRows(); if (currentId && !document.activeElement?.closest?.("#ratebox")) renderDetail(currentId);
  } catch (e) { /* bedömningar visas inte om databasen inte svarar */ }
}
function wireRating(id) {
  const form = $("#ratebox"); if (!form) return;
  const draft = {};
  form.querySelectorAll(".scale").forEach(sc => sc.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    draft[sc.dataset.f] = +b.dataset.n; sc.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b));
  }));
  const btn = $("#saveRating"), st = $("#rateStatus");
  if (!sbReady()) { btn.disabled = true; st.textContent = "Bedömningar är inte aktiverade ännu. Mejla gärna i stället."; return; }
  form.addEventListener("submit", async e => {
    e.preventDefault();
    if ($("#webbplats").value) return;
    if (!draft.data && !draft.dok && !draft.tolk) { st.textContent = "Välj minst ett betyg mellan 1 och 5."; return; }
    btn.disabled = true; st.textContent = "Skickar…";
    const body = { kommun: id, data: draft.data || null, dok: draft.dok || null, tolk: draft.tolk || null, kommentar: $("#kommentar").value.trim().slice(0, 2000) || null };
    try {
      const r = await fetch(`${CFG.supabaseUrl}/rest/v1/bedomningar`, { method: "POST", headers: Object.assign(sbHeaders(), { "Prefer": "return=minimal" }), body: JSON.stringify(body) });
      if (!r.ok) throw new Error(String(r.status));
      const rated = store.get("lt_rated", {}); rated[id] = new Date().toISOString(); store.set("lt_rated", rated);
      st.textContent = "Tack! Din bedömning är skickad.";
      form.querySelectorAll(".scale button").forEach(x => x.setAttribute("aria-pressed", "false")); $("#kommentar").value = "";
      setTimeout(loadRatings, 800);
    } catch (err) {
      st.textContent = "Det gick inte att skicka just nu. Försök igen om en stund, eller mejla.";
    }
    btn.disabled = false;
  });
}

/* ---------- Analystexter ---------- */
// Enkel reserv om Markdown-biblioteket inte laddas: rubriker, stycken, fet, kursiv, länkar.
function simpleMd(md) {
  const inline = s => esc(s)
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
    .replace(/\*([^*]+)\*/g, "<i>$1</i>");
  return md.split(/\n{2,}/).map(b => {
    const h = b.match(/^(#{1,4})\s+(.*)$/);
    return h ? `<h${h[1].length}>${inline(h[2])}</h${h[1].length}>` : `<p>${inline(b.replace(/\n/g, " "))}</p>`;
  }).join("");
}
let TEXTS = [];
async function loadTexts() {
  try { const r = await fetch("texter/index.json", { cache: "no-cache" }); TEXTS = await r.json(); } catch (e) { TEXTS = []; }
}
async function openText(id) {
  if (!TEXTS.length) { $("#article").innerHTML = '<p class="muted">Inga texter hittades.</p>'; return; }
  const t = TEXTS.find(x => x.id === id) || TEXTS[0];
  $("#toc").innerHTML = TEXTS.map(x => `<button type="button" data-t="${esc(x.id)}" aria-current="${x.id === t.id}">${esc(x.titel)}</button>`).join("");
  let md = "";
  try { const r = await fetch("texter/" + t.fil, { cache: "no-cache" }); md = await r.text(); } catch (e) { md = "Texten kunde inte laddas."; }
  const html = window.marked ? window.marked.parse(md) : simpleMd(md);
  $("#article").innerHTML = `<div class="eyebrow">Analys ${t.utkast ? '<span class="draft">Utkast</span>' : ""}</div>${html}`;
  $("#article").querySelectorAll("a[href^='http']").forEach(a => { a.target = "_blank"; a.rel = "noopener"; });
}
$("#toc").addEventListener("click", e => { const b = e.target.closest("button[data-t]"); if (!b) return; openText(b.dataset.t); setHash("text-" + b.dataset.t); });

/* ---------- Start ---------- */
$("#statusdef").innerHTML = STATUS.map((s, i) => `<p><span class="pill s${i}">${esc(s.short)}</span> ${esc(s.d)}</p>`).join("");
(async function start() {
  try {
    const r = await fetch("data/kommuner.json", { cache: "no-cache" });
    DATA = await r.json();
  } catch (e) {
    $("#rows").innerHTML = '<tr><td colspan="7">Kommundata kunde inte laddas. Ladda om sidan.</td></tr>'; return;
  }
  byId = Object.fromEntries(DATA.map(k => [k.id, k]));
  setupFilters(); renderOverview(); renderRows();
  await loadTexts();
  if (!(location.hash || "").startsWith("#text-")) openText(TEXTS[0]?.id);
  route();
  loadRatings();
})();
})();
