"""
Main script to fetch all Polymarket markets and save to parquet file.
"""
import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.polymarket_client import PolymarketClient


def main():
    """Fetch all markets and save to parquet file."""
    print("=" * 60)
    print("Polymarket Market Data Fetcher")
    print("=" * 60)
    print()

    # Initialize the client
    client = PolymarketClient()

    # Fetch all markets
    markets = client.fetch_all_markets()

    if not markets:
        print("No markets fetched. Exiting.")
        return

    print()
    print("-" * 60)

    # Display summary
    print()
    print("=" * 60)
    print("Data Summary")
    print("=" * 60)
    print(f"Total markets: {len(markets)}")
    print()

    # Display some statistics
    print("=" * 60)
    print("Statistics")
    print("=" * 60)
    open_markets = [m for m in markets if m.is_open()]
    markets_with_odds = [m for m in markets if m.has_valid_odds()]
    total_volume = sum(m.volume for m in markets)
    avg_volume = total_volume / len(markets) if markets else 0

    print(f"Open markets: {len(open_markets)}")
    print(f"Markets with valid yes/no odds: {len(markets_with_odds)}")
    print(f"Total volume: ${total_volume:,.2f}")
    print(f"Average volume per market: ${avg_volume:,.2f}")
    print()

    # Show sample markets
    print("Sample markets:")
    for i, market in enumerate(markets[:3]):
        print(f"\n{i+1}. {market.title}")
        print(f"   ID: {market.market_id[:20]}...")
        print(f"   Yes: {market.yes_odds}, No: {market.no_odds}")
        print(f"   Status: {'Open' if market.is_open() else 'Closed'}")
    print()

    # Save to parquet (placeholder for DB)
    output_file = str(Path(__file__).parent.parent / "data" / "markets.parquet")
    client.save_to_parquet(markets, output_file)

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print(f"Market data saved to: {output_file}")
    print()
    print("To load the data:")
    print("  import pandas as pd")
    print(f"  df = pd.read_parquet('{output_file}')")
    print()


if __name__ == "__main__":
    main()
