export const SOURCE_STALE_AFTER_DAYS = 5;
const DAY_MS = 24 * 60 * 60 * 1000;
const STALE_AFTER_MS = SOURCE_STALE_AFTER_DAYS * DAY_MS;

function observedTimestamp(value, now) {
  if (!Number.isFinite(now) || typeof value !== "string" || !value.trim()) return null;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) && timestamp <= now ? timestamp : null;
}

export function sourceFreshness(source, now = Date.now()) {
  const details = source && typeof source === "object" ? source : {};
  const current = Number(now);
  const lastRead = observedTimestamp(details.last_success_at, current);
  const unchanged = observedTimestamp(details.stock_unchanged_since, current);
  const state = {
    status: lastRead === null ? "unverified" : unchanged === null ? "untracked" : "current",
    reason: "",
    days: null,
    label: "",
    lastReadAt: lastRead === null ? "" : details.last_success_at,
    unchangedSince: unchanged === null ? "" : details.stock_unchanged_since,
  };

  if (unchanged !== null && current - unchanged >= STALE_AFTER_MS) {
    const days = Math.floor((current - unchanged) / DAY_MS);
    return { ...state, status: "stale", reason: "unchanged", days, label: `Stock sin cambios detectados desde hace ${days} días.` };
  }
  return state;
}
