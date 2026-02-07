# Changelog: Three-Step Pipeline Architecture

## Summary

Added an intermediate layer between market fetching and pair creation. The workflow is now:

1. **Fetch Markets** → All markets saved to parquet
2. **Extract Keyword Markets** → Keyword-specific markets saved to separate files (**NEW**)
3. **Create Pairs** → Pairs created from keyword-specific markets

This modular approach allows for complex keyword-specific logic at each step.

## New Components

### 1. Models

**backend/models/keyword_market.py**
- `KeywordMarkets` - Pydantic model representing a collection of markets for a specific keyword
- Helper methods: `count()`, `open_markets()`, `markets_with_odds()`
- Save/load functions: `save_keyword_markets_to_parquet()`, `load_keyword_markets_from_parquet()`

### 2. Services

**backend/services/keyword_markets.py**
- `extract_keyword_markets()` - Filter markets by keyword
- `process_all_keywords()` - Main function for Step 2
- `load_keyword_markets_for_keyword()` - Load keyword markets from storage
- `get_available_keywords()` - Get list of processed keywords

### 3. Scripts

**scripts/extract_keyword_markets.py** (NEW)
- Runs Step 2 of the pipeline
- Reads all markets, filters by keyword, saves to separate files
- Configuration: Edit `keywords` list to add more keywords

### 4. Updated Services

**backend/services/market_pairs.py**
- Updated to read from keyword-specific files instead of filtering on the fly
- `create_pairs_from_keyword_markets()` - Create pairs from KeywordMarkets object
- `find_and_pair_markets_multi_keyword()` - Updated to use new workflow
- Option to save individual keyword pairs to `data/pairs/{keyword}_pairs.parquet`

### 5. Examples

**examples/three_step_workflow.py**
- Complete demonstration of the three-step pipeline
- Shows how each step works and connects

## Data Flow

### Before (2 steps)
```
Polymarket API
     ↓
All Markets (parquet)
     ↓
Filter by keywords + Create pairs (in one step)
     ↓
Market Pairs (parquet)
```

### After (3 steps)
```
Polymarket API
     ↓
All Markets (parquet)
     ↓
Extract by keyword (separate step)
     ↓
Keyword Markets (parquet per keyword)
     ↓
Create pairs (reads keyword markets)
     ↓
Market Pairs (parquet per keyword + combined)
```

## File Structure Changes

```
data/
├── markets.parquet                 # Step 1 output (unchanged)
├── keywords/                       # Step 2 output (NEW)
│   ├── Iran.parquet               # Markets for Iran keyword
│   ├── Trump.parquet              # Markets for Trump keyword
│   └── {keyword}.parquet          # Markets for other keywords
├── pairs/                         # Step 3 output per keyword (NEW)
│   ├── Iran_pairs.parquet         # Pairs for Iran
│   ├── Trump_pairs.parquet        # Pairs for Trump
│   └── {keyword}_pairs.parquet    # Pairs for other keywords
└── market_pairs.parquet           # Step 3 combined output (unchanged)
```

## Usage

### Quick Start (Full Pipeline)
```bash
# Run all steps
python scripts/fetch_markets.py
python scripts/extract_keyword_markets.py
python scripts/find_market_pairs.py
```

### Adding New Keywords
```python
# Edit scripts/extract_keyword_markets.py
keywords = ["Iran", "Trump", "Bitcoin", "Election"]
```

```bash
# Re-run steps 2 and 3
python scripts/extract_keyword_markets.py
python scripts/find_market_pairs.py
```

### Re-generating Pairs Only
```bash
# If keyword markets already extracted, just regenerate pairs
python scripts/find_market_pairs.py
```

## Benefits

### 1. Modularity
Each step is independent:
- Re-fetch markets without recreating pairs
- Re-extract keywords without re-fetching
- Re-create pairs without re-extracting

### 2. Flexibility for Complex Logic
Easy to add keyword-specific logic:

```python
# In keyword_markets.py
def extract_keyword_markets(all_markets, keyword, filter_open_only=True):
    # Filter by keyword
    keyword_markets = [m for m in all_markets if keyword in m.title]

    # ADD CUSTOM LOGIC HERE
    if keyword == "Iran":
        # Special filtering for Iran markets
        keyword_markets = [m for m in keyword_markets if m.volume > 1000]

    return KeywordMarkets(keyword=keyword, markets=keyword_markets)
```

```python
# In market_pairs.py
def create_pairs_from_keyword_markets(keyword_markets, output_dir=None):
    # ADD CUSTOM LOGIC HERE
    if keyword_markets.keyword == "Trump":
        # Different pairing strategy for Trump
        pairs = custom_trump_pairing(keyword_markets.markets)
    else:
        # Standard pairing
        pairs = create_market_pairs(keyword_markets.markets)

    return pairs
```

### 3. Performance
- Process each keyword independently
- Cache intermediate results
- Parallel processing possible (future enhancement)
- Avoid re-computing everything when adding keywords

### 4. Better Organization
- Clear separation of concerns
- Each step has a single responsibility
- Easier to understand and maintain

## Migration from Old Workflow

If you have existing code using the old 2-step workflow:

### Old Way
```python
from backend.services.market_pairs import find_and_pair_markets

# This used to do filtering + pairing in one step
pairs = find_and_pair_markets(
    input_file="data/markets.parquet",
    output_file="data/market_pairs.parquet",
    keywords=["Iran", "Trump"]
)
```

### New Way
```python
# Step 2: Extract keyword markets
from backend.services.keyword_markets import process_all_keywords

keyword_markets_list = process_all_keywords(
    input_file="data/markets.parquet",
    keywords=["Iran", "Trump"],
    output_dir="data/keywords"
)

# Step 3: Create pairs from keyword markets
from backend.services.market_pairs import find_and_pair_markets_multi_keyword

pairs = find_and_pair_markets_multi_keyword(
    keywords=["Iran", "Trump"],
    keywords_dir="data/keywords",
    output_file="data/market_pairs.parquet"
)
```

Or simply run the scripts:
```bash
python scripts/extract_keyword_markets.py
python scripts/find_market_pairs.py
```

## Backward Compatibility

The old `find_and_pair_markets()` function still exists but is deprecated. It now internally uses the old workflow (filters all markets on the fly). Consider migrating to the new 3-step approach for better flexibility.

## Future Enhancements

With this architecture, we can easily add:

1. **Keyword-specific time windows**: Different end date filters per keyword
2. **Custom pair scoring**: Rank pairs differently per keyword
3. **Parallel processing**: Process each keyword in parallel
4. **Incremental updates**: Only re-process changed keywords
5. **Keyword dependencies**: Create pairs across different keywords
6. **Advanced filtering**: ML-based market selection per keyword

## Files Modified

### Created
- `backend/models/keyword_market.py`
- `backend/services/keyword_markets.py`
- `scripts/extract_keyword_markets.py`
- `examples/three_step_workflow.py`
- `ARCHITECTURE.md`
- `CHANGELOG_THREE_STEP.md` (this file)

### Modified
- `backend/models/__init__.py` - Export KeywordMarkets
- `backend/services/market_pairs.py` - Updated to use keyword markets
- `scripts/find_market_pairs.py` - Updated to run Step 3
- `README.md` - Updated Quick Start and Configuration sections

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed explanation of the three-step pipeline
- **[README.md](README.md)** - Updated with new workflow
- **[examples/three_step_workflow.py](examples/three_step_workflow.py)** - Complete working example
