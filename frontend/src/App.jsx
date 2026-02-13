import { useState, useEffect } from 'react';
import { getPortfolio, executeTrade, resetPortfolio } from './services/api';
import PairCard from './components/PairCard';
import PortfolioPanel from './components/PortfolioPanel';
import axios from 'axios';

function App() {
  const [pairs, setPairs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);
  const [arbCount, setArbCount] = useState(0);
  const [selectedKeyword, setSelectedKeyword] = useState('all');
  const [keywords, setKeywords] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [showArbitrageOnly, setShowArbitrageOnly] = useState(false);
  const [portfolio, setPortfolio] = useState(null);
  const [tradingPairId, setTradingPairId] = useState(null);

  useEffect(() => {
    loadKeywords();
    loadPortfolio();
  }, []);

  useEffect(() => {
    loadPairs();
  }, [selectedKeyword, showArbitrageOnly]);

  const loadKeywords = async () => {
    try {
      const response = await axios.get('http://localhost:8001/api/keywords');
      setKeywords(response.data.keywords);
    } catch (err) {
      console.error('Error loading keywords:', err);
    }
  };

  const loadPortfolio = async () => {
    try {
      const data = await getPortfolio();
      setPortfolio(data);
    } catch (err) {
      console.error('Error loading portfolio:', err);
    }
  };

  const loadPairs = async () => {
    try {
      setLoading(true);
      const keyword = selectedKeyword === 'all' ? null : selectedKeyword;
      const response = await axios.get('http://localhost:8001/api/pairs', {
        params: {
          limit: 3000,
          offset: 0,
          keyword: keyword,
          arbitrage_only: showArbitrageOnly || undefined,
        }
      });
      // Sort: arbitrage pairs first (by profit desc), then non-arb pairs
      const sorted = [...response.data.pairs].sort((a, b) => {
        const aArb = a.arbitrage?.has_arbitrage ? 1 : 0;
        const bArb = b.arbitrage?.has_arbitrage ? 1 : 0;
        if (aArb !== bArb) return bArb - aArb;
        if (aArb && bArb) return (b.arbitrage.profit_pct || 0) - (a.arbitrage.profit_pct || 0);
        return 0;
      });
      setPairs(sorted);
      setTotal(response.data.total);
      setArbCount(response.data.arbitrage_count || 0);
      setError(null);
      loadPortfolio();
    } catch (err) {
      console.error('Error loading pairs:', err);
      setError(err.response?.data?.detail || 'Failed to load market pairs. Make sure the API server is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (pairId, amount) => {
    try {
      setTradingPairId(pairId);
      const result = await executeTrade(pairId, amount);
      setPortfolio(result.portfolio);
    } catch (err) {
      const message = err.response?.data?.detail || 'Trade failed. Please try again.';
      alert(message);
    } finally {
      setTradingPairId(null);
    }
  };

  const handleReset = async () => {
    if (!confirm('Reset portfolio to $10,000? All positions will be lost.')) return;
    try {
      const data = await resetPortfolio();
      setPortfolio(data);
    } catch (err) {
      console.error('Error resetting portfolio:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">PolymarketAgent</h1>
              <p className="text-sm text-gray-500 mt-1">Market Pairs Analysis</p>
            </div>
            <div className="flex items-center gap-4">
              {!loading && arbCount > 0 && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800">
                  {arbCount} arbitrage {arbCount === 1 ? 'opportunity' : 'opportunities'}
                </span>
              )}
              {!loading && <span className="text-sm text-gray-600">{total} total pairs</span>}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Portfolio Panel */}
        <PortfolioPanel portfolio={portfolio} onReset={handleReset} />

        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading market pairs...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 font-medium">Error</p>
            <p className="text-red-600 text-sm mt-1">{error}</p>
            <button
              onClick={loadPairs}
              className="mt-3 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && pairs.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-600 text-lg">No market pairs found</p>
            <p className="text-gray-500 text-sm mt-2">
              {showArbitrageOnly
                ? 'No arbitrage opportunities detected with current odds.'
                : <>Run <code className="bg-gray-100 px-2 py-1 rounded">python find_market_pairs.py</code> to generate pairs</>
              }
            </p>
          </div>
        )}

        {!loading && !error && pairs.length > 0 && (
          <div>
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-700">
                    Market Pairs
                  </h2>
                  <p className="text-sm text-gray-500 mt-1">
                    Showing {pairs.length} of {total} pairs
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  {/* Arbitrage Only Toggle */}
                  <button
                    onClick={() => setShowArbitrageOnly(!showArbitrageOnly)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
                      showArbitrageOnly
                        ? 'bg-green-50 border-green-300 text-green-800'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Arbitrage Only
                    {showArbitrageOnly && (
                      <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>

                  {/* Keyword Filter Dropdown */}
                  <div className="relative">
                    <button
                      onClick={() => setDropdownOpen(!dropdownOpen)}
                      className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                      </svg>
                      Filter: {selectedKeyword === 'all' ? 'All Keywords' : selectedKeyword}
                      <svg className={`w-4 h-4 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {dropdownOpen && (
                      <>
                        <div
                          className="fixed inset-0 z-10"
                          onClick={() => setDropdownOpen(false)}
                        />

                        <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
                          <div className="p-2">
                            <label className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer">
                              <input
                                type="radio"
                                name="keyword-filter"
                                checked={selectedKeyword === 'all'}
                                onChange={() => {
                                  setSelectedKeyword('all');
                                  setDropdownOpen(false);
                                }}
                                className="w-4 h-4 text-blue-600"
                              />
                              <span className="ml-3 text-sm text-gray-700 font-medium">
                                All Keywords
                              </span>
                              <span className="ml-auto text-xs text-gray-500">
                                {keywords.reduce((sum, kw) => sum + kw.pair_count, 0).toLocaleString()}
                              </span>
                            </label>

                            <div className="border-t border-gray-200 my-2" />

                            {keywords.map((kw) => (
                              <label
                                key={kw.keyword}
                                className="flex items-center px-3 py-2 hover:bg-gray-50 rounded cursor-pointer"
                              >
                                <input
                                  type="radio"
                                  name="keyword-filter"
                                  checked={selectedKeyword === kw.keyword}
                                  onChange={() => {
                                    setSelectedKeyword(kw.keyword);
                                    setDropdownOpen(false);
                                  }}
                                  className="w-4 h-4 text-blue-600"
                                />
                                <span className="ml-3 text-sm text-gray-700">
                                  {kw.keyword}
                                </span>
                                <span className="ml-auto text-xs text-gray-500">
                                  {kw.pair_count.toLocaleString()}
                                </span>
                              </label>
                            ))}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="space-y-4">
              {pairs.map((pair) => (
                <PairCard
                  key={pair.pair_id}
                  pair={pair}
                  onApprove={handleApprove}
                  isTrading={tradingPairId === pair.pair_id}
                />
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            PolymarketAgent UI • Market Pairs Analysis Tool
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
