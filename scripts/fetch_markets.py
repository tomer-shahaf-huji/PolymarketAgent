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

    # Convert to DataFrame
    df = client.markets_to_dataframe(markets)

    # Display summary
    print()
    print("=" * 60)
    print("Data Summary")
    print("=" * 60)
    print(f"Total markets: {len(df)}")
    print()
    print("Column Info:")
    print(df.info())
    print()
    print("Sample Data (first 5 rows):")
    print(df.head())
    print()

    # Display some statistics
    print("=" * 60)
    print("Statistics")
    print("=" * 60)
    print(f"Markets with valid yes/no odds: {df[df['yes_odds'].notna() & df['no_odds'].notna()].shape[0]}")
    print(f"Total volume: ${df['volume'].sum():,.2f}")
    print(f"Average volume per market: ${df['volume'].mean():,.2f}")
    print()

    # Save to parquet
    output_file = str(Path(__file__).parent.parent / "data" / "markets.parquet")
    client.save_to_parquet(df, output_file)

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
