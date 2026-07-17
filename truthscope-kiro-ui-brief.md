# Truthscope UI · Kiro Build Brief

A complete steering + spec document for building the Truthscope demo frontend. Target: a UI that reads as a precision instrument built by a design-led team, demoed on a projector to judges in 90 seconds. Everything below is derived from Truthscope Design Doc v2 and the actual dependency set in package.json.

---

## 0. How to feed this to Kiro

1. Drop this file at `.kiro/steering/truthscope-ui.md` so it rides along with every request.
2. Optional split if you prefer Kiro's default steering trio: §1 → `product.md`, §2 + §9 → `tech.md`, §3 through §8 + §10 + §11 → `design.md`.
3. Start a **spec session** (not vibe mode) with this kickoff prompt:

> Build the Truthscope demo frontend described in `.kiro/steering/truthscope-ui.md`. Work in the build order from §12. Phase 1 is the app shell, design tokens, mock SSE client, and the Level 0 verdict card with the provisional-to-final swap. Do not touch backend code, do not add dependencies beyond `lucide-react`, and follow the stack rules in §2 exactly. Generate requirements and tasks from §7 and §12.

4. When Kiro proposes its design.md, check it against §11 (the blacklist) before approving tasks. That is where agentic slop sneaks in.

---

## 1. Mission and context

- **Product:** Truthscope, an adversarial fact-checker with progressive disclosure. One claim in, four zoom levels out: Verdict (L0), Facet Spectrum (L1), Pro/Con Debate (L2), Evidence Detail (L3).
- **Setting:** 6-hour hackathon build, judged live. The UI is the product's face and half the score.
- **The audience is judges standing 3 meters from a projector.** Every sizing, contrast, and motion decision optimizes for that. Big type, high contrast, motion moments that read from across a room.
- **Data arrives as a stream.** Provisional verdict at ~3 seconds, facets resolving one by one over ~15 seconds, then a final verdict that visibly replaces the provisional one. The UI's job is to make waiting look like working.
- **Honesty is the brand.** Real counts only, "no counter-evidence found" rendered as a positive finding, confidence shown with its inputs. The design language must feel calibrated and forensic, never decorative.
- **Name note:** the team may rename to Prism, Facet, Spectrum, or Lens. Keep the product name in a single exported constant (`lib/brand.ts`) and reference it everywhere. The design language below survives any of those names.

---

## 2. Hard stack rules (Kiro must not deviate)

These match the installed dependencies exactly. Violating any of these produces broken builds or dead imports.

1. **Next.js 16, App Router.** `app/` directory. Turbopack dev is the default, don't fight it.
2. **This is effectively a single-screen streaming client app.** Keep `app/layout.tsx` as the server shell (fonts, metadata, background) and make the experience one client tree mounted from `app/page.tsx`. Do not chase RSC purity or server actions during a 6-hour sprint. `"use client"` at the top of the experience root is correct here.
3. **Tailwind v4, CSS-first config. There is no `tailwind.config.js` and Kiro must not create one.** All tokens live in `app/globals.css` via `@import "tailwindcss"` and `@theme` blocks (§4). Custom utilities via `@utility` if needed. The PostCSS config already exists and is correct; do not touch it.
4. **Animation is the `motion` package, v12.** Import from `"motion/react"`: `import { motion, AnimatePresence, MotionConfig, useReducedMotion } from "motion/react"`. **Never import from `framer-motion`, it is not installed.** Motion components require client components.
5. **Colors in oklch,** defined once as tokens. Never use Tailwind's default palette classes (`bg-slate-900`, `text-emerald-500`, etc.). If a color isn't a token, it doesn't ship.
6. **Dependencies:** the only addition allowed is `lucide-react` for icons. No shadcn, no Radix, no chart libs, no clsx/cva unless Kiro writes a 5-line local helper instead.
7. **TypeScript everywhere.** The SSE event types in §9 are the single source of truth for data shapes.
8. **No localStorage/sessionStorage.** All state in memory (React state). This is a demo client, not an app with persistence.

---

## 3. Design direction: "Spectral Instrument"

The concept: **Truthscope is an optical instrument.** A prism takes one beam of light and splits it into measurable wavelengths; Truthscope takes one claim and splits it into measurable facets. The UI should look like a piece of calibrated lab equipment for truth: a spectrometer readout, not a news website and not a chatbot.

Why this direction and not the obvious ones:

- It is derived from the product's own metaphor (the design doc literally calls L1 a "facet spectrum"), so every visual choice has a story the pitcher can say out loud.
- Dark surfaces are a functional choice for projectors (dark UIs with bright data read far better under venue lighting than white pages), not an aesthetic default.
- It gives a **principled color system**: color in this UI means exactly one thing, verdict status. Nothing else gets to be colorful. That restraint is what separates "instrument" from "dashboard template."

### The signature element: the Spectrum Bar

One element carries the whole concept. A slim horizontal bar (8px tall) at the top of the verdict card, divided into three equal segments, one per facet, in fixed order: Fact, Scale, Stakeholder Reactions.

- **Pending:** segment is a faint neutral with a slow left-to-right shimmer (the only ambient animation allowed anywhere).
- **Resolved:** the segment fills with that facet's status color via a quick spring wipe, at the moment the SSE event lands.
- **Final verdict:** a single bright light-sweep travels across the full bar once, then the bar goes still. This is the visual punctuation for the provisional-to-final swap.
- **Interactive:** clicking a segment scrolls to / expands that facet. Hovering shows a tooltip with the facet's score input (the F6 confidence inputs made visible).
- A miniature version of the bar appears in the L1 header, so the motif recurs.

One element that encodes progress, composition, confidence inputs, and navigation. Spend all the boldness here; keep everything around it quiet.

### Color

Two-layer system on cold charcoal. Backgrounds carry a slight blue-violet cast (optical lab, not pure black, and never `#000`).

**Status scale (the only expressive color in the product):**

| Status | Role | Token |
|---|---|---|
| Confirmed | 1.0 | spectral green |
| Mostly confirmed | 0.75 | yellow-green |
| Disputed | 0.5 | amber |
| Refuted | 0 | red-orange |
| Unclear / insufficient data | excluded | **pure achromatic gray** |

Unclear being literally colorless is intentional and worth saying in the pitch: no wavelength means no light means no data.

**One interactive accent** ("beam", a cool cyan) for focus rings, links, zoom affordances, and the light-sweep. It never labels a verdict.

Status colors are used at full strength for text, icons, and borders, and at 10 to 14 percent alpha for fills (Tailwind v4 opacity modifiers on the tokens, e.g. `bg-status-confirmed/12`). Never large solid blocks of status color.

### Surfaces and depth

- Depth via **1px hairline borders** (`--color-line`) and surface steps, not drop shadows. The only shadow in the app is under the L3 modal.
- Card radius 10px, inner elements 6px. Full-round pills are reserved for status chips only.
- A barely-there noise texture (2 to 3 percent opacity, tiny inline SVG `feTurbulence` data URI on the body) to stop dark-gradient banding on projectors. No visible gradients anywhere else.

---

## 4. Design tokens (paste-ready `app/globals.css`)

```css
@import "tailwindcss";

/* Fonts are injected by next/font as CSS vars on <html>; inline so utilities resolve them */
@theme inline {
  --font-display: var(--font-schibsted);
  --font-mono: var(--font-fragment);
}

@theme {
  /* Surfaces: cold charcoal with a violet cast */
  --color-ink-950: oklch(0.16 0.012 265);  /* app background */
  --color-ink-900: oklch(0.20 0.014 265);  /* card surface */
  --color-ink-850: oklch(0.23 0.016 265);  /* raised: modal, hover */
  --color-line:    oklch(0.32 0.02 265);   /* hairline borders */

  /* Text */
  --color-fog-100: oklch(0.95 0.005 265);  /* primary */
  --color-fog-400: oklch(0.74 0.012 265);  /* secondary */
  --color-fog-600: oklch(0.56 0.012 265);  /* muted, timestamps */

  /* Interactive accent: the beam */
  --color-beam:    oklch(0.83 0.11 210);

  /* Status scale: the only expressive color in the product */
  --color-status-confirmed: oklch(0.78 0.17 152);
  --color-status-mostly:    oklch(0.82 0.15 120);
  --color-status-disputed:  oklch(0.80 0.15 85);
  --color-status-refuted:   oklch(0.68 0.21 25);
  --color-status-unclear:   oklch(0.65 0 0);      /* deliberately achromatic */

  /* Shape */
  --radius-card: 10px;
  --radius-inner: 6px;

  /* Motion durations (reference from JS too) */
  --duration-swap: 700ms;
  --duration-wipe: 350ms;
}

@layer base {
  body {
    background: var(--color-ink-950);
    color: var(--color-fog-100);
    font-family: var(--font-display), system-ui, sans-serif;
  }
  ::selection { background: oklch(0.83 0.11 210 / 0.25); }
  :focus-visible {
    outline: 2px solid var(--color-beam);
    outline-offset: 2px;
  }
}

@utility tnum {
  font-variant-numeric: tabular-nums;
}
```

Rule for Kiro: every color reference in components is one of these tokens. If a design need arises that no token covers, add a token, don't inline a value.

---

## 5. Typography

Two families total, loaded via `next/font/google` in `app/layout.tsx` with `variable:` set to `--font-schibsted` and `--font-fragment`.

- **Schibsted Grotesk** (400 / 500 / 700): display and all UI text. Chosen deliberately: it was commissioned by a Nordic news media group, so the letterforms literally come from journalism. Free pitch line if anyone asks about the type.
- **Fragment Mono** (400): all *evidence material*. Quotes, URLs, counts, timestamps, badges, author handles, the confidence inputs line. The rule that makes the design coherent: **if the backend grepped it, counted it, or fetched it, it renders in mono.** UI chrome speaks Schibsted, data speaks mono. (If Fragment Mono renders poorly at small sizes, IBM Plex Mono is the approved fallback.)

Scale (desktop, the demo target):

- Verdict line: `clamp(2.25rem, 4vw, 3.5rem)`, weight 700, tight tracking (-0.02em). Readable from the back of the room.
- Section headers (facet names, PRO/CON): 1.125rem, weight 500.
- Body / evidence claims: 1rem, line-height 1.55.
- Mono data (counts, badges, URLs): 0.8125rem, `tnum` on anything numeric.
- Eyebrow labels (PRELIMINARY, VERDICT, EVIDENCE): 0.6875rem mono, uppercase, letter-spacing 0.12em, `--color-fog-600`.

---

## 6. Layout and the zoom model

**One screen. No routes.** The zoom is spatial, not navigational, so the demo never loses context.

```
┌──────────────────────────────────────────────┐
│  brand mark          sources · quotes (mono) │  ← slim top bar
├──────────────────────────────────────────────┤
│  claim input (large, centered, autofocus)    │
├──────────────────────────────────────────────┤
│  L0  VERDICT CARD                            │
│      [ spectrum bar ]                        │
│      verdict line · confidence · counts      │
├──────────────────────────────────────────────┤
│  L1  FACET SPECTRUM (3 rows)                 │
│      ▸ row click expands L2 inline ─┐        │
│      ┌──────────────────────────────┘        │
│      │ L2 DEBATE (pro | con, tilting scale)  │
│      │   evidence row click → L3 MODAL       │
└──────────────────────────────────────────────┘
```

- Max content width 1120px, centered, generous vertical rhythm (48 to 64px between levels).
- L2 expands **inline under its facet row** with a `layout` animation (accordion), pushing content down. Only one facet open at a time. Do not navigate away.
- L3 is a centered modal over a scrim (`--color-ink-950` at 70 percent), the app's one shadow, closes on Escape and scrim click, focus trapped.
- Before first query: the input sits alone in the upper third with a one-line subtitle. Empty states invite action, no illustration art.
- Responsive floor: must not break at 1280×720 (common projector) and must be presentable on a phone (single column, spectrum bar full-width). Do not spend hackathon time on mobile perfection.

---

## 7. Component specs

Suggested file layout:

```
app/layout.tsx            fonts, metadata, body bg
app/page.tsx              mounts <TruthscopeApp/>
components/app.tsx        "use client" root: state machine + SSE wiring
components/claim-input.tsx
components/verdict-card.tsx
components/spectrum-bar.tsx
components/facet-spectrum.tsx   (list) + facet-row.tsx
components/debate-view.tsx      (L2) + evidence-item.tsx
components/evidence-modal.tsx   (L3)
components/count-ticker.tsx
components/status-chip.tsx
lib/brand.ts  lib/types.ts  lib/sse.ts  lib/mock-sse.ts
```

### L0 · Verdict Card (two states, the hero)

**Provisional state** (arrives ~3s after submit):
- Eyebrow: `PRELIMINARY · VERIFYING ACROSS 3 FACETS` in mono with a subtle pulse (pending elements are the only things allowed to pulse).
- Early read in display type at ~60 percent of final verdict size, `--color-fog-100`.
- Spectrum bar in full pending shimmer.
- `Sources so far: N` as a live mono ticker.
- Card border: `--color-line`. No status color yet, the system hasn't earned it.

**Final state** (replaces provisional):
- Verdict phrase huge in display type: `Mostly true` with qualifier `· scale disputed` in mono at smaller size.
- Confidence chip: band label (HIGH / MODERATE / LOW / CONTESTED) in the band's dominant status color at 12 percent fill, **with its inputs directly beneath in mono**: `2/3 facets confirmed · 9 of 11 quality sources agree`. The inputs line is not optional, it is the F6 feature.
- Counts row in mono with `tnum`: `Sources examined: 11 · Quotes verified: 6/6` plus a check icon.
- `Zoom in` affordance in `--color-beam` with a down chevron.
- Card left-edge gets a 3px inset rule in the verdict's dominant status color. That rule and the spectrum bar are the only status color on the card besides the chip.

**The swap** is the demo's money shot, spec in §8.

### L1 · Facet Spectrum

Three fixed rows in fixed order: `Fact`, `Scale`, `Stakeholder Reactions`. Each row:

- Left: facet name (display, 500) with a lucide icon at 1.5px stroke (e.g. `check-circle-2`, `bar-chart-3`, `users`). **Never emoji.**
- Middle: one-line summary in `--color-fog-400` (`5% filing vs 8-10% leak`).
- Right: status chip (pill, mono uppercase, status color text on 12 percent fill) plus evidence count in mono (`7 sources`).
- Pending rows render as skeletons shaped exactly like resolved rows (shimmering line where the summary goes, hollow chip), so resolution is a fill-in, not a layout jump.
- Stakeholder Reactions when resolved shows its two sub-buckets inline in the summary: `Named: CEO memo, analysts · Grassroots: top Reddit threads`.
- Entire row is a `<button>`, keyboard focusable, chevron rotates when expanded.

### L2 · Debate View (inline expansion)

- Header: facet name + status chip + **the tilting scale**: a minimal SVG beam and fulcrum (two lines and a triangle, hairline weight, no clip art). Beam tilt maps to quality-weighted evidence balance from the facet payload, clamped to ±12°, animated with a soft spring. This is the doc's ⚖️ moment done as an instrument needle, not an emoji.
- Two columns under headers `PRO` and `CON` (eyebrow style) with the position summary next to each (`5% official` / `higher estimates`).
- Evidence items: source name (display, 500), one-line claim, then the quote's first ~90 chars in mono `--color-fog-400`, a verified check in `--color-status-confirmed` when `verified`, and a `▸` affordance. Click opens L3.
- **The F4 positive-empty state:** when `con_empty` is true, the CON column renders a single centered statement, check icon in confirmed green: `No credible counter-evidence found`, subtitle in mono: `Searched N sources · 0 verifiable counterclaims`. Style it as a *finding*, same card treatment as evidence, never as a gray empty state. The scale rests fully tilted PRO.
- **Stakeholder Reactions variant:** columns become `NAMED` and `GRASSROOTS` instead of PRO/CON, and the scale is hidden (reactions aren't adversarial). Grassroots items show `u/handle` and score in mono with the permalink.

### L3 · Evidence Modal

Chain-of-custody layout, top to bottom:

1. The full quote, large-ish mono (1rem), in quotation marks, with a 2px left rule in the status color of its facet.
2. Source line: favicon-less, just `reuters.com` in display 500 + `Open source ↗` link in `--color-beam` (opens new tab, this gets clicked live in the demo, make the hit area generous).
3. Timestamp in mono muted: `3 hours ago · Mar 14, 2026`.
4. **The verification badge, the product's thesis:** check icon + `QUOTE VERIFIED` eyebrow + one line: `Exact match found in fetched page text`. Confirmed green text on 12 percent fill, full-width strip. If unverified somehow reaches the UI, show a gray `Not verified · excluded from scoring` strip instead of hiding it.
5. Optional bias tag if present in payload: `Source bias: Center · static lookup` in mono muted. The `static lookup` suffix stays, it's the honesty story.

### Chrome

- Top bar: brand wordmark left (display 700, letter-spaced), live global counts right in mono, ticking as `counts` events land.
- Claim input: single large field, 1.125rem, dark surface, hairline border, beam focus ring, placeholder `Paste a claim or controversy...`, Enter submits, button label `Check it`. During a run the button becomes `Checking...` disabled; a subtle `New check` resets.

---

## 8. Motion system (Motion 12, `motion/react`)

Global rules first:

- Wrap the app in `<MotionConfig reducedMotion="user">`. Under reduced motion everything crossfades in 150ms, shimmer and sweep are disabled, the scale snaps to its angle.
- Animate `transform` and `opacity` only. No width/height/top/left animation except Motion `layout` transitions, which handle the accordion.
- Nothing loops except the pending shimmer. When the system is done, the screen is *still*. Stillness reads as confidence.

Three orchestrated moments, in priority order:

1. **The provisional → final swap (the money shot).** `AnimatePresence mode="popLayout"` on the card body keyed by state. Provisional exits with slight upward drift + fade (200ms). Final enters with a settle spring (`{ type: "spring", stiffness: 260, damping: 24 }`) from `y: 12, scale: 0.985`. As it lands: the light-sweep crosses the spectrum bar once (700ms, a skewed beam-colored gradient strip moving via transform), and the left-edge status rule wipes in top-to-bottom. Total impression ~800ms. It should feel like an instrument locking onto a reading.
2. **Facet stream-in.** Each row's transition from skeleton to resolved fires when its SSE event lands (real timing IS the stagger, don't fake one). Chip springs in (`stiffness: 400, damping: 30`), summary crossfades, spectrum bar segment wipes with a 350ms ease-out. Counts tick upward (see below).
3. **Zoom transitions.** Facet row → L2: `layout` accordion at spring `{ stiffness: 300, damping: 32 }`; give the facet name a `layoutId` so it glides from row into the debate header (shared element = the "zoom" feeling for free). L3 modal: scrim fade 200ms, panel spring from `scale: 0.96, y: 8`.

Micro (cheap, high polish-per-line):

- **Count ticker:** animate numeric changes with a short spring on a `useSpring`/`useTransform` value, rendered with `tnum`. Numbers that visibly tick upward are the "it's really working" signal.
- Verified badge check draws in with an SVG `pathLength` animation (300ms) when the modal opens.
- Evidence rows: hover raises surface to `--color-ink-850` and nudges the `▸` 2px right, 120ms.
- Scale tilt: soft spring (`stiffness: 120, damping: 14`), so it wobbles once and settles like a real balance.

---

## 9. Data contract and mock SSE

The UI is built **entirely against a mock first** (Person C's track in the design doc). Real SSE plugs in later with zero component changes.

`lib/types.ts` (single source of truth):

```ts
export type FacetId = "fact" | "scale" | "stakeholders";

export type FacetStatus =
  | "pending" | "confirmed" | "mostly_confirmed"
  | "disputed" | "refuted" | "unclear";

export type ConfidenceBand = "high" | "moderate" | "low" | "contested";

export interface Evidence {
  id: string;
  side: "pro" | "con" | "named" | "grassroots";
  claim: string;            // one-line argument
  quote: string;            // verbatim from page
  url: string;
  source: string;           // "reuters.com" or "u/handle"
  publishedAt?: string;     // ISO
  verified: boolean;        // quote-grep result
  score?: number;           // grassroots upvotes
  bias?: "left" | "center" | "right";
}

export type StreamEvent =
  | { type: "provisional"; claim: string; earlyRead: string; sourcesSoFar: number }
  | { type: "facet"; facet: FacetId; status: FacetStatus; summary: string;
      evidence: Evidence[]; conEmpty?: boolean; conSearched?: number }
  | { type: "counts"; sourcesExamined: number; quotesVerified: number; quotesTotal: number }
  | { type: "final"; verdict: string; qualifier?: string; band: ConfidenceBand;
      facetScores: Record<FacetId, number | null>;   // null = unclear/excluded
      agreement: { agree: number; total: number } };
```

- `lib/sse.ts`: thin `EventSource` wrapper that parses events into `StreamEvent` and hands them to one reducer in `components/app.tsx`. All state transitions in that one reducer, components stay dumb.
- `lib/mock-sse.ts`: replays a scripted Meta-layoffs run with realistic delays (provisional at 2.5s, counts ticking every ~1.5s, facets at 6s / 9s / 13s, final at 14s). Include one facet resolving `disputed`, the Fact facet with `conEmpty: true`, and Stakeholders with both `named` and `grassroots` items. Active when `NEXT_PUBLIC_MOCK=1` or `?mock=1`. Add a second scripted run for a settled fact ("is the earth round") that short-circuits to one confirm lane, since judges will try it.
- **Schema is provisional:** flag in code comments that field names get locked with Person D at hour 0. Isolate all parsing in `lib/sse.ts` so a rename touches one file.
- Never hardcode counts or source numbers in components (F9). If it looks like a number, it came from an event.

---

## 10. Copy deck (use these strings verbatim)

The design doc already wrote good interface copy. Do not let Kiro paraphrase it.

- `PRELIMINARY · VERIFYING ACROSS 3 FACETS`
- `Early read: {earlyRead}`
- `Sources so far: {n}` / `Sources examined: {n}` / `Quotes verified: {a}/{b}`
- `{a}/{b} facets confirmed · {x} of {y} quality sources agree`
- `Insufficient data` (the unclear state, never "unknown" or "error")
- `No credible counter-evidence found`
- `Exact match found in fetched page text`
- `Source bias: {label} · static lookup`
- `Zoom in` / `Open source`
- Buttons: `Check it`, `Checking...`, `New check`
- Tone rules: sentence case everywhere except eyebrows and chips (uppercase mono). No exclamation marks. Errors state what happened and what to do: `Stream dropped. Retrying...` then `Couldn't reach the pipeline. Check the backend and try again.` Never apologize, never joke.

---

## 11. Blacklist (instant rejection in review)

The tells that make a UI read as AI-generated. If any of these appear in Kiro's output, reject the task result:

- `tailwind.config.js` / `.ts`, or any `framer-motion` import
- Tailwind default palette classes, `#000` backgrounds, purple-to-blue gradients, glassmorphism / `backdrop-blur` cards
- Emoji as icons (the design doc sketches use 🟢⚖️💬 as shorthand; the build uses lucide at 1.5px stroke or small custom SVGs)
- `rounded-full` on anything except status chips; shadow stacks (`shadow-lg` everywhere); borders thicker than 1px except the two specced status rules
- Confetti, sparkles, typewriter text effects, skeleton shimmer on anything that isn't genuinely pending, infinite ambient background animation
- Placeholder anything: lorem ipsum, `example.com`, fake counts, "42 sources"
- Center-aligned body paragraphs, letter-spaced lowercase body text
- A settings page, dark/light toggle, auth screens, or any surface the 90-second demo never shows. Scope is the demo flow, nothing else.

---

## 12. Build order and definition of done

Build order (mirrors the hackathon timeline, each phase demoable):

1. **Shell + tokens + mock stream.** Fonts, `globals.css` from §4, `lib/types.ts`, mock SSE replaying end to end in the console.
2. **L0 + spectrum bar** against the mock, including the provisional→final swap. This alone is demo-worthy; treat it as the quality bar.
3. **L1 rows** with skeleton→resolved transitions and real-time stream-in.
4. **L2 debate** with accordion expansion, tilting scale, positive-empty CON state, stakeholder variant.
5. **L3 modal** with verification badge and live link.
6. **Polish pass:** count tickers, badge draw-in, hover states, reduced-motion audit, 1280×720 projector check (crank brightness, stand back 3 meters).

Definition of done:

- [ ] Provisional verdict visible < 5s on mock; final swap animation lands as specced
- [ ] Three facets resolve at independent times with no layout jump
- [ ] Full L0 → L1 → L2 → L3 zoom on one topic, mouse and keyboard (Tab/Enter/Escape all work, focus visible)
- [ ] Every count on screen traces to a `StreamEvent`, zero hardcoded numbers
- [ ] `conEmpty` renders as a positive finding in confirmed green
- [ ] Confidence chip always shows its inputs line
- [ ] Evidence modal link opens the real URL in a new tab
- [ ] Settled-fact mock run renders a single confirm lane without fake debate
- [ ] `prefers-reduced-motion` path verified
- [ ] No blacklist item present; every color on screen is a §4 token
- [ ] Legible at 1280×720 from 3 meters

Ship it.
