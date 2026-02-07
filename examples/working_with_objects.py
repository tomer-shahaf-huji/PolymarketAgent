"""
Example: Working with Market and MarketPair objects

This script demonstrates the object-oriented approach to working with
Polymarket data using Pydantic models.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.market import (
    Market,
    MarketPair,
    load_markets_from_parquet,
    markets_to_dataframe,
    save_markets_to_parquet
)


def main():
    print("=" * 60)
    print("Working with Market Objects")
    print("=" * 60)
    print()

    # Load markets from parquet (placeholder for DB query)
    markets_file = Path(__file__).parent.parent / "data" / "markets.parquet"
    markets = load_markets_from_parquet(str(markets_file))

    print(f"Loaded {len(markets)} Market objects from {markets_file.name}")
    print()

    # Filter markets using object methods
    open_markets = [m for m in markets if m.is_open()]
    markets_with_odds = [m for m in markets if m.has_valid_odds()]

    print(f"Open markets: {len(open_markets)}")
    print(f"Markets with valid odds: {len(markets_with_odds)}")
    print()

    # Work with individual Market objects
    print("-" * 60)
    print("Sample Market Object")
    print("-" * 60)
    if markets:
        market = markets[0]
        print(f"Title: {market.title}")
        print(f"Market ID: {market.market_id[:30]}...")
        print(f"URL: {market.url}")
        print(f"Yes odds: {market.yes_odds}")
        print(f"No odds: {market.no_odds}")
        print(f"Is open: {market.is_open()}")
        print(f"Has valid odds: {market.has_valid_odds()}")

        if market.has_valid_odds():
            edge = market.implied_edge()
            print(f"Implied edge: {edge:.4f}" if edge else "N/A")
    print()

    # Search for markets by keyword
    print("-" * 60)
    print("Finding Markets by Keyword")
    print("-" * 60)
    import re
    keyword = "Trump"
    pattern = re.compile(rf'\b{keyword}\b', re.IGNORECASE)
    trump_markets = [m for m in markets if pattern.search(m.title)]
    print(f"Found {len(trump_markets)} markets with '{keyword}' in title")

    # Show top 3
    for i, m in enumerate(trump_markets[:3]):
        print(f"\n{i+1}. {m.title[:70]}...")
        print(f"   Yes: {m.yes_odds}, No: {m.no_odds}, Open: {m.is_open()}")
    print()

    # Create MarketPair objects
    print("-" * 60)
    print("Creating MarketPair Objects")
    print("-" * 60)

    # Get open Trump markets with valid odds
    trump_open = [m for m in trump_markets if m.is_open() and m.has_valid_odds()]

    if len(trump_open) >= 2:
        # Create a sample pair
        pair = MarketPair(
            pair_id="Trump_0001",
            keyword="Trump",
            market1=trump_open[0],
            market2=trump_open[1]
        )

        print(f"Created MarketPair: {pair.pair_id}")
        print(f"  Market 1: {pair.market1.title[:60]}...")
        print(f"  Market 2: {pair.market2.title[:60]}...")
        print(f"  Both open: {pair.both_markets_open()}")
        print(f"  Both have odds: {pair.both_have_valid_odds()}")
        print()

    # Convert to DataFrame when needed (placeholder for DB)
    print("-" * 60)
    print("Converting to DataFrame (Placeholder for DB)")
    print("-" * 60)

    # Take a small subset for demo
    sample_markets = markets[:100]
    df = markets_to_dataframe(sample_markets)

    print(f"Converted {len(sample_markets)} Market objects to DataFrame")
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print("✓ Loaded Market objects from parquet (placeholder for DB)")
    print("✓ Used object methods for filtering and analysis")
    print("✓ Created MarketPair objects")
    print("✓ Converted back to DataFrame when needed")
    print()
    print("Next steps:")
    print("  - Replace parquet with actual database (PostgreSQL, etc.)")
    print("  - Add more business logic to Market and MarketPair classes")
    print("  - Use objects throughout the application")
    print()


if __name__ == "__main__":
    main()
