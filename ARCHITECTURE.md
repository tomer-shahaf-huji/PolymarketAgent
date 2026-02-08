# Architecture: Three-Step Data Pipeline

## Overview

The application uses a **three-step data pipeline** to process Polymarket data. Each step works with **Pydantic objects** for type safety and validation. Parquet files serve as **placeholders for a future database**.

## Pipeline Steps

```
┌─────────────────────────────────────────────────────────────────┐
│                     STEP 1: Fetch Markets                       │
│                                                                  │
│  Polymarket API → Market objects → data/markets.parquet         │
│                                                                  │
│  Script: scripts/fetch_markets.py                               │
│  Service: backend/services/polymarket_client.py                 │
│  Model: backend/models/market.py (Market)                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                STEP 2: Extract Keyword Markets                  │
│                                                                  │
│  All markets → KeywordMarkets objects →                         │
│                 data/keywords/{keyword}.parquet                 │
│                                                                  │
│  Script: scripts/extract_keyword_markets.py                     │
│  Service: backend/services/keyword_markets.py                   │
│  Model: backend/models/keyword_market.py (KeywordMarkets)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            STEP 3: LLM-Driven Implication Pairing               │
│                                                                  │
│  Keyword markets → LLM analysis → MarketPair objects →          │
│                    data/pairs/{keyword}_pairs.parquet            │
│                    data/market_pairs.parquet (combined)          │
│                                                                  │
│  Script: scripts/find_market_pairs.py                           │
│  Service: backend/services/market_pairs.py                      │
│  LLM Client: backend/services/llm_client.py                    │
│  Model: backend/models/market.py (MarketPair)                   │
│  Mock data: data/mock/{keyword}_llm_response.json               │
└─────────────────────────────────────────────────────────────────┘
```

## Step 3: How LLM Pairing Works

Instead of brute-force combinations, the pipeline uses an LLM to identify **implication pairs** (A → B):

1. **Filter** keyword markets to those with valid odds (limit: 100 per keyword)
2. **Build prompt** with system instructions, few-shot examples, and market list
3. **LLM analyzes** markets and returns pairs where Market A resolving YES logically guarantees Market B also resolves YES
4. **Create MarketPair objects** mapping LLM index-based IDs back to Market objects

**Implication types the LLM identifies:**
- **Temporal Inclusion:** "Event by March" → "Event by June"
- **Numerical Inclusion:** "BTC > $100k" → "BTC > $90k"
- **Categorical Inclusion:** "Israel strikes Iran" → "US or Israel strikes Iran"

**Mock mode:** Currently uses pre-computed LLM responses stored in `data/mock/`. Set `use_mock=False` when real LLM API credentials are configured.

## Why Three Steps?

### Modularity
Each step is independent and can be run separately:
- Re-fetch markets without recreating pairs
- Re-extract keywords without re-fetching
- Re-create pairs without re-extracting

### Flexibility for Complex Logic
The separation allows for complex filtering at each step:

**Step 2 (Extract Keywords):**
- Apply keyword-specific filters
- Use different time windows per keyword
- Implement custom market selection logic
- Pre-compute keyword-specific features

**Step 3 (LLM Pairing):**
- LLM identifies logical implication relationships
- Each pair includes reasoning explaining the A → B logic
- Supports different pairing strategies (implication, arbitrage, future: triplets)

### Performance
- Process each keyword independently
- Cache intermediate results
- Parallel processing possible
- Avoid re-computing everything

## Data Models

### Market (Step 1)
```python
from backend.models.market import Market

market = Market(
    market_id="0x123...",
    title="Will Bitcoin reach $100k?",
    yes_odds=0.45,
    no_odds=0.55,
    active=True,
    closed=False,
    # ... other fields
)

# Helper methods
market.is_open()           # True if active and not closed
market.has_valid_odds()    # True if yes/no odds exist
market.implied_edge()      # Calculate edge/overround
```

### KeywordMarkets (Step 2)
```python
from backend.models.keyword_market import KeywordMarkets

keyword_markets = KeywordMarkets(
    keyword="Iran",
    markets=[market1, market2, market3, ...]
)

# Helper methods
keyword_markets.count()             # Number of markets
keyword_markets.open_markets()      # Filter for open markets
keyword_markets.markets_with_odds() # Filter for markets with odds
```

### MarketPair (Step 3)
```python
from backend.models.market import MarketPair

pair = MarketPair(
    pair_id="Iran_0001",
    keyword="Iran",
    market1=trigger_market,   # If this resolves YES...
    market2=implied_market,   # ...then this must also resolve YES
    reasoning="Temporal Inclusion: Event by March implies event by June"
)

# Helper methods
pair.both_markets_open()        # Both markets open?
pair.both_have_valid_odds()     # Both have valid odds?
```

### LLMPairResult (Step 3 intermediate)
```python
from backend.services.llm_client import LLMPairResult

result = LLMPairResult(
    trigger_market_id="31",    # Index in the market list
    implied_market_id="13",    # Index in the market list
    reasoning="Temporal Inclusion: ..."
)
```

## File Structure

```
data/
├── markets.parquet                 # All markets (Step 1 output)
├── keywords/                       # Step 2 output
│   ├── Iran.parquet               # Iran-related markets
│   ├── Trump.parquet              # Trump-related markets
│   └── {keyword}.parquet          # Other keywords
├── mock/                          # Mock LLM responses (Step 3 input)
│   ├── Iran_llm_response.json    # Pre-computed Iran pairs
│   └── Trump_llm_response.json   # Pre-computed Trump pairs
├── pairs/                         # Step 3 output (individual)
│   ├── Iran_pairs.parquet         # Pairs for Iran
│   ├── Trump_pairs.parquet        # Pairs for Trump
│   └── {keyword}_pairs.parquet    # Other keyword pairs
└── market_pairs.parquet           # Step 3 output (combined)
```

## Running the Pipeline

### Full Pipeline (All Steps)
```bash
# Step 1: Fetch all markets from Polymarket
python scripts/fetch_markets.py

# Step 2: Extract markets for each keyword
python scripts/extract_keyword_markets.py

# Step 3: LLM identifies implication pairs (mock mode)
python scripts/find_market_pairs.py
```

### Modifying Keywords
Edit `scripts/extract_keyword_markets.py`:
```python
keywords = ["Iran", "Trump", "Bitcoin", "Election"]
```

Then re-run steps 2 and 3:
```bash
python scripts/extract_keyword_markets.py
python scripts/find_market_pairs.py
```

### Adding Mock LLM Responses
To add mock responses for a new keyword, create `data/mock/{keyword}_llm_response.json`:
```json
[
  {
    "trigger_market_id": "0",
    "implied_market_id": "1",
    "reasoning": "Temporal Inclusion: ..."
  }
]
```

## Database Migration Path

When ready to replace parquet with a database:

### Step 1: Markets Table
```sql
CREATE TABLE markets (
    market_id VARCHAR PRIMARY KEY,
    title TEXT,
    description TEXT,
    url TEXT,
    yes_odds FLOAT,
    no_odds FLOAT,
    end_date TIMESTAMP,
    active BOOLEAN,
    closed BOOLEAN,
    volume FLOAT,
    liquidity FLOAT
);
```

### Step 2: Keyword Markets Table
```sql
CREATE TABLE keyword_markets (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR,
    market_id VARCHAR REFERENCES markets(market_id)
);

CREATE INDEX idx_keyword ON keyword_markets(keyword);
```

### Step 3: Market Pairs Table
```sql
CREATE TABLE market_pairs (
    pair_id VARCHAR PRIMARY KEY,
    keyword VARCHAR,
    reasoning TEXT,
    market1_id VARCHAR REFERENCES markets(market_id),
    market2_id VARCHAR REFERENCES markets(market_id)
);
```

## Next Steps

1. **Real LLM integration**: Configure API credentials in `llm_client.py`
2. **Triplet support**: Extend to identify three-market logic chains
3. **Add more keywords**: Edit `extract_keyword_markets.py`
4. **Database integration**: Replace parquet functions with DB operations
5. **Parallel processing**: Process keywords in parallel
