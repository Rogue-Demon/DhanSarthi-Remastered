import React from 'react';
import { motion } from 'framer-motion';
import { ANIMATION_DURATIONS } from '@/constants';

export const SlideDown = ({ children, delay = 0, duration = ANIMATION_DURATIONS.NORMAL, yOffset = -15, ...props }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: yOffset }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: yOffset }}
      transition={{ duration, delay, ease: [0.16, 1, 0.3, 1] }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default SlideDown;
