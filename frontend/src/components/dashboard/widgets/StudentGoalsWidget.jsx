import React from 'react';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function StudentGoalsWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock savings goals
  const goals = [
    { title: 'MacBook Pro Fund', icon: 'Laptop', target: 40000, current: 12450, due: 'Dec 2026', color: '#8B5CF6' },
    { title: 'Semester Books', icon: 'BookOpen', target: 2000, current: 1500, due: 'Oct 2026', color: '#10B981' },
  ];

  // Mock Achievements
  const achievements = [
    { title: 'First Budget Created', desc: 'Unlocked bronze saver badge', icon: 'Award', color: '#F59E0B' },
    { title: '7-Day Saving Streak', desc: 'Saved pocket money consecutively', icon: 'Flame', color: '#EF4444' },
    { title: 'Savings Champion', desc: 'Revenues exceeded expenses by 30%', icon: 'Trophy', color: '#10B981' },
  ];

  // Mock AI Insights
  const insights = [
    { text: 'You stayed within food & beverage budgets this week.', icon: 'CheckCircle', color: '#10B981' },
    { text: "Laptop goal is 31% complete. You're on track!", icon: 'Sparkles', color: '#8B5CF6' },
    { text: 'Education costs increased by 5% due to course subscriptions.', icon: 'AlertCircle', color: '#3B82F6' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Goal tracking')}
      onRefresh={() => console.log('Goals refresh')}
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
      <div className="flex flex-col lg:flex-row gap-8 w-full select-none text-left">
        {/* COLUMN 1: GOALS TRACKER CARDS (40% width) */}
        <div className="flex-1 lg:flex-[1.3] flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <LucideIcons.Target className="h-4.5 w-4.5 text-primary" />
              <h4 className="text-sm font-extrabold text-text-primary uppercase tracking-wider">
                Goal Trackers
              </h4>
            </div>
            <Button
              variant="ghost"
              size="xs"
              className="p-0 text-xs font-bold text-primary hover:bg-transparent"
              onClick={() => alert('Add Goal form placeholder')}
              iconLeft={<LucideIcons.Plus className="h-3.5 w-3.5" />}
            >
              Add Goal
            </Button>
          </div>

          <div className="flex flex-col gap-4">
            {goals.map((goal, idx) => {
              const GoalIcon = LucideIcons[goal.icon] || LucideIcons.Compass;
              const progressPct = Math.round((goal.current / goal.target) * 100);
              const remaining = goal.target - goal.current;

              return (
                <div
                  key={goal.title}
                  className="clay-surface bg-card border border-white/60 dark:border-white/5 p-4 flex gap-4 shadow-card hover:border-primary/20 transition-all duration-200"
                >
                  {/* Custom circular progress ring representation using simple SVG */}
                  <div className="relative h-14 w-14 flex items-center justify-center shrink-0">
                    <svg className="h-full w-full transform -rotate-90" viewBox="0 0 36 36">
                      <path
                        className="text-muted"
                        strokeWidth="3.5"
                        stroke="currentColor"
                        fill="transparent"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <path
                        className="transition-all duration-500"
                        strokeWidth="3.5"
                        strokeDasharray={`${progressPct}, 100`}
                        strokeLinecap="round"
                        stroke={goal.color}
                        fill="transparent"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center text-white shrink-0 p-3 rounded-full">
                      <div
                        className="h-7 w-7 rounded-full flex items-center justify-center text-white"
                        style={{ background: goal.color }}
                      >
                        <GoalIcon className="h-3.5 w-3.5" />
                      </div>
                    </div>
                  </div>

                  {/* Text metrics */}
                  <div className="flex-1 flex flex-col gap-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-black text-text-primary leading-none">
                        {goal.title}
                      </span>
                      <span className="text-[10px] font-black text-text-muted">
                        Est: {goal.due}
                      </span>
                    </div>
                    
                    {/* Progress values */}
                    <div className="flex justify-between items-center text-[10px] font-semibold text-text-secondary mt-1">
                      <span>₹{goal.current.toLocaleString()} / ₹{goal.target.toLocaleString()}</span>
                      <span className="font-bold text-text-primary">{progressPct}%</span>
                    </div>

                    {/* Tiny progress bar */}
                    <div className="w-full bg-muted h-1 rounded-full overflow-hidden mt-1">
                      <div className="h-full rounded-full" style={{ width: `${progressPct}%`, backgroundColor: goal.color }} />
                    </div>

                    <div className="flex justify-between items-center text-[8px] font-bold text-text-muted mt-1 uppercase tracking-wider">
                      <span>Remaining: ₹{remaining.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* COLUMN 2: ACHIEVEMENTS LIST (30% width) */}
        <div className="flex-1 flex flex-col gap-4 border-t lg:border-t-0 lg:border-x border-border/60 pt-4 lg:pt-0 lg:px-6">
          <div className="flex items-center gap-2">
            <LucideIcons.Award className="h-4.5 w-4.5 text-primary" />
            <h4 className="text-sm font-extrabold text-text-primary uppercase tracking-wider">
              Achievements
            </h4>
          </div>

          <div className="flex flex-col gap-3">
            {achievements.map((ach, idx) => {
              const AchIcon = LucideIcons[ach.icon] || LucideIcons.Award;
              return (
                <motion.div
                  key={ach.title}
                  initial={{ opacity: 0, x: shouldReduceMotion ? 0 : 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex items-center gap-3 relative group"
                >
                  <div
                    className="h-9 w-9 rounded-xl flex items-center justify-center text-white shrink-0 shadow-sm border border-white/20 dark:border-white/5"
                    style={{ background: ach.color }}
                  >
                    <AchIcon className="h-4.5 w-4.5" />
                  </div>
                  <div className="flex flex-col text-left">
                    <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors duration-200">
                      {ach.title}
                    </span>
                    <span className="text-[10px] font-bold text-text-muted mt-0.5 leading-tight">
                      {ach.desc}
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* COLUMN 3: AI SMART INSIGHTS (30% width) */}
        <div className="flex-1 flex flex-col gap-4 border-t lg:border-t-0 pt-4 lg:pt-0">
          <div className="flex items-center gap-2">
            <LucideIcons.Sparkles className="h-4.5 w-4.5 text-primary animate-pulse" />
            <h4 className="text-sm font-extrabold text-text-primary uppercase tracking-wider">
              Smart Insights
            </h4>
          </div>

          <div className="flex flex-col gap-3">
            {insights.map((ins, idx) => {
              const InsIcon = LucideIcons[ins.icon] || LucideIcons.Sparkles;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="p-3 rounded-2xl bg-primary/5 border border-primary/10 flex gap-3 items-start hover:bg-primary/8 transition-colors duration-200"
                >
                  <div className="h-5 w-5 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-primary mt-0.5">
                    <InsIcon className="h-3 w-3" />
                  </div>
                  <p className="text-[11px] font-bold text-text-secondary leading-normal">
                    {ins.text}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default StudentGoalsWidget;
