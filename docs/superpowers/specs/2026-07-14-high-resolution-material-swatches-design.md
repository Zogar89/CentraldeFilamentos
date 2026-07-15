# High-Resolution Material Swatches Design

## Goal

Remove visible blur when a material swatch is opened in the image preview while preserving the currently approved material model and its appearance.

## Root Cause

Material swatches are stored at 160 x 160 pixels and displayed at approximately 336 x 336 CSS pixels in the preview modal. The browser must enlarge the raster asset beyond its native size, which softens edges and finish detail.

## Design

- Preserve the existing shading model, finish profiles, lighting, rounded mask and lossless WebP output.
- Change the public output size from 160 x 160 to 320 x 320 pixels.
- Reuse the renderer's existing 320 x 320 internal render instead of downsampling it to 160 x 160. This improves preview sharpness without increasing the per-asset shading workload.
- Set supersampling to 1 because the native output now equals the previous internal render size.
- Increment `RENDERER_VERSION` from 1 to 2 so every generated URL changes and browsers cannot reuse an older 160 x 160 asset.
- Regenerate both Pantone and estimated material swatches at version 2. Products with Pantone continue to use only Pantone assets; products without Pantone continue to use estimated assets.
- Keep the table presentation at 24 x 24 CSS pixels and keep the existing preview modal dimensions.

## Data and Asset Contract

- Pantone URL: `assets/material-swatches/pantone-<pantone>-<finish>-v2.webp`.
- Estimated URL: `assets/material-swatches/estimated-<product-id>-<finish>-v2.webp`.
- Every referenced version 2 WebP must report native dimensions of 320 x 320 pixels.
- Version 1 files may remain unreferenced; generated-data cleanup can remove them only when the v2 coverage verification passes.
- No RGB estimate, confidence band, finish or Pantone metadata changes as part of this work.

## Testing

- Update the renderer contract test to require 320 x 320 output and version 2 URLs.
- Verify a rendered swatch keeps transparent rounded corners and the same lighting direction.
- Verify Pantone exclusion and estimated rendering behavior remain unchanged.
- Regenerate all referenced assets and assert every referenced WebP is 320 x 320.
- Run the complete Python suite and the Vite production build.

## Scope

This change affects only raster output resolution, asset versioning and generated WebP references. It does not redesign the swatch, change the frontend layout or alter color estimates.
