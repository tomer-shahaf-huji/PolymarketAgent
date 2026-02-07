"""
Polymarket Client for fetching and processing market data.
"""
import os
import time
from typing import Optional, List, Dict, Set
import pandas as pd
from py_clob_client.client import ClobClient

from backend.models.market import Market, markets_to_dataframe, save_markets_to_parquet, load_markets_from_parquet


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

    def fetch_all_markets(
        self,
        limit: Optional[int] = None,
        output_file: Optional[str] = None,
        batch_size: int = 10,
        resume: bool = True
    ) -> List[Market]:
        """
        Fetch all markets from Polymarket with pagination and incremental saving.

        Args:
            limit: Optional limit on total number of markets to fetch
            output_file: Path to save markets incrementally (saves every batch_size pages)
            batch_size: Number of pages to fetch before saving (default: 10)
            resume: If True and output_file exists, load existing markets and skip duplicates

        Returns:
            List of Market objects
        """
        # Load existing markets if resuming
        existing_market_ids: Set[str] = set()
        existing_markets: List[Market] = []

        if resume and output_file and os.path.exists(output_file):
            print(f"Resuming from existing file: {output_file}")
            try:
                existing_markets = load_markets_from_parquet(output_file)
                existing_market_ids = {m.market_id for m in existing_markets}
                print(f"Loaded {len(existing_markets)} existing markets")
                print(f"Will skip duplicates and continue fetching new markets")
            except Exception as e:
                print(f"Warning: Could not load existing markets: {e}")
                print("Starting fresh fetch")

        raw_markets = []
        all_markets = list(existing_markets)  # Start with existing markets
        next_cursor = 'MA=='  # Default cursor for first page
        page_count = 0
        new_markets_count = 0

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

                print(f"Fetched page {page_count}: {len(page_markets)} markets")

                # Save batch incrementally
                if output_file and page_count % batch_size == 0:
                    # Convert new raw markets to Market objects
                    batch_markets = self._convert_raw_markets_to_objects(
                        raw_markets,
                        existing_market_ids
                    )

                    # Add to all markets and update existing IDs
                    all_markets.extend(batch_markets)
                    existing_market_ids.update(m.market_id for m in batch_markets)
                    new_markets_count += len(batch_markets)

                    # Save to file
                    self._save_batch(all_markets, output_file, page_count)

                    # Clear raw markets buffer
                    raw_markets = []

                # Check if we've reached the limit
                if limit and (len(existing_markets) + new_markets_count) >= limit:
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
            print(f"Progress saved up to page {(page_count // batch_size) * batch_size}")
            # Process remaining raw markets before returning
            if raw_markets:
                print(f"Processing {len(raw_markets)} markets from incomplete batch...")
                batch_markets = self._convert_raw_markets_to_objects(
                    raw_markets,
                    existing_market_ids
                )
                all_markets.extend(batch_markets)

                if output_file:
                    self._save_batch(all_markets, output_file, page_count, is_error=True)

        # Process any remaining raw markets
        if raw_markets:
            print(f"Processing final batch of {len(raw_markets)} raw markets...")
            batch_markets = self._convert_raw_markets_to_objects(
                raw_markets,
                existing_market_ids
            )
            all_markets.extend(batch_markets)

            if output_file:
                self._save_batch(all_markets, output_file, page_count, is_final=True)

        print(f"Successfully fetched {len(all_markets)} total Market objects")
        if existing_markets:
            print(f"  Existing: {len(existing_markets)}")
            print(f"  New: {len(all_markets) - len(existing_markets)}")

        return all_markets

    def _convert_raw_markets_to_objects(
        self,
        raw_markets: List[Dict],
        existing_ids: Set[str]
    ) -> List[Market]:
        """
        Convert raw API responses to Market objects, skipping duplicates.

        Args:
            raw_markets: List of raw market dictionaries
            existing_ids: Set of market IDs to skip (already processed)

        Returns:
            List of Market objects
        """
        markets = []
        skipped = 0

        for raw_market in raw_markets:
            market_id = raw_market.get('condition_id', '')

            # Skip if already exists
            if market_id in existing_ids:
                skipped += 1
                continue

            try:
                market = Market.from_api_response(raw_market)
                markets.append(market)
            except Exception as e:
                print(f"Warning: Failed to parse market {market_id}: {e}")
                continue

        if skipped > 0:
            print(f"  Skipped {skipped} duplicate markets")
        if markets:
            print(f"  Converted {len(markets)} new markets to Market objects")

        return markets

    def _save_batch(
        self,
        markets: List[Market],
        filepath: str,
        page_count: int,
        is_final: bool = False,
        is_error: bool = False
    ) -> None:
        """
        Save a batch of markets to parquet file.

        Args:
            markets: List of all Market objects (including existing)
            filepath: Path to output file
            page_count: Current page count
            is_final: Whether this is the final save
            is_error: Whether this save is due to an error
        """
        try:
            save_markets_to_parquet(markets, filepath)
            status = "ERROR RECOVERY" if is_error else ("FINAL" if is_final else "BATCH")
            print(f"  [{status}] Saved {len(markets)} markets to {filepath} (after page {page_count})")
        except Exception as e:
            print(f"  ERROR: Failed to save batch: {e}")

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
