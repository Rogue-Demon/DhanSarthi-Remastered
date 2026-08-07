import React from 'react';
import { motion } from 'framer-motion';
import { ANIMATION_DURATIONS } from '@/constants';

export const FadeIn = ({ children, delay = 0, duration = ANIMATION_DURATIONS.FAST, ...props }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration, delay, ease: 'easeOut' }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default FadeIn;
