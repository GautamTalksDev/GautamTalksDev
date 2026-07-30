<div align="center">

<img src="./assets/datasheet.svg" width="100%" alt="Datasheet — G. Khosla, Computer Engineering, University of Ottawa" />

<a href="https://www.linkedin.com/in/gautam-khosla/"><img src="https://img.shields.io/badge/LinkedIn-111111?style=flat-square&logo=linkedin&logoColor=f4f2ec" alt="LinkedIn"/></a>
<a href="http://www.youtube.com/@GautamKhoslaOfficial"><img src="https://img.shields.io/badge/YouTube-111111?style=flat-square&logo=youtube&logoColor=f4f2ec" alt="YouTube"/></a>
<a href="https://bio.site/gautamtalks"><img src="https://img.shields.io/badge/Links-111111?style=flat-square&logoColor=f4f2ec" alt="Links"/></a>
<a href="mailto:developwith.gt@gmail.com"><img src="https://img.shields.io/badge/Email-111111?style=flat-square&logo=maildotru&logoColor=f4f2ec" alt="Email"/></a>

</div>

<br/>

I build systems where the hard part is what happens when something fails — real-time scheduling guarantees, tenant isolation, human approval gates. Computer Engineering at the University of Ottawa, open to **backend / systems / infrastructure internships**.

<br/>

<div align="center">
<img src="./assets/status.svg" width="100%" alt="Live status panel, regenerated daily by GitHub Actions" />
</div>

<sub>Not a badge service. A scheduled Action queries the GitHub API each morning, renders this SVG, and commits it back to the repo — [`scripts/gen-status.mjs`](./scripts/gen-status.mjs)</sub>

---

## 01 · AEGIS

<sub>`C++20` · `QNX 8.0 RTOS` · `Raspberry Pi 5` · `TFLite` · [repo →](https://github.com/GautamTalksDev/AEGIS)</sub>

Deterministic edge-AI worksite safety system. Person and PPE detection run entirely on-device — the safety loop never touches the network. GPIO and relay fire at `SCHED_FIFO` priority 30; audio playback sits at priority 8, so I/O can never delay an alarm. Four QNX processes communicate over `MsgSend`/`MsgReceive` with trivially-copyable POD structs.

## 02 · HyperShift

<sub>`Next.js 14` · `Node` · `Turborepo` · `Postgres` · [repo →](https://github.com/GautamTalksDev/HyperShift) · [**live demo →**](https://hyper-shift-dashboard.vercel.app)</sub>

Describe infrastructure in plain English; five specialized agents plan, build, scan, deploy, and monitor it. Approval gates before anything ships, workspace isolation, immutable audit log, REST API and CLI.

## 03 · MetaShift

<sub>`Express` · `React` · `Supabase` · `PLpgSQL` · [repo →](https://github.com/GautamTalksDev/MetaShift)</sub>

Multi-tenant observability plane — conflict detection, auto-resolution, incident replay. Ten SQL migrations with tenant-scoped row-level security, usage metering, audit log, revocable API keys.

## 04 · Work-Shift

<sub>`Fastify` · `Cloudflare Workers` · `pnpm monorepo` · `Playwright` · [repo →](https://github.com/GautamTalksDev/Work-Shift)</sub>

AI approval inbox for Slack — nothing sends until a human approves it. Ships with `docs/AUTOMATION_REALITY.md`, which states plainly which parts are automated, which are human-in-the-loop, and which are demo-only.

## 05 · DSA

<sub>`Java` · [repo →](https://github.com/GautamTalksDev/DSA-Programming-Assignments)</sub>

Data structures and algorithms implemented through university coursework.

---

## Stack

**Systems** `C++20` `QNX` `Linux` `CMake` `TFLite` `OpenCV`
**Backend** `Node` `TypeScript` `Fastify` `Express` `Python` `Java`
**Data** `PostgreSQL` `Supabase` `MongoDB` `row-level security`
**Platform** `Docker` `Vercel` `Render` `Cloudflare Workers` `GitHub Actions`

---

<div align="center">
<img src="https://raw.githubusercontent.com/GautamTalksDev/GautamTalksDev/output/snake.svg" alt="Contribution graph, consumed" width="100%"/>
</div>
