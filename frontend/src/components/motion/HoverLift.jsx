import React from 'react';
import { motion } from 'framer-motion';

export const HoverLift = ({ children, yOffset = -4, scale = 1.015, ...props }) => {
  return (
    <motion.div
      whileHover={{ y: yOffset, scale }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default HoverLift;
