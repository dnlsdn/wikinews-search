// Web interface (owner: Fabio). Plain JavaScript, no build step.
// Step F3a: search box, configuration selector, result list. Filters, pagination, document view
// and compare mode come in step F3b.

const $ = (id) => document.getElementById(id);

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

async function loadConfigs() {
  const data = await getJson("/api/configs");
  $("config").innerHTML = data.configs
    .map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`)
    .join("");
  $("config").value = data.default;
}

function renderHit(hit) {
  const image = hit.image_url ? `<img src="${escapeHtml(hit.image_url)}" alt="">` : "";
  const meta = [hit.date || "no date", hit.agencies.join(", ")].filter(Boolean).join(" · ");
  const tags = hit.categories.map((c) => `<span class="tag">${escapeHtml(c)}</span>`).join("");
  const unpublished = hit.published ? "" : ` <span class="unpublished">not published</span>`;
  // The snippet comes from the API with <em> highlight tags and is inserted as HTML.
  return `<li class="hit">${image}<div>
    <a class="title" href="${escapeHtml(hit.url)}">${escapeHtml(hit.title)}</a>${unpublished}
    <div class="meta">${escapeHtml(meta)}</div>
    <div class="snippet">${hit.snippet || ""}</div>
    <div class="tags">${tags}</div>
  </div></li>`;
}

async function runSearch(event) {
  if (event) event.preventDefault();
  const q = $("q").value.trim();
  if (!q) return;
  const params = new URLSearchParams({ q, config: $("config").value });
  $("status").textContent = "Searching...";
  try {
    const data = await getJson(`/api/search?${params}`);
    $("status").textContent = `${data.total} results in ${data.took_ms} ms (${data.config})`;
    $("results").innerHTML = data.hits.map(renderHit).join("");
  } catch (err) {
    $("status").textContent = `Error: ${err.message}`;
    $("results").innerHTML = "";
  }
}

$("search-form").addEventListener("submit", runSearch);
loadConfigs().catch((err) => {
  $("status").textContent = `Error: ${err.message}`;
});
