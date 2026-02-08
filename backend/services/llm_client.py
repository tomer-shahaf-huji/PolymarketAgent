"""
LLM Client for analyzing market pairs.

Uses an LLM to identify "implication pairs" (A -> B) from a list of keyword markets.
Currently supports mock mode (loads pre-computed responses from JSON files).
Real LLM API integration will be added later.
"""
import json
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from backend.models.market import Market


# Default limit on markets sent to the LLM per keyword
DEFAULT_MARKETS_LIMIT = 100


class LLMPairResult(BaseModel):
    """A single implication pair identified by the LLM."""

    trigger_market_id: str = Field(..., description="Index ID of the trigger market (A)")
    implied_market_id: str = Field(..., description="Index ID of the implied market (B)")
    reasoning: str = Field(..., description="Why A -> B")


# --- Prompt templates ---

SYSTEM_INSTRUCTIONS = """
You are an expert Market Logic Analyzer for an arbitrage trading bot.
Your goal is to identify "Subset Markets" where the resolution of one market (Market A) strictly implies the resolution of another market (Market B).

**The Logical Rule (A -> B):**
If Market A resolves to "YES", then Market B **MUST** logically also resolve to "YES".
If this condition is met, we call this a "Risk-Free Logic Chain."

**Criteria for Implication:**
1. **Numerical Inclusion:** If A is "BTC > $100k" and B is "BTC > $90k", then A -> B.
2. **Categorical Inclusion:** If A is "Taylor Swift wins Grammy" and B is "Female Artist wins Grammy", then A -> B.
3. **Temporal Inclusion:** If A is "Event happens by Tuesday" and B is "Event happens by Friday", then A -> B.

**Constraint:**
- Ignore all prices and odds. Focus ONLY on the definitions/text.
- Ignore correlation. "Oil prices up" often means "Gas prices up", but it is not a *logical guarantee*. Mark these as NO.
"""

FEW_SHOT_EXAMPLES = """
Here are examples of how you should analyze pairs:

---
**Example 1:**
Market A: "Bitcoin to hit $80k by Dec 31"
Market B: "Bitcoin to hit $75k by Dec 31"
**Analysis:** If BTC hits $80k, it must have passed $75k. The date is the same.
**Output:** MATCH (A -> B)

---
**Example 2:**
Market A: "Republicans win US Presidency"
Market B: "Donald Trump wins US Presidency"
**Analysis:** Trump is a Republican, but a different Republican could theoretically win. Trump winning implies Republicans win (B -> A), but Republicans winning does NOT imply Trump wins.
**Output:** NO MATCH (Direction wrong)

---
**Example 3:**
Market A: "SpaceX Starship launches in Q1"
Market B: "SpaceX Starship launches in 2024"
**Analysis:** Q1 is a subset of 2024. If it launches in Q1, it effectively launches in 2024.
**Output:** MATCH (A -> B)

---
**Example 4:**
Market A: "Ethereum hits $3000"
Market B: "Solana hits $200"
**Analysis:** These are correlated assets, but one happening does not force the other to happen by definition.
**Output:** NO MATCH
"""


def build_prompt(
    markets: List[Market],
    valid_indices: List[int],
    limit: int = DEFAULT_MARKETS_LIMIT,
) -> str:
    """
    Build the full LLM prompt for market pair analysis.

    Markets are tagged with their original index in the full keyword market list.
    Only markets at valid_indices (those with valid odds) are included in the prompt,
    but their IDs reflect their original position so results can be mapped back.

    Args:
        markets: Full list of Market objects (all keyword markets)
        valid_indices: Indices of markets with valid odds to include
        limit: Max number of markets to include in the prompt

    Returns:
        Full prompt string ready to send to an LLM
    """
    markets_text = ""
    for idx in valid_indices[:limit]:
        market = markets[idx]
        markets_text += f"ID {idx}: {market.title} (Description: {market.description})\n"

    prompt = f"""{SYSTEM_INSTRUCTIONS}

{FEW_SHOT_EXAMPLES}

---
**YOUR TASK:**
Analyze the following list of markets. Identify ALL pairs where Market A -> Market B.
Return the output as a JSON list of pairs: {{"trigger_market_id": "A", "implied_market_id": "B", "reasoning": "..."}}

**MARKET LIST:**
{markets_text}
"""
    return prompt


def _get_mock_path(keyword: str) -> Path:
    """Get the path to the mock response file for a keyword."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "data" / "mock" / f"{keyword}_llm_response.json"


def analyze_markets(
    keyword: str,
    markets: List[Market],
    valid_indices: List[int],
    use_mock: bool = True,
) -> List[LLMPairResult]:
    """
    Analyze a list of markets to identify implication pairs (A -> B).

    In mock mode, loads pre-computed results from data/mock/{keyword}_llm_response.json.
    In real mode (future), will send the prompt to an LLM API.

    Args:
        keyword: The keyword for this market group (e.g., "Iran", "Trump")
        markets: Full list of Market objects (all keyword markets)
        valid_indices: Indices of markets with valid odds
        use_mock: If True, use mock responses. If False, call real LLM API.

    Returns:
        List of LLMPairResult objects

    Raises:
        NotImplementedError: If use_mock=False (real LLM not yet configured)
        FileNotFoundError: If mock file doesn't exist for the given keyword
    """
    if not use_mock:
        # Placeholder for real LLM API integration
        _prompt = build_prompt(markets, valid_indices)
        raise NotImplementedError(
            "Real LLM API not configured yet. "
            "Set use_mock=True or add your LLM API credentials."
        )

    # Mock mode: load from JSON file
    mock_path = _get_mock_path(keyword)

    if not mock_path.exists():
        raise FileNotFoundError(
            f"Mock LLM response not found: {mock_path}\n"
            f"No mock data available for keyword '{keyword}'."
        )

    with open(mock_path, "r") as f:
        raw_results = json.load(f)

    results = [LLMPairResult(**item) for item in raw_results]
    print(f"  LLM analysis: loaded {len(results)} implication pairs (mock mode)")
    return results
