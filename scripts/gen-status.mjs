// Generates assets/status.svg from live GitHub API data. Run by .github/workflows/status.yml
import { writeFileSync, mkdirSync } from "node:fs";

const USER = process.env.GH_USER || "GautamTalksDev";
const H = { "User-Agent": USER, Accept: "application/vnd.github+json",
            ...(process.env.GITHUB_TOKEN && { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` }) };

const j = async (u) => { const r = await fetch(u, { headers: H });
  if (!r.ok) throw new Error(`${r.status} ${u}`); return r.json(); };

const user  = await j(`https://api.github.com/users/${USER}`);
const repos = await j(`https://api.github.com/users/${USER}/repos?per_page=100&sort=pushed`);
const ev    = await j(`https://api.github.com/users/${USER}/events/public?per_page=100`);

const langs = {};
for (const r of repos) if (r.language) langs[r.language] = (langs[r.language] || 0) + 1;
const topLangs = Object.entries(langs).sort((a, b) => b[1] - a[1]).slice(0, 4);

const push = ev.find((e) => e.type === "PushEvent");
const msg = (push?.payload?.commits?.at(-1)?.message || "—").split("\n")[0].slice(0, 52);
const where = push ? push.repo.name.split("/")[1] : "—";
const since = push ? Math.max(0, Math.round((Date.now() - new Date(push.created_at)) / 3.6e6)) : null;

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const built = new Date().toISOString().replace("T", " ").slice(0, 16) + " UTC";

const stat = (x, label, value, accent) => `
  <text x="${x}" y="62" font-size="11" fill="#6b665c" letter-spacing="1.2">${esc(label)}</text>
  <text x="${x}" y="98" font-size="30" font-weight="700" fill="${accent}">${esc(value)}</text>`;

const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 210" width="1000" height="210" role="img" aria-label="Live status panel">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0%" stop-color="#f4f2ec"/><stop offset="100%" stop-color="#eeebe2"/></linearGradient>
<clipPath id="c"><rect width="1000" height="210" rx="14"/></clipPath></defs>
<g clip-path="url(#c)" font-family="Courier New,monospace">
<rect width="1000" height="210" fill="url(#g)"/>
<text x="34" y="34" font-size="12" fill="#8a8578" letter-spacing="2">LIVE SYSTEM STATUS</text>
<circle cx="196" cy="30" r="4" fill="#c0392b"><animate attributeName="opacity" values="1;0.2;1" dur="2s" repeatCount="indefinite"/></circle>
<text x="966" y="34" text-anchor="end" font-size="11" fill="#8a8578">rebuilt ${esc(built)}</text>
<line x1="34" y1="46" x2="966" y2="46" stroke="#111111"/>
${stat(34,  "PUBLIC REPOS",  user.public_repos,                    "#c0392b")}
${stat(234, "LANGUAGES",     Object.keys(langs).length,            "#111111")}
${stat(414, "LAST PUSH",     since === null ? "—" : since + "h",   "#c0392b")}
${stat(594, "FOLLOWING",     user.following,                       "#111111")}
${stat(774, "STACK",         topLangs.map(([l]) => l[0]).join(""), "#111111")}
<line x1="34" y1="126" x2="966" y2="126" stroke="#111111"/>
<text x="34" y="154" font-size="13" fill="#6b665c">last commit <tspan fill="#c0392b">${esc(where)}</tspan></text>
<text x="34" y="176" font-size="13" fill="#333333">"${esc(msg)}"</text>
<text x="966" y="176" text-anchor="end" font-size="12" fill="#8a8578">${topLangs.map(([l, n]) => `${l.toLowerCase()}:${n}`).join("  ")}</text>
<rect x="0.5" y="0.5" width="999" height="209" rx="14" fill="none" stroke="#111111"/>
</g></svg>`;

mkdirSync("assets", { recursive: true });
writeFileSync("assets/status.svg", svg);
console.log("wrote assets/status.svg");
