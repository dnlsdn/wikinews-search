// Web interface (owner: Fabio). Plain JavaScript, no build step.
//
// The page has two views:
//   search view    ?q=...&config=...&category=...  (all the state is in the query string, so a
//                  demo query can be opened from a link and the browser's back button works)
//   document view  #/doc/<id>                      (the hash, so the search state stays below it)
// Compare mode runs the same query, filters and page with two configurations side by side.

const $ = (id) => document.getElementById(id);
const PAGE_SIZE = 10;

const app = {
  defaultConfig: null,
  configNames: [],
  requestId: 0, // responses of an older request are ignored (filters clicked quickly)
  facets: { key: null, data: null },
  lastUrl: null, // the URL last routed: hashchange and popstate can both fire for one click
  lastSearch: null, // the query string whose results are on screen
  cameFromSearch: false,
};

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text == null ? "" : String(text);
  return div.innerHTML;
}

async function getJson(url) {
  const resp = await fetch(url);
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

// ---- state <-> URL ----------------------------------------------------------------------------

function validConfig(name) {
  return app.configNames.includes(name) ? name : null;
}

function otherConfig(name) {
  // The second column defaults to the semantic configuration: lexical against semantic is E3.
  if (name !== "knn" && app.configNames.includes("knn")) return "knn";
  return app.configNames.find((c) => c !== name) || name;
}

function readState() {
  const p = new URLSearchParams(location.search);
  const config = validConfig(p.get("config")) || app.defaultConfig;
  const compare = p.get("compare") === "1";
  return {
    q: (p.get("q") || "").trim(),
    config,
    compare,
    config2: validConfig(p.get("config2")) || otherConfig(config),
    page: Math.max(1, parseInt(p.get("page") || "1", 10) || 1),
    date_from: p.get("date_from") || "",
    date_to: p.get("date_to") || "",
    categories: p.getAll("category"),
    agencies: p.getAll("agency"),
    published: p.get("published") === "true",
  };
}

function filterParams(s, p) {
  if (s.date_from) p.set("date_from", s.date_from);
  if (s.date_to) p.set("date_to", s.date_to);
  s.categories.forEach((c) => p.append("category", c));
  s.agencies.forEach((a) => p.append("agency", a));
  if (s.published) p.set("published", "true");
  return p;
}

function urlParams(s) {
  const p = new URLSearchParams();
  if (s.q) p.set("q", s.q);
  p.set("config", s.config);
  if (s.compare) {
    p.set("compare", "1");
    p.set("config2", s.config2);
  }
  if (s.page > 1) p.set("page", String(s.page));
  return filterParams(s, p);
}

function apiParams(s, config) {
  const p = new URLSearchParams({ q: s.q, config, page: String(s.page), size: String(PAGE_SIZE) });
  return filterParams(s, p);
}

function checkedValues(facet) {
  return [...document.querySelectorAll(`input[data-facet="${facet}"]:checked`)].map((i) => i.value);
}

function formState() {
  return {
    q: $("q").value.trim(),
    config: $("config").value,
    compare: $("compare").checked,
    config2: $("config2").value,
    page: 1, // every new query or filter starts again from the first page
    date_from: $("date-from").value,
    date_to: $("date-to").value,
    categories: checkedValues("category"),
    agencies: checkedValues("agency"),
    published: $("published").checked,
  };
}

function navigate(state) {
  history.pushState(null, "", `?${urlParams(state)}`);
  app.lastUrl = null; // an explicit action always searches again
  app.lastSearch = null;
  route();
}

function syncForm(s) {
  $("q").value = s.q;
  $("config").value = s.config;
  $("compare").checked = s.compare;
  $("config2").hidden = !s.compare;
  $("config2").value = s.config2;
  $("date-from").value = s.date_from;
  $("date-to").value = s.date_to;
  $("published").checked = s.published;
  renderFacets(app.facets.data, s);
}

// ---- routing ----------------------------------------------------------------------------------

function route() {
  const url = location.search + location.hash;
  if (url === app.lastUrl) return;
  app.lastUrl = url;
  const match = location.hash.match(/^#\/doc\/(.+)$/);
  if (match) {
    showDoc(decodeURIComponent(match[1]));
    return;
  }
  app.cameFromSearch = false;
  $("doc-view").hidden = true;
  $("search-view").hidden = false;
  document.title = "Wikinews search";
  const s = readState();
  syncForm(s);
  if (location.search !== app.lastSearch) runSearch(s);
}

// ---- search view ------------------------------------------------------------------------------

function renderHit(hit, rank) {
  const image = hit.image_url ? `<img src="${escapeHtml(hit.image_url)}" alt="" loading="lazy">` : "";
  const meta = [hit.date || "no date", hit.agencies.join(", ")].filter(Boolean).join(" · ");
  const tags = hit.categories.map((c) => `<span class="tag">${escapeHtml(c)}</span>`).join("");
  const unpublished = hit.published ? "" : ` <span class="unpublished">not published</span>`;
  // The snippet comes from the API already escaped, with <em> highlight tags: inserted as HTML.
  return `<li class="hit"><span class="rank">${rank}</span>${image}<div>
    <a class="title" href="#/doc/${encodeURIComponent(hit.id)}">${escapeHtml(hit.title)}</a>${unpublished}
    <div class="meta">${escapeHtml(meta)}</div>
    <div class="snippet">${hit.snippet || ""}</div>
    <div class="tags">${tags}</div>
  </div></li>`;
}

function summary(data) {
  return `${data.total} results in ${data.took_ms} ms`;
}

function renderColumn(config, result, s) {
  const header = s.compare
    ? `<h2>${escapeHtml(config)}</h2><div class="column-status">${
        result.status === "fulfilled" ? summary(result.value) : ""
      }</div>`
    : "";
  if (result.status === "rejected") {
    return `<section class="column">${header}<p class="column-status">Error: ${escapeHtml(
      result.reason.message
    )}</p></section>`;
  }
  const hits = result.value.hits;
  const first = (s.page - 1) * PAGE_SIZE + 1;
  const items = hits.length
    ? hits.map((h, i) => renderHit(h, first + i)).join("")
    : `<li class="column-status">No results.</li>`;
  return `<section class="column">${header}<ol class="results">${items}</ol></section>`;
}

function renderFacets(data, s) {
  renderFacet("facet-categories", "category", data ? data.categories : [], s.categories);
  renderFacet("facet-agencies", "agency", data ? data.agencies : [], s.agencies);
}

function renderFacet(listId, facet, buckets, selected) {
  // Selected values stay visible even when they are not among the top buckets of this query.
  const items = buckets.map((b) => ({ value: b.value, count: b.count }));
  for (const value of selected) {
    if (!items.some((i) => i.value === value)) items.unshift({ value, count: null });
  }
  $(listId).innerHTML = items.length
    ? items
        .map(
          (i) => `<li><label>
            <input type="checkbox" data-facet="${facet}" value="${escapeHtml(i.value)}"${
            selected.includes(i.value) ? " checked" : ""
          }>
            <span>${escapeHtml(i.value)}</span>
            <span class="count">${i.count == null ? "" : i.count}</span>
          </label></li>`
        )
        .join("")
    : `<li class="empty">none</li>`;
}

async function loadFacets(s) {
  // Facets depend on the query and the configuration's index, not on the filters or the page.
  const key = `${s.q}\u0000${s.config}`;
  if (app.facets.key === key) return app.facets.data;
  const data = await getJson(`/api/facets?${new URLSearchParams({ q: s.q, config: s.config })}`);
  app.facets = { key, data };
  return data;
}

async function runSearch(s) {
  const id = ++app.requestId;
  const configs = s.compare ? [s.config, s.config2] : [s.config];
  $("columns").className = s.compare ? "compare" : "";
  const facetsPromise = loadFacets(s).catch(() => null);

  if (!s.q) {
    $("status").textContent = "";
    $("columns").innerHTML = "";
    $("pager").hidden = true;
    const facets = await facetsPromise;
    if (id === app.requestId) renderFacets(facets, s);
    app.lastSearch = location.search;
    return;
  }

  $("status").textContent = "Searching...";
  const results = await Promise.allSettled(
    configs.map((c) => getJson(`/api/search?${apiParams(s, c)}`))
  );
  const facets = await facetsPromise;
  if (id !== app.requestId) return; // a newer search started meanwhile

  const ok = results.filter((r) => r.status === "fulfilled");
  if (s.compare) {
    $("status").textContent = `Comparing ${s.config} and ${s.config2}`;
  } else if (ok.length) {
    $("status").textContent = `${summary(ok[0].value)} (${s.config})`;
  } else {
    $("status").textContent = "";
  }
  $("columns").innerHTML = configs.map((c, i) => renderColumn(c, results[i], s)).join("");
  renderFacets(facets, s);

  // search() does not count all matches, so "next" is offered when some column filled the page.
  const full = ok.some((r) => r.value.hits.length === PAGE_SIZE);
  $("pager").hidden = !ok.length || (s.page === 1 && !full);
  $("prev").disabled = s.page <= 1;
  $("next").disabled = !full;
  $("page-label").textContent = `Page ${s.page}`;
  app.lastSearch = location.search;
}

// ---- document view ----------------------------------------------------------------------------

function wikipediaUrl(entity) {
  return `https://it.wikipedia.org/wiki/${encodeURIComponent(entity.replace(/ /g, "_"))}`;
}

function renderSource(src) {
  const title = src.title ? escapeHtml(src.title) : "(untitled)";
  const link = src.url ? `<a href="${escapeHtml(src.url)}" rel="noopener">${title}</a>` : title;
  const parts = [src.agency ? escapeHtml(src.agency) : null, link, src.date ? escapeHtml(src.date) : null];
  const foreign = src.foreign ? ` <span class="unpublished">foreign language</span>` : "";
  return `<li>${parts.filter(Boolean).join(" · ")}${foreign}</li>`;
}

function renderDoc(doc) {
  const unpublished = doc.published ? "" : ` <span class="unpublished">not published</span>`;
  const image = doc.image_url ? `<img src="${escapeHtml(doc.image_url)}" alt="">` : "";
  const tags = doc.categories.map((c) => `<span class="tag">${escapeHtml(c)}</span>`).join("");
  const sources = doc.sources.length
    ? `<h2>Sources</h2><ul>${doc.sources.map(renderSource).join("")}</ul>`
    : "";
  const entities = doc.entities.length
    ? `<h2>Linked Wikipedia entities</h2><ul>${doc.entities
        .map((e) => `<li><a href="${wikipediaUrl(e)}" rel="noopener">${escapeHtml(e)}</a></li>`)
        .join("")}</ul>`
    : "";
  return `${image}
    <h1>${escapeHtml(doc.title)}</h1>
    <div class="meta">${escapeHtml(doc.date || "no date")}${unpublished}</div>
    <div class="tags">${tags}</div>
    <div class="body">${escapeHtml(doc.body)}</div>
    ${sources}
    ${entities}
    <h2>Original page</h2>
    <p><a href="${escapeHtml(doc.url)}" rel="noopener">${escapeHtml(doc.url)}</a></p>`;
}

async function showDoc(id) {
  $("search-view").hidden = true;
  $("doc-view").hidden = false;
  $("back").href = location.pathname + location.search;
  $("doc").innerHTML = `<p class="unpublished">Loading...</p>`;
  window.scrollTo(0, 0);
  try {
    const doc = await getJson(`/api/doc/${encodeURIComponent(id)}`);
    document.title = `${doc.title} - Wikinews search`;
    $("doc").innerHTML = renderDoc(doc);
  } catch (err) {
    $("doc").innerHTML = `<p>Error: ${escapeHtml(err.message)}</p>`;
  }
}

// ---- events -----------------------------------------------------------------------------------

function onControlChange() {
  const s = formState();
  if (!s.q && !app.lastSearch) return;
  navigate(s);
}

$("search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  navigate(formState());
});

$("config").addEventListener("change", onControlChange);
$("config2").addEventListener("change", onControlChange);
$("compare").addEventListener("change", () => {
  if ($("compare").checked && $("config2").value === $("config").value) {
    $("config2").value = otherConfig($("config").value);
  }
  onControlChange();
});
for (const id of ["date-from", "date-to", "published"]) {
  $(id).addEventListener("change", onControlChange);
}
$("filters").addEventListener("change", (event) => {
  if (event.target.dataset.facet) onControlChange();
});
$("clear-filters").addEventListener("click", () => {
  navigate({ ...formState(), date_from: "", date_to: "", categories: [], agencies: [], published: false });
});

function goToPage(delta) {
  const s = readState();
  navigate({ ...s, page: Math.max(1, s.page + delta) });
  window.scrollTo(0, 0);
}
$("prev").addEventListener("click", () => goToPage(-1));
$("next").addEventListener("click", () => goToPage(1));

document.addEventListener("click", (event) => {
  // Remember that the document was opened from the results, so "back" can return to them.
  if (event.target.closest("a.title")) app.cameFromSearch = true;
});
$("back").addEventListener("click", (event) => {
  event.preventDefault();
  if (app.cameFromSearch) {
    history.back();
  } else {
    history.pushState(null, "", $("back").getAttribute("href"));
    route();
  }
});

window.addEventListener("popstate", route);
window.addEventListener("hashchange", route);

async function start() {
  try {
    const data = await getJson("/api/configs");
    app.defaultConfig = data.default;
    app.configNames = data.configs;
    const options = data.configs
      .map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`)
      .join("");
    $("config").innerHTML = options;
    $("config2").innerHTML = options;
  } catch (err) {
    $("status").textContent = `Error: ${err.message}`;
    return;
  }
  route();
}

start();
