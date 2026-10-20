import assert from "node:assert/strict";
import test from "node:test";

import { sourceFreshness } from "../src/lib/sourceFreshness.js";

const NOW = Date.parse("2026-10-25T13:05:36-03:00");
const DAY_MS = 86_400_000;
const isoAgo = (milliseconds) => new Date(NOW - milliseconds).toISOString();
const source = (unchangedSince, lastRead = isoAgo(0)) => ({
  last_success_at: lastRead,
  stock_unchanged_since: unchangedSince,
});

test("warns at 120 hours without a stock change even when reads remain successful", () => {
  const since = isoAgo(5 * DAY_MS);
  assert.equal(sourceFreshness(source(since, isoAgo(60_000)), NOW - 1).status, "current");
  const result = sourceFreshness(source(since), NOW);
  assert.equal(result.status, "stale");
  assert.equal(result.reason, "unchanged");
  assert.equal(result.days, 5);
  assert.match(result.label, /sin cambios detectados.*5 días/);
});

test("uses elapsed hours and timezone offsets across the five-day boundary", () => {
  const since = "2026-10-20T16:05:36Z";
  const freshRead = "2026-10-25T16:00:00Z";
  assert.equal(sourceFreshness(source(since, freshRead), NOW - 60_000).status, "current");
  assert.equal(sourceFreshness(source(since, freshRead), NOW).reason, "unchanged");
});

test("an old successful read does not replace the age of unchanged stock", () => {
  const result = sourceFreshness(source(isoAgo(8 * DAY_MS), isoAgo(6 * DAY_MS)), NOW);
  assert.equal(result.status, "stale");
  assert.equal(result.reason, "unchanged");
  assert.equal(result.days, 8);
  assert.match(result.label, /sin cambios detectados.*8 días/);
  assert.equal(result.lastReadAt, isoAgo(6 * DAY_MS));
});

test("an old read alone never alerts, including after a recent failed attempt", () => {
  for (const baseline of [isoAgo(DAY_MS), undefined]) {
    const result = sourceFreshness({
      ...source(baseline, isoAgo(5 * DAY_MS)),
      last_attempt_at: isoAgo(0),
      status: "error",
    }, NOW);
    assert.notEqual(result.status, "stale");
    assert.equal(result.reason, "");
    assert.equal(result.days, null);
    assert.equal(result.label, "");
    assert.equal(result.lastReadAt, isoAgo(5 * DAY_MS));
  }
});

test("missing tracking in older payloads remains unknown without inventing a change date", () => {
  const result = sourceFreshness({ last_success_at: isoAgo(0) }, NOW);
  assert.equal(result.status, "untracked");
  assert.equal(result.unchangedSince, "");
  assert.equal(result.label, "");
  const legacy = sourceFreshness({ last_success_at: isoAgo(7 * DAY_MS) }, NOW);
  assert.equal(legacy.status, "untracked");
  assert.equal(legacy.reason, "");
  assert.equal(legacy.label, "");
  assert.equal(legacy.days, null);
  assert.equal(legacy.lastReadAt, isoAgo(7 * DAY_MS));
});

test("missing, invalid and future dates do not create false alarms or render invalid dates", () => {
  for (const date of [undefined, "", "not-a-date", isoAgo(-DAY_MS)]) {
    const result = sourceFreshness({ last_success_at: date, stock_unchanged_since: date }, NOW);
    assert.equal(result.status, "unverified");
    assert.equal(result.label, "");
    assert.equal(result.lastReadAt, "");
    assert.equal(result.unchangedSince, "");
  }
  assert.equal(sourceFreshness(null, NOW).status, "unverified");
  assert.equal(sourceFreshness(source(isoAgo(0)), NaN).status, "unverified");
  assert.equal(sourceFreshness(source(isoAgo(0)), Infinity).status, "unverified");
});

test("one source cannot refresh another source's alarm", () => {
  const sources = [source(isoAgo(6 * DAY_MS)), source(isoAgo(DAY_MS))];
  assert.deepEqual(sources.map((item) => sourceFreshness(item, NOW).status), ["stale", "current"]);
});
