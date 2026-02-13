"""
FastAPI server for serving market pairs data to the React frontend.
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
from pydantic import BaseModel as PydanticBaseModel

# Initialize FastAPI app
app = FastAPI(
    title="PolymarketAgent API",
    description="API for serving market pairs and triplets",
    version="1.0.0"
)

# Enable CORS for React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache for pairs data (refreshes when file changes)
_pairs_cache = None
_pairs_cache_mtime = None


def load_pairs_data() -> pd.DataFrame:
    """Load market pairs from parquet file, refreshing if file changed."""
    global _pairs_cache, _pairs_cache_mtime

    project_root = Path(__file__).parent.parent.parent
    pairs_file = project_root / "data" / "market_pairs.parquet"

    if not pairs_file.exists():
        raise FileNotFoundError(
            f"Market pairs file not found: {pairs_file}\n"
            f"Please run 'python scripts/find_market_pairs.py' first."
        )

    current_mtime = pairs_file.stat().st_mtime

    if _pairs_cache is not None and _pairs_cache_mtime == current_mtime:
        return _pairs_cache

    _pairs_cache = pd.read_parquet(str(pairs_file))
    _pairs_cache_mtime = current_mtime
    return _pairs_cache


def format_pair(row: pd.Series) -> Dict[str, Any]:
    """Format a pair DataFrame row as JSON, including live arbitrage scan."""
    from backend.services.arbitrage_scanner import scan_pair_from_row

    result = {
        "pair_id": row["pair_id"],
        "keyword": row.get("keyword", None),
        "reasoning": row.get("reasoning", None) if pd.notna(row.get("reasoning", None)) else None,
        "arbitrage": scan_pair_from_row(row),
        "market1": {
            "id": row["market1_id"],
            "title": row["market1_title"],
            "url": row["market1_url"],
            "yes_odds": float(row["market1_yes_odds"]) if pd.notna(row["market1_yes_odds"]) else None,
            "no_odds": float(row["market1_no_odds"]) if pd.notna(row["market1_no_odds"]) else None,
        },
        "market2": {
            "id": row["market2_id"],
            "title": row["market2_title"],
            "url": row["market2_url"],
            "yes_odds": float(row["market2_yes_odds"]) if pd.notna(row["market2_yes_odds"]) else None,
            "no_odds": float(row["market2_no_odds"]) if pd.notna(row["market2_no_odds"]) else None,
        }
    }
    return result


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PolymarketAgent API",
        "version": "1.0.0",
        "endpoints": {
            "pairs": "/api/pairs?keyword={keyword}&limit={limit}&offset={offset}",
            "pair_by_id": "/api/pairs/{pair_id}",
            "keywords": "/api/keywords",
            "triplets": "/api/triplets",
            "docs": "/docs"
        }
    }


@app.get("/api/pairs")
async def get_pairs(
    limit: int = 100,
    offset: int = 0,
    keyword: str = None,
    arbitrage_only: bool = False,
) -> Dict[str, Any]:
    """
    Get all market pairs with pagination, keyword filtering, and arbitrage filtering.

    Args:
        limit: Maximum number of pairs to return (default: 100)
        offset: Number of pairs to skip (default: 0)
        keyword: Optional keyword to filter pairs by (e.g., "Iran", "Trump")
        arbitrage_only: If true, only return pairs with arbitrage opportunities

    Returns:
        JSON with pairs array and pagination info
    """
    try:
        df = load_pairs_data()

        # Filter by keyword if provided
        if keyword and 'keyword' in df.columns:
            df = df[df['keyword'] == keyword]

        # Format all pairs (includes arbitrage scan)
        all_pairs = [format_pair(row) for _, row in df.iterrows()]

        # Filter for arbitrage only if requested
        if arbitrage_only:
            all_pairs = [p for p in all_pairs if p["arbitrage"]["has_arbitrage"]]

        # Count arbitrage opportunities across all pairs
        arb_count = sum(1 for p in all_pairs if p["arbitrage"]["has_arbitrage"])

        # Apply pagination
        total = len(all_pairs)
        paginated_pairs = all_pairs[offset:offset + limit]

        response = {
            "pairs": paginated_pairs,
            "total": total,
            "arbitrage_count": arb_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }

        if keyword:
            response["filter"] = {"keyword": keyword}

        return response

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading pairs: {str(e)}")


@app.get("/api/pairs/{pair_id}")
async def get_pair(pair_id: str) -> Dict[str, Any]:
    """
    Get a specific market pair by ID.

    Args:
        pair_id: The pair ID to retrieve

    Returns:
        JSON with pair data
    """
    try:
        df = load_pairs_data()

        # Find the pair
        pair_row = df[df["pair_id"] == pair_id]

        if pair_row.empty:
            raise HTTPException(status_code=404, detail=f"Pair not found: {pair_id}")

        return format_pair(pair_row.iloc[0])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading pair: {str(e)}")


@app.get("/api/keywords")
async def get_keywords() -> Dict[str, Any]:
    """
    Get list of available keywords with pair counts.

    Returns:
        JSON with keywords array
    """
    try:
        df = load_pairs_data()

        if 'keyword' not in df.columns:
            return {"keywords": []}

        # Get keyword counts
        keyword_counts = df['keyword'].value_counts().to_dict()

        keywords = [
            {
                "keyword": keyword,
                "pair_count": int(count)
            }
            for keyword, count in keyword_counts.items()
        ]

        return {
            "keywords": keywords,
            "total_keywords": len(keywords)
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading keywords: {str(e)}")


@app.get("/api/triplets")
async def get_triplets() -> Dict[str, Any]:
    """
    Get market triplets (placeholder for future implementation).

    Returns:
        JSON with empty triplets array
    """
    return {
        "triplets": [],
        "total": 0,
        "message": "Triplets feature coming soon"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        df = load_pairs_data()
        return {
            "status": "healthy",
            "pairs_loaded": len(df)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


class TradeRequest(PydanticBaseModel):
    """Request body for executing a simulated trade."""
    pair_id: str
    amount: float


@app.get("/api/portfolio")
async def get_portfolio() -> Dict[str, Any]:
    """Get current portfolio with live position valuations."""
    try:
        from backend.services.portfolio_service import get_portfolio_with_values
        return get_portfolio_with_values()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading portfolio: {str(e)}")


@app.post("/api/trade")
async def execute_trade(request: TradeRequest) -> Dict[str, Any]:
    """
    Execute a simulated arbitrage trade on a pair.

    Body:
        pair_id: The pair to trade
        amount: Dollar amount per side (total cost = 2 * amount)
    """
    try:
        from backend.services.portfolio_service import execute_pair_trade

        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive.")
        if request.amount > 5000:
            raise HTTPException(status_code=400, detail="Maximum $5,000 per side per trade.")

        result = execute_pair_trade(request.pair_id, request.amount)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade execution error: {str(e)}")


@app.post("/api/portfolio/reset")
async def reset_portfolio_endpoint() -> Dict[str, Any]:
    """Reset portfolio to initial $10,000 state."""
    try:
        from backend.services.portfolio_service import reset_portfolio, get_portfolio_with_values

        reset_portfolio()
        return get_portfolio_with_values()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting portfolio: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
