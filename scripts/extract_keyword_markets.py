"""
Extract markets by keywords and save to separate files.

This is step 2 in the data pipeline:
1. fetch_markets.py - Fetch all markets
2. extract_keyword_markets.py - Extract markets by keyword (THIS SCRIPT)
3. find_market_pairs.py - Create pairs from keyword markets

This separation allows for more complex filtering logic and
independent processing of each keyword.
"""
import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.keyword_markets import process_all_keywords


def main():
    """Extract markets for each keyword and save to separate files."""

    # Configuration
    keywords = ["Iran", "Trump"]  # Add more keywords here as needed
    input_file = str(Path(__file__).parent.parent / "data" / "markets.parquet")
    output_dir = str(Path(__file__).parent.parent / "data" / "keywords")
    filter_open_only = True  # Set to False to include closed markets

    # Process keywords
    keyword_markets_list = process_all_keywords(
        input_file=input_file,
        keywords=keywords,
        output_dir=output_dir,
        filter_open_only=filter_open_only
    )

    # Done
    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  Run: python scripts/find_market_pairs.py")
    print("  This will create pairs from the extracted keyword markets")
    print()


if __name__ == "__main__":
    main()
