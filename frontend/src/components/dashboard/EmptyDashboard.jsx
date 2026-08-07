import React from 'react';
import { Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ROUTE_PATHS } from '@/constants';
import { useProfile } from '@/hooks';

/**
 * EmptyDashboard Component
 *
 * Fallback empty state view shown if no profile configurations are loaded or if
 * dashboard widgets are empty.
 */
export function EmptyDashboard() {
  const navigate = useNavigate();
  const { resetOnboarding } = useProfile();

  const handleConfigure = () => {
    resetOnboarding();
    navigate(ROUTE_PATHS.ONBOARDING);
  };

  return (
    <div className="clay-surface bg-card p-10 md:p-16 border border-white/60 dark:border-white/5 shadow-floating flex flex-col items-center justify-center text-center max-w-xl mx-auto my-12 select-none gap-6">
      {/* Decorative Blur Glow */}
      <div className="absolute top-0 right-0 w-24 h-24 rounded-full bg-primary/10 blur-2xl pointer-events-none" />

      {/* Large Rounded Icon */}
      <div className="p-5 rounded-3xl bg-primary/10 text-primary border border-primary/15 shadow-sm shrink-0 flex items-center justify-center">
        <LucideIcons.LayoutGrid className="h-10 w-10 stroke-[1.8] animate-pulse" />
      </div>

      {/* Headers */}
      <div className="flex flex-col gap-2">
        <h3 className="text-2xl font-black text-text-primary tracking-tight">
          No Profile Selected
        </h3>
        <p className="text-sm font-semibold text-text-secondary leading-relaxed max-w-md">
          To display your personalized financial dashboard, you must select your profile first. Choose between Student, Professional, or Business layouts.
        </p>
      </div>

      {/* Select Profile Button */}
      <Button
        variant="gradient"
        size="md"
        onClick={handleConfigure}
        className="px-6 py-3 font-bold rounded-2xl shadow-button gap-2 group mt-2"
        iconRight={
          <LucideIcons.ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
        }
      >
        Configure Dashboard Profile
      </Button>
    </div>
  );
}

export default EmptyDashboard;
