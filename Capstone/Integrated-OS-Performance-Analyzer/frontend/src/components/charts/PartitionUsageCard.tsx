import React from 'react';
import { HardDrive } from 'lucide-react';
import { DiskPartitionInfo } from '../../types/metrics';
import { formatBytes, getStatusColor } from '../../utils/formatters';

interface PartitionUsageCardProps {
  partitionInfo: DiskPartitionInfo;
}

export const PartitionUsageCard: React.FC<PartitionUsageCardProps> = ({ partitionInfo }) => {
  const { partition, usage } = partitionInfo;
  const percent = usage?.percent ?? 0;
  const status = getStatusColor(percent, 80, 90);

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md transition-all hover:border-gray-700 shadow-md">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-indigo-500/10 p-2.5 text-indigo-400 border border-indigo-500/20">
            <HardDrive className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-semibold text-sm text-white tracking-wide">
              {partition.mountpoint}
            </h4>
            <p className="text-xs text-gray-400 font-mono">
              {partition.device} <span className="text-gray-600">•</span> {partition.filesystem}
            </p>
            {partition.mountpoints && partition.mountpoints.length > 1 && (
              <div className="mt-1 flex flex-wrap items-center gap-1 text-[10px]">
                <span className="text-gray-500 font-sans">Also at:</span>
                {partition.mountpoints
                  .filter((m) => m !== partition.mountpoint)
                  .map((m) => (
                    <span key={m} className="font-mono text-cyan-400 bg-gray-800/80 px-1.5 py-0.5 rounded border border-gray-700/60">
                      {m}
                    </span>
                  ))}
              </div>
            )}
          </div>
        </div>
        <span className={`font-mono text-sm font-bold ${status.text}`}>
          {usage ? `${percent.toFixed(1)}%` : 'Inaccessible'}
        </span>
      </div>

      <div className="mt-4">
        <div className="h-2 w-full overflow-hidden rounded-full bg-gray-800">
          <div
            className={`h-full rounded-full transition-all duration-500 ${status.bar}`}
            style={{ width: `${Math.min(Math.max(percent, 0), 100)}%` }}
          />
        </div>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
        <div className="rounded-lg bg-gray-800/40 p-2 border border-gray-800">
          <div className="text-[10px] uppercase text-gray-500 font-semibold">Total</div>
          <div className="font-mono font-medium text-gray-200 mt-0.5">
            {formatBytes(usage?.total)}
          </div>
        </div>
        <div className="rounded-lg bg-gray-800/40 p-2 border border-gray-800">
          <div className="text-[10px] uppercase text-gray-500 font-semibold">Used</div>
          <div className="font-mono font-medium text-gray-200 mt-0.5">
            {formatBytes(usage?.used)}
          </div>
        </div>
        <div className="rounded-lg bg-gray-800/40 p-2 border border-gray-800">
          <div className="text-[10px] uppercase text-gray-500 font-semibold">Free</div>
          <div className="font-mono font-medium text-gray-200 mt-0.5">
            {formatBytes(usage?.free)}
          </div>
        </div>
      </div>
    </div>
  );
};
