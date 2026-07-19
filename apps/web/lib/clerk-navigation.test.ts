import assert from "node:assert/strict";
import test from "node:test";
import { navigateWithClerk, postAuthDestination } from "./clerk-navigation.ts";

test("routes the choose-organization task to workspace setup", () => {
  assert.equal(
    postAuthDestination("choose-organization", "/dashboard"),
    "/workspace/setup",
  );
});

test("keeps the requested destination when no organization task is pending", () => {
  assert.equal(postAuthDestination(null, "/platform"), "/platform");
});

test("uses client navigation for a relative Clerk-decorated URL", () => {
  const calls: string[] = [];

  navigateWithClerk(
    "/dashboard?__clerk_synced=true",
    (url) => calls.push(`router:${url}`),
    { assign: (url) => calls.push(`location:${url}`) },
  );

  assert.deepEqual(calls, ["router:/dashboard?__clerk_synced=true"]);
});

test("uses a full navigation for Clerk's external cookie handoff", () => {
  const calls: string[] = [];

  navigateWithClerk(
    "https://clerk.example/itp?redirect_url=%2Fdashboard",
    (url) => calls.push(`router:${url}`),
    { assign: (url) => calls.push(`location:${url}`) },
  );

  assert.deepEqual(calls, [
    "location:https://clerk.example/itp?redirect_url=%2Fdashboard",
  ]);
});
