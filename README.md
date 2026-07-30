<div align="center">

<img src="./assets/datasheet.svg" width="100%" alt="Datasheet — G. Khosla, Computer Engineering, University of Ottawa" />

<a href="https://www.linkedin.com/in/gautam-khosla/"><img src="https://img.shields.io/badge/LinkedIn-111111?style=flat-square&logo=linkedin&logoColor=f4f2ec" alt="LinkedIn"/></a>
<a href="http://www.youtube.com/@GautamKhoslaOfficial"><img src="https://img.shields.io/badge/YouTube-111111?style=flat-square&logo=youtube&logoColor=f4f2ec" alt="YouTube"/></a>
<a href="https://bio.site/gautamtalks"><img src="https://img.shields.io/badge/Links-111111?style=flat-square&logoColor=f4f2ec" alt="Links"/></a>
<a href="mailto:developwith.gt@gmail.com"><img src="https://img.shields.io/badge/Email-111111?style=flat-square&logo=maildotru&logoColor=f4f2ec" alt="Email"/></a>

</div>

<br/>

Computer Engineering at the University of Ottawa. Most of what I build is defined by its failure case rather than its happy path — an alarm that has to fire whether or not the network is up, a deploy pipeline that refuses to ship without a human signature, a database that must not leak one tenant's rows into another's.

Open to **backend / systems / infrastructure internships**.

<br/>

<div align="center">
<img src="./assets/status.svg" width="100%" alt="Live status panel, regenerated daily by GitHub Actions" />
</div>

<sub>Not a badge service. A scheduled Action queries the GitHub API each morning, renders this SVG, and commits it back to the repo — [`scripts/gen-status.mjs`](./scripts/gen-status.mjs)</sub>

---

## 01 · AEGIS

<sub>`C++20` · `QNX 8.0 RTOS` · `Raspberry Pi 5` · `TFLite` · [repo →](https://github.com/GautamTalksDev/AEGIS)</sub>

Worksite safety system that detects missing PPE and fires an alarm — entirely on-device, because a safety alarm that needs an API call to speak isn't a safety alarm.

GPIO and relay run at `SCHED_FIFO` priority 30; voice playback sits at priority 8, so audio I/O can never delay the alarm. Four QNX processes pass trivially-copyable POD structs over `MsgSend`/`MsgReceive`. The cloud makes the device smarter; it never makes it dependent.

## 02 · HyperShift

<sub>`Next.js 14` · `Node` · `Turborepo` · `Postgres` · [repo →](https://github.com/GautamTalksDev/HyperShift) · [**live demo →**](https://hyper-shift-dashboard.vercel.app)</sub>

Describe infrastructure in plain English and five specialized agents take it from there — plan, build, scan, deploy, monitor.

Every run is workspace-scoped, metered, and written to an immutable audit log. Nothing reaches production without passing an approval gate. REST API and CLI alongside the dashboard.

## 03 · MetaShift

<sub>`Express` · `React` · `Supabase` · `PLpgSQL` · [repo →](https://github.com/GautamTalksDev/MetaShift)</sub>

Multi-tenant observability plane: detects conflicts across distributed services, resolves what it can automatically, and lets you replay any incident from the event stream.

Ten SQL migrations building up tenant-scoped row-level security, usage metering, an append-only audit log, and revocable API keys.

## 04 · Work-Shift

<sub>`Fastify` · `Cloudflare Workers` · `pnpm monorepo` · `Playwright` · [repo →](https://github.com/GautamTalksDev/Work-Shift)</sub>

An approval inbox for AI-drafted Slack messages. Drafts queue up; nothing sends until a human clicks approve.

Ships with `docs/AUTOMATION_REALITY.md`, which labels every feature as fully automated, human-in-the-loop, or demo-only — because the useful thing to document is what *doesn't* work yet.

## 05 · DSA

<sub>`Java` · [repo →](https://github.com/GautamTalksDev/DSA-Programming-Assignments)</sub>

Data structures and algorithms, implemented from scratch through university coursework.

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
