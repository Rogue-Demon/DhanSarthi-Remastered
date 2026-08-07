import React from 'react';
import { ResponsiveContainer, LineChart, Line } from 'recharts';
import { Colors } from '@/config';

/**
 * MiniTrendChart Component
 * Sparkline micro trend chart for KPI metric summary cards.
 */
export function MiniTrendChart({
  data = [10, 15, 12, 18, 24, 20, 28],
  color = Colors.success,
  height = 36,
  width = 80,
}) {
  const chartData = data.map((v, i) => ({ val: v, i }));

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer>
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="val"
            stroke={color}
            strokeWidth={2.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default MiniTrendChart;
