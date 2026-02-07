import React from 'react';
import MarketBadge from './MarketBadge';
import ApproveButton from './ApproveButton';

const PairCard = ({ pair, onApprove }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4 hover:shadow-lg transition-shadow duration-200">
      <div className="flex justify-between items-start gap-6">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs text-gray-400 font-mono">{pair.pair_id}</span>
            {pair.keyword && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {pair.keyword}
              </span>
            )}
          </div>
          <MarketBadge market={pair.market1} marketNumber={1} />
          <div className="border-t border-gray-200 my-4"></div>
          <MarketBadge market={pair.market2} marketNumber={2} />
        </div>
        <div className="flex-shrink-0 self-center">
          <ApproveButton pairId={pair.pair_id} onApprove={onApprove} />
        </div>
      </div>
    </div>
  );
};

export default PairCard;
