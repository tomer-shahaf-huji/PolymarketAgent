# PolymarketAgent

A Python-based agent for analyzing and pairing Polymarket prediction markets to identify potential arbitrage opportunities.

## 📁 Project Structure

```
PolymarketAgent/
├── backend/                    # Backend services and API
│   ├── api/                   # FastAPI server
│   │   ├── __init__.py
│   │   └── server.py          # Main API server
│   ├── models/                # Pydantic data models
│   │   ├── __init__.py
│   │   └── market.py          # Market and MarketPair models
│   └── services/              # Business logic
│       ├── __init__.py
│       ├── polymarket_client.py   # Polymarket API client
│       └── market_pairs.py        # Market pairing logic
│
├── scripts/                    # Executable scripts
│   ├── fetch_markets.py       # Fetch all markets from Polymarket
│   ├── find_market_pairs.py   # Generate market pairs by keywords
│   └── run_ui.py              # Start both backend and frontend
│
├── examples/                   # Example scripts
│   └── working_with_objects.py # Demo of object-oriented workflow
│
├── data/                       # Data storage (placeholder for DB)
│   ├── markets.parquet        # All fetched markets (394K markets)
│   └── market_pairs.parquet   # Generated market pairs (114K pairs)
│
├── frontend/                   # React web UI
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   └── App.jsx           # Main application
│   ├── package.json
│   └── vite.config.js
│
├── requirements.txt            # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

**Backend (Python):**
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Linux/Mac

# Install requirements
pip install -r requirements.txt
```

**Frontend (Node.js):**
```bash
cd frontend
npm install
cd ..
```

### 2. Fetch Market Data

Fetch all markets from Polymarket (394,000 markets):
```bash
python scripts/fetch_markets.py
```

This will save data to `data/markets.parquet` (~35 MB).

### 3. Generate Market Pairs

Create pairs of related markets by keywords (e.g., "Iran", "Trump"):
```bash
python scripts/find_market_pairs.py
```

This will save pairs to `data/market_pairs.parquet` (~920 KB).

### 4. Start the UI

Launch both backend API and frontend:
```bash
python scripts/run_ui.py
```

This will:
- Start FastAPI backend on http://localhost:8000
- Start React frontend on http://localhost:5173
- Open your browser automatically

## 🔧 Configuration

### Adding New Keywords

Edit `scripts/find_market_pairs.py` and add keywords to the list:

```python
keywords = ["Iran", "Trump", "Election", "Bitcoin"]  # Add your keywords here
```

Then regenerate pairs:
```bash
python scripts/find_market_pairs.py
```

### API Endpoints

**Backend API (http://localhost:8000)**
- `GET /` - API information
- `GET /api/pairs?keyword={keyword}&limit={limit}&offset={offset}` - Get market pairs
- `GET /api/pairs/{pair_id}` - Get specific pair
- `GET /api/keywords` - Get available keywords with counts
- `GET /api/triplets` - Get market triplets (placeholder)
- `GET /docs` - Interactive API documentation

## 📊 Data

### Markets Data Schema
- `market_id` - Unique market identifier
- `title` - Market question
- `description` - Full description
- `url` - Link to Polymarket
- `active` - Is market active?
- `closed` - Is market closed?
- `yes_odds` - Current YES probability (0-1 scale)
- `no_odds` - Current NO probability (0-1 scale)
- `volume` - Total trading volume (USD)
- `liquidity` - Available liquidity (USD)
- `end_date` - Market close/resolution date

### Pairs Data Schema
- `pair_id` - Unique pair identifier (e.g., "Iran_0001", "Trump_0042")
- `keyword` - Keyword that generated this pair
- `market1_*` - First market fields (id, title, url, yes_odds, no_odds)
- `market2_*` - Second market fields (id, title, url, yes_odds, no_odds)

## 🧪 Development

### Running Services Individually

**Backend only:**
```bash
python -m uvicorn backend.api.server:app --reload --port 8000
```

**Frontend only:**
```bash
cd frontend
npm run dev
```

### Object-Oriented Approach with Pydantic

The codebase uses **Pydantic models** for type-safe, validated data objects:

#### Market Model
```python
from backend.models.market import Market

# Markets are objects with validation and helper methods
market = Market(
    market_id="0x123...",
    title="Will Bitcoin reach $100k?",
    yes_odds=0.45,
    no_odds=0.55,
    # ... other fields
)

# Rich methods available
market.is_open()           # Check if market is open
market.has_valid_odds()    # Check if odds are valid
market.implied_edge()      # Calculate edge/overround
```

#### MarketPair Model
```python
from backend.models.market import MarketPair

# Pairs are objects containing two Market instances
pair = MarketPair(
    pair_id="Iran_0001",
    keyword="Iran",
    market1=market1,  # Market object
    market2=market2   # Market object
)

# Helper methods
pair.both_markets_open()        # Both markets open?
pair.both_have_valid_odds()     # Both have valid odds?
```

#### Database Placeholder
Currently using Parquet files as a placeholder for a future database:

```python
from backend.models.market import (
    load_markets_from_parquet,    # Placeholder for DB query
    save_markets_to_parquet,      # Placeholder for DB insert
    markets_to_dataframe          # Convert objects to DataFrame
)

# Load Market objects (will become DB query)
markets = load_markets_from_parquet("data/markets.parquet")

# Work with objects
open_markets = [m for m in markets if m.is_open()]

# Save back (will become DB insert)
save_markets_to_parquet(markets, "data/markets.parquet")
```

See [`examples/working_with_objects.py`](examples/working_with_objects.py) for a complete example.

### Project Architecture

The project follows a clean architecture pattern:

1. **Backend Layer**
   - `backend/models/` - Pydantic data models with validation
   - `backend/services/` - Business logic (market fetching, pairing)
   - `backend/api/` - REST API endpoints (FastAPI)

2. **Scripts Layer**
   - Executable scripts for data operations
   - User-facing commands

3. **Data Layer**
   - Parquet files for efficient storage (placeholder for database)
   - Separate from code for clarity

4. **Frontend Layer**
   - React SPA with TailwindCSS
   - Communicates with backend via REST API

## 📈 Current Statistics

- **Total Markets**: 394,000
- **Open Markets**: 16,453
- **Total Pairs**: 114,951
  - Iran: 2,850 pairs (76 markets)
  - Trump: 112,101 pairs (474 markets)

## 🎯 Features

- ✅ Fetch all Polymarket markets
- ✅ Filter by multiple keywords with word boundary matching
- ✅ Generate market pairs automatically
- ✅ REST API with filtering and pagination
- ✅ React UI with dropdown keyword filter
- ✅ Real-time pair filtering by keyword
- ✅ Polymarket-style card interface
- ⏳ Approve mechanism (placeholder)
- ⏳ Triplet generation
- ⏳ Arbitrage strategy implementation

## 🏗️ High-Level Goal

The agent continuously monitors Polymarket markets, detects actionable opportunities, evaluates risk and expected value, and executes trades according to predefined strategies.

Primary objective:
> **Maximize long-term profit while minimizing risk and unintended behavior.**

## 🎲 Core Strategy (v1): Arbitrage

The first implemented strategy is **arbitrage detection**.

General idea:
- Detect price inconsistencies between:
  - YES / NO shares
  - Related or logically equivalent markets
- Calculate guaranteed or near-guaranteed profit after fees
- Execute trades atomically when possible

Constraints:
- Must account for fees, slippage, and liquidity
- No execution if profit margin is below configurable threshold
- Strategy must be deterministic and explainable

## 📋 Design Principles (IMPORTANT FOR LLMs)

LLMs contributing to this repository **must follow these principles**:

1. **Correctness over cleverness**
   - Simple, explicit logic is preferred over complex abstractions

2. **No silent behavior**
   - Every decision must be explainable via logs or return values

3. **Deterministic strategies**
   - Same inputs → same outputs
   - No randomness unless explicitly requested

4. **Separation of concerns**
   - Strategy logic MUST NOT place orders directly
   - Execution layer MUST NOT contain strategy logic

5. **Safety first**
   - Never place trades without explicit validation
   - Always assume APIs can fail or return stale data

## 🤖 Instructions for LLM Code Agents

### You are expected to:

- Respect existing file boundaries and abstractions
- Extend the system by **adding strategies**, not modifying core logic unless requested
- Write clear docstrings and comments explaining *why*, not just *what*
- Prefer pure functions for strategy evaluation
- Add logging for every decision that may result in a trade

### You must NOT:

- Introduce hidden side effects
- Hardcode API keys, secrets, or endpoints
- Change strategy behavior without updating documentation
- Optimize prematurely unless explicitly asked

## 📝 License

MIT

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!
