"""
Main script to find and pair keyword-related Polymarket markets.
"""
import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.market_pairs import find_and_pair_markets


def main():
    """Find and pair keyword-related markets."""
    # Define keywords to search for
    keywords = ["Iran", "Trump"]

    # Define data paths
    data_dir = Path(__file__).parent.parent / "data"
    input_file = str(data_dir / "markets.parquet")
    output_file = str(data_dir / "market_pairs.parquet")

    # Run the pairing service with multiple keywords
    pairs_df = find_and_pair_markets(
        keywords=keywords,
        input_file=input_file,
        output_file=output_file
    )

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if len(pairs_df) > 0:
        print(f"Total pairs created: {len(pairs_df)}")

        # Show breakdown by keyword
        if 'keyword' in pairs_df.columns:
            print()
            print("Breakdown by keyword:")
            for keyword in pairs_df['keyword'].unique():
                count = len(pairs_df[pairs_df['keyword'] == keyword])
                print(f"  - {keyword}: {count} pairs")

        print()
        print("Sample pairs (first 3):")
        print("-" * 60)

        # Display first 3 pairs with nice formatting
        for idx in range(min(3, len(pairs_df))):
            pair = pairs_df.iloc[idx]
            keyword = pair.get('keyword', 'unknown')
            print(f"\n{pair['pair_id']} (keyword: {keyword}):")
            print(f"  Market 1: {pair['market1_title'][:70]}...")
            print(f"    Yes: {pair['market1_yes_odds']}, No: {pair['market1_no_odds']}")
            print(f"  Market 2: {pair['market2_title'][:70]}...")
            print(f"    Yes: {pair['market2_yes_odds']}, No: {pair['market2_no_odds']}")

        print()
        print("-" * 60)
        print(f"Pairs saved to: {output_file}")
    else:
        print("No pairs created.")
        print("Possible reasons:")
        print("  - No keyword-related markets found")
        print("  - Only 1 market found per keyword (need at least 2 for pairs)")
        print("  - No open markets (all markets are closed)")

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
