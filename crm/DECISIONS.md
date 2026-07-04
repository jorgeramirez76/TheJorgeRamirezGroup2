# JRG-CRM Decisions Log

This file records implementation deviations and decisions for the CRM.

## Locked baseline

- Source of truth: `crm/MASTER_BUILD_PLAN.md`.
- Implementing agents must not redesign decisions marked LOCKED in the master plan.
- If a requirement is impossible as specified, implement the closest working alternative and record the deviation here with date, what changed, and why.

## Decisions

- 2026-07-03 — Source root is `crm/src/` (not `crm/server/src/` as written in a few places in `MASTER_BUILD_PLAN.md`, e.g. §6.1/§7/§9). Phase 1 scaffolding (`package.json`, `tsconfig.json`, `tests/`) was already in place using `crm/src/...` before schema/API code was written, so that layout was kept as the single source root for the whole `crm/server` process rather than introducing a redundant nested `server/` folder. All future phases should keep placing code under `crm/src/<area>/` (e.g. `crm/src/channels/imessage.ts`, `crm/src/ai/`, `crm/src/video/`) instead of `crm/server/src/...`.
