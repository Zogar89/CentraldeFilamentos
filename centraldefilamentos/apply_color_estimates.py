from __future__ import annotations

import argparse
from pathlib import Path

from centraldefilamentos.color_estimates import apply_color_estimates_to_stock, load_color_estimates


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply cached color estimates to stock JSON.")
    parser.add_argument("--stock-json", default="public/data/stock.json")
    parser.add_argument("--cache", default="centraldefilamentos/data/color_estimates.json")
    parser.add_argument("--public-dir", default="public")
    args = parser.parse_args()

    applied = apply_color_estimates_to_stock(
        Path(args.stock_json),
        load_color_estimates(Path(args.cache)),
        Path(args.public_dir),
    )
    print(f"Applied estimated colors to {applied} products")


if __name__ == "__main__":
    main()
