import React from 'react';
import { mockDatasets, Colors } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid } from '@/components/dashboard';
import { RadarChartCard, AreaChartCard } from '@/components/charts';

export function Trends() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Trend & Risk Analytics
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Multi-dimensional asset allocation radar and investment growth benchmarking.
        </p>
      </div>

      <DashboardGrid>
        {/* Radar Allocation Dimension */}
        <div className="lg:col-span-6 md:col-span-2 col-span-1">
          <RadarChartCard
            title="Portfolio Asset Distribution Radar"
            subtitle="Evaluating asset weights across 5 core classes"
            data={mockDatasets.assetAllocation}
            dataKey="A"
            subjectKey="subject"
            color={Colors.primary}
            height={280}
          />
        </div>

        {/* Investment Growth vs Benchmark */}
        <div className="lg:col-span-6 md:col-span-2 col-span-1">
          <AreaChartCard
            title="Portfolio vs Benchmark Index"
            subtitle="Comparing returns against market benchmark"
            data={mockDatasets.investmentGrowth}
            xAxisKey="period"
            dataKeys={[
              { key: 'portfolio', color: Colors.success, name: 'DhanSarthi Portfolio' },
              { key: 'benchmark', color: Colors.muted, name: 'Nifty Benchmark' },
            ]}
            height={280}
          />
        </div>
      </DashboardGrid>
    </motion.div>
  );
}

export default Trends;
