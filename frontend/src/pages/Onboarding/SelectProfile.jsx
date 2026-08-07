import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { useProfile } from '@/hooks';
import { getProfilesList } from '@/config/profiles.config';
import { onboardingConfig } from '@/config/onboarding.config';
import { ROUTE_PATHS, PROFILES } from '@/constants';
import { Button } from '@/components/ui';
import { ProfileCard } from '@/components/profile';
import { PageTransition, StaggerContainer, StaggerItem, FadeIn, ScaleIn } from '@/components/motion';
import * as LucideIcons from 'lucide-react';
import { Logo } from '@/components/common';

export function SelectProfile() {
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();
  const { profile, setProfile, completeOnboarding } = useProfile();
  
  // Track onboarding step: 'select' or 'confirm'
  const [subStep, setSubStep] = useState('select');
  // Temporary selection until confirmed
  const [selectedProfileName, setSelectedProfileName] = useState(profile || PROFILES.STUDENT);

  const profilesList = getProfilesList();
  const currentProfileConfig = profilesList.find((p) => p.name === selectedProfileName);

  const handleCardClick = (name) => {
    setSelectedProfileName(name);
  };

  const handleNext = () => {
    if (subStep === 'select') {
      // Set store profile but don't mark onboarding complete yet
      setProfile(selectedProfileName);
      setSubStep('confirm');
    }
  };

  const handleBack = () => {
    if (subStep === 'confirm') {
      setSubStep('select');
    } else {
      navigate(ROUTE_PATHS.ONBOARDING);
    }
  };

  const handleConfirm = () => {
    // Complete onboarding and redirect to dashboard
    setProfile(selectedProfileName);
    completeOnboarding();
    navigate(ROUTE_PATHS.DASHBOARD, { replace: true });
  };

  return (
    <PageTransition className="min-h-screen flex flex-col justify-between p-4 md:p-8 bg-background relative overflow-hidden">
      {/* Decorative Blur Backgrounds */}
      <div className="absolute top-[-10%] right-[-10%] w-[45vw] h-[45vw] rounded-full bg-primary/5 blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[45vw] h-[45vw] rounded-full bg-accent/5 blur-3xl pointer-events-none" />

      {/* Header Bar */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between z-10 py-2">
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => navigate(ROUTE_PATHS.ONBOARDING)}>
          <Logo size="md" />
          <span className="text-lg font-black tracking-tight bg-gradient-primary bg-clip-text text-transparent">
            धनSarthi
          </span>
        </div>

        {/* Stepper Status Indicators */}
        <div className="flex items-center gap-2">
          {[
            { step: 1, label: 'Welcome', active: false, done: true },
            { step: 2, label: 'Profile', active: subStep === 'select', done: subStep === 'confirm' },
            { step: 3, label: 'Confirm', active: subStep === 'confirm', done: false },
          ].map((item, idx) => (
            <React.Fragment key={item.step}>
              {idx > 0 && <div className={`w-6 h-[2px] rounded-full ${item.active || item.done ? 'bg-primary' : 'bg-border'}`} />}
              <div className="flex items-center gap-1.5">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black transition-all duration-300 ${
                    item.active
                      ? 'bg-primary text-white ring-4 ring-primary/20 scale-110'
                      : item.done
                      ? 'bg-success text-white'
                      : 'bg-muted text-text-muted border border-border'
                  }`}
                >
                  {item.done ? <LucideIcons.Check className="h-3.5 w-3.5 stroke-[3px]" /> : item.step}
                </div>
                <span className={`text-xs font-bold hidden sm:inline ${item.active ? 'text-primary' : 'text-text-muted'}`}>
                  {item.label}
                </span>
              </div>
            </React.Fragment>
          ))}
        </div>
      </header>

      {/* Main Content Layout */}
      <main className="flex-grow max-w-6xl w-full mx-auto flex flex-col justify-center py-8 z-10">
        <AnimatePresence mode="wait">
          {subStep === 'select' ? (
            /* STEP 2: PROFILE SELECTION CARD GRID */
            <motion.div
              key="select-profile-view"
              initial={{ opacity: 0, x: shouldReduceMotion ? 0 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: shouldReduceMotion ? 0 : -20 }}
              transition={{ duration: 0.25 }}
              className="flex flex-col gap-8 w-full"
            >
              {/* Header Title */}
              <div className="text-center max-w-2xl mx-auto flex flex-col gap-2">
                <span className="text-xs font-black text-primary uppercase tracking-widest">
                  Step 2 of 3
                </span>
                <h2 className="text-3xl md:text-4xl font-black text-text-primary tracking-tight leading-tight">
                  Choose your Financial Profile
                </h2>
                <p className="text-sm md:text-base text-text-secondary font-medium">
                  We'll customize your widgets, analytics charts, and AI advisors based on how you manage your capital.
                </p>
              </div>

              {/* Cards Grid */}
              <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 w-full px-2" staggerDelay={0.08}>
                {profilesList.map((prof) => (
                  <StaggerItem key={prof.name} className="h-full">
                    <ProfileCard
                      profile={prof}
                      selected={selectedProfileName === prof.name}
                      onClick={() => handleCardClick(prof.name)}
                    />
                  </StaggerItem>
                ))}
              </StaggerContainer>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-between border-t border-border/80 pt-6 mt-4 gap-4">
                <Button
                  variant="ghost"
                  onClick={handleBack}
                  className="px-6 py-2.5 font-bold rounded-xl text-text-secondary hover:text-text-primary self-start sm:self-center"
                  iconLeft={<LucideIcons.ArrowLeft className="w-4 h-4" />}
                >
                  Back
                </Button>
                <Button
                  variant="primary"
                  onClick={handleNext}
                  className="px-8 py-3 font-bold rounded-2xl w-full sm:w-auto shadow-button justify-between"
                  iconRight={<LucideIcons.ArrowRight className="w-4.5 h-4.5" />}
                >
                  Next Step
                </Button>
              </div>
            </motion.div>
          ) : (
            /* STEP 3: PERSONALIZED CONFIRMATION */
            <motion.div
              key="confirmation-view"
              initial={{ opacity: 0, x: shouldReduceMotion ? 0 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: shouldReduceMotion ? 0 : -20 }}
              transition={{ duration: 0.25 }}
              className="flex flex-col gap-6 w-full max-w-2xl mx-auto"
            >
              {/* Heading Section */}
              <div className="text-center flex flex-col gap-2">
                <span className="text-xs font-black text-primary uppercase tracking-widest">
                  Step 3 of 3
                </span>
                <h2 className="text-3xl md:text-4xl font-black text-text-primary tracking-tight">
                  {onboardingConfig.confirmation.heading}
                </h2>
                <p className="text-sm md:text-base text-text-secondary font-medium">
                  {onboardingConfig.confirmation.subheading}
                </p>
              </div>

              {/* Confirmation Claymorphism Showcase Card */}
              <ScaleIn className="clay-surface bg-card border-2 border-white p-8 flex flex-col items-center gap-6 shadow-floating text-center">
                {/* Glowing profile gradient top line */}
                <div
                  className="absolute top-0 left-0 right-0 h-1.5"
                  style={{ background: currentProfileConfig.gradient }}
                />

                {/* Profile Large Rounded Icon Container */}
                <div
                  className="flex items-center justify-center w-20 h-20 rounded-3xl bg-muted shadow-md border border-white/60 text-white"
                  style={{
                    background: currentProfileConfig.gradient,
                  }}
                >
                  {React.createElement(LucideIcons[currentProfileConfig.icon] || LucideIcons.User, {
                    className: 'w-10 h-10 stroke-[1.75]',
                  })}
                </div>

                {/* Profile Label */}
                <div className="flex flex-col gap-1.5">
                  <span className="text-xs font-black text-primary uppercase tracking-wider">
                    Selected Profile
                  </span>
                  <h3 className="text-2xl font-black text-text-primary tracking-tight">
                    {currentProfileConfig.label}
                  </h3>
                </div>

                {/* Personalized Welcome Message Bubble */}
                <div className="w-full bg-primary/5 border border-primary/10 rounded-2xl p-4 flex gap-3.5 items-start text-left max-w-md shadow-xs">
                  <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center text-white shrink-0 mt-0.5">
                    <LucideIcons.Sparkles className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex flex-col gap-1">
                    <p className="text-sm font-black text-primary">Personalized Prompt</p>
                    <p className="text-sm text-text-secondary font-medium italic">
                      "{currentProfileConfig.welcomeMessage}"
                    </p>
                  </div>
                </div>

                {/* Focus areas list cards */}
                <div className="w-full mt-2 flex flex-col gap-2">
                  <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">
                    Your Personalized Modules Include
                  </span>
                  <div className="grid grid-cols-2 gap-2.5">
                    {currentProfileConfig.focusAreas.map((area) => (
                      <div
                        key={area}
                        className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-muted/65 border border-border/80 shadow-xs"
                      >
                        <div className="h-2 w-2 rounded-full bg-primary shrink-0" />
                        <span className="text-xs font-bold text-text-primary">{area}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </ScaleIn>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-between border-t border-border/80 pt-6 gap-4">
                <Button
                  variant="ghost"
                  onClick={handleBack}
                  className="px-6 py-2.5 font-bold rounded-xl text-text-secondary hover:text-text-primary self-start sm:self-center"
                  iconLeft={<LucideIcons.ArrowLeft className="w-4 h-4" />}
                >
                  {onboardingConfig.confirmation.backText}
                </Button>
                <Button
                  variant="gradient"
                  size="lg"
                  onClick={handleConfirm}
                  className="px-8 py-3.5 font-bold rounded-2xl w-full sm:w-auto shadow-button justify-between group"
                  iconRight={
                    <LucideIcons.Sparkles className="w-5 h-5 transition-transform duration-300 group-hover:rotate-12" />
                  }
                >
                  {onboardingConfig.confirmation.ctaText}
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer copyright */}
      <footer className="max-w-6xl w-full mx-auto text-center py-4 border-t border-border/60 z-10">
        <p className="text-xs font-bold text-text-muted">
          &copy; {new Date().getFullYear()} {onboardingConfig.welcome.heading.split(' ').slice(0, 1)} DhanSarthi. All Rights Reserved.
        </p>
      </footer>
    </PageTransition>
  );
}

export default SelectProfile;
