import * as schema from '../db/schema.js';
import type { CrmDb } from '../db/client.js';
import { getSettings, upsertSetting } from '../settings/store.js';
import type { BlueBubblesChannel } from './bluebubbles.js';

export type ImessageHealth = { ok: boolean; lastCheckedAt: string; lastError: string | null; downSince: string | null };

/**
 * Persists the ping result to settings.imessage_health (consumed by the send gate to hold
 * iMessage sends, and by the dashboard channel-health light). Writes one audit_log alert on
 * the transition into "down" so repeated failed pings don't spam the log.
 */
export function recordHealthCheck(db: CrmDb, ok: boolean, error?: string): ImessageHealth {
  const now = new Date().toISOString();
  const previous = getSettings(db).imessage_health as ImessageHealth | undefined;
  const wasDown = previous?.ok === false;
  const health: ImessageHealth = {
    ok,
    lastCheckedAt: now,
    lastError: ok ? null : (error ?? 'BlueBubbles ping failed'),
    downSince: ok ? null : (wasDown ? previous!.downSince : now)
  };
  upsertSetting(db, 'imessage_health', health);

  if (!ok && !wasDown) {
    // TODO(jorge-verify): Phase 3 adds Gmail send — wire an email alert here once it exists.
    // Until then this audit_log row + settings.imessage_health is what the dashboard banner reads.
    db.insert(schema.auditLog).values({
      actor: 'system', action: 'alert', entity: 'channel', entityId: 'imessage',
      detail: { message: 'BlueBubbles health check failed — iMessage sends are paused until recovery.', ...health }
    }).run();
  }

  return health;
}

export function startBlueBubblesHealthCheck(db: CrmDb, channel: BlueBubblesChannel, opts: { intervalMs?: number } = {}) {
  const intervalMs = opts.intervalMs ?? 5 * 60_000;
  const timer = setInterval(() => {
    channel.ping()
      .then((ok) => recordHealthCheck(db, ok))
      .catch((err) => recordHealthCheck(db, false, err instanceof Error ? err.message : String(err)));
  }, intervalMs);
  timer.unref?.();
  return () => clearInterval(timer);
}
