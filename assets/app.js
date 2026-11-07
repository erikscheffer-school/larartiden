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
const fmt1 = x => x == null ? "–" : Number(x).toFixed(1).replace(".", ",");
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
};
const md = text => window.marked ? window.marked.parse(text) : simpleMd(text);
const extLinks = el => el.querySelectorAll("a[href^='http']").forEach(a => { a.target = "_blank"; a.rel = "noopener"; });

let DATA = [], byId = {}, RATINGS = {}, currentId = null;
let active = store.get("lt_status", [true, true, true, true, true, true]);
let sortKey = "s", sortDir = 1;

document.querySelectorAll(".asof").forEach(el => el.textContent = CFG.asof || "");
const mailLink = $("#mailLink");
if (mailLink) { mailLink.textContent = CFG.mail; mailLink.href = "mailto:" + CFG.mail; }

function toast(t) { const el = document.createElement("div"); el.className = "toast"; el.setAttribute("role", "status"); el.textContent = t; document.body.appendChild(el); setTimeout(() => el.remove(), 2600); }
function copy(text, ok) {
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(() => toast(ok), () => toast("Kopieringen misslyckades. Markera texten och kopiera själv."));
  else toast("Kopieringen misslyckades. Markera texten och kopiera själv.");
}
document.addEventListener("click", e => { if (e.target.closest("[data-copy-mail]")) copy(CFG.mail, "Adressen är kopierad"); });

/* ---------- Flikar och adresser ---------- */
const VIEWS = ["oversikt", "kommuner", "analys", "metod", "kontakt"];
function show(v, push) {
  if (!VIEWS.includes(v) || $("#tab-" + v).hidden) v = "oversikt";
  VIEWS.forEach(x => { $("#view-" + x).hidden = x !== v; $("#tab-" + x).setAttribute("aria-selected", x === v ? "true" : "false"); });
  if (push) setHash(v);
}
function setHash(h) { try { history.replaceState(null, "", "#" + h); } catch (e) { location.hash = h; } }
document.querySelectorAll("nav.tabs button").forEach(b => b.addEventListener("click", () => show(b.dataset.view, true)));
function route() {
  const h = (location.hash || "").slice(1);
  if (h.startsWith("kommun-") && byId[h.slice(7)]) { show("kommuner"); openDetail(h.slice(7), false); return; }
  if (h.startsWith("text-") && TEXTS.length) { show("analys"); openText(h.slice(5)); return; }
  if (h.startsWith("metod-")) { show("metod"); openMetod(h.slice(6)); return; }
  show(h || "oversikt");
}
window.addEventListener("hashchange", route);

/* ---------- Översikt ---------- */
function renderOverview() {
  const c = [0,0,0,0,0,0]; DATA.forEach(k => c[k.s]++);
  const sorted = [...DATA].sort((a, b) => a.s - b.s || a.k.localeCompare(b.k, "sv"));
  // En ruta per kommun, i statusordning. Rutorna är klickbara men tas inte med i tabbordningen, listan nedan och fliken Kommuner nås med tangentbord.
  $("#kgrid").innerHTML = sorted.map(k => `<button type="button" tabindex="-1" class="cell s${k.s}" data-open="${k.id}" title="${esc(k.k)}: ${esc(STATUS[k.s].short)}" aria-hidden="true"></button>`).join("");
  $("#legend").innerHTML = c.map((v, i) => `<li><span class="sq s${i}"></span><span class="lg-t">${esc(STATUS[i].n)}</span><span class="lg-n">${v}</span></li>`).join("");
  // Kort sammanställning per status. Fältet kort är en förenklad beloppsrad, hela texten finns på kommunens sida.
  $("#cases").innerHTML = [0, 1, 2].map(s => {
    const list = sorted.filter(k => k.s === s);
    if (!list.length) return "";
    const lbl = s === 2 ? "Beräknad kostnad" : "Belopp";
    return `<section class="case-group"><h3><span class="sq s${s}"></span>${esc(STATUS[s].short)} <span class="muted">${list.length}</span></h3><ul>` +
      list.map(k => `<li><button class="linklike" type="button" data-open="${k.id}">${esc(k.k)}</button><span class="case-l">${esc(k.l.replace(" län", ""))}</span><span class="case-m"><span class="sr">${lbl}: </span>${esc(k.kort || k.m || k.mk || "")}</span></li>`).join("") +
      `</ul></section>`;
  }).join("");
}
document.addEventListener("click", e => {
  const g = e.target.closest("[data-goto]"); if (g) { e.preventDefault(); show(g.dataset.goto, true); window.scrollTo(0, 0); return; }
  const b = e.target.closest("[data-open]"); if (!b) return; show("kommuner"); openDetail(b.dataset.open, true);
});

/* ---------- Kommunlistan ---------- */
function shortKf(s) {
  const d = s.match(/\d{4}-\d{2}-\d{2}/), m = s.match(/(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\s+\d{4}/i);
  const what = /beslutat/i.test(s) && !/ej verifierat|inte verifierat|ej bekräftat|inte bekräftat/i.test(s) ? "beslutat" : "planerat eller osäkert";
  return d ? `${d[0]} (${what})` : m ? `${m[0]} (${what})` : (s.length > 40 ? s.slice(0, 40) + "…" : s);
}
function sortVal(k, key) {
  if (key === "r") { const a = RATINGS[k.id]; return a ? -a.antal : 0; }
  if (key === "s") return k.s;
  return String(k[key] || "zzz");
}
function setupFilters() {
  const lans = [...new Set(DATA.map(k => k.l))].sort((a, b) => a.localeCompare(b, "sv"));
  $("#lan").innerHTML += lans.map(l => `<option>${esc(l)}</option>`).join("");
  $("#chips").insertAdjacentHTML("beforeend", STATUS.map((s, i) => `<label><input type="checkbox" data-i="${i}" ${active[i] ? "checked" : ""}><span class="sq s${i}"></span>${esc(s.short)}</label>`).join(""));
  $("#chips").addEventListener("change", e => { const b = e.target.closest("input[data-i]"); if (!b) return; active[+b.dataset.i] = b.checked; store.set("lt_status", active); renderRows(); });
  ["q", "lan"].forEach(id => document.getElementById(id).addEventListener("input", renderRows));
  document.querySelectorAll("th[data-sort]").forEach(th => th.addEventListener("click", () => { const k = th.dataset.sort; if (sortKey === k) sortDir *= -1; else { sortKey = k; sortDir = 1; } renderRows(); }));
  $("#rows").addEventListener("click", e => { const tr = e.target.closest("tr[data-id]"); if (tr) openDetail(tr.dataset.id, true); });
}
function renderRows() {
  const q = $("#q").value.trim().toLowerCase(), lan = $("#lan").value;
  const list = DATA.filter(k => active[k.s] && (!lan || k.l === lan) && (!q || k.k.toLowerCase().includes(q)))
    .sort((a, b) => { const x = sortVal(a, sortKey), y = sortVal(b, sortKey); return (x < y ? -1 : x > y ? 1 : a.k.localeCompare(b.k, "sv")) * sortDir; });
  document.querySelectorAll("th[data-sort]").forEach(th => th.setAttribute("aria-sort", th.dataset.sort === sortKey ? (sortDir > 0 ? "ascending" : "descending") : "none"));
  $("#count").textContent = `${list.length} av ${DATA.length} kommuner visas. Klicka på en kommun för detaljer.`;
  $("#rows").innerHTML = list.map(k => {
    const a = RATINGS[k.id];
    return `<tr data-id="${k.id}" aria-selected="${k.id === currentId}"><td class="k">${esc(k.k)}</td><td class="muted">${esc(k.l.replace(" län", ""))}</td><td style="white-space:nowrap"><span class="sq s${k.s}"></span>${esc(STATUS[k.s].short)}</td><td class="small">${esc(k.m || "") || '<span class="muted">–</span>'}</td><td class="small">${k.kf ? esc(shortKf(k.kf)) : '<span class="muted">Okänt</span>'}</td><td class="num">${a ? `${a.antal} st` : '<span class="muted">–</span>'}</td></tr>`;
  }).join("") || '<tr><td colspan="6" class="muted">Inga kommuner matchar filtret.</td></tr>';
}

/* ---------- Kommunsida ---------- */
const fact = (t, v, html) => v ? `<dt>${t}</dt><dd>${html ? v : esc(v)}</dd>` : "";
// Delar upp luckorna i punkter vid meningsslut, utan att bryta vid förkortningar som "s. 12" eller "t.ex.".
function gapList(text) {
  return String(text || "").split(/(?<=[.!?])\s+(?=[A-ZÅÄÖ"(])/).map(s => s.trim()).filter(Boolean);
}
function host(u) { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return u; } }
function linkify(s) { return esc(s).replace(/(https?:\/\/[^\s)]+[^\s).,;])/g, '<a href="$1" target="_blank" rel="noopener">länk</a>'); }
function openDetail(id, push) {
  currentId = id; renderDetail(id); renderRows();
  if (push) setHash("kommun-" + id);
  const el = $("#detail"); if (el && el.scrollIntoView) el.scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start"});
}
function renderDetail(id) {
  const k = byId[id]; if (!k) { $("#detail").innerHTML = ""; return; }
  const a = RATINGS[id], done = store.get("lt_rated", {})[id];
  const gaps = gapList(k.lu);
  const site = k.w ? `<a href="${esc(k.w)}" target="_blank" rel="noopener">${esc(k.w.replace(/^https?:\/\//, "").replace(/\/$/, ""))}</a>` : "";
  const kfText = k.kf ? `${esc(k.kf)}${k.kfu ? ` (<a href="${esc(k.kfu)}" target="_blank" rel="noopener">källa</a>)` : ""}` : "Inte känt. Leta efter kommunfullmäktiges sammanträdesdagar för hösten 2026.";
  const docs = (k.docs || []).map(d => `<li><b>${esc(d.t || "Dokument")}</b><div class="meta">${[d.d, d.sk, d.pr, d.nr === true ? "nämner reformen" : d.nr === false ? "nämner inte reformen" : ""].filter(Boolean).map(esc).join(", ")}</div>${d.c ? `<blockquote>${esc(d.c)}</blockquote>` : ""}${d.u ? `<a class="doclink" href="${esc(d.u)}" target="_blank" rel="noopener" title="${esc(d.u)}">Öppna dokumentet <span class="muted">(${esc(host(d.u))})</span></a>` : ""}</li>`).join("") || '<li class="muted">Inga dokument registrerade.</li>';
  const mailto = `mailto:${CFG.mail}?subject=${encodeURIComponent("Lärartiden i budgeten: " + k.k)}`;
  $("#detail").innerHTML = `<article class="detail" aria-labelledby="dh">
    <div class="head"><div><h2 id="dh">${esc(k.k)}</h2><p class="d-lan">${esc(k.l)}</p></div><button class="btn ghost" type="button" id="closeDetail">Stäng</button></div>
    <p class="status st${k.s}"><span class="sq s${k.s}"></span>${esc(STATUS[k.s].n)}</p>
    <p class="d-sum">${esc(k.sum || "")}</p>
    <dl class="facts">
      ${fact("Pengar kopplade till reformen", k.m)}${fact("Egen beräknad merkostnad", k.mk)}
      ${fact("Om statsbidraget", k.sb)}${fact("Om prislista eller samverkan", k.pl)}
      ${fact("Fullmäktiges budgetbeslut 2027", kfText, true)}
    </dl>
    <section class="gaps" aria-labelledby="gh-${k.id}">
      <h3 id="gh-${k.id}">Luckor i granskningen</h3>
      ${gaps.length ? `<p class="small" style="margin-bottom:8px">Det här har jag inte hittat eller inte kunnat kontrollera. Bilden av ${esc(k.k)} kan alltså ändras.</p><ul>${gaps.map(g => `<li>${linkify(g)}</li>`).join("")}</ul>` : '<p>Inga kända luckor antecknade.</p>'}
    </section>
    <section class="where" aria-labelledby="wh-${k.id}">
      <h3 id="wh-${k.id}">Var du kan fortsätta leta</h3>
      <ul>
        ${site ? `<li>Kommunens webbplats: ${site}. Politiska handlingar ligger oftast under rubriker som "Kommun och politik", "Politik och demokrati" eller "Möten, handlingar och protokoll". Många kommuner har en separat mötesportal dit sidan länkar.</li>` : ""}
        <li>När budgeten beslutas: ${kfText}</li>
        <li>Budgeten går oftast först till kommunstyrelsen, som lämnar ett förslag till beslut. Sedan beslutar kommunfullmäktige. Titta därför både i kommunstyrelsens och fullmäktiges kallelser och protokoll. Under ett valår ska det nyvalda fullmäktige fastställa budgeten, och det sker ofta i november eller december.</li>
        <li>Bra sökord i handlingarna: "budget 2027", "mål och budget", "flerårsplan", "ramar", "undervisningstid", "lärares arbetstid", "statsbidrag". Titta också i barn- och utbildningsnämndens (eller motsvarande nämnds) budgetunderlag.</li>
      </ul>
    </section>
    <h3>Granskade dokument</h3><ul class="docs">${docs}</ul>
    <form class="ratebox" id="ratebox" novalidate>
      <h3 style="margin:14px 0 0">Stämmer det här?</h3>
      <p class="small muted" style="margin:0">Känner du till kommunens budget? Bedöm uppgifterna från 1 (inte alls) till 5 (helt). Bedömningen är anonym.</p>
      <div class="agg">${a ? `<span>Bedömningar: <b>${a.antal}</b></span><span>Citat och uppgifter: <b>${fmt1(a.snitt_data)}</b></span><span>Rimliga dokument: <b>${fmt1(a.snitt_dok)}</b></span><span>Rimlig slutsats: <b>${fmt1(a.snitt_tolk)}</b></span>` : '<span>Inga bedömningar ännu.</span>'}</div>
      ${[["data","Stämmer citaten och uppgifterna?"],["dok","Är dokumenten rimliga att granska?"],["tolk","Är slutsatsen (status) rimlig?"]].map(([f, t]) => `<div class="rating-row"><span id="lbl-${f}">${t}</span><div class="scale" role="group" aria-labelledby="lbl-${f}" data-f="${f}">${[1,2,3,4,5].map(n => `<button type="button" aria-pressed="false" data-n="${n}">${n}</button>`).join("")}</div></div>`).join("")}
      <label class="small muted" for="kommentar">Kommentar eller bättre dokument (frivilligt)</label>
      <textarea id="kommentar" rows="3" maxlength="2000" placeholder="Vad stämmer inte? Länka gärna till ett dokument."></textarea>
      <input type="text" id="webbplats" name="webbplats" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px">
      <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center"><button class="btn" type="submit" id="saveRating">Skicka bedömning</button><span class="small muted" id="rateStatus" role="status">${done ? "Du har redan bedömt den här kommunen från den här webbläsaren." : ""}</span></div>
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
  if (!sbReady()) { btn.disabled = true; st.textContent = "Bedömningar är inte aktiverade. Mejla gärna i stället."; return; }
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
      st.textContent = "Tack! Bedömningen är skickad.";
      form.querySelectorAll(".scale button").forEach(x => x.setAttribute("aria-pressed", "false")); $("#kommentar").value = "";
      setTimeout(loadRatings, 800);
    } catch (err) {
      st.textContent = "Bedömningen kunde inte skickas. Försök igen om en stund eller mejla.";
    }
    btn.disabled = false;
  });
}

/* ---------- Markdown ---------- */
// Reserv om Markdown-biblioteket inte laddas: rubriker, stycken, listor, fet, kursiv, länkar.
function simpleMd(text) {
  const inline = s => esc(s)
    .replace(/\[([^\]]+)\]\(((?:https?:|#|[a-z])[^)\s"]*)\)/g, '<a href="$2">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
    .replace(/\*([^*]+)\*/g, "<i>$1</i>");
  return text.split(/\n{2,}/).map(b => {
    const h = b.match(/^(#{1,4})\s+(.*)$/);
    if (h) return `<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`;
    if (/^\d+\. /.test(b)) return "<ol>" + b.split(/\n(?=\d+\. )/).map(li => `<li>${inline(li.replace(/^\d+\. /, ""))}</li>`).join("") + "</ol>";
    if (/^[-*] /.test(b)) return "<ul>" + b.split(/\n(?=[-*] )/).map(li => `<li>${inline(li.replace(/^[-*] /, ""))}</li>`).join("") + "</ul>";
    return `<p>${inline(b.replace(/\n/g, " "))}</p>`;
  }).join("");
}

/* ---------- Analystexter (visas bara när texter/index.json innehåller texter) ---------- */
let TEXTS = [];
async function loadTexts() {
  try { const r = await fetch("texter/index.json", { cache: "no-cache" }); TEXTS = await r.json(); } catch (e) { TEXTS = []; }
  $("#tab-analys").hidden = !TEXTS.length;
}
async function openText(id) {
  if (!TEXTS.length) return;
  const t = TEXTS.find(x => x.id === id) || TEXTS[0];
  $("#toc").hidden = TEXTS.length < 2;
  $("#toc").innerHTML = TEXTS.map(x => `<button type="button" data-t="${esc(x.id)}" aria-current="${x.id === t.id}">${esc(x.titel)}</button>`).join("");
  let text = "";
  try { const r = await fetch("texter/" + t.fil, { cache: "no-cache" }); if (!r.ok) throw 0; text = await r.text(); } catch (e) { text = "Texten kunde inte laddas. Ladda om sidan."; }
  $("#article").innerHTML = (t.utkast ? '<p class="small muted">Utkast</p>' : "") + md(text);
  extLinks($("#article"));
}
$("#toc").addEventListener("click", e => { const b = e.target.closest("button[data-t]"); if (!b) return; openText(b.dataset.t); setHash("text-" + b.dataset.t); });

/* ---------- Metod, logg och prompt (filer i mappen metod/) ---------- */
const METOD = { metod: "metod/metod.md", logg: "metod/logg.md", prompt: "metod/prompt.md", utveckla: "metod/utveckla.md" };
async function openMetod(id) {
  if (!METOD[id]) id = "metod";
  document.querySelectorAll("#metodnav button").forEach(b => b.setAttribute("aria-current", b.dataset.m === id ? "true" : "false"));
  let text = "";
  try { const r = await fetch(METOD[id], { cache: "no-cache" }); if (!r.ok) throw 0; text = await r.text(); } catch (e) { $("#metodbody").innerHTML = "<p>Texten kunde inte laddas. Ladda om sidan.</p>"; return; }
  if (id === "prompt") {
    // Filen består av en inledning, en rad med "---PROMPT---" och sedan själva prompten.
    const [intro, prompt = ""] = text.split(/^---PROMPT---\s*$/m);
    const words = prompt.trim().split(/\s+/).length;
    $("#metodbody").innerHTML = md(intro) + `<div class="prompt-bar"><button class="btn" type="button" id="copyPrompt">Kopiera prompten</button><span class="small muted">${words.toLocaleString("sv-SE")} ord. Hela prompten visas nedan.</span></div><pre class="prompt" id="promptText" tabindex="0">${esc(prompt.trim())}</pre>`;
    $("#copyPrompt").addEventListener("click", () => copy(prompt.trim(), "Prompten är kopierad"));
  } else {
    $("#metodbody").innerHTML = md(text);
    if (id === "metod") {
      const slot = $("#metodbody").querySelector("#statusdef");
      if (slot) slot.innerHTML = STATUS.map((s, i) => `<p><span class="sq s${i}"></span><b>${esc(s.n)}.</b> ${esc(s.d)}</p>`).join("");
    }
  }
  extLinks($("#metodbody"));
}
$("#metodnav").addEventListener("click", e => { const b = e.target.closest("button[data-m]"); if (!b) return; openMetod(b.dataset.m); setHash("metod-" + b.dataset.m); });

/* ---------- Start ---------- */
(async function start() {
  try {
    const r = await fetch("data/kommuner.json", { cache: "no-cache" });
    DATA = await r.json();
  } catch (e) {
    $("#rows").innerHTML = '<tr><td colspan="6">Kommundata kunde inte laddas. Ladda om sidan.</td></tr>'; return;
  }
  byId = Object.fromEntries(DATA.map(k => [k.id, k]));
  setupFilters(); renderOverview(); renderRows();
  await loadTexts();
  if (TEXTS.length && !(location.hash || "").startsWith("#text-")) openText(TEXTS[0].id);
  if (!(location.hash || "").startsWith("#metod-")) openMetod("metod");
  route();
  loadRatings();
})();
})();
