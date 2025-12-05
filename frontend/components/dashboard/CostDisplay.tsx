import React from 'react';
import { DollarSign, Zap, FileText } from 'lucide-react';

interface CostDisplayProps {
  totalCost: number;
  inputTokens: number;
  outputTokens: number;
}

export function CostDisplay({ totalCost, inputTokens, outputTokens }: CostDisplayProps) {
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="bg-white p-4 rounded-lg shadow border border-gray-100">
        <div className="flex items-center gap-2 text-gray-500 mb-1">
          <DollarSign className="w-4 h-4" />
          <span className="text-xs font-medium uppercase">Total Cost</span>
        </div>
        <div className="text-2xl font-bold text-gray-900">${totalCost.toFixed(4)}</div>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow border border-gray-100">
        <div className="flex items-center gap-2 text-gray-500 mb-1">
          <FileText className="w-4 h-4" />
          <span className="text-xs font-medium uppercase">Input Tokens</span>
        </div>
        <div className="text-2xl font-bold text-gray-900">{inputTokens.toLocaleString()}</div>
      </div>

      <div className="bg-white p-4 rounded-lg shadow border border-gray-100">
        <div className="flex items-center gap-2 text-gray-500 mb-1">
          <Zap className="w-4 h-4" />
          <span className="text-xs font-medium uppercase">Output Tokens</span>
        </div>
        <div className="text-2xl font-bold text-gray-900">{outputTokens.toLocaleString()}</div>
      </div>
    </div>
  );
}
