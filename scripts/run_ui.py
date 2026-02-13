"""
Convenience script to start the FastAPI backend, React frontend,
and real-time price streamer all from a single terminal.
"""
import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path


def main():
    print("=" * 60)
    print("Starting PolymarketAgent UI")
    print("=" * 60)
    print()

    # Get project root directory
    project_root = Path(__file__).parent.parent
    data_file = project_root / "data" / "market_pairs.parquet"

    # Check if market_pairs.parquet exists
    if not data_file.exists():
        print("[!] Warning: market_pairs.parquet not found!")
        print("   Run 'python scripts/find_market_pairs.py' first to generate market pairs.")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    else:
        mtime = data_file.stat().st_mtime
        age_minutes = (time.time() - mtime) / 60
        print(f"[i] market_pairs.parquet last updated {age_minutes:.0f} minutes ago")
        print()

    # Start FastAPI backend
    print("1. Starting FastAPI backend server...")
    print("   URL: http://localhost:8001")
    print("   Docs: http://localhost:8001/docs")
    print()

    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api.server:app", "--reload", "--port", "8001"],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for backend to start
    print("   Waiting for backend to start...")
    time.sleep(3)

    # Start Vite frontend
    print()
    print("2. Starting React frontend (Vite dev server)...")
    print("   URL: http://localhost:5173")
    print()

    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(project_root / "frontend"),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for frontend to start
    print("   Waiting for frontend to start...")
    time.sleep(4)

    # Start price streamer
    streamer = None
    if data_file.exists():
        print()
        print("3. Starting real-time price streamer (WebSocket)...")
        streamer = subprocess.Popen(
            [sys.executable, str(project_root / "scripts" / "run_price_streamer.py")],
            cwd=str(project_root),
        )
        print("   [OK] Price streamer started")
    else:
        print()
        print("3. [SKIP] Price streamer not started (no pairs data yet)")

    # Open browser
    print()
    print("4. Opening browser...")
    try:
        webbrowser.open("http://localhost:5173")
        print("   [OK] Browser opened")
    except Exception as e:
        print(f"   [ERROR] Could not open browser: {e}")
        print("   Please manually navigate to http://localhost:5173")

    print()
    print("=" * 60)
    print("[OK] UI is running!")
    print("=" * 60)
    print()
    print("Services:")
    print("  • Frontend UI:      http://localhost:5173")
    print("  • Backend API:      http://localhost:8001")
    print("  • API Docs:         http://localhost:8001/docs")
    print("  • Price Streamer:   " + ("running" if streamer else "not started"))
    print()
    print("Press Ctrl+C to stop all services")
    print()

    try:
        # Keep the script running
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("Stopping services...")
        print("=" * 60)
        backend.terminate()
        frontend.terminate()
        if streamer:
            streamer.terminate()

        # Wait for graceful shutdown
        try:
            backend.wait(timeout=5)
            frontend.wait(timeout=5)
            if streamer:
                streamer.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend.kill()
            frontend.kill()
            if streamer:
                streamer.kill()

        print("[OK] All services stopped")
        print()


if __name__ == "__main__":
    main()
