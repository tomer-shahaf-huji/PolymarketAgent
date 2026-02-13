"""
Portfolio service for simulated trading.

Handles trade execution, portfolio valuation, and persistence.
All trades are simulation only -- no real money involved.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from backend.models.portfolio import Portfolio, Position

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
PORTFOLIO_FILE = PROJECT_ROOT / "data" / "portfolio.json"
PAIRS_FILE = PROJECT_ROOT / "data" / "market_pairs.parquet"


def get_portfolio() -> Portfolio:
    """Load the current portfolio from disk."""
    return Portfolio.load_from_json(str(PORTFOLIO_FILE))


def save_portfolio(portfolio: Portfolio) -> None:
    """Save the portfolio to disk."""
    portfolio.save_to_json(str(PORTFOLIO_FILE))


def reset_portfolio() -> Portfolio:
    """Reset portfolio to initial $10,000 state."""
    portfolio = Portfolio()
    save_portfolio(portfolio)
    return portfolio


def get_current_prices() -> Dict[str, Dict[str, Optional[float]]]:
    """
    Load current market prices from the pairs parquet file.

    Returns:
        Dict mapping market_id -> {"yes_odds": float, "no_odds": float}
    """
    if not PAIRS_FILE.exists():
        return {}

    df = pd.read_parquet(str(PAIRS_FILE))
    prices = {}

    for _, row in df.iterrows():
        m1_id = row.get("market1_id")
        m2_id = row.get("market2_id")

        if m1_id and m1_id not in prices:
            prices[m1_id] = {
                "yes_odds": float(row["market1_yes_odds"]) if pd.notna(row.get("market1_yes_odds")) else None,
                "no_odds": float(row["market1_no_odds"]) if pd.notna(row.get("market1_no_odds")) else None,
            }
        if m2_id and m2_id not in prices:
            prices[m2_id] = {
                "yes_odds": float(row["market2_yes_odds"]) if pd.notna(row.get("market2_yes_odds")) else None,
                "no_odds": float(row["market2_no_odds"]) if pd.notna(row.get("market2_no_odds")) else None,
            }

    return prices


def get_position_current_price(position: Position, prices: Dict) -> Optional[float]:
    """Get the current market price relevant to a position's outcome."""
    market_prices = prices.get(position.market_id)
    if not market_prices:
        return None

    if position.outcome == "YES":
        return market_prices.get("yes_odds")
    else:
        return market_prices.get("no_odds")


def get_portfolio_with_values() -> Dict[str, Any]:
    """
    Return portfolio with live position valuations.

    Each position gets current_price, current_value, and pnl fields
    based on the latest market prices from the parquet data.
    """
    portfolio = get_portfolio()
    prices = get_current_prices()

    positions_with_values = []
    total_position_value = 0.0

    for pos in portfolio.positions:
        current_price = get_position_current_price(pos, prices)
        current_value = pos.shares * current_price if current_price is not None else None

        pos_dict = pos.model_dump()
        pos_dict["current_price"] = current_price
        pos_dict["current_value"] = round(current_value, 2) if current_value is not None else None
        pos_dict["pnl"] = round(current_value - pos.cost_basis, 2) if current_value is not None else None
        positions_with_values.append(pos_dict)

        if current_value is not None:
            total_position_value += current_value

    return {
        "cash": round(portfolio.cash, 2),
        "starting_balance": portfolio.starting_balance,
        "positions": positions_with_values,
        "position_value": round(total_position_value, 2),
        "total_value": round(portfolio.cash + total_position_value, 2),
        "total_pnl": round((portfolio.cash + total_position_value) - portfolio.starting_balance, 2),
        "trade_count": portfolio.trade_count,
    }


def execute_pair_trade(pair_id: str, amount: float) -> Dict[str, Any]:
    """
    Execute a simulated arbitrage trade on a pair.

    Buys:
      - $amount of NO shares on market1 (child/trigger) at market1_no price
      - $amount of YES shares on market2 (parent/implied) at market2_yes price
    Total cost = 2 * amount

    Args:
        pair_id: The pair to trade on
        amount: Dollar amount per side (total cost will be 2 * amount)

    Returns:
        Dict with trade result and updated portfolio

    Raises:
        ValueError: If pair not found, prices unavailable, or insufficient cash
    """
    if not PAIRS_FILE.exists():
        raise ValueError("Market pairs data not found. Run the pipeline first.")

    df = pd.read_parquet(str(PAIRS_FILE))
    pair_row = df[df["pair_id"] == pair_id]

    if pair_row.empty:
        raise ValueError(f"Pair not found: {pair_id}")

    row = pair_row.iloc[0]

    # Extract prices
    market1_no = float(row["market1_no_odds"]) if pd.notna(row.get("market1_no_odds")) else None
    market2_yes = float(row["market2_yes_odds"]) if pd.notna(row.get("market2_yes_odds")) else None

    if market1_no is None or market2_yes is None:
        raise ValueError("Market prices not available for this pair.")

    if market1_no <= 0 or market2_yes <= 0:
        raise ValueError("Market prices must be positive.")

    total_cost = 2 * amount

    # Load portfolio and check cash
    portfolio = get_portfolio()

    if portfolio.cash < total_cost:
        raise ValueError(
            f"Insufficient cash. Need ${total_cost:.2f} but only have ${portfolio.cash:.2f}."
        )

    # Calculate shares: shares = amount / price
    market1_no_shares = amount / market1_no
    market2_yes_shares = amount / market2_yes

    # Create positions
    trade_num = portfolio.trade_count + 1

    pos1 = Position(
        position_id=f"{pair_id}_m1_NO_{trade_num}",
        pair_id=pair_id,
        market_id=row["market1_id"],
        market_title=row.get("market1_title", ""),
        outcome="NO",
        shares=round(market1_no_shares, 6),
        avg_price=market1_no,
        cost_basis=round(amount, 2),
    )

    pos2 = Position(
        position_id=f"{pair_id}_m2_YES_{trade_num}",
        pair_id=pair_id,
        market_id=row["market2_id"],
        market_title=row.get("market2_title", ""),
        outcome="YES",
        shares=round(market2_yes_shares, 6),
        avg_price=market2_yes,
        cost_basis=round(amount, 2),
    )

    # Update portfolio
    portfolio.cash -= total_cost
    portfolio.cash = round(portfolio.cash, 2)
    portfolio.positions.append(pos1)
    portfolio.positions.append(pos2)
    portfolio.trade_count = trade_num

    save_portfolio(portfolio)

    return {
        "success": True,
        "trade": {
            "pair_id": pair_id,
            "amount_per_side": amount,
            "total_cost": total_cost,
            "market1_no_shares": round(market1_no_shares, 6),
            "market1_no_price": market1_no,
            "market2_yes_shares": round(market2_yes_shares, 6),
            "market2_yes_price": market2_yes,
        },
        "portfolio": get_portfolio_with_values(),
    }
