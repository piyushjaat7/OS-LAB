import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface SeriesConfig {
  key: string;
  name: string;
  color: string;
  unit?: string;
}

interface LiveAreaChartProps {
  data: any[];
  series: SeriesConfig[];
  yDomain?: [number | 'auto', number | 'auto'];
  height?: number;
  valueFormatter?: (value: number) => string;
}

export const LiveAreaChart: React.FC<LiveAreaChartProps> = ({
  data,
  series,
  yDomain = [0, 100],
  height = 240,
  valueFormatter = (val) => `${val}%`,
}) => {
  return (
    <div style={{ width: '100%', height }} className="overflow-hidden">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            {series.map((s) => (
              <linearGradient key={s.key} id={`gradient-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={s.color} stopOpacity={0.35} />
                <stop offset="95%" stopColor={s.color} stopOpacity={0.0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
          <XAxis
            dataKey="timeStr"
            stroke="#6B7280"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={yDomain}
            stroke="#6B7280"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={valueFormatter}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111827',
              borderColor: '#374151',
              borderRadius: '0.75rem',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
              fontSize: '12px',
            }}
            labelStyle={{ color: '#9CA3AF', marginBottom: '4px' }}
            formatter={(val: any, name: any) => {
              if (val === null || val === undefined) return ['N/A', name];
              return [typeof val === 'number' ? valueFormatter(val) : val, name];
            }}
          />
          {series.map((s) => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={2}
              fillOpacity={1}
              fill={`url(#gradient-${s.key})`}
              isAnimationActive={false}
              connectNulls={true}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
