"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useSessionList } from "@clerk/nextjs";

export function PendingTaskRedirect() {
  const pathname = usePathname();
  const router = useRouter();
  const { isLoaded, sessions } = useSessionList();

  const task = sessions?.find((session) => session.status === "pending")?.currentTask;

  useEffect(() => {
    if (isLoaded && task?.key === "choose-organization" && pathname !== "/workspace/setup") {
      router.replace("/workspace/setup");
    }
  }, [isLoaded, pathname, router, task?.key]);

  return null;
}
