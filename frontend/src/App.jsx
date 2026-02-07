import { useState, useEffect } from 'react';
import { getPairs } from './services/api';
import PairCard from './components/PairCard';
import axios from 'axios';

function App() {
  const [pairs, setPairs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);
  const [selectedKeyword, setSelectedKeyword] = useState('all');
  const [keywords, setKeywords] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    loadKeywords();
  }, []);

  useEffect(() => {
    loadPairs();
  }, [selectedKeyword]);

  const loadKeywords = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/keywords');
      setKeywords(response.data.keywords);
    } catch (err) {
      console.error('Error loading keywords:', err);
    }
  };

  const loadPairs = async () => {
    try {
      setLoading(true);
      const keyword = selectedKeyword === 'all' ? null : selectedKeyword;
      const response = await axios.get('http://localhost:8000/api/pairs', {
        params: {
          limit: 3000,
          offset: 0,
          keyword: keyword
        }
      });
      setPairs(response.data.pairs);
      setTotal(response.data.total);
      setError(null);
    } catch (err) {
      console.error('Error loading pairs:', err);
      setError(err.response?.data?.detail || 'Failed to load market pairs. Make sure the API server is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = (pairId) => {
    console.log('Approved pair:', pairId);
    // Placeholder - will implement actual approval logic later
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
            <div className="text-sm text-gray-600">
              {!loading && <span>{total} total pairs</span>}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
              Run <code className="bg-gray-100 px-2 py-1 rounded">python find_market_pairs.py</code> to generate pairs
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
                      {/* Backdrop to close dropdown */}
                      <div
                        className="fixed inset-0 z-10"
                        onClick={() => setDropdownOpen(false)}
                      />

                      {/* Dropdown Menu */}
                      <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
                        <div className="p-2">
                          {/* All option */}
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

                          {/* Keyword options */}
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
            <div className="space-y-4">
              {pairs.map((pair) => (
                <PairCard key={pair.pair_id} pair={pair} onApprove={handleApprove} />
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
