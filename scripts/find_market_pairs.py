"""
Main script to create implication pairs from keyword-specific markets using LLM analysis.

This is step 3 in the data pipeline:
1. fetch_markets.py - Fetch all markets
2. extract_keyword_markets.py - Extract markets by keyword
3. find_market_pairs.py - LLM identifies implication pairs (THIS SCRIPT)

The LLM analyzes keyword markets and identifies pairs where Market A resolving YES
logically guarantees Market B also resolves YES (temporal, numerical, or categorical
inclusion). Currently uses mock LLM responses; will use real API later.

If pairs already exist, this script only refreshes prices (skips LLM).
Use --force to re-run the full LLM pipeline.
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.market_pairs import find_and_pair_markets_multi_keyword, refresh_pair_prices
from backend.models.market import market_pairs_to_dataframe


def main():
    """Create implication pairs from keyword markets via LLM analysis, or refresh prices."""
    parser = argparse.ArgumentParser(description="Find market pairs or refresh prices")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-running full LLM pipeline even if pairs exist"
    )
    args = parser.parse_args()

    # Define keywords to process
    keywords = ["Iran", "Trump"]

    # Define data paths
    data_dir = Path(__file__).parent.parent / "data"
    keywords_dir = str(data_dir / "keywords")
    output_file = str(data_dir / "market_pairs.parquet")

    pairs_exist = Path(output_file).exists()

    if pairs_exist and not args.force:
        # Refresh mode: update prices only, skip LLM
        print("[MODE] Pairs already exist -- refreshing prices only")
        print("       (use --force to re-run full LLM pipeline)")
        print()
        pairs = refresh_pair_prices(
            pairs_file=output_file,
            keywords_dir=keywords_dir,
            keywords=keywords,
        )
    else:
        # Full mode: run LLM-driven pairing
        if args.force and pairs_exist:
            print("[MODE] --force flag set -- re-running full LLM pipeline")
            print()
        pairs = find_and_pair_markets_multi_keyword(
            keywords=keywords,
            keywords_dir=keywords_dir,
            output_file=output_file,
            save_individual_pairs=True,
            use_mock=True,
        )

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if len(pairs) > 0:
        print(f"Total implication pairs: {len(pairs)}")

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

        for idx in range(min(3, len(pairs))):
            pair = pairs[idx]
            print(f"\n{pair.pair_id} (keyword: {pair.keyword}):")
            print(f"  Trigger:  {pair.market1.title[:70]}")
            print(f"    Yes: {pair.market1.yes_odds}, No: {pair.market1.no_odds}")
            print(f"  Implied:  {pair.market2.title[:70]}")
            print(f"    Yes: {pair.market2.yes_odds}, No: {pair.market2.no_odds}")
            print(f"  Reasoning: {pair.reasoning}")

        print()
        print("-" * 60)
        print(f"Pairs saved to: {output_file}")
        print(f"Individual keyword pairs saved to: {data_dir / 'pairs'}")
    else:
        print("No pairs created.")
        print("Possible reasons:")
        print("  - No keyword markets files found in data/keywords/")
        print("  - Run 'python scripts/extract_keyword_markets.py' first")
        print("  - No mock LLM responses found in data/mock/")

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
