"""
Main script to create pairs from keyword-specific markets.

This is step 3 in the data pipeline:
1. fetch_markets.py - Fetch all markets
2. extract_keyword_markets.py - Extract markets by keyword
3. find_market_pairs.py - Create pairs from keyword markets (THIS SCRIPT)
"""
import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.market_pairs import find_and_pair_markets_multi_keyword
from backend.models.market import market_pairs_to_dataframe


def main():
    """Create pairs from pre-extracted keyword markets."""
    # Define keywords to process
    keywords = ["Iran", "Trump"]

    # Define data paths
    data_dir = Path(__file__).parent.parent / "data"
    keywords_dir = str(data_dir / "keywords")
    output_file = str(data_dir / "market_pairs.parquet")

    # Run the pairing service
    # This reads from data/keywords/{keyword}.parquet files
    pairs = find_and_pair_markets_multi_keyword(
        keywords=keywords,
        keywords_dir=keywords_dir,
        output_file=output_file,
        save_individual_pairs=True  # Also save pairs per keyword in data/pairs/
    )

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if len(pairs) > 0:
        print(f"Total pairs created: {len(pairs)}")

        # Convert to DataFrame for analysis
        pairs_df = market_pairs_to_dataframe(pairs)

        # Show breakdown by keyword
        print()
        print("Breakdown by keyword:")
        for keyword in pairs_df['keyword'].unique():
            count = len(pairs_df[pairs_df['keyword'] == keyword])
            print(f"  - {keyword}: {count} pairs")

        print()
        print("Sample pairs (first 3):")
        print("-" * 60)

        # Display first 3 pairs
        for idx in range(min(3, len(pairs))):
            pair = pairs[idx]
            print(f"\n{pair.pair_id} (keyword: {pair.keyword}):")
            print(f"  Market 1: {pair.market1.title[:70]}...")
            print(f"    Yes: {pair.market1.yes_odds}, No: {pair.market1.no_odds}")
            print(f"  Market 2: {pair.market2.title[:70]}...")
            print(f"    Yes: {pair.market2.yes_odds}, No: {pair.market2.no_odds}")

        print()
        print("-" * 60)
        print(f"Pairs saved to: {output_file}")
        print(f"Individual keyword pairs saved to: {data_dir / 'pairs'}")
    else:
        print("No pairs created.")
        print("Possible reasons:")
        print("  - No keyword markets files found in data/keywords/")
        print("  - Run 'python scripts/extract_keyword_markets.py' first")
        print("  - Only 1 market found per keyword (need at least 2 for pairs)")

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
