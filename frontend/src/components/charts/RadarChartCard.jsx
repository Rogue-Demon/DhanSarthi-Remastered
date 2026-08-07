import React from 'react';
import {
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
} from 'recharts';
import * as LucideIcons from 'lucide-react';
import { Colors } from '@/config';

/**
 * RadarChartCard Component
 * Reusable Radar chart wrapper for asset allocations and risk dimensions.
 */
export function RadarChartCard({
  title = 'Radar Dimension Breakdown',
  subtitle,
  data = [],
  dataKey = 'A',
  subjectKey = 'subject',
  color = Colors.primary,
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
        <LucideIcons.Compass className="h-4 w-4 text-primary" />
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <RadarChart data={data}>
            <PolarGrid stroke="rgba(148, 163, 184, 0.2)" />
            <PolarAngleAxis
              dataKey={subjectKey}
              tick={{ fontSize: 10, fill: '#94A3B8', fontWeight: 700 }}
            />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1E1B4B',
                borderColor: '#7C3AED',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '11px',
                fontWeight: 700,
              }}
            />
            <Radar
              name="Allocation"
              dataKey={dataKey}
              stroke={color}
              fill={color}
              fillOpacity={0.4}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default RadarChartCard;
