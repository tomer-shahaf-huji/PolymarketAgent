import os
import time
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from dotenv import load_dotenv

class PolymarketClient:
    def __init__(self):
        load_dotenv()
        self.private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
        self.host = os.getenv("POLYMARKET_HOST", "https://clob.polymarket.com/")
        self.chain_id = int(os.getenv("POLYMARKET_CHAIN_ID", 137))
        
        if not self.private_key:
            raise ValueError("POLYMARKET_PRIVATE_KEY is not set in environment variables")

        self.client = ClobClient(
            host=self.host,
            key=self.private_key,
            chain_id=self.chain_id
        )

    def get_markets(self, next_cursor=""):
        """
        Fetches active markets.
        """
        return self.client.get_markets(next_cursor=next_cursor)

    def get_all_markets(self, limit=100):
        """
        Fetches all active markets using pagination.
        limit: Max number of pages to fetch (safety break).
        """
        all_markets = []
        next_cursor = ""
        page_count = 0

        while page_count < limit:
            try:
                resp = self.get_markets(next_cursor=next_cursor)
                if not resp or 'data' not in resp:
                    print(f"Empty response or error: {resp}")
                    break
                
                markets = resp['data']
                if not markets:
                    break
                
                all_markets.extend(markets)
                
                next_cursor = resp.get('next_cursor')
                if not next_cursor or next_cursor == "0":
                    break
                
                page_count += 1
                time.sleep(0.2) # Rate limit friendliness
            except Exception as e:
                print(f"Error fetching page {page_count}: {e}")
                break
        
        return all_markets

    def parse_market(self, market):
        """
        Extracts relevant fields from a raw market dictionary.
        Returns a dict with: Title, Description, Yes Odds, No Odds, URL
        """
        
        # Helper to get odds
        def get_odds(outcome_index):
            # Try outcomePrices first (if available)
            try:
                if 'outcomePrices' in market and market['outcomePrices']:
                    return float(market['outcomePrices'][outcome_index])
            except (IndexError, ValueError, TypeError):
                pass
            
            # Fallback to tokens
            try:
                if 'tokens' in market and len(market['tokens']) > outcome_index:
                    return float(market['tokens'][outcome_index].get('price', 0))
            except (IndexError, ValueError, TypeError):
                pass
                
            return 0.0

        yes_odds = get_odds(0) # outcome 0
        no_odds = get_odds(1)  # outcome 1

        # Construct URL (try market_slug first, then slug)
        slug = market.get('market_slug') or market.get('slug', '')
        url = f"https://polymarket.com/event/{slug}" if slug else "N/A"

        return {
            "ID": market.get('condition_id', 'N/A'),
            "Title": market.get('question', 'N/A'),
            "Description": market.get('description', 'N/A')[:100] + "..." if market.get('description') else "N/A", # Truncate description
            "Yes": yes_odds,
            "No": no_odds,
            "URL": url
        }

    def get_orderbook(self, token_id):
        """
        Fetches the order book for a specific token.
        """
        return self.client.get_order_book(token_id)

    def create_order(self, token_id, price, size, side):
        """
        Creates a limit order.
        side: "BUY" or "SELL"
        """
        order_args = OrderArgs(
            price=price,
            size=size,
            side=side.upper(),
            token_id=token_id
        )
        return self.client.create_order(order_args)

    def cancel_all(self):
        """
        Cancels all open orders.
        """
        return self.client.cancel_all()
