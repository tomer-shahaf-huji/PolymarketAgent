"""
Market Pairing Service for finding and pairing related Polymarket markets.
"""
from itertools import combinations
import os
import pandas as pd


def load_markets(filepath: str = "markets.parquet") -> pd.DataFrame:
    """
    Load market data from parquet file.

    Args:
        filepath: Path to the parquet file

    Returns:
        DataFrame with market data

    Raises:
        FileNotFoundError: If the parquet file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Market data file not found: {filepath}\n"
            f"Please run 'python fetch_markets.py' first to fetch market data."
        )

    print(f"Loading markets from {filepath}...")
    df = pd.read_parquet(filepath)
    print(f"Loaded {len(df)} markets")
    return df


def filter_open_markets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter for markets that are open (active and not closed).

    Args:
        df: DataFrame with market data

    Returns:
        Filtered DataFrame with only open markets
    """
    open_markets = df[(df['active'] == True) & (df['closed'] == False)]
    print(f"Found {len(open_markets)} open markets")
    return open_markets


def find_keyword_markets(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """
    Filter markets where title contains a specific keyword as a whole word (case-insensitive).

    Args:
        df: DataFrame with market data
        keyword: Keyword to search for in market titles

    Returns:
        Filtered DataFrame with keyword-related markets
    """
    # Use word boundaries to match whole words only
    # \b ensures we match "Iran" but not "Miran"
    pattern = rf'\b{keyword}\b'
    keyword_markets = df[df['title'].str.contains(pattern, case=False, na=False, regex=True)]
    print(f"Found {len(keyword_markets)} '{keyword}'-related markets")
    return keyword_markets


def create_market_pairs(markets: pd.DataFrame, keyword: str = None) -> pd.DataFrame:
    """
    Create all possible pairs (combinations) of markets.

    Args:
        markets: DataFrame with markets to pair
        keyword: Optional keyword tag to associate with these pairs

    Returns:
        DataFrame where each row represents a pair of markets
    """
    if len(markets) < 2:
        print(f"Need at least 2 markets to create pairs, found {len(markets)}")
        # Return empty DataFrame with expected schema
        columns = [
            'pair_id', 'keyword', 'market1_id', 'market1_title', 'market1_url',
            'market1_yes_odds', 'market1_no_odds', 'market2_id',
            'market2_title', 'market2_url', 'market2_yes_odds', 'market2_no_odds'
        ]
        return pd.DataFrame(columns=columns)

    print(f"Creating pairs from {len(markets)} markets...")

    # Generate all combinations
    pairs_data = []
    pair_count = 0

    for idx1, idx2 in combinations(markets.index, 2):
        market1 = markets.loc[idx1]
        market2 = markets.loc[idx2]

        pair_count += 1
        pairs_data.append({
            'pair_id': f"{keyword}_{pair_count:04d}" if keyword else f"pair_{pair_count:04d}",
            'keyword': keyword if keyword else None,
            'market1_id': market1['market_id'],
            'market1_title': market1['title'],
            'market1_url': market1['url'],
            'market1_yes_odds': market1['yes_odds'],
            'market1_no_odds': market1['no_odds'],
            'market2_id': market2['market_id'],
            'market2_title': market2['title'],
            'market2_url': market2['url'],
            'market2_yes_odds': market2['yes_odds'],
            'market2_no_odds': market2['no_odds']
        })

    pairs_df = pd.DataFrame(pairs_data)
    print(f"Created {len(pairs_df)} pairs")
    return pairs_df


def save_pairs(pairs_df: pd.DataFrame, filepath: str = "market_pairs.parquet") -> None:
    """
    Save pairs DataFrame to parquet file.

    Args:
        pairs_df: DataFrame with market pairs
        filepath: Path to output parquet file
    """
    print(f"Saving pairs to {filepath}...")

    pairs_df.to_parquet(filepath, engine='pyarrow', compression='snappy', index=False)

    # Print file size
    file_size = os.path.getsize(filepath) / 1024  # Convert to KB
    print(f"Successfully saved {len(pairs_df)} pairs to {filepath}")
    print(f"File size: {file_size:.2f} KB")


def find_and_pair_markets_multi_keyword(
    keywords: list[str],
    input_file: str = "markets.parquet",
    output_file: str = "market_pairs.parquet"
) -> pd.DataFrame:
    """
    Main function to find and pair markets for multiple keywords.

    This function:
    1. Loads market data from parquet file
    2. Filters for open markets
    3. For each keyword:
       - Filters for keyword-related markets
       - Creates all possible pairs
    4. Combines all pairs from all keywords
    5. Saves combined pairs to parquet file

    Args:
        keywords: List of keywords to search for (e.g., ["Iran", "Trump"])
        input_file: Path to input market data parquet file
        output_file: Path to output pairs parquet file

    Returns:
        DataFrame with market pairs from all keywords
    """
    print("=" * 60)
    print(f"Market Pairing Service - Multiple Keywords")
    print(f"Keywords: {', '.join(keywords)}")
    print("=" * 60)
    print()

    # Step 1: Load markets
    markets_df = load_markets(input_file)
    print()

    # Step 2: Filter for open markets
    open_markets = filter_open_markets(markets_df)
    print()

    # Step 3-4: For each keyword, find markets and create pairs
    all_pairs = []

    for keyword in keywords:
        print(f"Processing keyword: '{keyword}'")
        print("-" * 40)

        # Find markets for this keyword
        keyword_markets = find_keyword_markets(open_markets, keyword)

        if len(keyword_markets) >= 2:
            # Create pairs for this keyword
            pairs_df = create_market_pairs(keyword_markets, keyword)
            all_pairs.append(pairs_df)
            print(f"[OK] Created {len(pairs_df)} pairs for '{keyword}'")
        else:
            print(f"[SKIP] Skipping '{keyword}' (need at least 2 markets, found {len(keyword_markets)})")

        print()

    # Step 5: Combine all pairs
    if all_pairs:
        combined_pairs = pd.concat(all_pairs, ignore_index=True)
        print("=" * 60)
        print(f"Total pairs created: {len(combined_pairs)}")
        print("=" * 60)
        print()

        # Step 6: Save combined pairs
        save_pairs(combined_pairs, output_file)
        return combined_pairs
    else:
        print("No pairs created for any keyword")
        return pd.DataFrame()


def find_and_pair_markets(
    input_file: str = "markets.parquet",
    output_file: str = "market_pairs.parquet",
    keywords: list[str] = None
) -> pd.DataFrame:
    """
    Main function to find and pair keyword-related markets.

    This function:
    1. Loads market data from parquet file
    2. Filters for open markets
    3. Filters for keyword-related markets
    4. Creates all possible pairs
    5. Saves pairs to parquet file

    Args:
        input_file: Path to input market data parquet file
        output_file: Path to output pairs parquet file
        keywords: List of keywords to search for. If None, defaults to ["Iran", "Trump"]

    Returns:
        DataFrame with market pairs
    """
    # Default keywords if none provided
    if keywords is None:
        keywords = ["Iran", "Trump"]

    # Use multi-keyword function
    return find_and_pair_markets_multi_keyword(
        keywords=keywords,
        input_file=input_file,
        output_file=output_file
    )
