"use client";

import { useEffect, useState } from "react";
import {
  DEFAULT_PREFERENCES,
  loadPreferences,
  type UserPreferences,
} from "./preferences";

/**
 * React hook that reads UserPreferences from localStorage and re-renders
 * whenever they change (via the `p11_prefs_updated` custom event or the
 * `storage` event for cross-tab sync).
 */
export function usePreferences(): UserPreferences {
  const [prefs, setPrefs] = useState<UserPreferences>(DEFAULT_PREFERENCES);

  useEffect(() => {
    setPrefs(loadPreferences());

    const handler = () => setPrefs(loadPreferences());
    window.addEventListener("p11_prefs_updated", handler);
    window.addEventListener("storage", handler);
    return () => {
      window.removeEventListener("p11_prefs_updated", handler);
      window.removeEventListener("storage", handler);
    };
  }, []);

  return prefs;
}
