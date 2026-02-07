"""
Polymarket Client for fetching and processing market data.
"""
import time
from typing import Optional, List, Dict
import pandas as pd
from py_clob_client.client import ClobClient

from backend.models.market import Market, markets_to_dataframe, save_markets_to_parquet


class PolymarketClient:
    """Client for interacting with Polymarket API to fetch market data."""

    def __init__(self, host: str = "https://clob.polymarket.com"):
        """
        Initialize the Polymarket client.

        Args:
            host: The Polymarket CLOB API host URL
        """
        self.client = ClobClient(host)
        print(f"Initialized PolymarketClient with host: {host}")

    def fetch_all_markets(self, limit: Optional[int] = None) -> List[Market]:
        """
        Fetch all markets from Polymarket with pagination.

        Args:
            limit: Optional limit on total number of markets to fetch

        Returns:
            List of Market objects
        """
        raw_markets = []
        next_cursor = 'MA=='  # Default cursor for first page
        page_count = 0

        print("Fetching markets from Polymarket...")

        try:
            while True:
                # Fetch a page of markets
                response = self.client.get_markets(next_cursor=next_cursor)
                page_markets = response.get('data', [])

                if not page_markets:
                    break

                raw_markets.extend(page_markets)
                page_count += 1

                print(f"Fetched page {page_count}: {len(page_markets)} markets (total: {len(raw_markets)})")

                # Check if we've reached the limit
                if limit and len(raw_markets) >= limit:
                    raw_markets = raw_markets[:limit]
                    print(f"Reached limit of {limit} markets")
                    break

                # Get next cursor for pagination
                next_cursor = response.get("next_cursor")
                if not next_cursor:
                    print("No more pages available")
                    break

                # Rate limiting: small delay between requests
                time.sleep(0.1)

        except Exception as e:
            print(f"Error fetching markets: {e}")
            if raw_markets:
                print(f"Returning {len(raw_markets)} markets fetched before error")
            else:
                raise

        print(f"Successfully fetched {len(raw_markets)} total raw markets")
        print(f"Converting to Market objects...")

        # Convert raw API responses to Market objects
        markets = []
        for raw_market in raw_markets:
            try:
                market = Market.from_api_response(raw_market)
                markets.append(market)
            except Exception as e:
                print(f"Warning: Failed to parse market {raw_market.get('condition_id', 'unknown')}: {e}")
                continue

        print(f"Successfully created {len(markets)} Market objects")
        return markets

    def markets_to_dataframe(self, markets: List[Market]) -> pd.DataFrame:
        """
        Convert list of Market objects to a pandas DataFrame.
        Placeholder for database persistence.

        Args:
            markets: List of Market objects

        Returns:
            DataFrame with market data
        """
        return markets_to_dataframe(markets)

    def save_to_parquet(self, markets: List[Market], filepath: str = "markets.parquet") -> None:
        """
        Save Market objects to parquet file (placeholder for database).

        Args:
            markets: List of Market objects
            filepath: Path to output parquet file
        """
        save_markets_to_parquet(markets, filepath)

        # Print file size
        import os
        file_size = os.path.getsize(filepath) / (1024 * 1024)  # Convert to MB
        print(f"File size: {file_size:.2f} MB")
