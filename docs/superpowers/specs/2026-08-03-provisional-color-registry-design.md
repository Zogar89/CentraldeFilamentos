# Provisional Color Registry Design

## Objective

Prevent an unseen provider color from collapsing into `Sin color`, sharing a product id with another offer, or stopping the stock capture. A newly observed color must enter the catalog in the same successful capture with a stable identity and an explicit provisional state. It must not receive invented RGB, Pantone, or an unreviewed equivalence to an existing color.

The design complements the explicit `COLOR_RULES` list. Known rules remain the authoritative path for established names and aliases.

## Product Rules

- A known `COLOR_RULES` match remains canonical and has no provisional state.
- A stocked product that needs a color but resolves to `Sin color` becomes a provisional candidate before product grouping.
- A provisional candidate gets a deterministic identity from its source, normalized product context, and normalized supplier title. Two distinct supplier titles cannot collapse into one product card solely because both lack a known color rule.
- The first observed display label is retained for that candidate. Promoting it from `provisional` to `approved` changes only review status, never its identity or existing product id.
- The public product receives `color_review_status: "provisional"` only while the candidate remains provisional. Existing products keep their current public contract.
- The catalog displays a compact badge: `Color del proveedor · pendiente de normalizar` for that state. It does not claim a Pantone, RGB, physical match, or final supplier availability.
- PVA remains explicitly color-optional. A genuine PVA product without a color stays `Sin color` and never creates a candidate.
- If a title cannot yield a short human label, the product still receives a deterministic provisional identity and a source-title fallback label. Safety takes precedence over a pretty label.

## Durable Registry

Create `centraldefilamentos/data/color_registry.json` as versioned source-controlled state:

```json
{
  "version": 1,
  "candidates": {
    "grupo_senz|3n3|pla-silk|cascada": {
      "display_color": "Cascada",
      "status": "provisional",
      "source_id": "grupo_senz",
      "brand": "3N3",
      "variant": "PLA Silk",
      "first_seen_at": "2026-08-03T14:11:26-03:00",
      "last_seen_at": "2026-08-03T14:11:26-03:00",
      "examples": [
        "3N3 SILK CASCADA 1.75 MM X 1 KG"
      ]
    }
  }
}
```

The key is immutable and uses folded source, brand, variant, and candidate phrase. Records are written with stable JSON ordering. `examples` is a de-duplicated bounded list of supplier titles, so the state remains auditable without growing unboundedly.

Allowed statuses are `provisional` and `approved`. `approved` retains the same display color and candidate key but removes the public pending badge. A future alias-merging or identity migration is deliberately outside this change.

## Candidate Resolution and Build Flow

1. Load and validate the registry before collecting the public product payload.
2. Normalize each raw item using the current known rules.
3. If it has a known color, preserve the current path.
4. If its material is explicitly color-optional, preserve `Sin color` and do not observe it.
5. Otherwise derive a deterministic supplier candidate. The extractor removes recognizable brand, material/variant, diameter, weight, and presentation tokens; it uses the remaining phrase as a human label when safe and otherwise uses a source-title fallback.
6. Resolve the candidate from the registry or create an in-memory `provisional` record. Replace only the color used for grouping and identity; keep the original supplier title on the offer.
7. Group products and retain `_validate_unique_provider_offers` unchanged as the final integrity guard.
8. Add `color_review_status: "provisional"` to provisional public products, then render the catalog badge from that optional field.
9. Run existing quality checks. Only after a publishable build writes `stock.json`, write the updated registry, logs, snapshots, and history. A failed source or failed quality gate must not persist a transient candidate.
10. Add `centraldefilamentos/data/color_registry.json` to the Capture Stock Data commit list. It remains internal and is not copied to GitHub Pages.

The normal build remains offline with respect to color interpretation: it never calls an LLM, image model, browser automation, or external color service. The provider title is evidence of a supplier label, not proof of a visual value.

## Public Data and UI

Only provisional products receive the optional `color_review_status` field. Existing frontend readers remain backward-compatible because no established product gains a mandatory new field.

`CatalogExplorerResults.svelte` renders the pending badge next to the color/presentation identity. It must not change filtering, quote-list behavior, provider URLs, price/stock language, or material swatches. A provisional product may have no Pantone, image, estimate, or swatch; that is already a supported presentation state.

## Failure Handling

- Malformed registry JSON, duplicate keys, invalid status, missing required provenance, or an empty display color: fail the build before publication with the candidate key.
- Candidate extraction failure: publish the deterministic source-title fallback rather than `Sin color`; retain the raw title in the registry and technical log.
- A candidate seen again: refresh `last_seen_at` and examples deterministically; do not create another identity.
- A previously approved candidate seen again: keep its identity and omit the pending public field.
- Two unresolved titles from the same provider: generate different candidate identities and allow the duplicate-offer guard to validate the result.
- A PVA title without a color: remain colorless without a registry record.

## Observability

The technical build log records the number of provisional colors and their candidate keys. The business log uses a non-blocking warning that supplier-labeled colors were incorporated pending normalization. This makes the state discoverable without claiming that a failed capture succeeded or hiding a new label.

## Testing

- Registry parser accepts a valid candidate and rejects malformed version, key, status, dates, empty display label, and invalid examples.
- Two unseen Grupo Senz titles (`CASCADA`, `ZIRCONIA`) receive distinct provisional identities, generate registry entries, and do not raise repeated-provider validation. `PAPAYA` and `ALUMINIO` remain covered as known canonical colors by the original fix.
- Repeating the same input preserves candidate identity and does not duplicate examples.
- A known color keeps its current id and does not enter the registry.
- A colorless PVA item remains `Sin color` and does not enter the registry.
- An approved candidate preserves identity and removes `color_review_status`.
- A failed quality gate does not write registry state.
- Public serialization exposes the optional provisional status only when required.
- Frontend contract covers badge rendering only for `color_review_status: "provisional"`.
- The data-capture workflow stages the registry with the other internal generated state, without publishing it to `gh-pages`.
- Run `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos`, `npm.cmd run test:quote-list`, and `npm.cmd run build`.

## Scope Boundaries

This feature does not:

- replace `COLOR_RULES` or retroactively change known canonical colors;
- infer Pantone, RGB, image metadata, or material swatches for new candidates;
- auto-merge supplier aliases into an established color;
- add a runtime API, database, cookie, or server-side session;
- publish a failed-quality capture;
- remove the repeated-provider validation that caught the original incident.
