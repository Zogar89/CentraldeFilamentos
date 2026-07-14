# Estimated Color Fallback Design

## Objective

Provide an orientative rendered color for every catalog product that has no resolvable manufacturer Pantone value. Estimated colors improve visual comparison in the static catalog but never replace, populate or alter official Pantone data.

Products with a non-empty resolved `pantone_hex` are outside this feature. They keep their current Pantone-derived values, asset names and rendering flow without an estimated-color record.

## Product Rules

- Official Pantone data always wins and remains unchanged.
- An estimated color is created only when `pantone_hex` is empty.
- A local product image plus the product name is the preferred evidence.
- A product without a local image receives a name-only estimate and low confidence.
- The estimate represents the apparent base filament color, not lighting, reflections, spool, label, box or background.
- Fluorescent, translucent, metallic, pearl, silk, glitter, wood and multicolor products receive explicit warnings or reduced confidence when one RGB value cannot represent the physical effect.
- Estimated RGB values are screen-orientation aids, not Pantone matches, print standards or physical color guarantees.
- Availability and final appearance must still be confirmed with the provider.

## Durable Estimate Cache

Create `centraldefilamentos/data/color_estimates.json`, keyed by `product_id`. Every record contains:

```json
{
  "pla-pla-boutique-acqua-175-1000-grilon3": {
    "estimated_hex": "#009DCE",
    "confidence_band": "high",
    "confidence_interval": [0.8, 1.0],
    "source": "image_and_name",
    "material_finish": "satin",
    "evidence": "Visible wound filament is a uniform cyan-blue; the Acqua name supports the reading.",
    "warning": ""
  }
}
```

Allowed values are:

- `confidence_band`: `high`, `medium` or `low`;
- `confidence_interval`: `[0.8, 1.0]` for high, `[0.5, 0.79]` for medium, `[0.2, 0.49]` for low;
- `source`: `image_and_name` or `name_only`;
- `material_finish`: one of the existing material finish values.

The confidence interval is an operational review band, not a calibrated statistical probability. It makes uncertainty sortable and auditable without claiming scientific measurement.

The cache stores `material_finish` as an audit snapshot. During application, it must match the finish resolved by `resolve_material_appearance`; a mismatch fails validation rather than silently changing the product finish.

## Public Data Contract

For products using the fallback, `public/data/stock.json` adds:

- `estimated_color_hex`;
- `estimated_color_confidence_band`;
- `estimated_color_confidence_interval`;
- `estimated_color_source`;
- `estimated_color_warning`;
- the existing `material_finish`;
- the existing `material_swatch_url`, now pointing to the estimated-color render.

Products with Pantone do not receive the estimated-color fields. Their existing `pantone`, `pantone_hex`, `material_finish` and `material_swatch_url` behavior remains unchanged.

## Build Integration

The normal data build loads the estimate cache and applies a record only after resolving Pantone and finish:

1. Resolve manufacturer Pantone and material finish using the current logic.
2. If `pantone_hex` is non-empty, ignore any cached estimate for that product.
3. If `pantone_hex` is empty, look up the product id in the estimate cache.
4. Validate hexadecimal RGB, confidence band and interval, source, finish and required evidence.
5. Add estimated-color fields to the public product only when the cache record is valid.
6. Leave products without a valid estimate on the current name-based CSS fallback.

The build remains network-independent. It never calls an AI service, downloads an image or derives a new estimate automatically.

## Rendering

The existing Pillow renderer remains the single material-rendering implementation. Pantone assets keep their current names. Estimated assets use a separate stable namespace:

```text
assets/material-swatches/estimated-<product-id>-<finish>-v1.webp
```

The unique key includes product id, finish and renderer version. It deliberately does not use a Pantone prefix. If an estimate changes while renderer version stays constant, generation overwrites that product's estimated asset deterministically.

Generation must:

- render only products with an empty `pantone_hex` and valid `estimated_color_hex`;
- preserve the existing Pantone path for every resolved Pantone product;
- write `material_swatch_url` only after a valid non-empty WebP exists;
- remain idempotent when estimates and renderer version do not change;
- never create a comparison board or other review image.

## Initial Population

The current payload contains 301 products without resolved Pantone. Initial population processes them in batches of ten and reports progress after every completed batch.

- Products with a local image use image plus name and may receive high, medium or low confidence.
- Products without a local image use normalized color, material, variant, brand and provider names. They always receive low confidence with `source: name_only`.
- Equivalent presentations may share the same visible-color reasoning, but each `product_id` receives an explicit cache record because images, finish and future manufacturer data can diverge.
- The twelve approved pilot values seed the cache and remain subject to the same validation as all other records.

## Failure Handling

- Cached estimate for a Pantone product: ignore it and report it in the generation audit; do not modify the Pantone product.
- Invalid hexadecimal value: fail validation with the product id.
- Confidence band and interval mismatch: fail validation with the product id.
- Name-only record above low confidence: fail validation.
- Finish mismatch: fail validation with cached and resolved finishes.
- Missing local image for `image_and_name`: fail validation.
- Render failure: do not publish `material_swatch_url` for that estimate.
- Missing cache record: retain the current CSS fallback and report the uncovered product.

## Testing

### Unit Tests

- load and validate a complete estimate cache;
- reject invalid RGB values, confidence intervals, sources and missing evidence;
- require low confidence for name-only records;
- reject image-and-name records whose local image is missing;
- reject cached and resolved finish mismatches;
- ensure a Pantone product ignores an estimate and keeps its existing fields;
- ensure a no-Pantone product receives the estimated fields;
- verify stable estimated asset paths and renderer versions;
- verify estimated generation is idempotent;
- verify Pantone assets are not regenerated or renamed by the fallback path.

### Integration Verification

- run `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos`;
- generate material swatches twice and confirm the second run produces no data changes;
- verify every no-Pantone product has a valid cache record and non-empty rendered asset;
- verify no Pantone product has estimated-color fields;
- verify every referenced WebP exists and is non-empty;
- run `npm run build`;
- confirm Git status contains only the intended estimate, pipeline, test, generated JSON and generated asset changes.

## Scope Boundaries

This feature does not:

- change, infer or synthesize Pantone values;
- process products that already resolve a Pantone RGB value;
- call GPT-5.6 Luna or another API during normal builds;
- add runtime API calls to the GitHub Pages site;
- guarantee physical color matching;
- create contact sheets, comparison boards or visual findings reports;
- redesign the frontend or modify the in-progress summary and quote-list work.
