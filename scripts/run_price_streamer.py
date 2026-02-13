"""
Launch script for the real-time price streamer.

Connects to Polymarket's WebSocket API and streams price updates
for all token IDs in market_pairs.parquet. Prices are periodically
flushed back to parquet so the UI picks them up automatically.

Usage:
    python scripts/run_price_streamer.py
    python scripts/run_price_streamer.py --pairs-file data/market_pairs.parquet
    python scripts/run_price_streamer.py --flush-interval 10
"""
import argparse
import asyncio
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.price_streamer import PriceStreamer, FLUSH_INTERVAL


def main():
    parser = argparse.ArgumentParser(description="Real-time Polymarket price streamer")
    parser.add_argument(
        "--pairs-file",
        default=str(Path(__file__).parent.parent / "data" / "market_pairs.parquet"),
        help="Path to market_pairs.parquet file",
    )
    parser.add_argument(
        "--flush-interval",
        type=int,
        default=FLUSH_INTERVAL,
        help=f"Seconds between parquet flushes (default: {FLUSH_INTERVAL})",
    )
    args = parser.parse_args()

    pairs_file = Path(args.pairs_file)
    if not pairs_file.exists():
        print(f"Error: Pairs file not found: {pairs_file}")
        print("Run the pipeline first: python scripts/find_market_pairs.py --force")
        sys.exit(1)

    streamer = PriceStreamer(pairs_file=str(pairs_file))

    # Override flush interval if specified
    import backend.services.price_streamer as streamer_mod
    streamer_mod.FLUSH_INTERVAL = args.flush_interval

    # Handle Ctrl+C gracefully
    def handle_shutdown(sig, frame):
        print("\n[Streamer] Shutting down...")
        streamer.stop()

    signal.signal(signal.SIGINT, handle_shutdown)

    print("=" * 60)
    print("Polymarket Real-Time Price Streamer")
    print(f"Pairs file: {pairs_file}")
    print(f"Flush interval: {args.flush_interval}s")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    asyncio.run(streamer.run())


if __name__ == "__main__":
    main()
