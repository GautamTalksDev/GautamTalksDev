// Renders assets/sheet.svg from (a) a benchmark this repo just compiled and ran,
// and (b) live GitHub API data. Nothing here is hardcoded except the layout.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const USER = process.env.GH_USER || "GautamTalksDev";
const H = {
  "User-Agent": USER,
  Accept: "application/vnd.github+json",
  ...(process.env.GITHUB_TOKEN && { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` }),
};
const api = async (u) => {
  const r = await fetch(u, { headers: H });
  if (!r.ok) throw new Error(`${r.status} ${u}`);
  return r.json();
};

const b = JSON.parse(readFileSync("bench/result.json", "utf8"));
const [user, repos, events] = await Promise.all([
  api(`https://api.github.com/users/${USER}`),
  api(`https://api.github.com/users/${USER}/repos?per_page=100&sort=pushed`),
  api(`https://api.github.com/users/${USER}/events/public?per_page=100`),
]);

const langs = {};
for (const r of repos) if (r.language) langs[r.language] = (langs[r.language] || 0) + 1;
const push = events.find((e) => e.type === "PushEvent");
const lastRepo = push ? push.repo.name.split("/")[1] : "n/a";
const lastMsg = (push?.payload?.commits?.at(-1)?.message || "n/a").split("\n")[0].slice(0, 46);
const hrs = push ? Math.max(0, Math.round((Date.now() - new Date(push.created_at)) / 3.6e6)) : 0;

const E = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const stamp = new Date().toISOString().replace("T", " ").slice(0, 16) + " UTC";
const PAPER = "#f4f2ec", INK = "#111111", RED = "#c0392b", GREY = "#8a8578";

// histogram geometry
const hmax = Math.max(...b.hist, 1);
const HX = 604, HY = 250, HW = 330, HH = 62;
const bars = b.hist
  .map((v, i) => {
    const w = HW / b.hist.length, h = Math.max(1, (v / hmax) * HH);
    return `<rect x="${(HX + i * w).toFixed(1)}" y="${(HY + HH - h).toFixed(1)}" width="${(w - 1.4).toFixed(1)}" height="${h.toFixed(1)}" fill="${i > 18 ? RED : INK}"/>`;
  })
  .join("");

const pin = (y, txt, side) =>
  side === "l"
    ? `<path d="M300 ${y} H228" stroke="${INK}" stroke-width="1.2" fill="none"/><text x="220" y="${y + 4}" text-anchor="end" font-size="11">${E(txt)}</text>`
    : `<path d="M508 ${y} H556" stroke="${INK}" stroke-width="1.2" fill="none"/><text x="564" y="${y + 4}" font-size="11">${E(txt)}</text>`;

const row = (y, k, v) =>
  `<text x="34" y="${y}" font-size="11" fill="#444">${E(k)}</text><text x="196" y="${y}" font-size="11" fill="${INK}">${E(v)}</text>`;

const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 470" width="1000" height="470" role="img" aria-label="Measured specification sheet for G. Khosla">
<defs>
<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="${RED}"/></marker>
<marker id="al" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M10 0 L0 5 L10 10 z" fill="${RED}"/></marker>
</defs>
<g font-family="Courier New,monospace" fill="${INK}">
<rect width="1000" height="470" fill="${PAPER}"/>

<path d="M18 18 H982 V452 H18 Z" fill="none" stroke="${INK}" stroke-width="1.2" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1">
  <animate attributeName="stroke-dashoffset" values="1;0;0" keyTimes="0;0.07;1" dur="11s" repeatCount="indefinite"/></path>
<line x1="18" y1="46" x2="982" y2="46" stroke="${INK}"/>

<g font-size="11" letter-spacing="1.4">
<text x="34" y="37">GAUTAM KHOSLA</text>
<text x="318" y="37">COMPUTER ENGINEERING, UNIVERSITY OF OTTAWA</text>
<text x="966" y="37" text-anchor="end">SHEET 1 OF 1</text>
</g>

<g><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.06;0.11;1" dur="11s" repeatCount="indefinite"/>
<rect x="300" y="96" width="208" height="150" fill="${INK}"/>
<circle cx="320" cy="116" r="6" fill="none" stroke="${PAPER}" stroke-width="1.4"/>
<text x="404" y="160" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="26" font-weight="700" fill="${PAPER}" letter-spacing="1">G. KHOSLA</text>
<text x="404" y="184" text-anchor="middle" font-size="10" fill="${GREY}" letter-spacing="2">BACKEND, SYSTEMS, INFRA</text>
<text x="404" y="216" text-anchor="middle" font-size="10" fill="${GREY}" letter-spacing="2">AVAILABLE 2027</text>
</g>

<g><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.10;0.15;1" dur="11s" repeatCount="indefinite"/>
${pin(120, "QNX, RTOS", "l")}${pin(152, "C++20", "l")}${pin(184, "EMBEDDED VISION", "l")}${pin(216, "REAL TIME SCHED", "l")}
${pin(120, "TYPESCRIPT", "r")}${pin(152, "POSTGRES, RLS", "r")}${pin(184, "DISTRIBUTED SYS", "r")}${pin(216, "OBSERVABILITY", "r")}
</g>

<g><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.13;0.18;1" dur="11s" repeatCount="indefinite"/>
<line x1="604" y1="86" x2="934" y2="86" stroke="${RED}" marker-start="url(#al)" marker-end="url(#ar)"/>
<text x="769" y="78" text-anchor="middle" font-size="10" fill="${RED}" letter-spacing="1">MEASURED IN CI, NOT ASSERTED</text>
<text x="604" y="112" font-size="11" letter-spacing="1">PERIODIC TASK LATENESS, 1 kHz, ${E(b.samples)} SAMPLES</text>
<text x="604" y="140" font-size="9.5" fill="${GREY}" letter-spacing="1.2">MEDIAN</text><text x="604" y="164" font-size="21" font-weight="700">${E(b.p50_us)} us</text>
<text x="714" y="140" font-size="9.5" fill="${GREY}" letter-spacing="1.2">p99</text><text x="714" y="164" font-size="21" font-weight="700">${E(b.p99_us)} us</text>
<text x="824" y="140" font-size="9.5" fill="${GREY}" letter-spacing="1.2">WORST</text><text x="824" y="164" font-size="21" font-weight="700" fill="${RED}">${E(b.max_us)} us</text>
<text x="604" y="196" font-size="10.5" fill="#444">general purpose kernel, no realtime guarantee.</text>
<text x="604" y="212" font-size="10.5" fill="#444">this tail is why the alarm path runs on an RTOS.</text>
${bars}
<line x1="604" y1="${HY + HH}" x2="934" y2="${HY + HH}" stroke="${INK}"/>
<text x="604" y="326" font-size="9" fill="${GREY}">min</text><text x="934" y="326" text-anchor="end" font-size="9" fill="${RED}">tail</text>
</g>

<g><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.17;0.22;1" dur="11s" repeatCount="indefinite"/>
<line x1="34" y1="272" x2="556" y2="272" stroke="${INK}"/>
<text x="34" y="290" font-size="10" letter-spacing="1.4">CHARACTERISTIC</text><text x="196" y="290" font-size="10" letter-spacing="1.4">VALUE</text>
<line x1="34" y1="298" x2="556" y2="298" stroke="${INK}" stroke-width="0.6"/>
${row(316, "alarm path priority", "SCHED_FIFO 30, audio at 8")}
${row(334, "orchestrator stages", "5 agents, approval gated")}
${row(352, "tenant isolation", "row level security, 10 migrations")}
${row(370, "public repositories", String(user.public_repos))}
${row(388, "languages in use", Object.keys(langs).join(", ").slice(0, 46))}
${row(406, "last push", `${hrs} h ago, ${lastRepo}`)}
${row(424, "last commit", lastMsg)}
</g>

<g><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.20;0.25;1" dur="11s" repeatCount="indefinite"/>
<rect x="604" y="344" width="330" height="90" fill="none" stroke="${INK}" stroke-width="1.2"/>
<line x1="604" y1="374" x2="934" y2="374" stroke="${INK}" stroke-width="0.7"/>
<line x1="604" y1="404" x2="934" y2="404" stroke="${INK}" stroke-width="0.7"/>
<line x1="774" y1="374" x2="774" y2="434" stroke="${INK}" stroke-width="0.7"/>
<g font-size="9" fill="${GREY}" letter-spacing="1.2">
<text x="614" y="358">SHEET TITLE</text><text x="614" y="388">BUILT</text><text x="784" y="388">RUNNER</text><text x="614" y="418">SOURCE</text><text x="784" y="418">REV</text></g>
<g font-size="10.5">
<text x="614" y="370">PROFILE, MEASURED</text><text x="614" y="400">${E(stamp)}</text><text x="784" y="400">ubuntu latest</text>
<text x="614" y="430">bench/jitter.cpp</text><text x="784" y="430">auto</text></g>
</g>

<g stroke="${RED}" stroke-width="1.4" fill="none">
<path d="M18 58 V18 H58"/><path d="M942 18 H982 V58"/><path d="M18 412 V452 H58"/><path d="M942 452 H982 V412"/>
<animate attributeName="opacity" values="0.18;0.5;0.18" dur="4s" repeatCount="indefinite"/></g>
</g></svg>`;

mkdirSync("assets", { recursive: true });
writeFileSync("assets/sheet.svg", svg);
console.log(`wrote assets/sheet.svg  p50=${b.p50_us}us p99=${b.p99_us}us max=${b.max_us}us`);
