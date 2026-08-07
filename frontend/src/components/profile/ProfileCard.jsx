import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';
import { Badge } from '@/components/ui';

export function ProfileCard({
  profile,
  selected = false,
  disabled = false,
  onClick,
  onSelect,
  className,
  ...props
}) {
  const shouldReduceMotion = useReducedMotion();
  const IconComponent = LucideIcons[profile.icon] || LucideIcons.User;

  // Handle keyboard selection
  const handleKeyDown = (e) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick?.();
    }
  };

  // Animation variants
  const cardVariants = {
    initial: {
      scale: 1,
      y: 0,
      boxShadow: 'var(--shadow-card)',
    },
    hover: {
      scale: shouldReduceMotion ? 1 : 1.03,
      y: shouldReduceMotion ? 0 : -6,
      boxShadow: '0 20px 32px rgba(124, 58, 237, 0.08), 0 8px 16px rgba(124, 58, 237, 0.04)',
      transition: {
        type: 'spring',
        stiffness: 400,
        damping: 20,
      },
    },
    selected: {
      scale: shouldReduceMotion ? 1 : 1.01,
      y: 0,
      boxShadow: '0 4px 12px rgba(124, 58, 237, 0.05)',
      transition: {
        type: 'spring',
        stiffness: 400,
        damping: 25,
      },
    },
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      whileHover={!disabled && !selected ? 'hover' : undefined}
      animate={selected ? 'selected' : 'initial'}
      onClick={!disabled ? onClick : undefined}
      onKeyDown={handleKeyDown}
      tabIndex={disabled ? -1 : 0}
      role="radio"
      aria-checked={selected}
      aria-disabled={disabled}
      className={cn(
        // Base claymorphism card surface
        'clay-surface relative flex flex-col justify-between w-full h-full p-6 text-left border cursor-pointer select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
        // Selected state styling
        selected
          ? 'border-primary bg-primary/5 ring-1 ring-primary'
          : 'border-border hover:border-primary/30 bg-card',
        // Disabled state styling
        disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        className
      )}
      {...props}
    >
      {/* Decorative gradient light glow in the top corner for premium feel */}
      <div
        className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-10 pointer-events-none transition-all duration-300"
        style={{
          background: profile.gradient || 'var(--gradient-primary)',
        }}
      />

      {/* Selected Indicator Checkmark */}
      <div className="absolute top-4 right-4 flex items-center justify-center">
        <div
          className={cn(
            'w-6 h-6 rounded-full border flex items-center justify-center transition-all duration-300',
            selected
              ? 'bg-primary border-primary text-white scale-100'
              : 'border-text-muted/30 bg-transparent scale-90'
          )}
        >
          <LucideIcons.Check
            className={cn('h-3.5 w-3.5 stroke-[3px] transition-transform duration-300', selected ? 'scale-100' : 'scale-0')}
          />
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {/* Profile Large Icon with custom glass-like clay container */}
        <div
          className="flex items-center justify-center w-14 h-14 rounded-2xl bg-muted shadow-sm transition-all duration-300 border border-white/40 dark:border-white/5"
          style={{
            background: selected
              ? `linear-gradient(135deg, ${profile.color}15 0%, ${profile.color}25 100%)`
              : undefined,
            color: selected ? profile.color : 'var(--text-secondary)',
          }}
        >
          <IconComponent className="w-7 h-7 stroke-[1.75]" />
        </div>

        {/* Profile Name & Description */}
        <div className="flex flex-col gap-1">
          <h3 className="text-xl font-extrabold text-text-primary tracking-tight">
            {profile.label}
          </h3>
          <p className="text-sm text-text-secondary leading-relaxed min-h-[40px]">
            {profile.shortDescription}
          </p>
        </div>

        {/* Features List */}
        <div className="flex flex-col gap-2 mt-2">
          <span className="text-[11px] font-bold text-text-muted uppercase tracking-wider">
            Key Focus Areas
          </span>
          <div className="flex flex-wrap gap-1.5">
            {profile.features.slice(0, 4).map((feat) => (
              <Badge
                key={feat}
                variant="secondary"
                className={cn(
                  'text-xs font-semibold px-2 py-0.5 rounded-full border border-border shadow-xs transition-colors duration-200',
                  selected && 'bg-primary/10 border-primary/20 text-primary'
                )}
              >
                {feat}
              </Badge>
            ))}
            {profile.features.length > 4 && (
              <span className="text-xs text-text-muted font-medium self-center pl-1">
                +{profile.features.length - 4} more
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Mini Illustration Placeholder */}
      <div className="relative w-full h-24 mt-6 rounded-xl bg-muted/50 border border-dashed border-border/80 flex items-center justify-center overflow-hidden transition-all duration-300 group">
        {/* Soft background pattern to look premium */}
        <div className="absolute inset-0 opacity-5 bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:16px_16px]" />
        
        {/* Illustrative icons dynamic container */}
        <div className="flex items-center gap-1.5 z-10 transition-transform duration-300 group-hover:scale-105">
          <IconComponent
            className="w-8 h-8 opacity-40 transition-colors duration-300"
            style={{ color: selected ? profile.color : 'inherit' }}
          />
          <LucideIcons.ArrowRight className="w-4 h-4 opacity-20 text-text-muted" />
          <LucideIcons.LineChart
            className="w-8 h-8 opacity-40 transition-colors duration-300"
            style={{ color: selected ? profile.color : 'inherit' }}
          />
        </div>
        
        {/* Bottom border color bar */}
        <div
          className={cn(
            'absolute bottom-0 left-0 right-0 h-1 transition-all duration-300',
            selected ? 'opacity-100' : 'opacity-0'
          )}
          style={{ background: profile.gradient || 'var(--gradient-primary)' }}
        />
      </div>
    </motion.div>
  );
}

export default ProfileCard;
