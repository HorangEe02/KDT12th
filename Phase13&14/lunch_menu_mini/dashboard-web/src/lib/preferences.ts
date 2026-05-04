/**
 * Phase 3 — user personalization.
 *
 * Preferences are stored in localStorage under `p11_user_prefs` so the
 * Next.js app stays stateless-server-friendly. All getters are hydration-safe
 * (typeof window checks).
 */
import type { Restaurant } from "./types";

export interface UserPreferences {
  /** Categories the user explicitly likes (boosts score). */
  favoriteCategories: string[];
  /** Categories the user wants to see less of (penalises score). */
  dislikedCategories: string[];
  /** Ingredient/allergen keywords to filter out entirely. */
  allergies: string[];
  /** Dietary tags: "vegetarian", "low-sodium", "high-protein", ... */
  dietaryTags: string[];
  /** Hard cap — restaurants priced above this are filtered. 0 = no cap. */
  maxPrice: number;
  /**
   * Weight (0~1) for downweighting recently-visited restaurants.
   * 0 = ignore history. 0.5 = halve score of restaurants visited in last 7d.
   */
  recencyPenalty: number;
  /** When true, personalization is active. Allows one-toggle disable. */
  enabled: boolean;
  /** First-visit flag. False after onboarding. */
  onboardingComplete: boolean;
}

export const DEFAULT_PREFERENCES: UserPreferences = {
  favoriteCategories: [],
  dislikedCategories: [],
  allergies: [],
  dietaryTags: [],
  maxPrice: 0,
  recencyPenalty: 0.3,
  enabled: true,
  onboardingComplete: false,
};

const STORAGE_KEY = "p11_user_prefs";

// =============================================================================
// Storage
// =============================================================================
export function loadPreferences(): UserPreferences {
  if (typeof window === "undefined") return DEFAULT_PREFERENCES;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_PREFERENCES;
    const parsed = JSON.parse(raw) as Partial<UserPreferences>;
    return { ...DEFAULT_PREFERENCES, ...parsed };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function savePreferences(prefs: UserPreferences): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    // Notify other tabs / components
    window.dispatchEvent(new CustomEvent("p11_prefs_updated"));
  } catch {
    /* quota exceeded — ignore */
  }
}

export function updatePreferences(patch: Partial<UserPreferences>): UserPreferences {
  const next = { ...loadPreferences(), ...patch };
  savePreferences(next);
  return next;
}

export function isOnboardingComplete(): boolean {
  if (typeof window === "undefined") return true; // SSR: assume yes
  return loadPreferences().onboardingComplete;
}

// =============================================================================
// Personalization scoring
// =============================================================================
/**
 * Returns a multiplier ∈ [0, 1.5] to apply to the composite score.
 *
 * - Favorite category: +0.20
 * - Disliked category: -0.30
 * - Price over cap: filtered upstream (return 0)
 * - Over-cap (soft): -0.15
 * - Recently visited: -recencyPenalty × visitRatio
 * - Dietary/allergy filtering happens upstream — this returns 0 so the item
 *   can be dropped.
 */
export function personalizedMultiplier(
  r: Restaurant,
  prefs: UserPreferences,
): number {
  if (!prefs.enabled) return 1.0;

  // Hard filter: price cap
  if (prefs.maxPrice > 0 && r.price > prefs.maxPrice * 1.5) {
    return 0;
  }

  let mult = 1.0;

  if (prefs.favoriteCategories.includes(r.category)) {
    mult += 0.2;
  }
  if (prefs.dislikedCategories.includes(r.category)) {
    mult -= 0.3;
  }

  // Soft price penalty
  if (prefs.maxPrice > 0 && r.price > prefs.maxPrice) {
    mult -= 0.15;
  }

  // Recency penalty — visits is a proxy for recent visits
  if (prefs.recencyPenalty > 0 && r.visits > 0) {
    const normalized = Math.min(r.visits / 20, 1); // 20 visits → max penalty
    mult -= prefs.recencyPenalty * normalized;
  }

  return Math.max(0, Math.min(mult, 1.5));
}

/**
 * Allergen matcher — simple substring check against the restaurant name
 * and menuType. Used before scoring to remove unsafe items.
 *
 * For production, this should delegate to `nlp_research` B2 NER via
 * `/nlp/v2/menu/extract`.
 */
export function hasAllergenConflict(
  r: Restaurant,
  prefs: UserPreferences,
): boolean {
  if (!prefs.enabled || prefs.allergies.length === 0) return false;
  const haystack = `${r.name} ${r.menuType}`.toLowerCase();
  return prefs.allergies.some((a) =>
    a && haystack.includes(a.toLowerCase().trim())
  );
}

/**
 * Filters + scores a list of restaurants.
 * Returns an array with `personalizedScore` added.
 */
export function applyPersonalization<T extends Restaurant & { score: number }>(
  items: T[],
  prefs: UserPreferences,
): (T & { personalizedScore: number; personalizedMultiplier: number })[] {
  return items
    .filter((r) => !hasAllergenConflict(r, prefs))
    .map((r) => {
      const m = personalizedMultiplier(r, prefs);
      return {
        ...r,
        personalizedMultiplier: m,
        personalizedScore: Math.round(r.score * m),
      };
    })
    .filter((r) => r.personalizedMultiplier > 0);
}

// =============================================================================
// Presets
// =============================================================================
export const DIETARY_TAGS = [
  "vegetarian",
  "vegan",
  "low-sodium",
  "high-protein",
  "low-carb",
  "halal",
  "kosher",
];

export const COMMON_ALLERGENS = [
  "땅콩", "새우", "우유", "계란", "밀", "메밀", "콩", "복숭아", "토마토",
  "고등어", "조개",
];
