import React from 'react';
import { motion } from 'framer-motion';
import { ANIMATION_DURATIONS } from '@/constants';

export const PageTransition = ({ children, ...props }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ duration: ANIMATION_DURATIONS.NORMAL, ease: 'easeOut' }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default PageTransition;
