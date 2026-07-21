import { expect, test } from "@playwright/test";
import { setupClerkTestingToken } from "@clerk/testing/playwright";

const testEmail = `ringiq-e2e-${Date.now()}+clerk_test@example.com`;
const testPassword = "RingIQ-E2E-Password-2026!";
const clerkTestCode = "424242";

test.describe.serial("Clerk verification handoff", () => {
  test.beforeEach(async ({ context }) => {
    await setupClerkTestingToken({ context });
  });

  test("new account verification activates the session and opens organization setup", async ({ page }) => {
    await page.goto("/sign-up");

    await page.getByLabel("First name").fill("RingIQ");
    await page.getByLabel("Last name").fill("E2E");
    await page.getByLabel("Work email").fill(testEmail);
    await page.getByLabel("Password", { exact: true }).fill(testPassword);
    await page.getByRole("button", { name: "Create account" }).click();

    await page.getByLabel("Verification code").fill(clerkTestCode);
    await page.getByRole("button", { name: "Verify email" }).click();

    await expect(page).toHaveURL(/\/workspace\/setup$/, { timeout: 20_000 });
    await expect(page.getByText("You're already signed in.")).toHaveCount(0);
  });

  test("sign-in verification never returns an active user to an auth form", async ({ page }) => {
    await page.goto("/sign-in");

    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel("Password", { exact: true }).fill(testPassword);
    await page.getByRole("button", { name: "Sign in" }).click();

    await page.getByLabel("Verification code").fill(clerkTestCode);
    await page.getByRole("button", { name: "Verify and continue" }).click();

    await expect(page).toHaveURL(/\/workspace\/setup$/, { timeout: 20_000 });
    await expect(page.getByLabel("Email")).toHaveCount(0);
    await expect(page.getByText("You're already signed in.")).toHaveCount(0);
  });

  test("platform invitation acceptance never falls through without a ticket", async ({ page }) => {
    await page.goto("/platform/accept-invitation");

    await expect(page.getByText("This platform invitation link is missing its ticket.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Accept invitation" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Platform sign in" })).toBeVisible();
  });
});
