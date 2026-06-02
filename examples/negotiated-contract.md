# Example: Negotiated contract on disk

This is what a `workspace/contract.md` file looks like in practice: the load-bearing artifact for ACS principle #3 (negotiated contracts, not handed-down specs).

The example shows one full negotiation for a single sprint, with three rounds of back-and-forth before the contract seals.

---

```markdown
# Contract - Sprint 2: Sprite Editor

**Sprint ID:** sprint-2
**Generator session:** gen-2026-05-25-12:00:00
**Evaluator session:** eval-2026-05-25-12:00:00
**Status:** SEALED · 2026-05-25T12:18:42Z

---

## Round 1 - Generator proposal (2026-05-25T12:00:14Z)

### Scope
I will build a 32×32 pixel sprite editor as a single HTML page. It includes:
- A canvas for drawing
- A color palette (8 preset colors)
- Mouse-click painting
- A "Save PNG" button

### Testable assertions
1. Page loads in < 500ms
2. Clicking a palette color changes the active color
3. Clicking the canvas paints a pixel
4. Save button downloads a 32×32 PNG file

### Criteria (5 items)
1. Canvas is visible
2. Palette is visible
3. Mouse click on canvas paints
4. Mouse click on palette changes color
5. Save button works

---

## Round 1 - Evaluator response (2026-05-25T12:03:09Z)

**REJECT - see below**

### On scope
Too narrow. A "sprite editor" without undo, animation frames, or zoom is
not a sprite editor; it's a paint canvas. Either rename the sprint or
expand the scope.

### On testable assertions
- "Page loads in < 500ms" - fine, measurable
- "Clicking a palette color changes the active color" - needs assertion
  about the visual indication of active color
- "Save button downloads a 32×32 PNG file" - needs a *round-trip* test:
  save, reload the PNG, assert pixel equality with the canvas state

### On criteria (5 items)
This is the worst part. Five criteria is not enough. Per ACS principle #3:
≥ 20 granular criteria. Vague criteria → vague critiques → no fix.

Expand to ≥ 20 criteria. Include:
- Accessibility (keyboard navigation, ARIA labels)
- Visual craft (color of selected swatch, hover states)
- Edge cases (canvas overflow if window resizes, palette wrapping)
- Persistence behaviors (does state survive page refresh? specify)

---

## Round 2 - Generator counter-proposal (2026-05-25T12:09:37Z)

### Revised scope
Building a 32×32 pixel sprite editor with:
- Canvas with grid
- Color palette (full 54-color 8-bit preset, NES-style)
- Mouse-click painting + drag-painting
- Undo / redo (10-step history)
- Zoom controls (1x / 4x / 8x preview)
- Save PNG + reload PNG (round-trip)

I'm deferring animation frame timeline to sprint-3 (separate sprint).
Negotiable.

### Testable assertions (12 items)
1. Page loads in < 500ms
2. Canvas renders a visible 32×32 grid
3. Palette renders all 54 colors
4. Click palette swatch - that swatch shows active border
5. Click on canvas - pixel paints in active color
6. Drag across canvas - line of pixels paints
7. Ctrl+Z undoes last paint action
8. Ctrl+Shift+Z redoes
9. Zoom button cycles 1x → 4x → 8x → 1x
10. Save button downloads `.png` file
11. Round-trip: save → reload → canvas state equal at pixel level
12. Page refresh - canvas state restored from localStorage

### Criteria (24 items)
[functional - 12 from above]
13. Canvas is visible without horizontal scroll on 1280×800
14. Palette swatches are ≥ 24px tap target (touch-friendly)
15. Selected swatch shows ≥ 3px highlighted border
16. Hover state on swatches has visible color shift
17. Empty canvas shows a faint grid (every 8 pixels)
18. Zoom level visible in UI
19. Undo button disabled when history empty
20. Redo button disabled when no redo available
21. Save PNG produces a 32×32 image, not the full window
22. ARIA labels on all palette swatches and action buttons
23. Keyboard navigation: Tab cycles through palette + buttons
24. No console errors during any of the above

### Animation frame deferral
Deferring to sprint-3. Reason: scope creep risk; want to lock down the
single-frame editor first. If you reject the deferral, propose alternative.

---

## Round 2 - Evaluator response (2026-05-25T12:13:21Z)

### On scope
Accepted with one addition: include a "Clear canvas" button (criteria 25).
Otherwise good.

### On deferral of animation frames
Accepted. Logical sprint boundary.

### On testable assertions
12 items - adequate. Round-trip test is now there. Good.

### On criteria
24 - meets the ≥ 20 floor. Add #25: "Clear canvas" button with
confirmation. Add #26: "Undo after clear" restores cleared state (test
the undo stack survives clear).

That brings you to 26. Acceptable.

### One non-negotiable
Criterion #18 ("Zoom level visible in UI"): I want a specific zoom
indicator, not just inferring from canvas size. Spell out: "Zoom level
text displayed in top-right corner, format `1x`/`4x`/`8x`."

---

## Round 3 - Generator accept (2026-05-25T12:18:05Z)

Accepting all three:
- #25: Clear canvas button with confirmation
- #26: Undo after clear restores cleared state
- Refinement to #18: Zoom level text in top-right corner, format `1x`/`4x`/`8x`

Final criterion count: 26.

**Generator-side seal:** Ready to build.

---

## Round 3 - Evaluator accept (2026-05-25T12:18:42Z)

**Evaluator-side seal:** Contract accepted. Begin build.

**STATUS: SEALED**

Generator may now proceed with implementation. Evaluator will run
verification against this contract (NOT against the original Planner
sprint description) once Generator hands off via progress.md.
```

---

## Notes on the example

- **Three rounds is typical.** Fewer means the Evaluator is rubber-stamping; more means the Planner specified too much up front.
- **The Evaluator's first rejection should be substantive.** "Five criteria isn't enough" is a real critique; "good but needs more" is not.
- **Deferrals are negotiated, not unilateral.** Generator can propose a deferral (e.g. animation frames → next sprint); Evaluator can accept or reject.
- **The contract grades against itself, not against the upstream spec.** This is what stops cascading errors over multi-hour runs (ACS principle #5).
- **Timestamps matter.** They make the negotiation auditable when reading traces post-hoc (ACS principle #10).
