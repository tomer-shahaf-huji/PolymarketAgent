"""
Pydantic models for Polymarket markets and market pairs.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, field_validator
import pandas as pd


class Market(BaseModel):
    """Represents a single Polymarket market."""

    market_id: str = Field(..., description="Unique identifier for the market (condition_id)")
    title: str = Field(..., description="Market question/title")
    description: str = Field(default="", description="Market description")
    url: str = Field(..., description="URL to the market on Polymarket")

    yes_odds: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability for 'Yes' outcome")
    no_odds: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability for 'No' outcome")

    end_date: Optional[datetime] = Field(None, description="Market end date")
    active: bool = Field(default=False, description="Whether the market is active")
    closed: bool = Field(default=False, description="Whether the market is closed")

    volume: float = Field(default=0.0, ge=0.0, description="Trading volume in USD")
    liquidity: float = Field(default=0.0, ge=0.0, description="Available liquidity in USD")

    class Config:
        json_schema_extra = {
            "example": {
                "market_id": "0x123abc...",
                "title": "Will Bitcoin reach $100k in 2024?",
                "description": "This market resolves to Yes if...",
                "url": "https://polymarket.com/event/btc-100k",
                "yes_odds": 0.45,
                "no_odds": 0.55,
                "end_date": "2024-12-31T23:59:59Z",
                "active": True,
                "closed": False,
                "volume": 150000.0,
                "liquidity": 25000.0
            }
        }

    @field_validator('yes_odds', 'no_odds', mode='before')
    @classmethod
    def validate_odds(cls, v: Optional[float]) -> Optional[float]:
        """Validate that odds are between 0 and 1, handling NaN as None."""
        import math
        # Handle NaN values from pandas (convert to None)
        if v is not None and isinstance(v, float) and math.isnan(v):
            return None
        # Validate range
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Odds must be between 0.0 and 1.0')
        return v

    def is_open(self) -> bool:
        """Check if the market is open for trading."""
        return self.active and not self.closed

    def has_valid_odds(self) -> bool:
        """Check if the market has valid yes/no odds."""
        return self.yes_odds is not None and self.no_odds is not None

    def implied_edge(self) -> Optional[float]:
        """
        Calculate the implied edge/overround.
        Returns None if odds are not available.

        In a fair market, yes_odds + no_odds should equal 1.0.
        The edge is the deviation from 1.0.
        """
        if not self.has_valid_odds():
            return None
        return abs(1.0 - (self.yes_odds + self.no_odds))

    def to_dict(self) -> dict:
        """Convert Market to dictionary format."""
        return {
            'market_id': self.market_id,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'yes_odds': self.yes_odds,
            'no_odds': self.no_odds,
            'end_date': self.end_date,
            'active': self.active,
            'closed': self.closed,
            'volume': self.volume,
            'liquidity': self.liquidity
        }

    @classmethod
    def from_api_response(cls, raw_market: dict) -> 'Market':
        """
        Create a Market instance from raw API response.

        Args:
            raw_market: Raw market dictionary from Polymarket API

        Returns:
            Market instance
        """
        # Extract basic fields
        market_id = raw_market.get('condition_id', '')
        title = raw_market.get('question', '')
        description = raw_market.get('description', '')
        slug = raw_market.get('market_slug', '')

        # Construct URL from slug
        url = f"https://polymarket.com/event/{slug}" if slug else ""

        # Extract yes/no odds from tokens array
        tokens = raw_market.get('tokens', [])
        yes_odds = None
        no_odds = None

        for token in tokens:
            outcome = token.get('outcome', '').lower()
            price = token.get('price')

            if price is not None:
                price = float(price)
                if outcome == 'yes':
                    yes_odds = price
                elif outcome == 'no':
                    no_odds = price

        # Extract additional fields
        end_date_str = raw_market.get('end_date_iso')
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        # Market status flags
        active = raw_market.get('active', False)
        closed = raw_market.get('closed', False)

        # Volume and liquidity (not available in standard endpoint)
        volume = 0.0
        liquidity = 0.0

        return cls(
            market_id=market_id,
            title=title,
            description=description,
            url=url,
            yes_odds=yes_odds,
            no_odds=no_odds,
            end_date=end_date,
            active=active,
            closed=closed,
            volume=volume,
            liquidity=liquidity
        )


class MarketPair(BaseModel):
    """Represents a pair of related Polymarket markets."""

    pair_id: str = Field(..., description="Unique identifier for this pair")
    keyword: Optional[str] = Field(None, description="Keyword that relates these markets")

    market1: Market = Field(..., description="First market in the pair")
    market2: Market = Field(..., description="Second market in the pair")

    class Config:
        json_schema_extra = {
            "example": {
                "pair_id": "Iran_0001",
                "keyword": "Iran",
                "market1": {
                    "market_id": "0x123...",
                    "title": "Will Iran win the 2026 FIFA World Cup?",
                    "url": "https://polymarket.com/event/...",
                    "yes_odds": 0.0025,
                    "no_odds": 0.9975,
                },
                "market2": {
                    "market_id": "0x456...",
                    "title": "Iran nuclear test before 2027?",
                    "url": "https://polymarket.com/event/...",
                    "yes_odds": 0.095,
                    "no_odds": 0.905,
                }
            }
        }

    def both_markets_open(self) -> bool:
        """Check if both markets in the pair are open."""
        return self.market1.is_open() and self.market2.is_open()

    def both_have_valid_odds(self) -> bool:
        """Check if both markets have valid odds."""
        return self.market1.has_valid_odds() and self.market2.has_valid_odds()

    def to_dict(self) -> dict:
        """Convert MarketPair to dictionary format (flat structure for DataFrame)."""
        return {
            'pair_id': self.pair_id,
            'keyword': self.keyword,
            'market1_id': self.market1.market_id,
            'market1_title': self.market1.title,
            'market1_url': self.market1.url,
            'market1_yes_odds': self.market1.yes_odds,
            'market1_no_odds': self.market1.no_odds,
            'market2_id': self.market2.market_id,
            'market2_title': self.market2.title,
            'market2_url': self.market2.url,
            'market2_yes_odds': self.market2.yes_odds,
            'market2_no_odds': self.market2.no_odds,
        }


def markets_to_dataframe(markets: List[Market]) -> pd.DataFrame:
    """
    Convert a list of Market objects to a pandas DataFrame.
    Placeholder for database persistence.

    Args:
        markets: List of Market objects

    Returns:
        DataFrame with market data
    """
    if not markets:
        return pd.DataFrame()

    data = [market.to_dict() for market in markets]
    return pd.DataFrame(data)


def market_pairs_to_dataframe(pairs: List[MarketPair]) -> pd.DataFrame:
    """
    Convert a list of MarketPair objects to a pandas DataFrame.
    Placeholder for database persistence.

    Args:
        pairs: List of MarketPair objects

    Returns:
        DataFrame with market pair data
    """
    if not pairs:
        return pd.DataFrame()

    data = [pair.to_dict() for pair in pairs]
    return pd.DataFrame(data)


def save_markets_to_parquet(markets: List[Market], filepath: str) -> None:
    """
    Save Market objects to parquet file (placeholder for DB).

    Args:
        markets: List of Market objects
        filepath: Path to output parquet file
    """
    df = markets_to_dataframe(markets)
    df.to_parquet(filepath, engine='pyarrow', compression='snappy', index=False)
    print(f"Saved {len(markets)} markets to {filepath}")


def save_market_pairs_to_parquet(pairs: List[MarketPair], filepath: str) -> None:
    """
    Save MarketPair objects to parquet file (placeholder for DB).

    Args:
        pairs: List of MarketPair objects
        filepath: Path to output parquet file
    """
    df = market_pairs_to_dataframe(pairs)
    df.to_parquet(filepath, engine='pyarrow', compression='snappy', index=False)
    print(f"Saved {len(pairs)} market pairs to {filepath}")


def load_markets_from_parquet(filepath: str) -> List[Market]:
    """
    Load Market objects from parquet file (placeholder for DB).

    Args:
        filepath: Path to parquet file

    Returns:
        List of Market objects
    """
    df = pd.read_parquet(filepath)
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

    return markets
