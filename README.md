<p align="center">
  <img src="assets/banner.svg" width="100%" alt="Timing trace of the AEGIS alarm path. Worst observed 12.9 ms against a 20 ms deadline.">
</p>

<p align="center">
  <code>MLH Best Use of Snowflake API</code> ·
  <code>D3 Security Challenge, HackConcordia</code> ·
  <code>Top 9, Backboard.io x McHacks</code>
</p>

Computer Engineering at the University of Ottawa. I build systems that are defined by their failure case, not their happy path. Four of those failure cases, and what I did about each.

### An alarm that has to fire when the network is gone

`AEGIS` runs person and PPE detection on QNX 8.0 Neutrino on a Raspberry Pi 5, in C++20. The relay and GPIO fire on a `SCHED_FIFO` thread at priority 30. Offline WAV playback runs at priority 8, so audio I/O can never delay the alarm. The voice a worker hears was generated at build time and baked onto the device, because a safety alarm that needs an API call to speak is not a safety alarm.

Four QNX processes talk over `MsgSend` with trivially copyable POD structs. The banner above is that path, measured against a 20 ms deadline. Worst observed is 12.9 ms.

**[AEGIS](https://github.com/GautamTalksDev/AEGIS)** · C++20 · QNX Neutrino · TFLite · CMake cross compilation · cuHacking 7

### Fourteen upstream APIs, any of which can go down

`Chronos Cloud` ingests 14 live third party feeds across four domains over a NATS broker. Every one of them has a fallback path, so an upstream outage degrades the service instead of taking it down. Nothing acts on the world without a human approving it first. Technical lead of four, delivered in 36 hours.

**[Chronos Cloud](https://github.com/Rayyan0080/chronosccloud.tech)** · Python · NATS · Solace PubSub+ · MongoDB · MapLibre · uOttaHack 8

### Analytics that must never slow down the live read path

`AeroGuard` splits storage by access pattern instead of by convenience: live operational state in MongoDB, analytical processing in Snowflake, independent of each other, so a heavy query can never contend with a real time read. Triage output is confidence scored and fully audited, so an operator can see why the system said what it said. Shipped in 24 hours with a 7 test end to end suite. That storage split is what the Snowflake award was for.

**[AeroGuard](https://github.com/GautamTalksDev/aeroguard-tech)** · Python · FastAPI · MongoDB · Snowflake · WebSockets · HackConcordia

### A database that must never leak one tenant into another

`MetaShift` enforces isolation at the row, not in application code, using PostgreSQL row level security scoped to `tenant_id`. Application bugs cannot bypass it, because the check happens below the application. Every conflict it detects is replayable from the event stream.

**[MetaShift](https://github.com/GautamTalksDev/MetaShift)** · Node · Supabase · PostgreSQL RLS · WebSockets

---

Two more where the interesting decision was refusing to act:

**[Work-Shift](https://github.com/GautamTalksDev/Work-Shift)** queues AI drafts in Slack and sends nothing until a human clicks approve. The file worth reading is the one that makes approval idempotent, so a double click cannot double send. Fastify, Cloudflare Workers, Playwright.

**[HyperShift](https://github.com/GautamTalksDev/HyperShift)** turns plain English into infrastructure through five stages on a durable BullMQ pipeline. Policy checks and approval gates sit between plan and apply, so the system can refuse its own plan. Turborepo, shared Zod contracts across every service boundary.

`NeuroDesk` routes natural language intent to specialized agents behind budget limits and approval gates, on async FastAPI with Redis and SSE. `Omni Context OS` is a stateful RAG memory layer unifying context across Slack, email, and web.

---

**Systems** `C++20` `QNX Neutrino` `Linux` `CMake` `TFLite` `SCHED_FIFO`
**Backend** `TypeScript` `Node` `Fastify` `Express` `Python` `FastAPI` `Java`
**Messaging** `NATS` `Solace PubSub+` `BullMQ` `Redis` `WebSockets` `SSE`
**Data** `PostgreSQL` `row level security` `Prisma` `Supabase` `MongoDB Atlas` `Snowflake`
**Platform** `Docker` `Turborepo` `Cloudflare Workers` `GitHub Actions` `Render` `Vercel`

Open to backend, systems, and infrastructure internships.
[developwith.gt@gmail.com](mailto:developwith.gt@gmail.com) · [LinkedIn](https://www.linkedin.com/in/gautam-khosla/) · [YouTube](http://www.youtube.com/@GautamKhoslaOfficial)
