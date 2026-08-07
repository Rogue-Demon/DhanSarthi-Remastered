import React from 'react';
import { motion } from 'framer-motion';
import { ANIMATION_DURATIONS } from '@/constants';

export const ScaleIn = ({ children, delay = 0, duration = ANIMATION_DURATIONS.NORMAL, startScale = 0.95, ...props }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: startScale }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: startScale }}
      transition={{ duration, delay, ease: [0.16, 1, 0.3, 1] }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default ScaleIn;
