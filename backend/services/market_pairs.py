"""
Market Pairing Service for finding and pairing related Polymarket markets.
"""
from itertools import combinations
import os
import re
from typing import List
import pandas as pd

from backend.models.market import Market, MarketPair, load_markets_from_parquet, save_market_pairs_to_parquet


def load_markets(filepath: str = "markets.parquet") -> List[Market]:
    """
    Load market data from parquet file as Market objects.

    Args:
        filepath: Path to the parquet file

    Returns:
        List of Market objects

    Raises:
        FileNotFoundError: If the parquet file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Market data file not found: {filepath}\n"
            f"Please run 'python fetch_markets.py' first to fetch market data."
        )

    print(f"Loading markets from {filepath}...")
    markets = load_markets_from_parquet(filepath)
    print(f"Loaded {len(markets)} markets")
    return markets


def filter_open_markets(markets: List[Market]) -> List[Market]:
    """
    Filter for markets that are open (active and not closed).

    Args:
        markets: List of Market objects

    Returns:
        Filtered list with only open markets
    """
    open_markets = [m for m in markets if m.is_open()]
    print(f"Found {len(open_markets)} open markets")
    return open_markets


def find_keyword_markets(markets: List[Market], keyword: str) -> List[Market]:
    """
    Filter markets where title contains a specific keyword as a whole word (case-insensitive).

    Args:
        markets: List of Market objects
        keyword: Keyword to search for in market titles

    Returns:
        Filtered list with keyword-related markets
    """
    # Use word boundaries to match whole words only
    # \b ensures we match "Iran" but not "Miran"
    pattern = rf'\b{keyword}\b'
    regex = re.compile(pattern, re.IGNORECASE)

    keyword_markets = [m for m in markets if regex.search(m.title)]
    print(f"Found {len(keyword_markets)} '{keyword}'-related markets")
    return keyword_markets


def create_market_pairs(markets: List[Market], keyword: str = None) -> List[MarketPair]:
    """
    Create all possible pairs (combinations) of markets.

    Args:
        markets: List of Market objects to pair
        keyword: Optional keyword tag to associate with these pairs

    Returns:
        List of MarketPair objects
    """
    if len(markets) < 2:
        print(f"Need at least 2 markets to create pairs, found {len(markets)}")
        return []

    print(f"Creating pairs from {len(markets)} markets...")

    # Generate all combinations
    pairs = []
    pair_count = 0

    for idx1, idx2 in combinations(range(len(markets)), 2):
        market1 = markets[idx1]
        market2 = markets[idx2]

        pair_count += 1
        pair_id = f"{keyword}_{pair_count:04d}" if keyword else f"pair_{pair_count:04d}"

        pair = MarketPair(
            pair_id=pair_id,
            keyword=keyword,
            market1=market1,
            market2=market2
        )
        pairs.append(pair)

    print(f"Created {len(pairs)} pairs")
    return pairs


def save_pairs(pairs: List[MarketPair], filepath: str = "market_pairs.parquet") -> None:
    """
    Save MarketPair objects to parquet file (placeholder for DB).

    Args:
        pairs: List of MarketPair objects
        filepath: Path to output parquet file
    """
    print(f"Saving pairs to {filepath}...")

    save_market_pairs_to_parquet(pairs, filepath)

    # Print file size
    file_size = os.path.getsize(filepath) / 1024  # Convert to KB
    print(f"Successfully saved {len(pairs)} pairs to {filepath}")
    print(f"File size: {file_size:.2f} KB")


def find_and_pair_markets_multi_keyword(
    keywords: list[str],
    input_file: str = "markets.parquet",
    output_file: str = "market_pairs.parquet"
) -> List[MarketPair]:
    """
    Main function to find and pair markets for multiple keywords.

    This function:
    1. Loads market data from parquet file
    2. Filters for open markets
    3. For each keyword:
       - Filters for keyword-related markets
       - Creates all possible pairs
    4. Combines all pairs from all keywords
    5. Saves combined pairs to parquet file (placeholder for DB)

    Args:
        keywords: List of keywords to search for (e.g., ["Iran", "Trump"])
        input_file: Path to input market data parquet file
        output_file: Path to output pairs parquet file

    Returns:
        List of MarketPair objects from all keywords
    """
    print("=" * 60)
    print(f"Market Pairing Service - Multiple Keywords")
    print(f"Keywords: {', '.join(keywords)}")
    print("=" * 60)
    print()

    # Step 1: Load markets
    markets = load_markets(input_file)
    print()

    # Step 2: Filter for open markets
    open_markets = filter_open_markets(markets)
    print()

    # Step 3-4: For each keyword, find markets and create pairs
    all_pairs = []

    for keyword in keywords:
        print(f"Processing keyword: '{keyword}'")
        print("-" * 40)

        # Find markets for this keyword
        keyword_markets = find_keyword_markets(open_markets, keyword)

        if len(keyword_markets) >= 2:
            # Create pairs for this keyword
            pairs = create_market_pairs(keyword_markets, keyword)
            all_pairs.extend(pairs)
            print(f"[OK] Created {len(pairs)} pairs for '{keyword}'")
        else:
            print(f"[SKIP] Skipping '{keyword}' (need at least 2 markets, found {len(keyword_markets)})")

        print()

    # Step 5: Combine all pairs
    if all_pairs:
        print("=" * 60)
        print(f"Total pairs created: {len(all_pairs)}")
        print("=" * 60)
        print()

        # Step 6: Save combined pairs
        save_pairs(all_pairs, output_file)
        return all_pairs
    else:
        print("No pairs created for any keyword")
        return []


def find_and_pair_markets(
    input_file: str = "markets.parquet",
    output_file: str = "market_pairs.parquet",
    keywords: list[str] = None
) -> List[MarketPair]:
    """
    Main function to find and pair keyword-related markets.

    This function:
    1. Loads market data from parquet file
    2. Filters for open markets
    3. Filters for keyword-related markets
    4. Creates all possible pairs
    5. Saves pairs to parquet file (placeholder for DB)

    Args:
        input_file: Path to input market data parquet file
        output_file: Path to output pairs parquet file
        keywords: List of keywords to search for. If None, defaults to ["Iran", "Trump"]

    Returns:
        List of MarketPair objects
    """
    # Default keywords if none provided
    if keywords is None:
        keywords = ["Iran", "Trump"]

    # Use multi-keyword function
    return find_and_pair_markets_multi_keyword(
        keywords=keywords,
        input_file=input_file,
        output_file=output_file
    )
