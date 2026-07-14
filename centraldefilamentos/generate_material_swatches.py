from __future__ import annotations

import argparse
from pathlib import Path

from centraldefilamentos.material_swatches import apply_material_swatches_to_stock


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic material swatches for stock products")
    parser.add_argument("--stock-json", type=Path, default=Path("public/data/stock.json"))
    parser.add_argument("--public-dir", type=Path, default=Path("public"))
    args = parser.parse_args()
    generated = apply_material_swatches_to_stock(args.stock_json, args.public_dir)
    print(f"Generated {generated} material swatches")


if __name__ == "__main__":
    main()
