import React from 'react';
import { motion } from 'framer-motion';
import DashboardGrid from './DashboardGrid';

/**
 * WidgetSkeleton Component
 * Placeholder skeleton for individual widgets.
 */
export function WidgetSkeleton({ className, ...props }) {
  return (
    <div
      className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex flex-col justify-between min-h-[220px] animate-pulse"
      {...props}
    >
      {/* Header Row */}
      <div className="flex items-center justify-between border-b border-border/50 pb-3">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-xl bg-muted shrink-0" />
          <div className="h-4 w-28 rounded bg-muted" />
        </div>
        <div className="h-6 w-12 rounded-lg bg-muted" />
      </div>

      {/* Body Area */}
      <div className="flex-1 flex flex-col justify-between py-4 gap-3">
        <div className="flex flex-col gap-2">
          <div className="h-3 w-[90%] rounded bg-muted" />
          <div className="h-3 w-[70%] rounded bg-muted" />
        </div>
        
        {/* Mock wireframe strip */}
        <div className="h-10 w-full rounded-xl bg-muted/65 border border-dashed border-border" />
      </div>

      {/* Footer Row */}
      <div className="flex justify-between items-center border-t border-border/50 pt-3">
        <div className="h-4.5 w-16 rounded-full bg-muted" />
        <div className="h-3 w-20 rounded bg-muted" />
      </div>
    </div>
  );
}

/**
 * SummaryStripSkeleton Component
 * Skeletons for the metric summary strip.
 */
export function SummaryStripSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
      {[1, 2, 3, 4].map((item) => (
        <div
          key={item}
          className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 animate-pulse"
        >
          <div className="flex flex-col gap-2 flex-1">
            <div className="h-2.5 w-16 rounded bg-muted" />
            <div className="h-6 w-24 rounded bg-muted" />
            <div className="h-2 w-20 rounded bg-muted" />
          </div>
          <div className="h-10 w-10 rounded-2xl bg-muted shrink-0" />
        </div>
      ))}
    </div>
  );
}

/**
 * DashboardLoader Component
 * Renders a full skeleton dashboard layout during profile switches or initial load.
 */
export function DashboardLoader() {
  return (
    <div className="flex flex-col gap-8 w-full max-w-[1400px] mx-auto select-none">
      {/* Banner Skeleton */}
      <div className="w-full h-44 rounded-3xl bg-muted border border-border/50 animate-pulse relative overflow-hidden flex flex-col justify-center p-8 gap-4">
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-2xl bg-card/45" />
          <div className="flex flex-col gap-2">
            <div className="h-3 w-24 rounded bg-card/30" />
            <div className="h-6 w-64 rounded bg-card/40" />
          </div>
        </div>
        <div className="h-3.5 w-[85%] rounded bg-card/25" />
      </div>

      {/* Summary Strip Skeleton */}
      <SummaryStripSkeleton />

      {/* Widgets Grid Skeleton */}
      <div className="flex flex-col gap-4">
        {/* Section title placeholder */}
        <div className="h-6 w-40 rounded bg-muted animate-pulse" />
        
        <DashboardGrid>
          <WidgetSkeleton className="lg:col-span-6" />
          <WidgetSkeleton className="lg:col-span-6" />
          <WidgetSkeleton className="lg:col-span-8" />
          <WidgetSkeleton className="lg:col-span-4" />
          <WidgetSkeleton className="lg:col-span-12" />
        </DashboardGrid>
      </div>
    </div>
  );
}

export default DashboardLoader;
