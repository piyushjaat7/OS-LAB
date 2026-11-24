import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading telemetry data...',
  size = 'md',
}) => {
  const sizeMap = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }[size];

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <Loader2 className={`${sizeMap} animate-spin text-cyan-400 mb-3`} />
      <p className="text-sm text-gray-400 font-medium">{message}</p>
    </div>
  );
};
