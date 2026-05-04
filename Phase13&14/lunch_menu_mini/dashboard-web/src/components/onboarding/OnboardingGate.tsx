"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { loadPreferences } from "@/lib/preferences";
import { loadCurrentUser } from "@/lib/auth";

/**
 * First-run gate.
 *
 * 1. No current user  → `/login`
 * 2. Onboarding not done → `/onboarding`
 * 3. Otherwise → no-op
 *
 * Mounted in the root layout so every route change re-checks. Cheap; no
 * network calls.
 */
const PUBLIC_ROUTES = new Set(["/login", "/onboarding"]);

export default function OnboardingGate() {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (PUBLIC_ROUTES.has(pathname)) return;

    const user = loadCurrentUser();
    if (!user) {
      router.replace("/login");
      return;
    }

    const prefs = loadPreferences();
    if (!prefs.onboardingComplete) {
      router.replace("/onboarding");
    }
  }, [pathname, router]);

  return null;
}
