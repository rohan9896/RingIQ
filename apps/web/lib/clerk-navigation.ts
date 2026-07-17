import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

export function navigateWithClerk(url: string, router: AppRouterInstance) {
  if (url.startsWith("http")) {
    window.location.href = url;
    return;
  }

  router.push(url);
}
