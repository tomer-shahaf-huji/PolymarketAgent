import pytest
import pandas as pd
import os
from unittest.mock import MagicMock
from client.market_data import fetch_markets_as_dataframe, save_markets_to_parquet

@pytest.fixture
def mock_client():
    client = MagicMock()
    # Mock parse_market to return a dict
    client.parse_market.side_effect = lambda m: m
    return client

def test_fetch_markets_as_dataframe(mock_client):
    # Mock fetch response
    mock_client.get_all_markets.return_value = [{'ID': '1'}, {'ID': '2'}]
    
    df = fetch_markets_as_dataframe(mock_client, limit=1)
    
    assert len(df) == 2
    assert df.iloc[0]['ID'] == '1'
    assert df.iloc[1]['ID'] == '2'

def test_fetch_markets_empty(mock_client):
    mock_client.get_all_markets.return_value = []
    df = fetch_markets_as_dataframe(mock_client)
    assert df.empty

def test_save_markets_to_parquet(tmp_path):
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    file_path = tmp_path / "test.parquet"
    
    save_markets_to_parquet(df, str(file_path))
    
    assert os.path.exists(file_path)
    # Read back to verify
    read_df = pd.read_parquet(file_path)
    assert read_df.equals(df)

def test_save_empty_dataframe(tmp_path):
    df = pd.DataFrame()
    file_path = tmp_path / "test_empty.parquet"
    
    save_markets_to_parquet(df, str(file_path))
    
    assert not os.path.exists(file_path)
