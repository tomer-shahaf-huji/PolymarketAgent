"""
Keyword Markets Service for extracting and organizing markets by keywords.

This service sits between market fetching and pair creation:
1. Reads all markets from storage
2. Filters markets by each keyword
3. Saves keyword-specific market collections

This allows for more complex filtering logic and separate processing per keyword.
"""
import os
import re
from pathlib import Path
from typing import List

from backend.models.market import Market, load_markets_from_parquet
from backend.models.keyword_market import (
    KeywordMarkets,
    save_keyword_markets_to_parquet,
    load_keyword_markets_from_parquet
)


def extract_keyword_markets(
    all_markets: List[Market],
    keyword: str,
    filter_open_only: bool = True
) -> KeywordMarkets:
    """
    Extract markets related to a specific keyword.

    Args:
        all_markets: List of all Market objects
        keyword: Keyword to search for in market titles
        filter_open_only: If True, only include open markets

    Returns:
        KeywordMarkets object containing filtered markets
    """
    # Use word boundaries to match whole words only
    pattern = rf'\b{keyword}\b'
    regex = re.compile(pattern, re.IGNORECASE)

    # Filter by keyword
    keyword_markets = [m for m in all_markets if regex.search(m.title)]

    # Optionally filter for open markets only
    if filter_open_only:
        keyword_markets = [m for m in keyword_markets if m.is_open()]

    print(f"Found {len(keyword_markets)} markets for keyword '{keyword}'" +
          (f" (open markets only)" if filter_open_only else ""))

    return KeywordMarkets(keyword=keyword, markets=keyword_markets)


def process_all_keywords(
    input_file: str,
    keywords: List[str],
    output_dir: str,
    filter_open_only: bool = True
) -> List[KeywordMarkets]:
    """
    Process all keywords and extract their markets.

    This is the main function for the keyword extraction step.
    Reads all markets and creates separate collections for each keyword.

    Args:
        input_file: Path to parquet file with all markets
        keywords: List of keywords to process
        output_dir: Directory to save keyword-specific market files
        filter_open_only: If True, only include open markets

    Returns:
        List of KeywordMarkets objects
    """
    print("=" * 60)
    print("Keyword Markets Extraction Service")
    print(f"Keywords: {', '.join(keywords)}")
    print("=" * 60)
    print()

    # Load all markets
    print(f"Loading all markets from {input_file}...")
    all_markets = load_markets_from_parquet(input_file)
    print(f"Loaded {len(all_markets)} total markets")
    print()

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Process each keyword
    all_keyword_markets = []

    for keyword in keywords:
        print("-" * 60)
        print(f"Processing keyword: '{keyword}'")
        print("-" * 60)

        # Extract markets for this keyword
        keyword_markets = extract_keyword_markets(
            all_markets,
            keyword,
            filter_open_only=filter_open_only
        )

        if keyword_markets.count() == 0:
            print(f"[SKIP] No markets found for '{keyword}'")
            print()
            continue

        # Save to file
        output_file = os.path.join(output_dir, f"{keyword}.parquet")
        save_keyword_markets_to_parquet(keyword_markets, output_file)

        all_keyword_markets.append(keyword_markets)

        # Show statistics
        open_count = len(keyword_markets.open_markets())
        odds_count = len(keyword_markets.markets_with_odds())
        print(f"  Open markets: {open_count}")
        print(f"  Markets with odds: {odds_count}")
        print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    total_extracted = sum(km.count() for km in all_keyword_markets)
    print(f"Total keywords processed: {len(all_keyword_markets)}")
    print(f"Total markets extracted: {total_extracted}")
    print()

    for km in all_keyword_markets:
        print(f"  {km.keyword}: {km.count()} markets")

    print()
    print(f"Files saved to: {output_dir}")
    print()

    return all_keyword_markets


def load_keyword_markets_for_keyword(
    keyword: str,
    keywords_dir: str = "data/keywords"
) -> KeywordMarkets:
    """
    Load keyword markets from storage.

    Args:
        keyword: The keyword to load
        keywords_dir: Directory containing keyword market files

    Returns:
        KeywordMarkets object

    Raises:
        FileNotFoundError: If keyword file doesn't exist
    """
    filepath = os.path.join(keywords_dir, f"{keyword}.parquet")

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Keyword markets file not found: {filepath}\n"
            f"Please run 'python scripts/extract_keyword_markets.py' first."
        )

    print(f"Loading markets for keyword '{keyword}' from {filepath}...")
    keyword_markets = load_keyword_markets_from_parquet(filepath)
    print(f"Loaded {keyword_markets.count()} markets for '{keyword}'")

    return keyword_markets


def get_available_keywords(keywords_dir: str = "data/keywords") -> List[str]:
    """
    Get list of available keywords from the keywords directory.

    Args:
        keywords_dir: Directory containing keyword market files

    Returns:
        List of available keywords
    """
    if not os.path.exists(keywords_dir):
        return []

    keywords = []
    for filename in os.listdir(keywords_dir):
        if filename.endswith('.parquet'):
            keyword = filename.replace('.parquet', '')
            keywords.append(keyword)

    return sorted(keywords)
