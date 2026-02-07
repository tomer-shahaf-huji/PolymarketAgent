"""
Example: Three-Step Data Pipeline with Object-Oriented Models

This demonstrates the complete data pipeline:
1. Fetch all markets from Polymarket
2. Extract keyword-specific markets
3. Create pairs from keyword markets

Each step works with Pydantic objects and saves to parquet (placeholder for DB).
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.polymarket_client import PolymarketClient
from backend.services.keyword_markets import process_all_keywords
from backend.services.market_pairs import find_and_pair_markets_multi_keyword


def step1_fetch_markets(limit=1000):
    """
    Step 1: Fetch all markets from Polymarket.

    Returns Market objects and saves to parquet.
    """
    print("=" * 70)
    print("STEP 1: Fetch Markets from Polymarket")
    print("=" * 70)
    print()

    client = PolymarketClient()
    markets = client.fetch_all_markets(limit=limit)

    # Save to parquet (placeholder for DB)
    output_file = str(Path(__file__).parent.parent / "data" / "markets.parquet")
    client.save_to_parquet(markets, output_file)

    print(f"✓ Fetched and saved {len(markets)} Market objects")
    print()

    return markets


def step2_extract_keyword_markets(keywords):
    """
    Step 2: Extract markets for each keyword.

    Reads all markets and creates KeywordMarkets objects for each keyword.
    Saves to data/keywords/{keyword}.parquet
    """
    print("=" * 70)
    print("STEP 2: Extract Keyword-Specific Markets")
    print("=" * 70)
    print()

    input_file = str(Path(__file__).parent.parent / "data" / "markets.parquet")
    output_dir = str(Path(__file__).parent.parent / "data" / "keywords")

    keyword_markets_list = process_all_keywords(
        input_file=input_file,
        keywords=keywords,
        output_dir=output_dir,
        filter_open_only=True
    )

    print(f"✓ Extracted markets for {len(keyword_markets_list)} keywords")
    print()

    return keyword_markets_list


def step3_create_pairs(keywords):
    """
    Step 3: Create pairs from keyword markets.

    Reads KeywordMarkets from data/keywords/ and creates MarketPair objects.
    Saves to data/market_pairs.parquet and data/pairs/{keyword}_pairs.parquet
    """
    print("=" * 70)
    print("STEP 3: Create Market Pairs")
    print("=" * 70)
    print()

    keywords_dir = str(Path(__file__).parent.parent / "data" / "keywords")
    output_file = str(Path(__file__).parent.parent / "data" / "market_pairs.parquet")

    pairs = find_and_pair_markets_multi_keyword(
        keywords=keywords,
        keywords_dir=keywords_dir,
        output_file=output_file,
        save_individual_pairs=True
    )

    print(f"✓ Created {len(pairs)} MarketPair objects")
    print()

    return pairs


def main():
    """Run the complete 3-step pipeline."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "THREE-STEP DATA PIPELINE EXAMPLE" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    # Configuration
    keywords = ["Iran", "Trump"]
    fetch_limit = 1000  # Limit for demo; set to None for all markets

    print(f"Keywords: {', '.join(keywords)}")
    print(f"Fetch limit: {fetch_limit if fetch_limit else 'All markets'}")
    print()

    # Step 1: Fetch markets
    try:
        markets = step1_fetch_markets(limit=fetch_limit)
    except Exception as e:
        print(f"✗ Step 1 failed: {e}")
        print("Note: For this demo to work, you need access to Polymarket API")
        print("If you already have data/markets.parquet, skip to step 2")
        return

    # Step 2: Extract keyword markets
    try:
        keyword_markets_list = step2_extract_keyword_markets(keywords)
    except Exception as e:
        print(f"✗ Step 2 failed: {e}")
        return

    # Step 3: Create pairs
    try:
        pairs = step3_create_pairs(keywords)
    except Exception as e:
        print(f"✗ Step 3 failed: {e}")
        return

    # Summary
    print("=" * 70)
    print("PIPELINE COMPLETE ✓")
    print("=" * 70)
    print()
    print("Data Flow:")
    print("  1. Polymarket API → Market objects → data/markets.parquet")
    print("  2. All markets → KeywordMarkets objects → data/keywords/{keyword}.parquet")
    print("  3. Keyword markets → MarketPair objects → data/pairs/{keyword}_pairs.parquet")
    print()
    print("Results:")
    print(f"  • Total markets fetched: {len(markets)}")
    print(f"  • Keywords processed: {len(keyword_markets_list)}")
    for km in keyword_markets_list:
        print(f"    - {km.keyword}: {km.count()} markets")
    print(f"  • Total pairs created: {len(pairs)}")
    print()
    print("File Structure:")
    print("  data/")
    print("  ├── markets.parquet           (all markets)")
    print("  ├── keywords/")
    for keyword in keywords:
        print(f"  │   ├── {keyword}.parquet         (keyword-specific markets)")
    print("  ├── pairs/")
    for keyword in keywords:
        print(f"  │   ├── {keyword}_pairs.parquet   (keyword-specific pairs)")
    print("  └── market_pairs.parquet      (all pairs combined)")
    print()
    print("Benefits of This Approach:")
    print("  ✓ Modular - Each step is independent and can be re-run")
    print("  ✓ Flexible - Easy to add complex logic at each step")
    print("  ✓ Type-safe - All data is validated Pydantic objects")
    print("  ✓ DB-ready - Replace parquet saves with DB inserts when ready")
    print()


if __name__ == "__main__":
    main()
