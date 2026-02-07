import os
import sys

# Add the parent directory to sys.path to allow importing polymarket_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import PolymarketClient
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    try:
        client = PolymarketClient()
        print("Successfully initialized PolymarketClient")
        
        # Example: Fetch markets
        print("Fetching markets...")
        markets = client.get_markets()
        if markets and 'data' in markets:
            print(f"Found {len(markets['data'])} markets.")
            if len(markets['data']) > 0:
                print("First market example:", markets['data'][0])
        else:
            print("No markets found or error fetching markets.")
            print(markets)

        # Example: Fetch Order Book (using a dummy token_id or one from markets if available)
        # if markets and 'data' in markets and len(markets['data']) > 0:
        #     first_market = markets['data'][0]
        #     # Assuming the market data structure has a token_id or condition_id.
        #     # You might need to inspect the market data structure to get the correct token_id.
        #     # print("Fetching order book for first market...")
        #     # print(client.get_orderbook(first_market['token_id']))

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
