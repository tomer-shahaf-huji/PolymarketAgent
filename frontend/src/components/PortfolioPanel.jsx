import React, { useState } from 'react';

const PortfolioPanel = ({ portfolio, onReset }) => {
  const [showPositions, setShowPositions] = useState(false);

  if (!portfolio) return null;

  const pnlColor = portfolio.total_pnl >= 0 ? 'text-green-700' : 'text-red-700';
  const pnlBg = portfolio.total_pnl >= 0 ? 'bg-green-50' : 'bg-red-50';

  const formatMoney = (val) =>
    val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  // Group positions by pair_id
  const grouped = {};
  for (const pos of portfolio.positions) {
    if (!grouped[pos.pair_id]) grouped[pos.pair_id] = [];
    grouped[pos.pair_id].push(pos);
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6 border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-800">Simulated Portfolio</h2>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">{portfolio.trade_count} trades</span>
          <button
            onClick={onReset}
            className="text-xs text-red-500 hover:text-red-700 underline"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Cash</div>
          <div className="text-xl font-bold text-gray-900">${formatMoney(portfolio.cash)}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Positions</div>
          <div className="text-xl font-bold text-gray-900">${formatMoney(portfolio.position_value)}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Total Value</div>
          <div className="text-xl font-bold text-gray-900">${formatMoney(portfolio.total_value)}</div>
        </div>
        <div className={`${pnlBg} rounded-lg p-3`}>
          <div className="text-xs text-gray-500 uppercase tracking-wide">P&L</div>
          <div className={`text-xl font-bold ${pnlColor}`}>
            {portfolio.total_pnl >= 0 ? '+' : ''}${formatMoney(portfolio.total_pnl)}
          </div>
        </div>
      </div>

      {/* Positions Toggle */}
      {portfolio.positions.length > 0 && (
        <div className="mt-4">
          <button
            onClick={() => setShowPositions(!showPositions)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
          >
            <svg className={`w-4 h-4 transition-transform ${showPositions ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            {showPositions ? 'Hide' : 'Show'} {portfolio.positions.length} positions
          </button>

          {showPositions && (
            <div className="mt-3 space-y-3">
              {Object.entries(grouped).map(([pairId, positions]) => {
                const pairCost = positions.reduce((s, p) => s + p.cost_basis, 0);
                const pairValue = positions.reduce((s, p) => s + (p.current_value ?? 0), 0);
                const pairPnl = pairValue - pairCost;
                const allHaveValues = positions.every((p) => p.current_value !== null);

                return (
                  <div key={pairId} className="border border-gray-200 rounded-lg overflow-hidden">
                    {/* Pair header */}
                    <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
                      <span className="text-xs font-mono text-gray-500">{pairId}</span>
                      <div className="flex items-center gap-4 text-xs">
                        <span className="text-gray-500">Cost: <span className="font-mono font-medium text-gray-700">${pairCost.toFixed(2)}</span></span>
                        <span className="text-gray-500">Value: <span className="font-mono font-medium text-gray-700">{allHaveValues ? `$${pairValue.toFixed(2)}` : 'N/A'}</span></span>
                        <span className={`font-mono font-bold ${allHaveValues && pairPnl >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                          {allHaveValues ? `${pairPnl >= 0 ? '+' : ''}$${pairPnl.toFixed(2)}` : ''}
                        </span>
                      </div>
                    </div>
                    {/* Position rows */}
                    <table className="w-full text-sm">
                      <tbody>
                        {positions.map((pos) => (
                          <tr key={pos.position_id} className="border-b border-gray-100 last:border-b-0">
                            <td className="py-2 pl-4 pr-4 max-w-xs truncate" title={pos.market_title}>
                              {pos.market_title}
                            </td>
                            <td className="py-2 pr-4">
                              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                pos.outcome === 'YES' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {pos.outcome}
                              </span>
                            </td>
                            <td className="py-2 pr-4 text-right font-mono">{pos.shares.toFixed(2)}</td>
                            <td className="py-2 pr-4 text-right font-mono">{(pos.avg_price * 100).toFixed(1)}c</td>
                            <td className="py-2 pr-4 text-right font-mono">${pos.cost_basis.toFixed(2)}</td>
                            <td className="py-2 pr-4 text-right font-mono">
                              {pos.current_value !== null ? `$${pos.current_value.toFixed(2)}` : 'N/A'}
                            </td>
                            <td className={`py-2 pr-4 text-right font-mono ${
                              pos.pnl !== null && pos.pnl >= 0 ? 'text-green-700' : 'text-red-700'
                            }`}>
                              {pos.pnl !== null ? `${pos.pnl >= 0 ? '+' : ''}$${pos.pnl.toFixed(2)}` : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PortfolioPanel;
