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
│                   STEP 3: Create Pairs                          │
│                                                                  │
│  Keyword markets → MarketPair objects →                         │
│                    data/pairs/{keyword}_pairs.parquet           │
│                    data/market_pairs.parquet (combined)         │
│                                                                  │
│  Script: scripts/find_market_pairs.py                           │
│  Service: backend/services/market_pairs.py                      │
│  Model: backend/models/market.py (MarketPair)                   │
└─────────────────────────────────────────────────────────────────┘
```

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

**Step 3 (Create Pairs):**
- Different pairing strategies per keyword
- Apply keyword-specific pair filters
- Compute arbitrage opportunities
- Select optimal pairs based on criteria

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
    market1=market1,  # Full Market object
    market2=market2   # Full Market object
)

# Helper methods
pair.both_markets_open()        # Both markets open?
pair.both_have_valid_odds()     # Both have valid odds?
```

## File Structure

```
data/
├── markets.parquet                 # All markets (Step 1 output)
├── keywords/                       # Step 2 output
│   ├── Iran.parquet               # Iran-related markets
│   ├── Trump.parquet              # Trump-related markets
│   └── {keyword}.parquet          # Other keywords
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

# Step 3: Create pairs from keyword markets
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

### Adding Custom Logic

**Example: Custom keyword filtering in Step 2**

Edit `backend/services/keyword_markets.py`:
```python
def extract_keyword_markets(all_markets, keyword, filter_open_only=True):
    # Standard filtering
    pattern = rf'\b{keyword}\b'
    regex = re.compile(pattern, re.IGNORECASE)
    keyword_markets = [m for m in all_markets if regex.search(m.title)]

    # ADD CUSTOM LOGIC HERE
    if keyword == "Iran":
        # Only include markets ending within 6 months for Iran
        cutoff = datetime.now() + timedelta(days=180)
        keyword_markets = [
            m for m in keyword_markets
            if m.end_date and m.end_date <= cutoff
        ]

    # Optionally filter for open markets
    if filter_open_only:
        keyword_markets = [m for m in keyword_markets if m.is_open()]

    return KeywordMarkets(keyword=keyword, markets=keyword_markets)
```

**Example: Custom pairing logic in Step 3**

Edit `backend/services/market_pairs.py`:
```python
def create_pairs_from_keyword_markets(keyword_markets, output_dir=None):
    keyword = keyword_markets.keyword
    markets = keyword_markets.markets

    # ADD CUSTOM LOGIC HERE
    if keyword == "Trump":
        # For Trump, only pair markets with similar end dates
        pairs = []
        for m1, m2 in combinations(markets, 2):
            if abs((m1.end_date - m2.end_date).days) <= 30:
                pair = MarketPair(
                    pair_id=f"{keyword}_{len(pairs):04d}",
                    keyword=keyword,
                    market1=m1,
                    market2=m2
                )
                pairs.append(pair)
    else:
        # Standard pairing for other keywords
        pairs = create_market_pairs(markets, keyword)

    return pairs
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

Replace:
```python
# Old: Parquet
save_markets_to_parquet(markets, "data/markets.parquet")

# New: Database
session.bulk_save_objects(markets)
session.commit()
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

Replace:
```python
# Old: Parquet per keyword
save_keyword_markets_to_parquet(km, f"data/keywords/{keyword}.parquet")

# New: Database
for market in keyword_markets.markets:
    session.add(KeywordMarket(keyword=keyword, market_id=market.market_id))
session.commit()
```

### Step 3: Market Pairs Table
```sql
CREATE TABLE market_pairs (
    pair_id VARCHAR PRIMARY KEY,
    keyword VARCHAR,
    market1_id VARCHAR REFERENCES markets(market_id),
    market2_id VARCHAR REFERENCES markets(market_id)
);
```

Replace:
```python
# Old: Parquet
save_market_pairs_to_parquet(pairs, "data/market_pairs.parquet")

# New: Database
session.bulk_save_objects(pairs)
session.commit()
```

## Benefits

### Type Safety
- Pydantic validates all data automatically
- Catches errors early
- Better IDE support

### Testability
- Each step can be unit tested independently
- Mock objects easily
- Test complex logic in isolation

### Maintainability
- Clear separation of concerns
- Easy to understand data flow
- Each step has a single responsibility

### Scalability
- Steps can run in parallel for different keywords
- Easy to add caching layers
- Can distribute processing

## Next Steps

1. **Add more keywords**: Edit `extract_keyword_markets.py`
2. **Custom filtering**: Modify `keyword_markets.py`
3. **Advanced pairing**: Enhance `market_pairs.py`
4. **Database integration**: Replace parquet functions with DB operations
5. **Add caching**: Cache intermediate results
6. **Parallel processing**: Process keywords in parallel
