"""Calibration tracking: Brier scores, accuracy tracking, and calibration corrections.

This module is the core learning feedback loop. When trades resolve, Claude records
outcomes, computes Brier scores, tracks per-category accuracy, and auto-generates
calibration corrections that feed back into future analysis.
"""

import json
from datetime import datetime, timezone

from lib.logging_setup import get_logger

log = get_logger("calibration")

# The 6 standard market categories
CATEGORIES = ["crypto", "politics", "sports", "commodities", "entertainment", "finance"]


def compute_brier_score(stated_prob: float, outcome: str) -> float:
    """Compute Brier score: (stated_prob - actual)^2.

    Args:
        stated_prob: Probability stated at entry (0.0 to 1.0).
        outcome: "WIN" or "LOSS".

    Returns:
        Brier score (0.0 = perfect, 1.0 = worst).
    """
    actual = 1.0 if outcome == "WIN" else 0.0
    return (stated_prob - actual) ** 2


def interpret_error(error_pp: float, n_trades: int) -> str:
    """Interpret calibration error as a human-readable assessment.

    Args:
        error_pp: Average error in percentage points (positive = underconfident,
                  negative = overconfident).
        n_trades: Number of trades in the sample.

    Returns:
        Human-readable calibration assessment with recommendations.
    """
    if n_trades < 5:
        return "INSUFFICIENT DATA (< 5 trades)"
    if error_pp > 20:
        return "UNDERCONFIDENT -- can size up slightly"
    elif error_pp > 10:
        return "Slightly underconfident"
    elif error_pp >= -10:
        return "WELL CALIBRATED"
    elif error_pp >= -20:
        return "Slightly OVERCONFIDENT -- require +6pp edge, -25% size"
    elif error_pp >= -30:
        return "OVERCONFIDENT -- require +8pp edge, -50% size"
    else:
        return "SEVERELY OVERCONFIDENT -- require +10pp edge, max 1% bankroll"


def record_calibration_outcome(store, market_id: str, category: str,
                               stated_prob: float, outcome: str,
                               pnl: float = 0.0, notes: str = "") -> dict:
    """Record a trade outcome to the calibration database.

    Args:
        store: DataStore instance with calibration_records table.
        market_id: Market condition ID.
        category: Market category (one of CATEGORIES).
        stated_prob: Probability stated at entry (0.0 to 1.0).
        outcome: "WIN" or "LOSS".
        pnl: Realized P&L in dollars.
        notes: Optional notes.

    Returns:
        Dict with brier_score, error_pp, category, market_id.
    """
    brier = compute_brier_score(stated_prob, outcome)
    actual = 1 if outcome == "WIN" else 0
    error_pp = (stated_prob - actual) * 100  # positive = underconfident, negative = overconfident
    now = datetime.now(timezone.utc).isoformat()

    store.conn.execute(
        """INSERT INTO calibration_records
           (timestamp, market_id, category, stated_prob, actual_outcome,
            brier_score, error_pp, pnl, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (now, market_id, category, stated_prob, actual, brier, error_pp, pnl, notes)
    )
    store.conn.commit()

    log.info(
        f"Recorded outcome: {market_id} {category} prob={stated_prob:.2f} "
        f"outcome={outcome} brier={brier:.4f} error_pp={error_pp:.1f}"
    )

    return {
        "brier_score": brier,
        "error_pp": error_pp,
        "category": category,
        "market_id": market_id,
    }


def get_calibration_summary(store) -> dict:
    """Compute calibration summary from all recorded outcomes.

    Args:
        store: DataStore instance.

    Returns:
        Dict structured like calibration.json schema with summary and categories.
    """
    rows = store.conn.execute("SELECT * FROM calibration_records").fetchall()
    rows = [dict(r) for r in rows]

    if not rows:
        categories = {}
        for cat in CATEGORIES:
            categories[cat] = {
                "trades": 0, "brier": None, "error_pp": None,
                "win_rate": None, "total_pnl": 0.0,
            }
        return {
            "summary": {
                "total_trades": 0,
                "overall_brier": None,
                "overall_error_pp": None,
            },
            "categories": categories,
        }

    # Overall stats
    total = len(rows)
    overall_brier = sum(r["brier_score"] for r in rows) / total
    overall_error_pp = sum(r["error_pp"] for r in rows) / total
    overall_wins = sum(1 for r in rows if r["actual_outcome"] == 1)
    overall_win_rate = overall_wins / total

    # Per-category stats
    categories = {}
    for cat in CATEGORIES:
        cat_rows = [r for r in rows if r["category"] == cat]
        if not cat_rows:
            categories[cat] = {
                "trades": 0, "brier": None, "error_pp": None,
                "win_rate": None, "total_pnl": 0.0,
            }
        else:
            n = len(cat_rows)
            wins = sum(1 for r in cat_rows if r["actual_outcome"] == 1)
            categories[cat] = {
                "trades": n,
                "brier": sum(r["brier_score"] for r in cat_rows) / n,
                "error_pp": sum(r["error_pp"] for r in cat_rows) / n,
                "win_rate": wins / n,
                "total_pnl": sum(r["pnl"] for r in cat_rows),
            }

    return {
        "summary": {
            "total_trades": total,
            "overall_brier": overall_brier,
            "overall_error_pp": overall_error_pp,
            "overall_win_rate": overall_win_rate,
        },
        "categories": categories,
    }


def get_calibration_health(store) -> dict:
    """Check calibration health for the live trading gate.

    Returns a structured health report with per-category bias data.
    A category is "unhealthy" if its average error_pp <= -20 (overconfident
    by 20+ percentage points) with >= 5 trades.

    Args:
        store: DataStore instance.

    Returns:
        Dict with:
          - healthy (bool): True if no category exceeds -20pp bias
          - categories (dict): per-category {trades, error_pp, healthy, assessment}
          - worst_bias (float|None): most negative error_pp across categories
          - worst_category (str|None): category with worst bias
    """
    summary = get_calibration_summary(store)
    categories = {}
    worst_bias = None
    worst_category = None

    for cat in CATEGORIES:
        stats = summary["categories"].get(cat, {})
        n = stats.get("trades", 0)
        error_pp = stats.get("error_pp")

        if n < 5 or error_pp is None:
            categories[cat] = {
                "trades": n,
                "error_pp": error_pp,
                "healthy": True,  # insufficient data = not unhealthy
                "assessment": "INSUFFICIENT DATA" if n < 5 else "NO DATA",
            }
        else:
            cat_healthy = error_pp > -20
            assessment = interpret_error(error_pp, n)
            categories[cat] = {
                "trades": n,
                "error_pp": round(error_pp, 2),
                "healthy": cat_healthy,
                "assessment": assessment,
            }
            if worst_bias is None or error_pp < worst_bias:
                worst_bias = error_pp
                worst_category = cat

    overall_healthy = all(c["healthy"] for c in categories.values())

    return {
        "healthy": overall_healthy,
        "categories": categories,
        "worst_bias": round(worst_bias, 2) if worst_bias is not None else None,
        "worst_category": worst_category,
    }


def generate_corrections(store) -> list[dict]:
    """Generate calibration corrections for categories with significant bias.

    For each category with >= 5 trades, if |avg error_pp| > 10, generate a
    correction entry.

    Args:
        store: DataStore instance.

    Returns:
        List of correction dicts with category, direction, amount, reason, etc.
    """
    summary = get_calibration_summary(store)
    corrections = []

    for cat, stats in summary["categories"].items():
        if stats["trades"] < 5:
            continue

        avg_error = stats["error_pp"]
        if abs(avg_error) <= 10:
            continue

        n = stats["trades"]
        win_rate = stats["win_rate"]
        avg_stated = sum(
            r["stated_prob"] for r in
            store.conn.execute(
                "SELECT stated_prob FROM calibration_records WHERE category = ?",
                (cat,)
            ).fetchall()
        ) / n

        if avg_error < -10:
            direction = "subtract"
        else:
            direction = "add"

        # Conservative 70% of observed error, capped at 20pp
        amount = min(abs(avg_error) / 100 * 0.7, 0.20)

        assessment = interpret_error(avg_error, n)
        reason = (
            f"{assessment} over {n} trades "
            f"(avg stated {avg_stated * 100:.1f}%, actual win rate {win_rate * 100:.1f}%)"
        )

        corrections.append({
            "category": cat,
            "direction": direction,
            "amount": round(amount, 4),
            "reason": reason,
            "data_points": n,
            "expires_after_n_trades": 10,
        })

    return corrections


def regenerate_calibration_json(store, json_path: str = "knowledge/calibration.json") -> None:
    """Regenerate calibration.json from current DB state.

    Called after each record_outcome to keep the JSON file fresh for
    the calibration-check skill to consume.

    Args:
        store: DataStore instance.
        json_path: Path to write the calibration JSON file.
    """
    summary = get_calibration_summary(store)
    corrections = generate_corrections(store)
    now = datetime.now(timezone.utc).isoformat()

    # Build the calibration.json structure matching seed schema
    output = {
        "schema_version": "1.0",
        "description": "Calibration tracking - populated by Claude after each trade resolution",
        "last_updated": now,
        "summary": {
            "total_trades": summary["summary"]["total_trades"],
            "overall_brier": summary["summary"]["overall_brier"],
            "overall_error_pp": summary["summary"]["overall_error_pp"],
        },
        "categories": {},
        "corrections": {
            "description": "Category-level calibration corrections. Populated when error_pp exceeds threshold.",
            "active": corrections,
        },
    }

    # Populate all 6 categories (always present, nulls for empty)
    for cat in CATEGORIES:
        cat_stats = summary["categories"].get(cat, {})
        output["categories"][cat] = {
            "trades": cat_stats.get("trades", 0),
            "brier": cat_stats.get("brier"),
            "error_pp": cat_stats.get("error_pp"),
            "win_rate": cat_stats.get("win_rate"),
            "total_pnl": cat_stats.get("total_pnl", 0.0),
        }

    # Ensure parent directory exists
    import os
    os.makedirs(os.path.dirname(json_path) if os.path.dirname(json_path) else ".", exist_ok=True)

    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

    log.info(f"Regenerated {json_path}: {summary['summary']['total_trades']} trades")
