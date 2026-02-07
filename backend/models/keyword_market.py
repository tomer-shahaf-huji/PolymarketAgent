"""
Pydantic models for keyword-based market collections.
"""
from typing import List
from pydantic import BaseModel, Field
import pandas as pd

from .market import Market, markets_to_dataframe


class KeywordMarkets(BaseModel):
    """Represents a collection of markets related to a specific keyword."""

    keyword: str = Field(..., description="The keyword used to filter markets")
    markets: List[Market] = Field(..., description="List of markets matching this keyword")

    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "Iran",
                "markets": [
                    {
                        "market_id": "0x123...",
                        "title": "Will Iran win the 2026 FIFA World Cup?",
                        "yes_odds": 0.0025,
                        "no_odds": 0.9975,
                    }
                ]
            }
        }

    def count(self) -> int:
        """Get the number of markets in this collection."""
        return len(self.markets)

    def open_markets(self) -> List[Market]:
        """Get only the open markets from this collection."""
        return [m for m in self.markets if m.is_open()]

    def markets_with_odds(self) -> List[Market]:
        """Get only markets with valid odds."""
        return [m for m in self.markets if m.has_valid_odds()]

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            'keyword': self.keyword,
            'markets': [m.to_dict() for m in self.markets]
        }


def save_keyword_markets_to_parquet(keyword_markets: KeywordMarkets, filepath: str) -> None:
    """
    Save KeywordMarkets to parquet file (placeholder for DB).

    Args:
        keyword_markets: KeywordMarkets object
        filepath: Path to output parquet file
    """
    # Convert markets to DataFrame and add keyword column
    df = markets_to_dataframe(keyword_markets.markets)
    df['keyword'] = keyword_markets.keyword

    df.to_parquet(filepath, engine='pyarrow', compression='snappy', index=False)
    print(f"Saved {len(keyword_markets.markets)} '{keyword_markets.keyword}' markets to {filepath}")


def load_keyword_markets_from_parquet(filepath: str) -> KeywordMarkets:
    """
    Load KeywordMarkets from parquet file (placeholder for DB).

    Args:
        filepath: Path to parquet file

    Returns:
        KeywordMarkets object
    """
    df = pd.read_parquet(filepath)

    # Extract keyword (should be same for all rows)
    keyword = df['keyword'].iloc[0] if len(df) > 0 else ""

    # Remove keyword column before converting to Market objects
    df = df.drop(columns=['keyword'])

    markets = []
    for _, row in df.iterrows():
        market = Market(
            market_id=row['market_id'],
            title=row['title'],
            description=row.get('description', ''),
            url=row['url'],
            yes_odds=row.get('yes_odds'),
            no_odds=row.get('no_odds'),
            end_date=row.get('end_date'),
            active=row.get('active', False),
            closed=row.get('closed', False),
            volume=row.get('volume', 0.0),
            liquidity=row.get('liquidity', 0.0)
        )
        markets.append(market)

    return KeywordMarkets(keyword=keyword, markets=markets)
