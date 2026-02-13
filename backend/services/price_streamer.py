"""
Real-time price streamer using Polymarket WebSocket API.

Connects to the public MARKET channel and streams price updates
for all token IDs found in market_pairs.parquet. Periodically
flushes updated prices back to the parquet file so the UI
picks them up via the server's mtime-aware cache.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

try:
    import websockets
except ImportError:
    raise ImportError("websockets package required: pip install websockets")

from backend.models.market import load_market_pairs_from_parquet, save_market_pairs_to_parquet

# Constants
WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
PING_INTERVAL = 10  # seconds
FLUSH_INTERVAL = 5  # seconds - write prices to parquet
RECONNECT_DELAY = 3  # seconds before reconnect attempt
MAX_ASSETS_PER_CONNECTION = 500

PROJECT_ROOT = Path(__file__).parent.parent.parent
PAIRS_FILE = PROJECT_ROOT / "data" / "market_pairs.parquet"


class PriceStreamer:
    """
    WebSocket price streamer for Polymarket markets.

    Subscribes to price_change events for all token IDs in the pairs file,
    keeps an in-memory price dict, and periodically flushes to parquet.
    """

    def __init__(self, pairs_file: str = str(PAIRS_FILE)):
        self.pairs_file = pairs_file
        # token_id -> {"best_bid": float, "best_ask": float}
        self.prices: Dict[str, Dict[str, float]] = {}
        # token_id -> market mapping for flush
        self.token_to_market: Dict[str, dict] = {}
        self.token_ids: list[str] = []
        self._dirty = False  # whether prices changed since last flush
        self._running = False
        self._update_count = 0

    def load_token_ids(self) -> list[str]:
        """Load all unique token IDs from the pairs parquet file."""
        pairs = load_market_pairs_from_parquet(self.pairs_file)

        token_ids = set()
        self.token_to_market = {}

        for pair in pairs:
            for market, prefix in [(pair.market1, "market1"), (pair.market2, "market2")]:
                if market.yes_token_id:
                    token_ids.add(market.yes_token_id)
                    self.token_to_market[market.yes_token_id] = {
                        "market_id": market.market_id,
                        "outcome": "yes",
                    }
                if market.no_token_id:
                    token_ids.add(market.no_token_id)
                    self.token_to_market[market.no_token_id] = {
                        "market_id": market.market_id,
                        "outcome": "no",
                    }

        self.token_ids = list(token_ids)
        print(f"[Streamer] Loaded {len(self.token_ids)} unique token IDs from {len(pairs)} pairs")
        return self.token_ids

    def flush_prices_to_parquet(self) -> None:
        """Write updated prices from in-memory dict back to parquet."""
        if not self._dirty:
            return

        try:
            pairs = load_market_pairs_from_parquet(self.pairs_file)
            updated = 0

            for pair in pairs:
                for market in [pair.market1, pair.market2]:
                    # Update YES price
                    if market.yes_token_id and market.yes_token_id in self.prices:
                        price_data = self.prices[market.yes_token_id]
                        new_price = price_data.get("best_bid")
                        if new_price is not None and new_price != market.yes_odds:
                            market.yes_odds = new_price
                            updated += 1

                    # Update NO price
                    if market.no_token_id and market.no_token_id in self.prices:
                        price_data = self.prices[market.no_token_id]
                        new_price = price_data.get("best_bid")
                        if new_price is not None and new_price != market.no_odds:
                            market.no_odds = new_price
                            updated += 1

            if updated > 0:
                save_market_pairs_to_parquet(pairs, self.pairs_file)
                print(f"[Streamer] Flushed {updated} price updates to parquet")

            self._dirty = False
        except Exception as e:
            print(f"[Streamer] Error flushing prices: {e}")

    def handle_message(self, raw_message: str) -> None:
        """Process an incoming WebSocket message."""
        try:
            messages = json.loads(raw_message)

            # The WS can send a single message or an array
            if not isinstance(messages, list):
                messages = [messages]

            for msg in messages:
                event_type = msg.get("event_type")

                if event_type == "price_change":
                    asset_id = msg.get("asset_id")
                    if asset_id and asset_id in self.token_to_market:
                        price_data = msg.get("price", {})
                        if isinstance(price_data, dict):
                            best_bid = price_data.get("best_bid")
                            best_ask = price_data.get("best_ask")
                        else:
                            # Sometimes price is a flat number
                            best_bid = float(price_data) if price_data else None
                            best_ask = None

                        if best_bid is not None:
                            best_bid = float(best_bid)
                            if asset_id not in self.prices:
                                self.prices[asset_id] = {}
                            self.prices[asset_id]["best_bid"] = best_bid
                            if best_ask is not None:
                                self.prices[asset_id]["best_ask"] = float(best_ask)
                            self._dirty = True
                            self._update_count += 1

                elif event_type == "last_trade_price":
                    asset_id = msg.get("asset_id")
                    if asset_id and asset_id in self.token_to_market:
                        price = msg.get("price")
                        if price is not None:
                            price = float(price)
                            if asset_id not in self.prices:
                                self.prices[asset_id] = {}
                            # Use last trade price as best_bid if we don't have one yet
                            if "best_bid" not in self.prices[asset_id]:
                                self.prices[asset_id]["best_bid"] = price
                                self._dirty = True
                                self._update_count += 1

        except json.JSONDecodeError:
            pass  # Skip non-JSON messages (pong, etc.)
        except Exception as e:
            print(f"[Streamer] Error processing message: {e}")

    async def _ping_loop(self, ws) -> None:
        """Send PING frames to keep the connection alive."""
        while self._running:
            try:
                await ws.send("PING")
                await asyncio.sleep(PING_INTERVAL)
            except Exception:
                break

    async def _flush_loop(self) -> None:
        """Periodically flush prices to parquet."""
        while self._running:
            await asyncio.sleep(FLUSH_INTERVAL)
            self.flush_prices_to_parquet()

    async def _connect_and_stream(self) -> None:
        """Connect to WebSocket and process messages."""
        print(f"[Streamer] Connecting to {WS_URL}")

        async with websockets.connect(WS_URL) as ws:
            print("[Streamer] Connected!")

            # Subscribe to all token IDs
            # Respect the 500 asset limit per subscription message
            for i in range(0, len(self.token_ids), MAX_ASSETS_PER_CONNECTION):
                batch = self.token_ids[i:i + MAX_ASSETS_PER_CONNECTION]
                subscribe_msg = json.dumps({
                    "assets_ids": batch,
                    "type": "market",
                })
                await ws.send(subscribe_msg)
                print(f"[Streamer] Subscribed to {len(batch)} assets (batch {i // MAX_ASSETS_PER_CONNECTION + 1})")

            # Start ping loop
            ping_task = asyncio.create_task(self._ping_loop(ws))

            try:
                async for message in ws:
                    if not self._running:
                        break
                    if message == "PONG":
                        continue
                    self.handle_message(message)
            finally:
                ping_task.cancel()

    async def run(self) -> None:
        """Main run loop with auto-reconnect."""
        self.load_token_ids()

        if not self.token_ids:
            print("[Streamer] No token IDs found. Run the pipeline with --force first to populate token IDs.")
            return

        self._running = True

        # Start flush loop
        flush_task = asyncio.create_task(self._flush_loop())

        try:
            while self._running:
                try:
                    await self._connect_and_stream()
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"[Streamer] Connection closed: {e}. Reconnecting in {RECONNECT_DELAY}s...")
                except Exception as e:
                    print(f"[Streamer] Error: {e}. Reconnecting in {RECONNECT_DELAY}s...")

                if self._running:
                    await asyncio.sleep(RECONNECT_DELAY)
        finally:
            self._running = False
            flush_task.cancel()
            # Final flush
            self.flush_prices_to_parquet()
            print(f"[Streamer] Stopped. Total price updates received: {self._update_count}")

    def stop(self) -> None:
        """Signal the streamer to stop."""
        self._running = False
        print("[Streamer] Stop signal received")
