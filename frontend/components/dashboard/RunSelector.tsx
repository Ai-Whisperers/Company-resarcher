import React from 'react';

interface Run {
  task_id: string;
  company_name: string;
  status: string;
  progress: number;
}

interface RunSelectorProps {
  runs: Run[];
  selectedRunId: string | null;
  onSelectRun: (runId: string) => void;
}

export function RunSelector({ runs, selectedRunId, onSelectRun }: RunSelectorProps) {
  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-sm text-gray-500 uppercase tracking-wider">Active Runs</h3>
      <div className="space-y-1">
        {runs.map((run) => (
          <button
            key={run.task_id}
            onClick={() => onSelectRun(run.task_id)}
            className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
              selectedRunId === run.task_id
                ? "bg-blue-100 text-blue-900 font-medium"
                : "hover:bg-gray-100 text-gray-700"
            }`}
          >
            <div className="flex justify-between items-center">
              <span>{run.company_name}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                run.status === 'completed' ? 'bg-green-100 text-green-800' :
                run.status === 'failed' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {run.status}
              </span>
            </div>
            <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
              <div 
                className="bg-blue-600 h-1.5 rounded-full transition-all duration-500" 
                style={{ width: `${run.progress * 100}%` }}
              />
            </div>
          </button>
        ))}
        {runs.length === 0 && (
          <div className="text-sm text-gray-400 italic px-3 py-2">No active runs</div>
        )}
      </div>
    </div>
  );
}
