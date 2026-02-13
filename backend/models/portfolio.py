"""
Pydantic models for the simulated trading portfolio.
"""
import json
from datetime import datetime
from typing import List
from pathlib import Path
from pydantic import BaseModel, Field


class Position(BaseModel):
    """A single open position in the simulated portfolio."""

    position_id: str = Field(..., description="Unique ID for this position")
    pair_id: str = Field(..., description="The pair this position belongs to")
    market_id: str = Field(..., description="The market this position is in")
    market_title: str = Field(default="", description="Market title for display")
    outcome: str = Field(..., description="YES or NO")
    shares: float = Field(..., ge=0.0, description="Number of shares held")
    avg_price: float = Field(..., ge=0.0, le=1.0, description="Average price paid per share")
    cost_basis: float = Field(..., ge=0.0, description="Total cost (shares * avg_price)")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When the position was opened",
    )


class Portfolio(BaseModel):
    """The full simulated portfolio state."""

    cash: float = Field(default=10000.0, description="Available cash balance in USD")
    starting_balance: float = Field(default=10000.0, description="Initial starting balance")
    positions: List[Position] = Field(default_factory=list, description="Open positions")
    trade_count: int = Field(default=0, description="Total number of trades executed")

    def save_to_json(self, filepath: str) -> None:
        """Persist portfolio to a JSON file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str) -> "Portfolio":
        """Load portfolio from JSON file, or return default if not found."""
        path = Path(filepath)
        if not path.exists():
            return cls()
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)
