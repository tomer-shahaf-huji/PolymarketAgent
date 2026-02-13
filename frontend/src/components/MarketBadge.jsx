import React from 'react';

const MarketBadge = ({ market, marketRole, action }) => {
  const formatOdds = (odds) => {
    if (odds === null || odds === undefined) return 'N/A';
    return `${(odds * 100).toFixed(1)}%`;
  };

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm text-gray-500">{marketRole}</span>
        {action && (
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
            action === "BUY YES"
              ? 'bg-green-600 text-white'
              : 'bg-red-600 text-white'
          }`}>
            {action}
          </span>
        )}
      </div>
      <h3 className="font-semibold text-lg mb-3 text-gray-800 leading-tight">
        {market.title}
      </h3>
      <div className="flex gap-2">
        <span className={`px-4 py-2 rounded-md font-medium text-sm ${
          action === "BUY YES"
            ? 'bg-green-200 text-green-900 ring-2 ring-green-500'
            : 'bg-green-100 text-green-800'
        }`}>
          Yes: {formatOdds(market.yes_odds)}
        </span>
        <span className={`px-4 py-2 rounded-md font-medium text-sm ${
          action === "BUY NO"
            ? 'bg-red-200 text-red-900 ring-2 ring-red-500'
            : 'bg-red-100 text-red-800'
        }`}>
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
