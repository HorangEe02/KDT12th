"use client";

import { useEffect, useState } from "react";
import { loadCurrentUser, type CurrentUser } from "./auth";

/**
 * React hook that reads the current user from localStorage and re-renders
 * whenever `p11_auth_updated` (custom event) or `storage` (cross-tab) fires.
 */
export function useAuth(): CurrentUser | null {
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    setUser(loadCurrentUser());
    const handler = () => setUser(loadCurrentUser());
    window.addEventListener("p11_auth_updated", handler);
    window.addEventListener("storage", handler);
    return () => {
      window.removeEventListener("p11_auth_updated", handler);
      window.removeEventListener("storage", handler);
    };
  }, []);

  return user;
}
