import pytest
from unittest.mock import MagicMock
from client.client import PolymarketClient

@pytest.fixture
def mock_clob_client():
    return MagicMock()

@pytest.fixture
def polymarket_client(mock_clob_client, monkeypatch):
    monkeypatch.setenv("POLYMARKET_PRIVATE_KEY", "test_key")
    # Mock ClobClient initialization
    with monkeypatch.context() as m:
        m.setattr("client.client.ClobClient", MagicMock(return_value=mock_clob_client))
        client = PolymarketClient()
        client.client = mock_clob_client  # Ensure our mock is used
        return client

def test_parse_market(polymarket_client):
    raw_market = {
        'condition_id': '123',
        'question': 'Will it rain?',
        'description': 'A market about rain.',
        'market_slug': 'will-it-rain',
        'outcomePrices': ["0.6", "0.4"],
        'tokens': [{'price': 0.6}, {'price': 0.4}]
    }
    
    parsed = polymarket_client.parse_market(raw_market)
    
    assert parsed['ID'] == '123'
    assert parsed['Title'] == 'Will it rain?'
    assert parsed['Yes'] == 0.6
    assert parsed['No'] == 0.4
    assert parsed['URL'] == 'https://polymarket.com/event/will-it-rain'

def test_parse_market_missing_data(polymarket_client):
    raw_market = {} # Empty market
    parsed = polymarket_client.parse_market(raw_market)
    
    assert parsed['ID'] == 'N/A'
    assert parsed['Title'] == 'N/A'
    assert parsed['Yes'] == 0.0
    assert parsed['No'] == 0.0
    assert parsed['URL'] == 'N/A'
