# Design System Strategy: Kinetic Precision

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Digital Powerhouse."** 

This isn't just another fitness tracker; it is an elite, AI-driven performance lab. We move beyond the "template" look by embracing **Kinetic Asymmetry** and **Tonal Depth**. The system is built on the tension between the "Hardcore" (deep charcoals, raw strength) and the "Precision AI" (neon greens, glassmorphism, hyper-clean typography). By utilizing overlapping elements and a non-linear grid, we create a sense of momentum—mimicking the explosive energy of a high-intensity workout.

## 2. Colors & Surface Architecture
We do not use color simply to decorate; we use it to signal energy and define structural hierarchy without the crutch of lines.

### The "No-Line" Rule
**Explicit Instruction:** Prohibit 1px solid borders for sectioning. Boundaries must be defined solely through background color shifts. For example, a `surface-container-low` section sitting on a `surface` background provides all the separation needed. This creates a sophisticated, "molded" look rather than a "sketched" look.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—like stacked sheets of frosted obsidian. 
- **Base Layer:** `surface` (#0e0e0e) for the primary application background.
- **Sectioning:** Use `surface-container-low` (#131313) for large layout blocks.
- **Interactive Cards:** Use `surface-container-high` (#201f1f) or `highest` (#262626) to bring actionable content toward the user.
- **The "Glass & Gradient" Rule:** Floating elements (Modals, Navigation Bars) must utilize Glassmorphism. Apply `surface_variant` at 60% opacity with a 20px backdrop blur to allow the vibrant `primary` data visualizations to "glow" through the interface.

### Signature Textures
Main CTAs and high-impact headers should utilize a subtle linear gradient: 
- `primary` (#ddffaf) to `primary-container` (#a2fe00). 
This transition provides a visual "soul" and a sense of movement that flat neon cannot achieve.

## 3. Typography: The Athletic Editorial
Our typography is the voice of the coach: authoritative, clear, and relentless.

- **Display & Headlines (Space Grotesk):** This is our "Athletic" face. It is wide, technical, and aggressive. Use `display-lg` for PR (Personal Record) celebrations and `headline-md` for workout titles. The tight letter-spacing and bold weight convey strength.
- **Body & Labels (Inter):** The "Functional" face. It is highly legible even at small sizes. Use `body-md` for exercise instructions and `label-sm` for technical data points.
- **Hierarchy via Scale:** We lean into extreme contrast. Pair a `display-sm` metric (e.g., "185kg") with a `label-md` caption in `on_surface_variant` (#adaaaa) to create an editorial, high-end feel.

## 4. Elevation & Depth: Tonal Layering
Traditional shadows are often "dirty." In this system, we use light and tone to create lift.

- **The Layering Principle:** Depth is achieved by "stacking." Place a `surface-container-highest` card on a `surface-container-low` section. The contrast in charcoal depth creates a natural lift.
- **Ambient Glows:** When a floating effect is required, shadows must be extra-diffused. Use the `primary` color (#ddffaf) at 5-10% opacity as a glow-drop shadow for active state buttons, suggesting the element is "powered on."
- **The "Ghost Border" Fallback:** If a border is required for accessibility, use `outline-variant` (#484847) at 20% opacity. **Never use 100% opaque borders.**

## 5. Components: Engineered for Performance

### Buttons (The "Power" Component)
- **Primary:** Gradient fill (`primary` to `primary-container`), black text (`on_primary_fixed`), `xl` corner radius (0.75rem). No border.
- **Secondary:** `surface-container-highest` background with `primary` text. Use for secondary actions like "View History."
- **Tertiary:** Ghost style. No background, `on_surface` text, with a subtle `primary` glow on hover.

### Cards & Data Visualizations
- **Cards:** Strictly no dividers. Separate content using `surface-container` shifts or vertical white space (32px+).
- **Data Viz:** Charts must use `primary` (#ddffaf) for success/growth and `tertiary` (#b2ffcb) for secondary metrics. Use `error` (#ff7351) sparingly for "Low Energy" or "Missed Goal" states.
- **Glass Accents:** Use for floating "Quick Stats" overlays during a workout.

### Inputs & Progress
- **Inputs:** `surface-container-highest` fill, no border. The "active" state is indicated by a 2px `primary` underline—never a full box stroke.
- **Progress Bars:** High-contrast. The track is `surface-container-high`, the fill is the `primary-container` neon gradient.

## 6. Do's and Don'ts

### Do:
- **Lean into Asymmetry:** It’s okay to have a 32px left margin and a 16px right margin for specific editorial "call-out" cards.
- **Use Large Type:** Don't be afraid to let a weight or a rep count dominate the screen.
- **Embrace the Dark:** Keep the `background` deep. The "Hardcore" vibe relies on the void between the neon elements.

### Don't:
- **No Divider Lines:** If you feel the need to add a line, use 24px of white space instead.
- **No Standard Grays:** Avoid neutral grays. Every "black" or "gray" should be a variant of our Deep Charcoal/Black palette to maintain tonal warmth.
- **No Round Corners Everywhere:** While buttons use `xl` (0.75rem), containers should lean toward `md` (0.375rem) to keep the "Precision/Technical" look. Total "full" rounding is reserved only for Chips and Pills.