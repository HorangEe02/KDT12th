# Design System Document: The Stadium Editorial

## 1. Overview & Creative North Star: "The Digital Curator"
This design system moves away from the static, data-heavy grid systems common in sports apps. Instead, we embrace **The Digital Curator**—a high-end, editorial approach that treats travel planning like a premium lifestyle magazine. 

We blend the precision of professional sports with the fluidity of high-end travel. By utilizing intentional asymmetry, overlapping elements (like a player action shot breaking the container boundary), and aggressive typographic scales, we create an experience that feels as dynamic as a ninth-inning home run. This is not just a utility; it is a personalized concierge for the KBO enthusiast.

## 2. Colors: Tonal Depth & Team Adaptability
Our palette is anchored in professional authority (`primary`: #00193c) but breathes through stadium-inspired accents (`secondary`: #1b6d24). 

### The Adaptive Primary
While our core identity uses Deep Navy, the `primary` and `primary-container` tokens are designed to be dynamic. When a user selects their team (e.g., LG Twins Red or Samsung Lions Blue), these tokens swap to the team's signature hue, instantly re-skinning the entire dashboard to feel "home-grown."

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to section content. Boundaries must be defined solely through background color shifts. Use `surface-container-low` for large sections sitting on a `surface` background. This creates a modern, "seamless" look that feels expensive rather than "templated."

### Surface Hierarchy & Nesting
Treat the UI as layered sheets of frosted glass. 
- **Base:** `surface` (#f8f9fa)
- **Sections:** `surface-container-low` (#f3f4f5)
- **Interactive Cards:** `surface-container-lowest` (#ffffff) to provide a "pop" of clean white.

### The "Glass & Gradient" Rule
To elevate CTAs, use a **Signature Texture**: a linear gradient from `primary` (#00193c) to `primary-container` (#002d62) at a 135-degree angle. For floating AI bot elements or stadium weather overlays, apply a `backdrop-filter: blur(12px)` using a semi-transparent `surface-variant`.

## 3. Typography: Dynamic Momentum
We use a dual-font strategy to balance "Sporty" and "Sophisticated."

*   **Display & Headlines (Plus Jakarta Sans):** Chosen for its geometric precision and wide stance. It feels fast, modern, and authoritative.
    *   *Usage:* Use `display-lg` for game scores and `headline-md` for itinerary headers.
*   **Body & Titles (Manrope):** A versatile sans-serif with excellent readability. It provides a functional "Travel Guide" feel.
    *   *Usage:* `title-md` for stadium names; `body-lg` for travel descriptions.

**Hierarchy Tip:** Always pair a `display-sm` heading with a `label-md` in all-caps (using 0.05em letter spacing) to create an editorial "kick."

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are too "heavy" for a modern sports app. We achieve lift through light.

*   **The Layering Principle:** Place a `surface-container-lowest` card on top of a `surface-container-low` background. The subtle shift from #f3f4f5 to #ffffff creates natural depth without visual noise.
*   **Ambient Shadows:** For floating action buttons or high-priority travel alerts, use a shadow with a 24px blur, 0px offset, and 6% opacity using the `on-surface` color. It should look like a soft glow, not a hard shadow.
*   **The "Ghost Border" Fallback:** If a divider is absolutely required for accessibility, use the `outline-variant` token at 15% opacity. Never use 100% opaque lines.
*   **Glassmorphism:** Use `surface_bright` at 80% opacity with a blur for top navigation bars, allowing the "Stadium Green" or "Team Red" colors of the content to bleed through as the user scrolls.

## 5. Components: Sporty & Refined

### Buttons
- **Primary:** Gradient fill (`primary` to `primary-container`), `rounded-md` (12px), with `on-primary` text. Use for "Book Trip" or "Find Tickets."
- **Secondary:** `secondary-container` fill with `on-secondary-container` text. High-energy for "Add to Itinerary."

### Cards & Lists
- **The "No-Divider" Rule:** Forbid the use of line dividers in lists. Use `0.75rem` vertical spacing (from the spacing scale) and subtle background shifts to separate game dates or hotel options.
- **Stadium Cards:** Use `rounded-lg` (1rem). Incorporate a subtle `secondary-fixed` (#a3f69c) accent bar (4px wide) on the left side of cards to indicate "Recommended" or "Live" status.

### AI/Bot Interface
- **The Concierge:** Use a glassmorphic container with a `surface-tint` (#3e5e95) glow. The AI icon should not be a standard robot, but a minimalist "Spark" icon using `tertiary`.

### Chips
- **Selection Chips:** Use `secondary-fixed-dim` for active states. The roundedness should be `full` to mimic the shape of a baseball stadium's perimeter.

## 6. Do's and Don'ts

### Do:
- **Asymmetric Layouts:** Allow images of baseball players or stadium landmarks to "break" the grid and overlap two different surface containers.
- **High Contrast Labels:** Use `label-sm` in bold with the `secondary` green for status updates (e.g., "ON TIME," "SOLD OUT").
- **Breathable White Space:** Ensure at least 24px of padding inside all primary cards to maintain a premium feel.

### Don't:
- **Overuse Shadows:** If you have more than three shadows on a single screen, the hierarchy is lost. Use tonal shifts instead.
- **Standard Grids:** Avoid the "3-column-row" look. Try a large "Hero" card followed by two staggered smaller cards.
- **Harsh Borders:** Never use a solid #000000 or high-contrast gray border. It kills the fluid, "Digital Curator" vibe.
- **Generic Icons:** Avoid stock travel icons. Use custom icons with a "thick-to-thin" line weight that mimics the movement of a baseball bat swing.