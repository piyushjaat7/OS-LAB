import React from 'react';
import { getStatusColor } from '../../utils/formatters';

interface ProgressBarProps {
  value: number | null | undefined;
  max?: number;
  label?: string;
  showPercent?: boolean;
  warningThreshold?: number;
  criticalThreshold?: number;
  heightClass?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  showPercent = true,
  warningThreshold = 75,
  criticalThreshold = 90,
  heightClass = 'h-2',
}) => {
  const percent = value !== null && value !== undefined && max > 0 ? (value / max) * 100 : 0;
  const status = getStatusColor(percent, warningThreshold, criticalThreshold);

  return (
    <div className="w-full">
      {(label || showPercent) && (
        <div className="flex justify-between text-xs mb-1.5 font-medium">
          {label && <span className="text-gray-400">{label}</span>}
          {showPercent && (
            <span className={`font-mono ${status.text}`}>
              {value !== null && value !== undefined ? `${percent.toFixed(1)}%` : 'N/A'}
            </span>
          )}
        </div>
      )}
      <div className={`w-full overflow-hidden rounded-full bg-gray-800 ${heightClass}`}>
        <div
          className={`h-full transition-all duration-500 rounded-full ${status.bar}`}
          style={{ width: `${Math.min(Math.max(percent, 0), 100)}%` }}
        />
      </div>
    </div>
  );
};
