# JRG-CRM Decisions Log

This file records implementation deviations and decisions for the CRM.

## Locked baseline

- Source of truth: `crm/MASTER_BUILD_PLAN.md`.
- Implementing agents must not redesign decisions marked LOCKED in the master plan.
- If a requirement is impossible as specified, implement the closest working alternative and record the deviation here with date, what changed, and why.

## Decisions

- 2026-07-03 — Source root is `crm/src/` (not `crm/server/src/` as written in a few places in `MASTER_BUILD_PLAN.md`, e.g. §6.1/§7/§9). Phase 1 scaffolding (`package.json`, `tsconfig.json`, `tests/`) was already in place using `crm/src/...` before schema/API code was written, so that layout was kept as the single source root for the whole `crm/server` process rather than introducing a redundant nested `server/` folder. All future phases should keep placing code under `crm/src/<area>/` (e.g. `crm/src/channels/imessage.ts`, `crm/src/ai/`, `crm/src/video/`) instead of `crm/server/src/...`.

- 2026-07-03 — Phase 2 (iMessage/BlueBubbles): the driver lives at `crm/src/channels/bluebubbles.ts` (not `imessage.ts` as named in §6.1) since it's specifically the BlueBubbles implementation of the `Channel` interface (`crm/src/channels/types.ts`) — a future `imessage-applescript` fallback driver (§6.1) would also implement `Channel` and could reasonably own the `imessage.ts` name once it exists.

- 2026-07-03 — `BLUEBUBBLES_WEBHOOK_SECRET` (in `.env.example`) is reserved but not enforced by `/webhooks/bluebubbles`. BlueBubbles has no built-in mechanism to sign or authenticate its outgoing webhook requests (no shared-secret header/param it will attach), and the endpoint is architecturally localhost-only (`CRM_HOST=127.0.0.1`, no tunnel path exposes it per §4/§10). If BlueBubbles ever runs on a separate host, revisit this — e.g. an nginx/Caddy reverse proxy in front that injects/checks the secret.

- 2026-07-03 — The send gate's "per-lead daily cap" (§6.3, §12) is implemented per **contact**, not per lead row. `messages` keys off `contact_id`, not `lead_id` (a contact can have both a buyer and seller lead), so the cap counts a contact's total outbound messages/day across all their leads and channels — the practical equivalent given the schema, and the safer reading of the compliance intent (don't over-text a person, regardless of how many pipeline entries they have).

- 2026-07-03 — Quiet-hours "next allowed window" math (`crm/src/sendgate/quiet-hours.ts`) computes the target-timezone UTC offset at the current instant and assumes it holds through the next occurrence of the window start. This is exact except on the ~2 days/year a DST transition falls between `now` and that next start, where it can be off by up to an hour — acceptable for v1; revisit with a proper tz library (e.g. `@js-temporal` or `date-fns-tz`) if that edge case ever matters in practice.

- 2026-07-03 — The STOP/opt-out confirmation (`crm/src/sendgate/optout.ts`) is inserted as a `messages` row with `status: 'queued'`, not actually dispatched through the `Channel`. There is no outbound dispatch/worker loop yet (that arrives with the workflow engine in Phase 5) — Phase 2's job is to prove the confirmation is queued exactly once per opt-out, which the tests do. Whatever picks up `queued` messages later must send this row through the normal send gate like any other outbound message.
