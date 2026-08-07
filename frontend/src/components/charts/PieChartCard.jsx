import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import * as LucideIcons from 'lucide-react';
import { Colors } from '@/config';

/**
 * PieChartCard Component
 * Reusable Pie/Donut chart wrapper using Recharts.
 */
export function PieChartCard({
  title = 'Distribution Breakdown',
  subtitle,
  data = [],
  dataKey = 'value',
  nameKey = 'name',
  innerRadius = 0,
  outerRadius = 80,
  height = 260,
  className = '',
}) {
  const defaultColors = [Colors.primary, Colors.accent, Colors.success, Colors.warning, Colors.info, Colors.danger];

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
        <LucideIcons.PieChart className="h-4 w-4 text-primary" />
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <PieChart>
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
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={innerRadius}
              outerRadius={outerRadius}
              paddingAngle={3}
              dataKey={dataKey}
              nameKey={nameKey}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color || defaultColors[index % defaultColors.length]}
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default PieChartCard;
