# AI Color Estimation Pilot Design

## Objective

Validate whether image-and-name analysis can provide a useful approximate RGB color for filament products that have no manufacturer Pantone value. The result is an orientative screen color for the existing material renderer, not a Pantone replacement or a claim of physical color accuracy.

The pilot uses the current Codex session so it does not require separate API billing. It validates the product idea, but it is not a reproducible benchmark of the `gpt-5.6-luna` API. Automating the process later will require an OpenAI API key and separate API billing.

## Current Coverage

The current stock payload contains 370 products. Of these, 301 have no resolved `pantone_hex`; 115 of those have a local product image that can be inspected without a network request.

The existing renderer already accepts an arbitrary RGB hex color and applies the resolved material finish. The pilot therefore does not need to modify the public UI, `stock.json`, metadata caches, or the renderer.

## Sample

Select 12 products from the 115 eligible products using a deliberately varied sample:

- light, dark and saturated colors;
- at least one neutral color;
- at least one fluorescent or translucent product when available;
- at least one metallic, silk, pearl or glitter product when available;
- at least two images with potentially difficult lighting, packaging or background colors.

Every selected product must have an empty `pantone_hex` and a local `image_url`. Products that already have an official Pantone-derived color are excluded.

## Estimation Contract

For each product, inspect:

- the local product image;
- display name;
- normalized color;
- material and variant;
- brand;
- resolved material finish.

Return one structured estimate:

```json
{
  "estimated_hex": "#RRGGBB",
  "confidence": "high | medium | low",
  "evidence": "short explanation of the visible filament region and name",
  "warning": "empty or a short ambiguity warning"
}
```

The estimate should target the apparent base filament color, ignoring the spool, label, background, shadows, highlights and transparent packaging as far as possible. The product name acts as supporting context, not as permission to ignore contradictory image evidence.

When the image does not expose a credible filament region, the result must be low confidence. The process must not invent a Pantone code.

## Rendering and Review

Use the existing deterministic material renderer with the estimated hex and the product's already resolved finish. Store all pilot outputs outside production paths under `C:\tmp\stockcentral-ai-color-pilot`.

Produce one comparison board containing, for each product:

- original product image;
- display name and normalized color;
- estimated hex and confidence;
- rendered material swatch;
- ambiguity warning when present.

The board is the review artifact. No pilot URL or estimated color is written to public product data.

## Success Criterion

The pilot is promising when at least 9 of the 12 estimates are accepted by visual review as useful orientation colors. Low-confidence cases count as failures unless their warning correctly identifies that no trustworthy estimate can be made.

The review should also record systematic failure modes, especially colored packaging, white-balance shifts, reflections, mixed-color filament, translucent material and product photos that reuse generic imagery.

## Follow-up Decision

If the pilot succeeds, the next design may introduce a reviewed metadata cache containing estimated hex, confidence, provenance and model version. That later workflow should use `gpt-5.6-luna` through the Responses API, run offline during data maintenance, require human approval for low-confidence results and never make API calls from the static GitHub Pages site.

If the pilot fails, keep the current name-based CSS fallback and consider deterministic image segmentation or manual overrides for the most important products.

## Scope Boundaries

This pilot does not:

- modify the public catalog or the in-progress summary migration;
- add an OpenAI dependency or API key;
- call the OpenAI API;
- claim that the current Codex session is running `gpt-5.6-luna`;
- infer or publish Pantone values;
- process products without local images;
- promise color matching across cameras, lighting conditions, monitors or physical filament batches.

## Verification

- confirm all 12 products lack `pantone_hex` and have local images;
- validate every estimated value against `^#[0-9A-F]{6}$`;
- confirm the renderer produces a non-empty 160 by 160 WebP for every estimate;
- confirm no repository production file changes while generating the pilot;
- visually inspect the comparison board and record accepted, rejected and uncertain results;
- report the acceptance count and observed failure modes before proposing automation.
