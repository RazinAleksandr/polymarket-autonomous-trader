#!/usr/bin/env python3
"""Record a trade outcome to calibration database and regenerate calibration.json."""

import argparse
import json
import os
import sys

# Ensure project root is on Python path so `lib` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.config import load_config
from lib.db import DataStore
from lib.errors import error_exit, EXIT_INVALID_ARG
from lib.logging_setup import get_logger
from lib.signals import register_shutdown_handler
from lib.calibration import record_calibration_outcome, regenerate_calibration_json

VALID_CATEGORIES = ["crypto", "politics", "sports", "commodities", "entertainment", "finance"]


def main():
    parser = argparse.ArgumentParser(
        description="Record a trade outcome to calibration database and regenerate calibration.json"
    )
    parser.add_argument(
        "--market-id",
        type=str,
        required=True,
        dest="market_id",
        help="Market condition ID",
    )
    parser.add_argument(
        "--stated-prob",
        type=float,
        required=True,
        dest="stated_prob",
        help="Stated probability at entry (0.0-1.0)",
    )
    parser.add_argument(
        "--actual",
        type=str,
        required=True,
        choices=["WIN", "LOSS"],
        help="Trade outcome: WIN or LOSS",
    )
    parser.add_argument(
        "--category",
        type=str,
        required=True,
        help="Market category (crypto, politics, sports, commodities, entertainment, finance)",
    )
    parser.add_argument(
        "--pnl",
        type=float,
        default=0.0,
        help="Realized P&L in dollars (default: 0.0)",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Optional notes",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )

    args = parser.parse_args()
    config = load_config(args)
    register_shutdown_handler()
    log = get_logger("record_outcome", config)

    # Validate stated_prob range
    if args.stated_prob < 0.0 or args.stated_prob > 1.0:
        error_exit(
            f"stated_prob must be between 0.0 and 1.0, got {args.stated_prob}",
            "INVALID_STATED_PROB",
            EXIT_INVALID_ARG,
        )

    # Validate category
    if args.category not in VALID_CATEGORIES:
        error_exit(
            f"category must be one of {VALID_CATEGORIES}, got '{args.category}'",
            "INVALID_CATEGORY",
            EXIT_INVALID_ARG,
        )

    try:
        store = DataStore(config.db_path)

        result = record_calibration_outcome(
            store,
            args.market_id,
            args.category,
            args.stated_prob,
            args.actual,
            args.pnl,
            args.notes,
        )

        # Determine calibration.json path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(project_root, "knowledge", "calibration.json")
        regenerate_calibration_json(store, json_path=json_path)

        store.close()

        # Build output
        output = {
            "market_id": args.market_id,
            "category": args.category,
            "stated_prob": args.stated_prob,
            "actual": args.actual,
            "brier_score": result["brier_score"],
            "error_pp": result["error_pp"],
            "pnl": args.pnl,
        }

        indent = 2 if args.pretty else None
        json.dump(output, sys.stdout, indent=indent)
        sys.stdout.write("\n")

    except Exception as e:
        log.error(f"Record outcome failed: {e}")
        error_exit(str(e), "RECORD_OUTCOME_FAILED")


if __name__ == "__main__":
    main()
