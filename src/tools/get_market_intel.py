#!/usr/bin/env python3
"""Get market intelligence for trading decisions.

Provides macro regime detection, crypto Fear & Greed, and category news sentiment.

Usage:
    python tools/get_market_intel.py --category crypto --pretty
    python tools/get_market_intel.py --overview --pretty
"""

import argparse
import json
import os
import sys

# Ensure project root is on Python path so `lib` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.errors import error_exit, EXIT_INVALID_ARG
from lib.logging_setup import get_logger
from lib.signals import register_shutdown_handler
from lib.market_intel import get_category_intel, get_market_overview, CATEGORIES

log = get_logger("get_market_intel")


def main():
    parser = argparse.ArgumentParser(
        description="Get market intelligence for trading decisions"
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=CATEGORIES,
        help=f"Category for category-specific intel. Choices: {', '.join(CATEGORIES)}",
    )
    parser.add_argument(
        "--overview",
        action="store_true",
        help="Return cross-category market overview with all macro indicators",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )

    args = parser.parse_args()

    # Validation: must provide either --category or --overview, not both, not neither
    if not args.category and not args.overview:
        error_exit(
            "Must provide either --category or --overview",
            "MISSING_ARG",
            EXIT_INVALID_ARG,
        )
    if args.category and args.overview:
        error_exit(
            "Cannot use both --category and --overview at the same time",
            "CONFLICTING_ARGS",
            EXIT_INVALID_ARG,
        )

    register_shutdown_handler()
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")

    if args.category:
        result = get_category_intel(args.category, api_key)
    else:
        result = get_market_overview(api_key)

    indent = 2 if args.pretty else None
    json.dump(result, sys.stdout, indent=indent)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
