import { ANIMATION_DURATIONS } from '@/constants';

export const animationVariants = {
  fadeIn: {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { duration: ANIMATION_DURATIONS.FAST, ease: 'easeOut' }
    },
    exit: { 
      opacity: 0,
      transition: { duration: ANIMATION_DURATIONS.FAST, ease: 'easeIn' }
    }
  },
  slideUp: {
    hidden: { y: 15, opacity: 0 },
    visible: { 
      y: 0, 
      opacity: 1,
      transition: { duration: ANIMATION_DURATIONS.NORMAL, ease: [0.16, 1, 0.3, 1] }
    },
    exit: { 
      y: 10, 
      opacity: 0,
      transition: { duration: ANIMATION_DURATIONS.NORMAL, ease: 'easeIn' }
    }
  },
  scaleIn: {
    hidden: { scale: 0.95, opacity: 0 },
    visible: { 
      scale: 1, 
      opacity: 1,
      transition: { duration: ANIMATION_DURATIONS.NORMAL, ease: [0.16, 1, 0.3, 1] }
    },
    exit: { 
      scale: 0.95, 
      opacity: 0,
      transition: { duration: ANIMATION_DURATIONS.NORMAL, ease: 'easeIn' }
    }
  }
};

export default {
  variants: animationVariants
};
