function zonedParts(tz: string, at: Date) {
  const fmt = new Intl.DateTimeFormat('en-US', {
    timeZone: tz, hour12: false,
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
  const parts = Object.fromEntries(fmt.formatToParts(at).map((p) => [p.type, p.value])) as Record<string, string>;
  return { year: Number(parts.year), month: Number(parts.month), day: Number(parts.day), hour: Number(parts.hour === '24' ? '0' : parts.hour), minute: Number(parts.minute), second: Number(parts.second) };
}

// Offset (ms) to ADD to a UTC instant to get that instant's wall-clock time in `tz`.
function zoneOffsetMs(tz: string, at: Date): number {
  const p = zonedParts(tz, at);
  const asUtc = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  return asUtc - at.getTime();
}

function minutesOfDay(hh: number, mm: number) {
  return hh * 60 + mm;
}

function parseHHMM(value: string) {
  const [hh, mm] = value.split(':').map(Number);
  return { hh, mm };
}

export type QuietHoursWindow = { timezone: string; start: string; end: string };

export function isWithinQuietHoursWindow(window: QuietHoursWindow, at: Date): boolean {
  const local = zonedParts(window.timezone, at);
  const nowMinutes = minutesOfDay(local.hour, local.minute);
  const start = parseHHMM(window.start);
  const end = parseHHMM(window.end);
  return nowMinutes >= minutesOfDay(start.hh, start.mm) && nowMinutes < minutesOfDay(end.hh, end.mm);
}

/** Next UTC instant at which the local wall clock in `window.timezone` reaches `window.start`. */
export function nextQuietHoursStart(window: QuietHoursWindow, at: Date): Date {
  const offsetMs = zoneOffsetMs(window.timezone, at);
  const local = zonedParts(window.timezone, at);
  const start = parseHHMM(window.start);
  let candidateUtcMs = Date.UTC(local.year, local.month - 1, local.day, start.hh, start.mm, 0) - offsetMs;
  if (candidateUtcMs <= at.getTime()) {
    candidateUtcMs = Date.UTC(local.year, local.month - 1, local.day + 1, start.hh, start.mm, 0) - offsetMs;
  }
  return new Date(candidateUtcMs);
}
