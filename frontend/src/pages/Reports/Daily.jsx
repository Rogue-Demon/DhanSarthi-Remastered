import React from 'react';
import { mockDatasets, Colors } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid } from '@/components/dashboard';
import { BarChartCard } from '@/components/charts';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function Daily() {
  const shouldReduceMotion = useReducedMotion();

  const transactions = [
    { desc: 'Grocery Store Purchase', cat: 'Groceries', amount: '-₹1,200', time: '02:30 PM', status: 'Debited' },
    { desc: 'Tutoring Payment Received', cat: 'Income', amount: '+₹15,000', time: '11:15 AM', status: 'Credited' },
    { desc: 'Coffee Shop Bill', cat: 'Food', amount: '-₹250', time: '09:45 AM', status: 'Debited' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Daily Transactions & Spending
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Analyze day-to-day inbound income credits and outbound spending debits.
        </p>
      </div>

      <DashboardGrid>
        {/* Daily Spending Bar Chart */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          <BarChartCard
            title="7-Day Expenditure Pattern"
            subtitle="Daily debits vs credits for current week"
            data={mockDatasets.dailySpending}
            xAxisKey="day"
            dataKeys={[
              { key: 'expense', color: Colors.danger, name: 'Daily Expense' },
              { key: 'income', color: Colors.success, name: 'Daily Income' },
            ]}
            height={280}
          />
        </div>

        {/* Daily Summary Card */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1 flex flex-col gap-4">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left h-full">
            <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
              Today's Tally
            </h4>

            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center text-xs font-semibold p-3 rounded-xl bg-muted/30 border border-border/60">
                <span className="text-text-secondary">Today Total Income</span>
                <span className="font-extrabold text-success">+₹15,000</span>
              </div>
              <div className="flex justify-between items-center text-xs font-semibold p-3 rounded-xl bg-muted/30 border border-border/60">
                <span className="text-text-secondary">Today Total Expense</span>
                <span className="font-extrabold text-danger">-₹1,700</span>
              </div>
              <div className="flex justify-between items-center text-xs font-semibold p-3 rounded-xl bg-primary/10 border border-primary/20">
                <span className="text-primary font-black">Today Net Surplus</span>
                <span className="font-extrabold text-primary">+₹13,300</span>
              </div>
            </div>
          </div>
        </div>

        {/* Daily Transactions Table */}
        <div className="lg:col-span-12 col-span-1">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left">
            <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
              Recent Today Transactions Log
            </h4>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-border/60 text-text-muted uppercase text-[9px] font-black tracking-wider">
                    <th className="pb-3 px-2">Description</th>
                    <th className="pb-3 px-2">Category</th>
                    <th className="pb-3 px-2">Time</th>
                    <th className="pb-3 px-2 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 font-semibold">
                  {transactions.map((t, idx) => (
                    <tr key={idx} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-2 text-text-primary font-bold">{t.desc}</td>
                      <td className="py-3 px-2 text-text-muted">{t.cat}</td>
                      <td className="py-3 px-2 text-text-muted">{t.time}</td>
                      <td className={`py-3 px-2 text-right font-black ${t.amount.startsWith('+') ? 'text-success' : 'text-danger'}`}>
                        {t.amount}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </DashboardGrid>
    </motion.div>
  );
}

export default Daily;
