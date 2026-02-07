import sys
import os
import pandas as pd

# Add the parent directory to sys.path to allow importing client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import PolymarketClient

def main():
    try:
        client = PolymarketClient()
        print("Fetching all markets (this may take a moment)...")
        
        # Consider a limit for testing, or remove for full fetch
        raw_markets = client.get_all_markets(limit=20) 
        print(f"Fetched {len(raw_markets)} markets.")

        parsed_data = []
        for m in raw_markets:
            parsed_data.append(client.parse_market(m))
        
        if not parsed_data:
            print("No markets found.")
            return

        # Create DataFrame
        df = pd.DataFrame(parsed_data)
        
        output_file = "markets.parquet"
        print(f"Saving to {output_file}...")
        df.to_parquet(output_file, index=False)
        print("Done.")
        
        # Verify
        print("\n--- Verification: Reading Parquet ---")
        read_df = pd.read_parquet(output_file)
        print(read_df[["Title", "Yes", "No", "URL"]].head())
        print(f"Total Rows: {len(read_df)}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
