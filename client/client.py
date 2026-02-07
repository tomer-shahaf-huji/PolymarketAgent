import os
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
