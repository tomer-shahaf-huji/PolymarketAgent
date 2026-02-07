"""
Convenience script to start both the FastAPI backend and React frontend servers.
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

    # Start FastAPI backend
    print("1. Starting FastAPI backend server...")
    print("   URL: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print()

    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api.server:app", "--reload", "--port", "8000"],
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

    # Open browser
    print()
    print("3. Opening browser...")
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
    print("  • Frontend UI:  http://localhost:5173")
    print("  • Backend API:  http://localhost:8000")
    print("  • API Docs:     http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop both servers")
    print()

    try:
        # Keep the script running
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("Stopping servers...")
        print("=" * 60)
        backend.terminate()
        frontend.terminate()

        # Wait for graceful shutdown
        try:
            backend.wait(timeout=5)
            frontend.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend.kill()
            frontend.kill()

        print("[OK] Servers stopped")
        print()


if __name__ == "__main__":
    main()
