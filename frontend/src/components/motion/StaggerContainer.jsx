import React from 'react';
import { motion } from 'framer-motion';

export const StaggerContainer = ({ children, staggerDelay = 0.05, delayChildren = 0, ...props }) => {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      exit="hidden"
      variants={{
        hidden: {},
        visible: {
          transition: {
            staggerChildren: staggerDelay,
            delayChildren,
          },
        },
      }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const StaggerItem = ({ children, ...props }) => {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 350, damping: 25 } },
      }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default StaggerContainer;
