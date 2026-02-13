import React, { useState } from 'react';

const ApproveButton = ({ pairId, onApprove, disabled }) => {
  const [amount, setAmount] = useState(100);

  const handleClick = () => {
    if (onApprove && amount > 0) {
      onApprove(pairId, amount);
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="flex items-center gap-1">
        <span className="text-sm text-gray-500">$</span>
        <input
          type="number"
          min="1"
          max="5000"
          step="10"
          value={amount}
          onChange={(e) => setAmount(Number(e.target.value))}
          className="w-20 px-2 py-1 border border-gray-300 rounded text-sm text-center focus:outline-none focus:ring-2 focus:ring-green-400"
          disabled={disabled}
        />
      </div>
      <button
        onClick={handleClick}
        disabled={disabled || amount <= 0}
        className={`px-6 py-2 rounded-lg font-semibold transition-colors duration-200 shadow-sm hover:shadow-md ${
          disabled
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-green-500 hover:bg-green-600 active:bg-green-700 text-white'
        }`}
      >
        {disabled ? 'Trading...' : 'Approve'}
      </button>
      <span className="text-xs text-gray-400">
        Total: ${(amount * 2).toLocaleString()}
      </span>
    </div>
  );
};

export default ApproveButton;
