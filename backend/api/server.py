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

# Cache for pairs data
_pairs_cache = None


def load_pairs_data() -> pd.DataFrame:
    """Load market pairs from parquet file."""
    global _pairs_cache

    if _pairs_cache is not None:
        return _pairs_cache

    # Get path relative to project root
    project_root = Path(__file__).parent.parent.parent
    pairs_file = project_root / "data" / "market_pairs.parquet"

    if not pairs_file.exists():
        raise FileNotFoundError(
            f"Market pairs file not found: {pairs_file}\n"
            f"Please run 'python scripts/find_market_pairs.py' first."
        )

    _pairs_cache = pd.read_parquet(str(pairs_file))
    return _pairs_cache


def format_pair(row: pd.Series) -> Dict[str, Any]:
    """Format a pair DataFrame row as JSON."""
    result = {
        "pair_id": row["pair_id"],
        "keyword": row.get("keyword", None),
        "reasoning": row.get("reasoning", None) if pd.notna(row.get("reasoning", None)) else None,
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
async def get_pairs(limit: int = 100, offset: int = 0, keyword: str = None) -> Dict[str, Any]:
    """
    Get all market pairs with pagination and optional keyword filtering.

    Args:
        limit: Maximum number of pairs to return (default: 100)
        offset: Number of pairs to skip (default: 0)
        keyword: Optional keyword to filter pairs by (e.g., "Iran", "Trump")

    Returns:
        JSON with pairs array and pagination info
    """
    try:
        df = load_pairs_data()

        # Filter by keyword if provided
        if keyword and 'keyword' in df.columns:
            df = df[df['keyword'] == keyword]

        # Apply pagination
        total = len(df)
        paginated_df = df.iloc[offset:offset + limit]

        # Convert to JSON format
        pairs = [format_pair(row) for _, row in paginated_df.iterrows()]

        response = {
            "pairs": pairs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }

        # Add keyword filter info if used
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
