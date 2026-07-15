from __future__ import annotations

import argparse
from pathlib import Path

from centraldefilamentos.material_swatches import apply_material_swatches_to_stock


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic material swatches for stock products")
    parser.add_argument("--stock-json", type=Path, default=Path("public/data/stock.json"))
    parser.add_argument("--public-dir", type=Path, default=Path("public"))
    args = parser.parse_args()
    def report_progress(completed: int, total: int) -> None:
        if completed % 10 == 0 or completed == total:
            print(f"Rendered estimated colors {completed}/{total}")

    generated = apply_material_swatches_to_stock(
        args.stock_json,
        args.public_dir,
        progress=report_progress,
    )
    print(f"Generated {generated} material swatches")


if __name__ == "__main__":
    main()
