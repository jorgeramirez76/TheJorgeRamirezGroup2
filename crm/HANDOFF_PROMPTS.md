# JRG-CRM Handoff Prompts

Use one prompt per implementation session. Every implementing model must read `crm/MASTER_BUILD_PLAN.md` and `crm/DECISIONS.md` first. Do not start the next phase in the same session. For implementation phases, follow §14: finish acceptance criteria, run tests, commit with `crm phase N: <what>`, and push to the working branch.

## Universal session instruction

```text
You are implementing JRG-CRM in repo `TheJorgeRamirezGroup2`, under `crm/`.
Read `crm/MASTER_BUILD_PLAN.md` and `crm/DECISIONS.md` fully before changing code. Follow LOCKED decisions exactly. Implement only the requested phase. Keep `.env`, `crm.db`, and backups out of git. Add/update tests for core logic. Before finishing, run the phase verification commands, commit with `crm phase N: <what>`, push to the working branch, and summarize: what shipped, how to test it, and what Jorge must do manually before the next phase. Record any deviation in `crm/DECISIONS.md`.
```

## Phase 1 — Skeleton + DB + Inbox core

```text
Implement Phase 1 from `crm/MASTER_BUILD_PLAN.md`: scaffold `crm/`, TypeScript Fastify server, SQLite/Drizzle schema + migrations, contacts/leads/messages CRUD API, seed script, Vitest setup, `.env.example`, and baseline docs. Acceptance: `npm run dev` boots, API CRUD round-trips, and tests are green. Stop after Phase 1.
```

## Phase 2 — iMessage channel

```text
Implement Phase 2 from `crm/MASTER_BUILD_PLAN.md`: BlueBubbles iMessage driver, webhook inbound normalization, send gate, quiet hours, suppressions, health check, and launchd plist/docs. Acceptance: loopback test vs mock BlueBubbles, STOP flow, and dedupe proven. Stop after Phase 2.
```

## Phase 3 — Gmail channel

```text
Implement Phase 3 from `crm/MASTER_BUILD_PLAN.md`: Gmail OAuth CLI, poller, threaded sends, open pixel, and bulk throttling. Acceptance: mock tests pass and real-account smoke-test instructions are documented. Stop after Phase 3.
```

## Phase 4 — AI engine + knowledge base

```text
Implement Phase 4 from `crm/MASTER_BUILD_PLAN.md`: Haiku classifier, Sonnet composer, persona builder script, KB extraction from town data, context assembler, autonomy gates, escalation, and token logging. Acceptance: golden transcript tests produce sane drafts; opt-out precedes AI. Stop after Phase 4.
```

## Phase 5 — Workflow engine + Lazy Agent templates

```text
Implement Phase 5 from `crm/MASTER_BUILD_PLAN.md`: workflow DSL executor, enrollments, waits, branches, all 12 seeded workflows, and scoring engine. Acceptance: simulated clock tests show New Buyer sequence executes, replies exit drip, and HOT escalates. Stop after Phase 5.
```

## Phase 6 — Website wiring + tracking

```text
Implement Phase 6 from `crm/MASTER_BUILD_PLAN.md`: site-lead webhook, tracker.js + identity stitch, form wiring to `/api/lead`, CSV import, and Cloudflare Tunnel docs. Acceptance: test harness form submit creates/merges contact and queues first touch in under 60 seconds subject to send gate. Stop after Phase 6.
```

## Phase 7 — Higgsfield video pipeline

```text
Implement Phase 7 from `crm/MASTER_BUILD_PLAN.md`: video provider interface, Higgsfield driver, script generation, poll worker, landing-page hosting, delivery, and post-video workflow. Acceptance: mocked render e2e goes trigger → script → ready → landing page exists → iMessage queued. Stop after Phase 7.
```

## Phase 8 — Dashboard

```text
Implement Phase 8 from `crm/MASTER_BUILD_PLAN.md`: Mission Control React/Vite dashboard pages, SSE, approval queue, reports, settings, and mobile-friendly styling. Acceptance: approve-edit-send loop works, kanban drag persists, and reports query real data. Stop after Phase 8.
```

## Phase 9 — Hardening + go-live

```text
Implement Phase 9 from `crm/MASTER_BUILD_PLAN.md`: backups, log rotation, error alerting, SETUP.md walkthrough, and end-to-end dry run procedure with Jorge's real accounts in approval mode. Acceptance: full pipeline demo on a test lead using Jorge's own second number. Stop after Phase 9.
```
