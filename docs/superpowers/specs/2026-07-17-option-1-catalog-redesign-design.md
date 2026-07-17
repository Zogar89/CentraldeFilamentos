# Option 1 Catalog Redesign

## Objective

Replace the current table-first home screen with the approved Option 1 experience: the maker chooses a material first, explores colors only inside that material, checks exact provider stock, and builds a local quote list without leaving the catalog.

## Product rule

Material is a hard constraint. A selected color never broadens the result set to another material. The initial state is PLA because it is the most common entry point in the current catalog, but the user can switch to PETG, ABS, TPU, Nylon, ASA, or the remaining materials grouped as Otros.

## Desktop layout

- A compact header contains the brand, global search, access to color comparison, and the current quote count.
- The main content and quote workspace form a two-column layout. The catalog is fluid; the quote workspace is a stable right rail.
- The catalog begins with material cards. Each card uses a real catalog image when available and exposes a clear selected state.
- A horizontal color ribbon contains only colors that exist for the selected material. Selecting a color filters the results and shows a compact context row with a link to compare tones.
- Secondary filters are diameter, presentation, weight, brand, provider, and stock. They never remove or weaken the active material constraint.
- Results use compact product rows instead of the old dense table. Every row shows a real product image, material color, product identity, exact presentation, stock by provider, and an add-to-quote action.
- The right rail reuses the current local quote state, quantity editing, provider coverage, JSON import/export, and WhatsApp message workflow.

## Mobile layout

- Material cards and colors become horizontal scrollers with 44 px minimum controls.
- Filters wrap into a compact disclosure.
- Product rows stack their provider availability while keeping the add action visible.
- The persistent desktop quote rail becomes the existing accessible drawer, opened by a sticky quote action.

## Existing behavior to preserve

- Static GitHub Pages architecture and `public/data/stock.json` contract.
- `localStorage` quote persistence, read-only protection for newer schemas, import/export, quantity controls, provider coverage, and WhatsApp messages.
- Image preview, accessibility semantics, focus management, reduced-motion behavior, and responsive routes.
- Existing Color Picker route. The new catalog links to it for detailed PLA comparison instead of duplicating its perceptual comparison engine.
- Existing URLs and page entry points.

## Visual system

- Light neutral background, white surfaces, teal accent, soft gray borders, and green stock status from the approved mock.
- Use the existing favicon as the brand asset and real product images from the generated catalog.
- One 12 px radius system for major surfaces and 8 px for compact controls.
- Typography remains system-native to avoid a new external font dependency.
- Motion is limited to selection, quote feedback, and drawers; reduced motion disables transitions.

## Empty, loading, and error states

- Loading keeps a clear catalog status message.
- A failed stock payload offers retry without losing a saved quote.
- A material or filter combination with no results explains the constraint and offers to clear secondary filters while retaining the selected material.
- An empty quote rail explains that items can be added from result rows and disables provider comparison.

## Acceptance criteria

- The home route opens with PLA visibly selected.
- Selecting a material limits colors and products to that material.
- Selecting a color never shows the same color in another material.
- Search and secondary filters combine with material and color.
- Provider stock values remain exact and tied to the published source rows.
- Adding a product updates the desktop quote rail without opening a redundant drawer; on mobile it opens the quote drawer.
- The existing provider comparison and WhatsApp preparation flow still works.
- Desktop and mobile have no horizontal document overflow, clipped primary controls, broken images, serious accessibility violations, or console errors.

## Approved visual truth

`C:/Users/Gabriel/.codex/generated_images/019f6ce6-9cac-7cf2-acf1-5b815f108303/exec-e997e27d-a116-43ff-b999-67b34aa03aab.png`

The approved image defines the hierarchy, palette, density, two-column desktop composition, material-first interaction, color ribbon, product rows, and quote rail. Real catalog data and existing product constraints take precedence over invented labels or providers in the image.
