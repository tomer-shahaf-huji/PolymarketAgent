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
        
        raw_markets = client.get_all_markets(limit=5) # Limit to 5 pages for demo speed
        print(f"Fetched {len(raw_markets)} markets.")

        parsed_data = []
        for m in raw_markets:
            parsed_data.append(client.parse_market(m))
        
        if not parsed_data:
            print("No markets found to display.")
            return

        # Create DataFrame
        df = pd.DataFrame(parsed_data)
        
        # Reorder/Select columns
        cols = ["Title", "Yes", "No", "URL"]
        if "Description" in df.columns:
             # Description can be long, maybe skip for table view or truncate more
             pass

        print("\n--- Market Data (Top 20) ---")
        # Set pandas display options to pretty print
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.max_colwidth', 50)
        
        print(df[cols].head(20))
        
        print(f"\nTotal Markets: {len(df)}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
