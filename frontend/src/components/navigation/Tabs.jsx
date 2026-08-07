import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/utils';

export const Tabs = ({
  tabs = [], // Array of { id, label, content }
  defaultTab,
  className,
  ...props
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  const activeContent = tabs.find((t) => t.id === activeTab)?.content;

  return (
    <div className={cn('flex flex-col gap-4 w-full', className)} {...props}>
      <div className="flex border-b border-border gap-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'pb-3 text-sm font-semibold relative cursor-pointer outline-none transition-colors duration-150',
              activeTab === tab.id ? 'text-primary' : 'text-text-secondary hover:text-text-primary'
            )}
          >
            {tab.label}
            {activeTab === tab.id && (
              <motion.div
                layoutId="activeTabIndicator"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              />
            )}
          </button>
        ))}
      </div>
      <div className="w-full">
        {activeContent}
      </div>
    </div>
  );
};

export default Tabs;
