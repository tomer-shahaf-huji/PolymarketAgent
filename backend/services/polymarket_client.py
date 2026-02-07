"""
Polymarket Client for fetching and processing market data.
"""
import time
from typing import Optional, List, Dict
import pandas as pd
from py_clob_client.client import ClobClient


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

    def fetch_all_markets(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch all markets from Polymarket with pagination.

        Args:
            limit: Optional limit on total number of markets to fetch

        Returns:
            List of market dictionaries
        """
        markets_list = []
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

                markets_list.extend(page_markets)
                page_count += 1

                print(f"Fetched page {page_count}: {len(page_markets)} markets (total: {len(markets_list)})")

                # Check if we've reached the limit
                if limit and len(markets_list) >= limit:
                    markets_list = markets_list[:limit]
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
            if markets_list:
                print(f"Returning {len(markets_list)} markets fetched before error")
            else:
                raise

        print(f"Successfully fetched {len(markets_list)} total markets")
        return markets_list

    def parse_market(self, market: Dict) -> Dict:
        """
        Parse a market dictionary to extract relevant fields.

        Args:
            market: Raw market dictionary from API

        Returns:
            Parsed market dictionary with standardized fields
        """
        try:
            # Extract basic fields
            market_id = market.get('condition_id', '')
            title = market.get('question', '')
            description = market.get('description', '')
            slug = market.get('market_slug', '')

            # Construct URL from slug
            url = f"https://polymarket.com/event/{slug}" if slug else ""

            # Extract yes/no odds from tokens array
            tokens = market.get('tokens', [])

            # Default values
            yes_odds = None
            no_odds = None

            # Map outcomes to prices
            for token in tokens:
                outcome = token.get('outcome', '').lower()
                price = token.get('price')

                if price is not None:
                    price = float(price)

                    # Check for yes/no outcomes
                    if outcome == 'yes':
                        yes_odds = price
                    elif outcome == 'no':
                        no_odds = price

            # Extract additional useful fields
            end_date = market.get('end_date_iso')

            # Note: Volume and liquidity are not available in this endpoint
            # Would need to use Gamma API or a different endpoint for these
            volume = 0.0
            liquidity = 0.0

            # Market status flags
            active = market.get('active', False)
            closed = market.get('closed', False)

            return {
                'url': url,
                'title': title,
                'description': description,
                'yes_odds': yes_odds,
                'no_odds': no_odds,
                'market_id': market_id,
                'end_date': end_date,
                'active': active,
                'closed': closed,
                'volume': volume,
                'liquidity': liquidity
            }

        except Exception as e:
            print(f"Warning: Error parsing market {market.get('condition_id', 'unknown')}: {e}")
            # Return a minimal valid dictionary
            return {
                'url': '',
                'title': market.get('question', ''),
                'description': market.get('description', ''),
                'yes_odds': None,
                'no_odds': None,
                'market_id': market.get('condition_id', ''),
                'end_date': None,
                'active': False,
                'closed': False,
                'volume': 0.0,
                'liquidity': 0.0
            }

    def markets_to_dataframe(self, markets: List[Dict]) -> pd.DataFrame:
        """
        Convert list of markets to a pandas DataFrame.

        Args:
            markets: List of raw market dictionaries

        Returns:
            DataFrame with parsed market data
        """
        print(f"Converting {len(markets)} markets to DataFrame...")

        parsed_markets = [self.parse_market(market) for market in markets]
        df = pd.DataFrame(parsed_markets)

        # Convert end_date to datetime
        if 'end_date' in df.columns and not df.empty:
            df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')

        print(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        return df

    def save_to_parquet(self, df: pd.DataFrame, filepath: str = "markets.parquet") -> None:
        """
        Save DataFrame to parquet file.

        Args:
            df: DataFrame to save
            filepath: Path to output parquet file
        """
        print(f"Saving data to {filepath}...")

        try:
            df.to_parquet(filepath, engine='pyarrow', compression='snappy', index=False)
            print(f"Successfully saved {len(df)} markets to {filepath}")

            # Print file size
            import os
            file_size = os.path.getsize(filepath) / (1024 * 1024)  # Convert to MB
            print(f"File size: {file_size:.2f} MB")

        except Exception as e:
            print(f"Error saving to parquet: {e}")
            raise
