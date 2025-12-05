import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';

interface ProgressPanelProps {
  status: string;
  stage: string;
  progress: number;
  activity: string;
  logs: string[];
}

export function ProgressPanel({ status, stage, progress, activity, logs }: ProgressPanelProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{stage}</h2>
          <p className="text-gray-500 mt-1 flex items-center gap-2">
            {status === 'in_progress' && <Loader2 className="w-4 h-4 animate-spin" />}
            {status === 'completed' && <CheckCircle2 className="w-4 h-4 text-green-500" />}
            {status === 'failed' && <XCircle className="w-4 h-4 text-red-500" />}
            <span className="capitalize">{status.replace('_', ' ')}</span>
          </p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-blue-600">{(progress * 100).toFixed(0)}%</div>
          <div className="text-sm text-gray-500">Overall Progress</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-100 rounded-full h-4 overflow-hidden">
        <div 
          className={cn(
            "h-full transition-all duration-500 ease-out",
            status === 'failed' ? "bg-red-500" : "bg-blue-600"
          )}
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      {/* Current Activity */}
      <div className="bg-blue-50 border border-blue-100 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-1">Current Activity</h4>
        <p className="text-blue-700 font-mono text-sm">{activity}</p>
      </div>

      {/* Live Logs */}
      <div className="border rounded-md overflow-hidden">
        <div className="bg-gray-50 px-4 py-2 border-b text-xs font-medium text-gray-500 uppercase">
          Live Logs
        </div>
        <div className="bg-gray-900 text-gray-300 p-4 h-64 overflow-y-auto font-mono text-xs space-y-1">
          {logs.map((log, i) => (
            <div key={i} className="break-all hover:bg-gray-800 px-1 rounded">
              <span className="text-gray-500 mr-2">[{new Date().toLocaleTimeString()}]</span>
              {log}
            </div>
          ))}
          <div id="log-end" />
        </div>
      </div>
    </div>
  );
}
