import React from 'react';
import { AlertCircle } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ElementType;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Available',
  description = 'Telemetry metrics are currently not reported for this component.',
  icon: Icon = AlertCircle,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-gray-800 rounded-xl bg-gray-900/30">
      <div className="rounded-full bg-gray-800/80 p-3 mb-4 text-gray-400">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-sm font-semibold text-gray-200">{title}</h3>
      <p className="mt-1 text-xs text-gray-400 max-w-sm">{description}</p>
    </div>
  );
};
