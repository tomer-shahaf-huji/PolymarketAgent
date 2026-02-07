import React from 'react';

const ApproveButton = ({ pairId, onApprove }) => {
  const handleClick = () => {
    console.log(`Approve button clicked for ${pairId}`);
    // Placeholder - does nothing for now
    if (onApprove) {
      onApprove(pairId);
    }
  };

  return (
    <button
      onClick={handleClick}
      className="bg-green-500 hover:bg-green-600 active:bg-green-700 text-white px-6 py-2 rounded-lg font-semibold transition-colors duration-200 shadow-sm hover:shadow-md"
    >
      Approve
    </button>
  );
};

export default ApproveButton;
