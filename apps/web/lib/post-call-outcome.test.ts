import assert from "node:assert/strict";
import test from "node:test";

import type { PostCallOutcome } from "./api-client.ts";
import { callbackDisplay, outcomeDisplayState } from "./post-call-outcome.ts";

function outcome(overrides: Partial<PostCallOutcome> = {}): PostCallOutcome {
  return {
    id: "outcome-1",
    processing_status: "completed",
    processing_error: null,
    processed_at: null,
    label: "callback_requested",
    confidence: 0.9,
    rationale: "Callback requested.",
    summary: "Customer asked for a callback.",
    qualification_facts: { area: null, budget: null, property_type: null, intent: null, timeline: null },
    evidence: [],
    callback_original_phrase: "Kal shaam call karna",
    callback_timezone: "Asia/Kolkata",
    callback_at: null,
    terminal_reason: "qualification_complete",
    ...overrides,
  };
}

test("shows processing, failed, needs-review, and legacy states", () => {
  assert.equal(outcomeDisplayState("completed", outcome({ processing_status: "pending" })).label, "Analyzing call");
  assert.equal(outcomeDisplayState("completed", outcome({ processing_status: "failed" })).label, "Outcome unavailable");
  assert.equal(outcomeDisplayState("completed", outcome({ label: "needs_review" })).label, "Needs review");
  assert.equal(outcomeDisplayState("completed", null).label, "Outcome not available");
  assert.equal(outcomeDisplayState("connected", null).label, "Awaiting call completion");
});

test("ambiguous callback displays the phrase and never invents a time", () => {
  assert.equal(
    callbackDisplay(outcome()),
    "Kal shaam call karna · Time not specified · Asia/Kolkata",
  );
});

test("normalized callbacks render in the stored tenant timezone", () => {
  const callbackAt = "2026-07-21T11:30:00Z";
  const expected = new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Kolkata",
  }).format(new Date(callbackAt));
  assert.equal(
    callbackDisplay(outcome({ callback_at: callbackAt })),
    `Kal shaam call karna · ${expected} · Asia/Kolkata`,
  );
});
