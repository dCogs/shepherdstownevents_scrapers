// export-analytics.mjs
const APP_ID    = "6934372591c2b97e6a5825e8";
const API_TOKEN = "e316a24b3f284a85968a4e948bf01586";
const BASE      = "https://app.base44.com";

const START = "2026-08-01T00:00:00Z";
const END   = "2026-09-01T00:00:00Z";

const OUT_FILE = `analytics_${START.slice(0,10)}_to_${END.slice(0,10)}.csv`;
const PAGE_LIMIT = 500;

const headers = {
  "api_key": API_TOKEN,
  "Content-Type": "application/json",
};

async function listEventNames() {
  const res = await fetch(`${BASE}/api/apps/${APP_ID}/analytics/names`, { headers });
  if (!res.ok) throw new Error(`names failed: ${res.status} ${await res.text()}`);
  return res.json();
}

async function queryAll(eventName) {
  const rows = [];
  let offset = 0;
  let hasMore = true;
  const q = { event_name: eventName, timestamp: { gte: START, lt: END } };
  while (hasMore) {
    const body = { q, limit: PAGE_LIMIT, offset };
    const res = await fetch(`${BASE}/api/apps/${APP_ID}/analytics/query`, {
      method: "POST", headers, body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`query failed: ${res.status} ${await res.text()}`);
    const data = await res.json();
    const page = Array.isArray(data.events) ? data.events
               : Array.isArray(data.results) ? data.results
               : Array.isArray(data.data) ? data.data : [];
    rows.push(...page);
    hasMore = !!data.has_more;
    offset = data.next_offset ?? (offset + page.length);
  }
  return rows;
}

function flatten(ev) {
  const out = {
    event_id: ev.event_id ?? ev.id ?? "",
    event_name: ev.event_name ?? "",
    timestamp: ev.timestamp ?? "",
    user_id: ev.user_id ?? "",
    session_id: ev.session_id ?? "",
    page_url: ev.page_url ?? "",
  };
  for (const [k, v] of Object.entries(ev.properties ?? {})) out[`prop_${k}`] = v;
  for (const [k, v] of Object.entries(ev.metadata ?? {}))   out[`meta_${k}`] = v;
  return out;
}

function toCsv(rows) {
  const keys = [...new Set(rows.flatMap(r => Object.keys(r)))];
  const esc = v => {
    if (v == null) return "";
    const s = typeof v === "object" ? JSON.stringify(v) : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [keys.join(","), ...rows.map(r => keys.map(k => esc(r[k])).join(","))].join("\n");
}

async function main() {
  let names;
  try { names = await listEventNames(); } catch (e) {
    console.warn("Could not list names:", e.message);
    names = null;
  }
  const allRows = [];
  if (Array.isArray(names) && names.length) {
    for (const name of names) allRows.push(...await queryAll(name));
  } else {
    allRows.push(...await queryAll(null));
  }
  const { writeFileSync } = await import("node:fs");
  writeFileSync(OUT_FILE, toCsv(allRows.map(flatten)));
  console.log(`Wrote ${allRows.length} events to ${OUT_FILE}`);
}

main().catch(e => { console.error(e); process.exit(1); });
