import assert from "node:assert/strict";
import test from "node:test";
import { resolvePostAuthDestination } from "./post-auth-destination.ts";

const session = (currentTaskKey?: string) => ({
  currentTask: currentTaskKey ? { key: currentTaskKey } : null,
  getToken: async () => "session-token",
});

test("routes a database-authorized platform identity to the platform", async () => {
  const destination = await resolvePostAuthDestination(
    session(),
    "/dashboard",
    async () => ({ role: "platform_operations" }),
  );

  assert.equal(destination, "/platform");
});

test("routes an organization-bearing identity to the tenant destination", async () => {
  const destination = await resolvePostAuthDestination(
    session(),
    "/dashboard",
    async () => {
      throw new Error("platform_identity_has_active_organization");
    },
  );

  assert.equal(destination, "/dashboard");
});

test("routes an unprovisioned personal identity to workspace setup", async () => {
  const destination = await resolvePostAuthDestination(
    session("choose-organization"),
    "/dashboard",
    async () => {
      throw new Error("platform_access_not_provisioned");
    },
  );

  assert.equal(destination, "/workspace/setup");
});

test("keeps an inactive platform identity out of tenant workspace setup", async () => {
  const destination = await resolvePostAuthDestination(
    session(),
    "/dashboard",
    async () => {
      throw new Error("platform_identity_inactive");
    },
  );

  assert.equal(destination, "/platform");
});

test("rethrows an unexpected platform lookup failure", async () => {
  await assert.rejects(
    resolvePostAuthDestination(session(), "/dashboard", async () => {
      throw new Error("identity_store_unavailable");
    }),
    /identity_store_unavailable/,
  );
});
