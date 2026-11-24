import React from 'react';
import { GanttSegment } from '../../types/metrics';

interface GanttChartProps {
  segments: GanttSegment[];
  totalTime: number;
}

const PROCESS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  P1: { bg: 'bg-blue-600', border: 'border-blue-400', text: 'text-white' },
  P2: { bg: 'bg-emerald-600', border: 'border-emerald-400', text: 'text-white' },
  P3: { bg: 'bg-amber-600', border: 'border-amber-400', text: 'text-white' },
  P4: { bg: 'bg-purple-600', border: 'border-purple-400', text: 'text-white' },
  P5: { bg: 'bg-rose-600', border: 'border-rose-400', text: 'text-white' },
  P6: { bg: 'bg-cyan-600', border: 'border-cyan-400', text: 'text-white' },
  P7: { bg: 'bg-indigo-600', border: 'border-indigo-400', text: 'text-white' },
  P8: { bg: 'bg-teal-600', border: 'border-teal-400', text: 'text-white' },
};

const IDLE_STYLE = {
  bg: 'bg-neutral-800 bg-[repeating-linear-gradient(45deg,#262626,#262626_10px,#1f1f1f_10px,#1f1f1f_20px)]',
  border: 'border-neutral-600',
  text: 'text-neutral-400 italic',
};

function getStyleForProcess(processId: string) {
  if (processId.toUpperCase() === 'IDLE') {
    return IDLE_STYLE;
  }
  if (PROCESS_COLORS[processId]) {
    return PROCESS_COLORS[processId];
  }
  // Deterministic fallback based on char codes
  const keys = Object.keys(PROCESS_COLORS);
  let hash = 0;
  for (let i = 0; i < processId.length; i++) {
    hash += processId.charCodeAt(i);
  }
  return PROCESS_COLORS[keys[hash % keys.length]];
}

export const GanttChart: React.FC<GanttChartProps> = ({ segments, totalTime }) => {
  if (!segments || segments.length === 0 || totalTime <= 0) {
    return (
      <div className="p-8 text-center text-neutral-400 bg-neutral-900 border border-neutral-800 rounded-lg">
        No execution timeline data available.
      </div>
    );
  }

  // Collect unique processes for legend
  const uniqueProcesses = Array.from(new Set(segments.map((s) => s.process_id)));

  return (
    <div className="w-full space-y-4">
      {/* Timeline Bar */}
      <div className="relative w-full">
        <div className="flex h-14 w-full rounded-lg overflow-hidden border border-neutral-700 shadow-inner bg-neutral-950">
          {segments.map((segment, idx) => {
            const widthPct = (segment.duration / totalTime) * 100;
            const style = getStyleForProcess(segment.process_id);
            const isIdle = segment.process_id.toUpperCase() === 'IDLE';

            return (
              <div
                key={`${segment.process_id}-${segment.start_time}-${idx}`}
                style={{ width: `${widthPct}%` }}
                className={`relative flex items-center justify-center border-r last:border-r-0 ${style.border} ${style.bg} ${style.text} transition-all duration-150 hover:brightness-110 group select-none`}
                title={`${segment.process_id}: [${segment.start_time} -> ${segment.end_time}] (Duration: ${segment.duration})`}
              >
                <span className="font-semibold text-xs sm:text-sm truncate px-1">
                  {isIdle ? 'IDLE' : segment.process_id}
                </span>

                {/* Hover Tooltip */}
                <div className="absolute bottom-full mb-2 hidden group-hover:flex flex-col items-center z-30 pointer-events-none">
                  <div className="bg-neutral-900 text-neutral-100 text-xs rounded py-1 px-2.5 border border-neutral-700 shadow-xl whitespace-nowrap">
                    <p className="font-bold text-sky-400">{segment.process_id}</p>
                    <p>Start: {segment.start_time}s | End: {segment.end_time}s</p>
                    <p>Duration: {segment.duration}s</p>
                  </div>
                  <div className="w-2 h-2 bg-neutral-900 border-r border-b border-neutral-700 transform rotate-45 -mt-1" />
                </div>
              </div>
            );
          })}
        </div>

        {/* Time Axis Markers */}
        <div className="relative w-full h-6 mt-1">
          {segments.map((segment, idx) => {
            const leftPct = (segment.start_time / totalTime) * 100;
            return (
              <span
                key={`tick-${idx}`}
                style={{ left: `${leftPct}%` }}
                className="absolute text-[11px] font-mono text-neutral-400 -translate-x-1/2"
              >
                {segment.start_time}
              </span>
            );
          })}
          {/* End tick */}
          <span
            style={{ left: '100%' }}
            className="absolute text-[11px] font-mono text-neutral-400 -translate-x-full"
          >
            {totalTime}
          </span>
        </div>
      </div>

      {/* Process Legend */}
      <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-neutral-800 text-xs">
        <span className="text-neutral-400 font-medium">Legend:</span>
        {uniqueProcesses.map((pId) => {
          const style = getStyleForProcess(pId);
          return (
            <div key={`legend-${pId}`} className="flex items-center gap-1.5">
              <span className={`w-3.5 h-3.5 rounded-sm border ${style.border} ${style.bg}`} />
              <span className="text-neutral-300 font-mono">{pId}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
