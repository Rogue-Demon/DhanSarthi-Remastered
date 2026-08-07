import React from 'react';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function BusinessInventoryWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock goals list
  const goals = [
    { title: 'Reduce OPEX overheads', current: 15, target: 20, progress: 75, due: 'Dec 2026', color: '#10B981' },
    { title: 'Sales revenue expansion', current: 55.8, target: 60, progress: 92, due: 'Mar 2027', color: '#7C3AED' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Corporate inventory assets and expansion goals')}
      onRefresh={() => console.log('Inventory refresh')}
    />
  );

  return (
    <WidgetContainer
      title={widget.title}
      icon={widget.icon}
      color={widget.color}
      sizeClass={sizeClass}
      toolbar={toolbar}
    >
      <div className="flex flex-col lg:flex-row gap-6 w-full select-none text-left font-sans">
        
        {/* COLUMN 1: INVENTORY & STOCK VALUATION (50% width) */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Warehouse Stock valuation
            </span>
            <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1.5 bg-warning/10 border-warning/20 text-warning rounded">
              Restock Alert
            </Badge>
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs font-semibold text-text-secondary bg-muted/30 p-2.5 rounded-lg border border-border/50">
              <span>Total Inventory Asset Value</span>
              <span className="font-extrabold text-text-primary">₹2,40,000</span>
            </div>
            <div className="flex justify-between items-center text-xs font-semibold text-text-secondary bg-muted/30 p-2.5 rounded-lg border border-border/50">
              <span>Low Stock Items Alert</span>
              <span className="font-extrabold text-danger">3 categories</span>
            </div>
          </div>
        </div>

        {/* COLUMN 2: CORPORATE GOALS & TARGETS (50% width) */}
        <div className="flex-1 border-t lg:border-t-0 lg:border-l border-border/60 pt-4 lg:pt-0 lg:pl-6 flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Corporate Goals & Targets
            </span>
            <Button
              variant="ghost"
              size="xs"
              className="p-0 text-[10px] font-bold text-primary hover:bg-transparent uppercase tracking-wider"
              onClick={() => alert('Goal creation wizard')}
              iconLeft={<LucideIcons.Plus className="h-3 w-3" />}
            >
              Add Target
            </Button>
          </div>

          {/* Goal progress cards list */}
          <div className="flex flex-col gap-3">
            {goals.map((goal, idx) => (
              <div key={idx} className="flex flex-col gap-1 text-xs">
                <div className="flex justify-between font-bold text-text-primary">
                  <span className="truncate max-w-[120px]">{goal.title}</span>
                  <span className="text-[10px] font-black text-text-muted">{goal.progress}%</span>
                </div>
                {/* Progress bar */}
                <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden border border-white/60 shadow-inner">
                  <div className="h-full rounded-full" style={{ width: `${goal.progress}%`, backgroundColor: goal.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </WidgetContainer>
  );
}

export default BusinessInventoryWidget;
