import React from 'react';

const MarketBadge = ({ market, marketNumber }) => {
  const formatOdds = (odds) => {
    if (odds === null || odds === undefined) return 'N/A';
    return `${(odds * 100).toFixed(1)}%`;
  };

  return (
    <div className="mb-6">
      <div className="text-sm text-gray-500 mb-1">Market {marketNumber}</div>
      <h3 className="font-semibold text-lg mb-3 text-gray-800 leading-tight">
        {market.title}
      </h3>
      <div className="flex gap-2">
        <span className="bg-green-100 text-green-800 px-4 py-2 rounded-md font-medium text-sm">
          Yes: {formatOdds(market.yes_odds)}
        </span>
        <span className="bg-red-100 text-red-800 px-4 py-2 rounded-md font-medium text-sm">
          No: {formatOdds(market.no_odds)}
        </span>
      </div>
      {market.url && (
        <a
          href={market.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 text-sm mt-2 inline-block"
        >
          View on Polymarket →
        </a>
      )}
    </div>
  );
};

export default MarketBadge;
