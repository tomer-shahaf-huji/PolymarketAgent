import os
import pandas as pd
from .client import PolymarketClient

def fetch_markets_as_dataframe(client: PolymarketClient, limit: int = 100) -> pd.DataFrame:
    """
    Fetches markets using the provided client and returns them as a pandas DataFrame.
    
    Args:
        client: An instance of PolymarketClient.
        limit: The maximum number of pages to fetch.
        
    Returns:
        pd.DataFrame: A DataFrame containing parsed market data.
    """
    print("Fetching all markets (this may take a moment)...")
    raw_markets = client.get_all_markets(limit=limit)
    print(f"Fetched {len(raw_markets)} markets.")

    parsed_data = []
    for m in raw_markets:
        parsed_data.append(client.parse_market(m))
    
    if not parsed_data:
        print("No markets found.")
        return pd.DataFrame()

    return pd.DataFrame(parsed_data)

def save_markets_to_parquet(df: pd.DataFrame, filename: str = "markets.parquet"):
    """
    Saves the provided DataFrame to a parquet file.
    
    Args:
        df: The DataFrame to save.
        filename: The output filename.
    """
    if df.empty:
        print("DataFrame is empty, not saving.")
        return

    print(f"Saving to {filename}...")
    # Ensure the directory exists if filename contains a path
    if os.path.dirname(filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
    df.to_parquet(filename, index=False)
    print("Done.")

