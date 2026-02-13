import React from 'react';
import MarketBadge from './MarketBadge';
import ApproveButton from './ApproveButton';

const PairCard = ({ pair, onApprove, isTrading }) => {
  const arb = pair.arbitrage;
  const hasArb = arb?.has_arbitrage;

  return (
    <div className={`rounded-lg shadow-md p-6 mb-4 transition-shadow duration-200 ${
      hasArb
        ? 'bg-green-50 border-2 border-green-400 hover:shadow-xl'
        : 'bg-white hover:shadow-lg'
    }`}>
      <div className="flex justify-between items-start gap-6">
        <div className="flex-1">
          {/* Header row: pair ID, keyword badge, arbitrage badge */}
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <span className="text-xs text-gray-400 font-mono">{pair.pair_id}</span>
            {pair.keyword && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {pair.keyword}
              </span>
            )}
            {hasArb && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-green-600 text-white">
                {arb.profit_pct.toFixed(1)}% Profit
              </span>
            )}
          </div>

          {/* Market 1 (Trigger/Child) */}
          <MarketBadge
            market={pair.market1}
            marketRole="Trigger (Child)"
            action={hasArb ? "BUY NO" : null}
          />

          <div className="border-t border-gray-200 my-4 relative">
            <span className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 bg-gray-100 text-gray-500 text-xs px-2 rounded">
              implies
            </span>
          </div>

          {/* Market 2 (Implied/Parent) */}
          <MarketBadge
            market={pair.market2}
            marketRole="Implied (Parent)"
            action={hasArb ? "BUY YES" : null}
          />

          {/* Reasoning */}
          {pair.reasoning && (
            <div className="mt-4 text-sm text-gray-600 bg-gray-50 rounded p-3">
              <span className="font-medium text-gray-700">Logic: </span>{pair.reasoning}
            </div>
          )}

          {/* Arbitrage Trade Summary */}
          {hasArb && (
            <div className="mt-4 bg-green-100 border border-green-300 rounded-lg p-4">
              <div className="text-sm font-bold text-green-800 mb-2">Arbitrage Trade</div>
              <div className="grid grid-cols-2 gap-2 text-sm text-green-900">
                <div>Buy YES: <span className="font-mono font-medium">{(arb.buy_yes_price * 100).toFixed(1)}¢</span></div>
                <div>Buy NO: <span className="font-mono font-medium">{(arb.buy_no_price * 100).toFixed(1)}¢</span></div>
                <div>Total Cost: <span className="font-mono font-medium">{(arb.cost * 100).toFixed(1)}¢</span></div>
                <div>Guaranteed Payout: <span className="font-mono font-medium">100.0¢</span></div>
              </div>
              <div className="mt-2 text-sm font-bold text-green-900">
                Risk-Free Profit: <span className="font-mono">{(arb.profit * 100).toFixed(1)}¢</span> per $1 ({arb.profit_pct.toFixed(1)}%)
              </div>
            </div>
          )}
        </div>
        <div className="flex-shrink-0 self-center">
          <ApproveButton pairId={pair.pair_id} onApprove={onApprove} disabled={isTrading} />
        </div>
      </div>
    </div>
  );
};

export default PairCard;
