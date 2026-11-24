import React from 'react';
import { getStatusColor } from '../../utils/formatters';

interface CoreUsageGridProps {
  perCoreUsage: (number | null)[] | null | undefined;
}

export const CoreUsageGrid: React.FC<CoreUsageGridProps> = ({ perCoreUsage }) => {
  if (!perCoreUsage || perCoreUsage.length === 0) {
    return (
      <div className="text-xs text-gray-500 italic p-4 text-center">
        Per-core utilization data unavailable
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
      {perCoreUsage.map((coreVal, idx) => {
        const status = getStatusColor(coreVal);
        return (
          <div
            key={idx}
            className="flex flex-col rounded-lg border border-gray-800 bg-gray-900/50 p-2.5 transition-all hover:border-gray-700"
          >
            <div className="flex justify-between items-center text-[11px] mb-1.5 font-medium">
              <span className="text-gray-400">Core {idx}</span>
              <span className={`font-mono ${status.text}`}>
                {coreVal !== null && coreVal !== undefined ? `${coreVal.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-800">
              <div
                className={`h-full rounded-full transition-all duration-300 ${status.bar}`}
                style={{ width: `${Math.min(Math.max(coreVal ?? 0, 0), 100)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
