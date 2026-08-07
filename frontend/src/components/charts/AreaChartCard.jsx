import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import * as LucideIcons from 'lucide-react';
import { Colors } from '@/config';

/**
 * AreaChartCard Component
 * Reusable area chart wrapper with subtle opacity gradients.
 */
export function AreaChartCard({
  title = 'Area Growth Trend',
  subtitle,
  data = [],
  dataKeys = [{ key: 'value', color: Colors.primary, name: 'Value' }],
  xAxisKey = 'month',
  height = 260,
  className = '',
}) {
  return (
    <div className={`clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left select-none ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-0.5">
          <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
            {title}
          </h4>
          {subtitle && (
            <span className="text-[10px] font-bold text-text-muted">{subtitle}</span>
          )}
        </div>
        <LucideIcons.Activity className="h-4 w-4 text-primary" />
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              {dataKeys.map((dk) => (
                <linearGradient key={`grad-${dk.key}`} id={`grad-${dk.key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={dk.color || Colors.primary} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={dk.color || Colors.primary} stopOpacity={0.0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.15)" />
            <XAxis
              dataKey={xAxisKey}
              tick={{ fontSize: 10, fill: '#94A3B8', fontWeight: 600 }}
              axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#94A3B8', fontWeight: 600 }}
              axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1E1B4B',
                borderColor: '#7C3AED',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '11px',
                fontWeight: 700,
                boxShadow: '0 10px 25px -5px rgba(0,0,0,0.3)',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '11px', fontWeight: 700, paddingTop: '10px' }} />
            {dataKeys.map((dk) => (
              <Area
                key={dk.key}
                type="monotone"
                dataKey={dk.key}
                name={dk.name || dk.key}
                stroke={dk.color || Colors.primary}
                fillOpacity={1}
                fill={`url(#grad-${dk.key})`}
                strokeWidth={2.5}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default AreaChartCard;
