"""
Market Pairing Service for finding and pairing related Polymarket markets.

This service uses LLM analysis to identify meaningful implication pairs (A -> B)
from keyword-specific market collections. It replaces the previous brute-force
combinations approach with intelligent, logic-based pair identification.

Pipeline: keyword markets -> LLM analysis -> MarketPair objects -> parquet
"""
import os
from typing import List
from pathlib import Path

from backend.models.market import Market, MarketPair, save_market_pairs_to_parquet
from backend.models.keyword_market import KeywordMarkets, load_keyword_markets_from_parquet
from backend.services.llm_client import (
    LLMPairResult,
    analyze_markets,
    DEFAULT_MARKETS_LIMIT,
)


def get_valid_market_indices(markets: List[Market]) -> List[int]:
    """
    Get indices of markets that have valid yes/no odds.

    Returns original indices (positions in the full list) so they match
    the IDs used in the LLM prompt and mock responses.

    Args:
        markets: Full list of Market objects

    Returns:
        List of indices into the original market list
    """
    valid_indices = [i for i, m in enumerate(markets) if m.has_valid_odds()]
    print(f"  Markets with valid odds: {len(valid_indices)} / {len(markets)}")
    return valid_indices


def create_pairs_from_llm_results(
    keyword: str,
    markets: List[Market],
    llm_results: List[LLMPairResult],
) -> List[MarketPair]:
    """
    Create MarketPair objects from LLM analysis results.

    The LLM returns index-based IDs that correspond to each market's original
    position in the full keyword market list (matching how they were presented
    in the prompt with their original indices preserved).

    Args:
        keyword: Keyword tag for these pairs
        markets: The full list of Market objects (index = original position)
        llm_results: List of LLMPairResult from the LLM

    Returns:
        List of MarketPair objects with reasoning
    """
    # Build index -> Market mapping from the FULL list
    index_to_market = {str(i): market for i, market in enumerate(markets)}

    pairs = []
    skipped = 0

    for result in llm_results:
        trigger = index_to_market.get(result.trigger_market_id)
        implied = index_to_market.get(result.implied_market_id)

        if trigger is None or implied is None:
            skipped += 1
            missing = []
            if trigger is None:
                missing.append(f"trigger={result.trigger_market_id}")
            if implied is None:
                missing.append(f"implied={result.implied_market_id}")
            print(f"  [WARN] Skipping pair: index not found ({', '.join(missing)})")
            continue

        pair_id = f"{keyword}_{len(pairs) + 1:04d}"
        pair = MarketPair(
            pair_id=pair_id,
            keyword=keyword,
            market1=trigger,
            market2=implied,
            reasoning=result.reasoning,
        )
        pairs.append(pair)

    if skipped > 0:
        print(f"  [WARN] Skipped {skipped} pairs due to missing market indices")

    print(f"  Created {len(pairs)} MarketPair objects")
    return pairs


def save_pairs(pairs: List[MarketPair], filepath: str) -> None:
    """
    Save MarketPair objects to parquet file (placeholder for DB).

    Args:
        pairs: List of MarketPair objects
        filepath: Path to output parquet file
    """
    save_market_pairs_to_parquet(pairs, filepath)

    file_size = os.path.getsize(filepath) / 1024
    print(f"  Saved {len(pairs)} pairs to {filepath} ({file_size:.2f} KB)")


def find_and_pair_markets_multi_keyword(
    keywords: list[str],
    keywords_dir: str = "data/keywords",
    output_file: str = "market_pairs.parquet",
    save_individual_pairs: bool = False,
    use_mock: bool = True,
    markets_limit: int = DEFAULT_MARKETS_LIMIT,
) -> List[MarketPair]:
    """
    Main function to create implication pairs from keyword markets using LLM analysis.

    This function:
    1. Loads keyword-specific market collections from keywords_dir
    2. For each keyword:
       a. Filters markets with valid odds
       b. Sends to LLM for implication analysis (or loads mock results)
       c. Creates MarketPair objects from LLM results
       d. Optionally saves pairs to keyword-specific file
    3. Combines all pairs from all keywords
    4. Saves combined pairs to parquet file (placeholder for DB)

    Args:
        keywords: List of keywords to process (e.g., ["Iran", "Trump"])
        keywords_dir: Directory containing keyword market files
        output_file: Path to output combined pairs parquet file
        save_individual_pairs: If True, save pairs for each keyword separately
        use_mock: If True, use mock LLM responses. If False, call real LLM API.
        markets_limit: Max number of markets to send to LLM per keyword

    Returns:
        List of MarketPair objects from all keywords
    """
    print("=" * 60)
    print("Market Pairing Service - LLM-Driven Analysis")
    print(f"Keywords: {', '.join(keywords)}")
    print(f"Mode: {'mock' if use_mock else 'live LLM'}")
    print("=" * 60)
    print()

    pairs_dir = os.path.join(os.path.dirname(output_file), "pairs") if save_individual_pairs else None

    all_pairs = []

    for keyword in keywords:
        print("-" * 60)
        print(f"Processing keyword: '{keyword}'")

        try:
            # 1. Load keyword markets
            keyword_markets = load_keyword_markets_from_parquet(
                os.path.join(keywords_dir, f"{keyword}.parquet")
            )
            all_markets = keyword_markets.markets
            print(f"  Loaded {len(all_markets)} markets")

            # 2. Get indices of markets with valid odds, apply limit
            valid_indices = get_valid_market_indices(all_markets)

            if len(valid_indices) < 2:
                print(f"  [SKIP] Need at least 2 valid markets, found {len(valid_indices)}")
                continue

            limited_indices = valid_indices[:markets_limit]
            if len(valid_indices) > markets_limit:
                print(f"  Limited to {markets_limit} markets (from {len(valid_indices)})")

            # 3. Run LLM analysis (uses original indices for market IDs)
            llm_results = analyze_markets(
                keyword, all_markets, limited_indices, use_mock=use_mock
            )

            # 4. Create MarketPair objects from LLM results (maps by original index)
            pairs = create_pairs_from_llm_results(keyword, all_markets, llm_results)

            # 5. Optionally save per-keyword pairs
            if pairs_dir and pairs:
                Path(pairs_dir).mkdir(parents=True, exist_ok=True)
                output_path = os.path.join(pairs_dir, f"{keyword}_pairs.parquet")
                save_pairs(pairs, output_path)

            all_pairs.extend(pairs)

        except FileNotFoundError as e:
            print(f"  [ERROR] {e}")
            print(f"  [SKIP] Skipping '{keyword}'")

        print()

    # Combine and save all pairs
    if all_pairs:
        print("=" * 60)
        print(f"Total implication pairs found: {len(all_pairs)}")
        print("=" * 60)
        print()
        save_pairs(all_pairs, output_file)
        return all_pairs
    else:
        print("No pairs created for any keyword")
        return []
