import React from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'
import { Button } from '@/components/ui'
import { Logo } from '@/components/common'
import { PageTransition, FadeIn, ScaleIn } from '@/components/motion'
import { onboardingConfig } from '@/config/onboarding.config'
import { ROUTE_PATHS } from '@/constants'
import * as LucideIcons from 'lucide-react'

export function Onboarding() {
  const navigate = useNavigate()
  const shouldReduceMotion = useReducedMotion()
  const welcomeData = onboardingConfig.welcome

  const handleGetStarted = () => {
    navigate(ROUTE_PATHS.REGISTER)
  }

  // Logo animation variants
  const logoVariants = {
    initial: { rotate: 0 },
    animate: {
      rotate: shouldReduceMotion ? 0 : [0, -5, 5, 0],
      transition: {
        repeat: Infinity,
        repeatType: 'reverse',
        duration: 6,
        ease: 'easeInOut',
      },
    },
  }

  // Main container entrance variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1,
      },
    },
  }

  return (
    <PageTransition className="min-h-screen flex items-center justify-center p-4 md:p-8 bg-background overflow-hidden relative">
      {/* Decorative premium background elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-primary/5 blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-accent/5 blur-3xl pointer-events-none" />

      {/* Main claymorphic shell for welcome card */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="clay-surface w-full max-w-5xl bg-card p-6 md:p-12 flex flex-col lg:flex-row items-center gap-10 md:gap-16 border border-white/50 shadow-modal"
      >
        {/* Left Side: Brand & Call to Action */}
        <div className="flex-1 flex flex-col items-start text-left gap-6 md:gap-8 max-w-lg z-10">
          {/* Logo & Brand Label */}
          <motion.div
            className="flex items-center gap-3"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <motion.div variants={logoVariants} initial="initial" animate="animate">
              <Logo size="lg" className="h-12 w-12" />
            </motion.div>
            <span className="text-2xl font-extrabold tracking-tight bg-gradient-primary bg-clip-text text-transparent">
              धनSarthi
            </span>
          </motion.div>

          {/* Heading with bold layout */}
          <div className="flex flex-col gap-2">
            <h1 className="text-4xl md:text-5xl font-black text-text-primary tracking-tight leading-[1.1] text-balance">
              {welcomeData.heading.split(' ').slice(0, 2).join(' ')}{' '}
              <span className="bg-gradient-hero bg-clip-text text-transparent">
                {welcomeData.heading.split(' ').slice(2).join(' ')}
              </span>
            </h1>
            <p className="text-lg md:text-xl font-bold text-primary/80 uppercase tracking-widest mt-1">
              {welcomeData.subheading}
            </p>
          </div>

          {/* Description */}
          <p className="text-base md:text-lg text-text-secondary leading-relaxed font-medium">
            {welcomeData.description}
          </p>

          {/* Call to Action Button */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4, type: 'spring', stiffness: 300, damping: 20 }}
            className="w-full sm:w-auto"
          >
            <Button
              variant="gradient"
              size="lg"
              onClick={handleGetStarted}
              className="px-8 py-4 font-bold text-lg rounded-2xl w-full sm:w-auto justify-between group shadow-button"
              iconRight={
                <LucideIcons.ArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
              }
            >
              {welcomeData.ctaText}
            </Button>
          </motion.div>

          {/* Core App Benefits List */}
          <div className="grid grid-cols-2 gap-4 w-full border-t border-border/80 pt-6 mt-2">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-sm font-semibold text-text-secondary">Claymorphic Design</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-sm font-semibold text-text-secondary">AI Advisor Ready</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-sm font-semibold text-text-secondary">Profile-Centric UX</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-sm font-semibold text-text-secondary">Zero-Config Setups</span>
            </div>
          </div>
        </div>

        {/* Right Side: Interactive Illustration Placeholder */}
        <div className="flex-1 w-full flex items-center justify-center relative min-h-[300px] lg:min-h-[450px]">
          {/* Background Ambient Circle Glow */}
          <div className="absolute w-72 h-72 rounded-full bg-gradient-primary opacity-10 blur-3xl pointer-events-none" />

          {/* Interactive Claymorphic Mockup Cards stacked */}
          <div className="relative w-full max-w-[400px] h-[340px] md:h-[400px]">
            {/* Card 1: Bottom Right Shadow Card */}
            <motion.div
              initial={{ opacity: 0, x: 20, y: 40 }}
              animate={{ opacity: 1, x: 0, y: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="absolute bottom-4 right-4 w-[75%] h-[160px] bg-card/90 clay-surface p-4 flex flex-col justify-between border border-white/40 dark:border-white/5 shadow-md"
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-success/15 flex items-center justify-center text-success">
                    <LucideIcons.TrendingUp className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-text-muted uppercase">Investments</p>
                    <p className="text-xs font-black text-text-primary">Portfolio Peak</p>
                  </div>
                </div>
                <span className="text-xs font-black text-success bg-success/10 px-2 py-0.5 rounded-full">
                  +12.4%
                </span>
              </div>
              <div className="h-16 w-full flex items-end gap-1.5 pt-2">
                {[40, 55, 45, 60, 75, 65, 85].map((val, idx) => (
                  <div
                    key={idx}
                    className="flex-1 bg-muted rounded-md relative overflow-hidden"
                    style={{ height: '100%' }}
                  >
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: `${val}%` }}
                      transition={{ delay: 0.6 + idx * 0.05, duration: 0.6 }}
                      className="absolute bottom-0 left-0 right-0 bg-primary/20 rounded-md"
                    />
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Card 2: Top Left Back Card */}
            <motion.div
              initial={{ opacity: 0, x: -30, y: -20 }}
              animate={{ opacity: 1, x: 0, y: 0 }}
              transition={{ delay: 0.1, duration: 0.5 }}
              className="absolute top-4 left-4 w-[70%] h-[150px] bg-card/85 clay-surface p-4 flex flex-col justify-between border border-white/40 dark:border-white/5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="h-6 w-16 rounded bg-muted animate-pulse" />
                <div className="h-4 w-4 rounded-full bg-primary/20" />
              </div>
              <div className="flex flex-col gap-2 mt-4">
                <div className="h-3 w-[90%] rounded bg-muted" />
                <div className="h-3 w-[60%] rounded bg-muted" />
              </div>
              <div className="flex items-center gap-1.5 mt-2">
                <div className="h-5 w-5 rounded-full bg-muted flex items-center justify-center">
                  <LucideIcons.PieChart className="h-3 w-3 text-text-muted" />
                </div>
                <div className="h-2 w-16 rounded bg-muted" />
              </div>
            </motion.div>

            {/* Card 3: Front & Center Main Showcase Card */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 200, damping: 20 }}
              className="absolute top-[22%] left-[12%] w-[76%] h-[200px] bg-card clay-surface p-5 flex flex-col justify-between border-2 border-white/60 shadow-floating z-20"
            >
              <div className="flex items-start justify-between">
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                    AI Financial Advisor
                  </span>
                  <h3 className="text-base font-black text-text-primary">Wealth Forecast</h3>
                </div>
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                  <LucideIcons.Bot className="h-4.5 w-4.5" />
                </div>
              </div>

              {/* Mock AI Tip Text bubble inside card */}
              <div className="bg-primary/5 border border-primary/15 rounded-xl p-3 flex gap-2.5 items-start mt-2">
                <div className="h-5 w-5 rounded-full bg-primary flex items-center justify-center text-white shrink-0 mt-0.5">
                  <LucideIcons.Sparkles className="h-3 w-3" />
                </div>
                <p className="text-[11px] font-bold text-primary leading-normal text-left">
                  "Based on your savings goals, selecting a Working Professional profile will
                  optimize tax planning."
                </p>
              </div>

              <div className="flex items-center justify-between mt-1 text-[10px] font-bold text-text-muted">
                <span>Personalized insights ready</span>
                <LucideIcons.Sparkles className="h-3.5 w-3.5 text-accent animate-pulse" />
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </PageTransition>
  )
}

export default Onboarding
