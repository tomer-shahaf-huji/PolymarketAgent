"""
Arbitrage Scanner for implication pairs.

Checks current market odds to find risk-free profit opportunities.
No LLM needed — pure math on prices. Runs on every odds update.

Given an implication pair (market1 → market2):
  - market1 = trigger/child (more specific event)
  - market2 = implied/parent (broader event)
  - If market1 YES, then market2 MUST also be YES

The trade when Price(child YES) > Price(parent YES):
  - Buy YES on market2 (parent)  → costs market2_yes
  - Buy NO on market1 (child)    → costs market1_no
  - Total cost = market2_yes + market1_no
  - Guaranteed payout = $1.00
  - Profit = 1.0 - cost
"""
from typing import Optional

import pandas as pd


def scan_pair(
    market1_yes: Optional[float],
    market1_no: Optional[float],
    market2_yes: Optional[float],
    market2_no: Optional[float],
    market1_title: str = "",
    market2_title: str = "",
    market1_url: str = "",
    market2_url: str = "",
) -> dict:
    """
    Check if an implication pair has an arbitrage opportunity.

    Args:
        market1_yes: Child/trigger market YES price
        market1_no: Child/trigger market NO price
        market2_yes: Parent/implied market YES price
        market2_no: Parent/implied market NO price
        market1_title: Child market title (for trade instructions)
        market2_title: Parent market title (for trade instructions)
        market1_url: Child market URL
        market2_url: Parent market URL

    Returns:
        Dict with arbitrage details
    """
    # Need valid odds on both markets
    if any(v is None for v in [market1_yes, market1_no, market2_yes, market2_no]):
        return {
            "has_arbitrage": False,
            "profit": 0.0,
            "profit_pct": 0.0,
            "cost": None,
            "buy_yes_title": None,
            "buy_yes_price": None,
            "buy_yes_url": None,
            "buy_no_title": None,
            "buy_no_price": None,
            "buy_no_url": None,
        }

    # The trade: Buy YES parent + Buy NO child
    cost = market2_yes + market1_no
    profit = 1.0 - cost
    has_arb = profit > 0

    return {
        "has_arbitrage": has_arb,
        "profit": round(profit, 6),
        "profit_pct": round(profit * 100, 2),
        "cost": round(cost, 6),
        "buy_yes_title": market2_title,
        "buy_yes_price": market2_yes,
        "buy_yes_url": market2_url,
        "buy_no_title": market1_title,
        "buy_no_price": market1_no,
        "buy_no_url": market1_url,
    }


def scan_pair_from_row(row: pd.Series) -> dict:
    """
    Scan a pair DataFrame row for arbitrage. Convenience wrapper for API use.

    Args:
        row: A pandas Series from the market_pairs parquet DataFrame

    Returns:
        Dict with arbitrage details
    """
    return scan_pair(
        market1_yes=float(row["market1_yes_odds"]) if pd.notna(row.get("market1_yes_odds")) else None,
        market1_no=float(row["market1_no_odds"]) if pd.notna(row.get("market1_no_odds")) else None,
        market2_yes=float(row["market2_yes_odds"]) if pd.notna(row.get("market2_yes_odds")) else None,
        market2_no=float(row["market2_no_odds"]) if pd.notna(row.get("market2_no_odds")) else None,
        market1_title=row.get("market1_title", ""),
        market2_title=row.get("market2_title", ""),
        market1_url=row.get("market1_url", ""),
        market2_url=row.get("market2_url", ""),
    )
