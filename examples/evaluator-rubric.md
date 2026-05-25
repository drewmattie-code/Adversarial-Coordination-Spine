# Example: Evaluator rubric (full-stack app)

A sample 26-criteria rubric for a generic full-stack web app. The Evaluator agent grades against this rubric (or one negotiated per sprint via `contract.md`). The point is granularity — vague criteria produce vague critiques, which produce no actionable fixes (ACS principle #3).

The rubric is broken into four weighted dimensions, following Anthropic's pattern from the AI Engineer talk. Weights are tunable per domain. Defaults assume the model is already pretty good at functionality (true for Opus 4.6-class models), so weight skews toward design and originality where models are weaker.

---

## Dimensions and weights

| Dimension | Weight | Rationale |
|---|---|---|
| Design | 35% | Models default to AI-slop aesthetics (purple gradients, generic layouts); this is where harshness pays |
| Originality | 25% | Models default to cliché; demand a point of view |
| Craft | 20% | Polish: spacing, hover states, edge-case handling |
| Functionality | 20% | Necessary floor, but most frontier models clear it; less weight |

---

## Criteria (26 items)

### Design (9 items · 35% weight)

1. **No purple-to-pink gradients.** AI-slop tell. Reject on sight unless the brand specifically calls for it.
2. **Typography has hierarchy.** ≥ 3 distinct text sizes used purposefully. No "all 16px" pages.
3. **Color palette is constrained.** Max 5 hues in the page (excluding image content). Generic rainbow palettes fail.
4. **Whitespace is generous, not nervous.** Comfortable air around primary content. Cramped pages fail.
5. **Layout has a focal point.** A first-glance test: where does the eye go? If the answer is "nowhere," reject.
6. **Interactive elements signal their state.** Hover, focus, active, disabled — all visibly distinct.
7. **Empty states are designed.** Not just "No items" gray text — actual designed empty states.
8. **Loading states exist.** Not just spinners — skeleton screens or progressive content reveal.
9. **Error states are humane.** Plain-language errors, not stack traces or codes.

### Originality (5 items · 25% weight)

10. **The page has a point of view.** A first-look stranger should be able to describe the product's personality in one sentence.
11. **The naming is not generic.** "MyApp" / "Dashboard" / "Welcome" fail. The artifact should name itself meaningfully (Anthropic's "retroforge" example).
12. **Microcopy is not corporate.** Buttons say something specific ("Save sprite", not "Save"). Labels describe content, not categories.
13. **The product makes a decision the user didn't ask for.** A good agent adds a thoughtful default the user benefits from. A bad agent is purely instruction-following.
14. **The design references something.** A retro game maker should *feel* retro. A finance dashboard should feel grounded. Genre signals are intentional.

### Craft (6 items · 20% weight)

15. **Alignment is exact.** No off-by-one-pixel rows of elements. Items in a list align on edges.
16. **Spacing is consistent.** 4 / 8 / 12 / 16 / 24 / 32 px scale — not random whatever-Tailwind-snapped-to.
17. **Hover transitions exist.** Buttons and links animate (subtly) on hover.
18. **Focus rings are present and visible.** Tab-navigable; visible focus indicator on every interactive element.
19. **No console errors on load or interaction.** Open devtools, do the user flow, watch console. Any error = reject.
20. **Responsive at 1280×800 and 375×667.** Doesn't have to be mobile-first, but must not break.

### Functionality (6 items · 20% weight)

21. **Primary user flow works end-to-end.** Without intervention.
22. **Test cases from the negotiated contract pass.** All of them. Not "mostly."
23. **No fake features.** Buttons that look implemented but have no backend pass = reject. Half-baked features fail (Anthropic specifically flags this).
24. **State persists where it should.** Refresh, navigate away and back — appropriate state survives.
25. **Edge cases handled.** Empty input, very long input, special characters, network failure. At least three edge cases verified.
26. **Performance is acceptable.** Page Time-to-Interactive < 3s on a moderate connection. Interactive elements respond < 100ms.

---

## Scoring

For each criterion, the Evaluator records:
- **PASS** (1.0)
- **PARTIAL** (0.5) — with a specific note on what's missing
- **FAIL** (0.0) — with a specific note on what's wrong

Weighted score = `Σ(criterion_score × dimension_weight / criteria_in_dimension)`

**Pass threshold for SEALED contract:** 0.85.
**First-pass rejection target:** rejection rate > 30% over the first 10 runs.

If the Evaluator is rubber-stamping (first-pass acceptance > 70%), the
prompt needs harsher calibration — add more "AI slop" example screenshots
to the system prompt, increase the weight on Design and Originality, or
tighten the partial-credit definition.

---

## Customizing per domain

This rubric is for full-stack web apps. For other domains, swap the dimensions:

| Domain | Suggested dimensions |
|---|---|
| Research synthesis | Accuracy / Completeness / Originality / Readability |
| Code library | API design / Documentation / Test coverage / Performance |
| Customer-support response | Accuracy / Tone / Completeness / Brevity |
| Sales outreach | Specificity / Relevance / Tone / Call-to-action clarity |
| Data analysis | Methodology / Reproducibility / Insight quality / Clarity of presentation |

Keep the weight-skew principle: weight harder on the dimensions where the model is weakest. Functionality usually doesn't need heavy weight on frontier models; taste does.

---

## Source

The four-dimension pattern (Design / Originality / Craft / Functionality) is documented in Anthropic's AI Engineer Summit 2026 talk by Ash Prabaker and Andrew Wilson, [Build Agents That Run for Hours (Without Losing the Plot)](https://www.youtube.com/watch?v=mR-WAvEPRwE). The 30%-rejection-rate calibration target is documented in the same talk.
