import React from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { useProfile, useAuth } from '@/hooks'
import { dashboardConfig } from '@/config'
import { PROFILES } from '@/constants'
import { Button } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { cn } from '@/utils'

/**
 * BusinessWelcomeHero Component
 *
 * A premium corporate hero banner designed specifically for the Business profile.
 * Highlights metrics (gross revenue, profit, opex), collection stats, and invoice actions.
 */
function BusinessWelcomeHero({ profileConfig, dashboardData, user }) {
  const shouldReduceMotion = useReducedMotion()

  const revenue = parseFloat(dashboardData?.summary?.total_income || 0)
  const opex = parseFloat(dashboardData?.summary?.total_expenses || 0)

  return (
    <div className="clay-surface bg-card border-2 border-white/60 dark:border-white/5 rounded-3xl p-6 md:p-8 shadow-floating text-left flex flex-col lg:flex-row items-center justify-between gap-8 overflow-hidden relative font-sans">
      {/* Clean corporate grid background accents (no playful elements) */}
      <div className="absolute top-[-10%] left-[-5%] w-48 h-48 rounded-full bg-primary/5 blur-2xl pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-60 h-60 rounded-full bg-primary/5 blur-3xl pointer-events-none" />

      {/* Left side: Heading, key KPI summary figures, and CTAs */}
      <div className="flex-grow flex flex-col items-start gap-4.5 z-10 max-w-xl">
        <div className="flex items-center gap-2">
          <Badge className="text-[9px] font-black uppercase tracking-widest bg-primary/15 border-primary/20 text-primary py-0.5 px-2 rounded-md">
            Corporate Statement
          </Badge>
          <div className="h-1.5 w-1.5 rounded-full bg-success shrink-0" />
          <span className="text-[9px] font-black text-text-muted uppercase tracking-widest leading-none">
            Status: Compliant (GST Active)
          </span>
        </div>

        {/* Headline */}
        <h2 className="text-2xl md:text-3xl font-extrabold text-text-primary tracking-tight leading-tight">
          Manage liquid cash flows and payrolls,{' '}
          <span className="bg-gradient-primary bg-clip-text text-transparent font-black">
            {user?.profile?.display_name ||
              user?.display_name ||
              user?.email?.split('@')[0] ||
              'Valued Member'}
          </span>
        </h2>

        {/* Description / Business message */}
        <p className="text-xs md:text-sm text-text-secondary leading-relaxed font-semibold">
          Your gross revenue is{' '}
          <span className="text-text-primary font-bold">₹{revenue.toLocaleString('en-IN')}</span>{' '}
          this month with an operating opex margin of{' '}
          <span className="text-text-primary font-bold">₹{opex.toLocaleString('en-IN')}</span>.
          Ensure pending collections are resolved.
        </p>

        {/* Primary/Secondary CTAs */}
        <div className="flex flex-wrap gap-3 w-full pt-1">
          <Button
            variant="gradient"
            size="sm"
            onClick={() => alert('Create Invoice template wizard')}
            className="rounded-xl font-bold shadow-button gap-1.5 shrink-0"
            iconLeft={<LucideIcons.FilePlus className="h-4 w-4" />}
          >
            Create Invoice
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => alert('Manage Payroll wizard')}
            className="rounded-xl font-bold border-border shadow-xs gap-1.5 text-text-secondary bg-card shrink-0 hover:border-primary/25"
            iconLeft={<LucideIcons.Users className="h-4 w-4 text-primary" />}
          >
            Manage Payroll
          </Button>
        </div>
      </div>

      {/* Right side: Corporate Mockup Illustration Placeholder */}
      <div className="flex-shrink-0 w-full lg:w-80 flex items-center justify-center relative z-10">
        <div className="clay-surface bg-muted/20 border border-border p-4.5 rounded-2xl w-full flex flex-col gap-3 select-none relative overflow-hidden">
          <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase tracking-wider">
            <span>Operational overheads (OPEX)</span>
            <LucideIcons.PieChart className="h-3 w-3 text-text-muted" />
          </div>

          {/* Simple breakdown comparison progress bars */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs font-semibold">
              <span className="text-text-secondary">Payroll (salaries)</span>
              <span className="font-extrabold text-text-primary">
                ₹{Math.round(opex * 0.4).toLocaleString('en-IN')}
              </span>
            </div>
            <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden border border-white/60 shadow-inner">
              <div className="bg-primary h-full rounded-full" style={{ width: '40%' }} />
            </div>
          </div>

          <div className="flex flex-col gap-2 border-t border-border/40 pt-2.5">
            <div className="flex justify-between items-center text-xs font-semibold">
              <span className="text-text-secondary">Office rent & utilities</span>
              <span className="font-extrabold text-text-primary">
                ₹{Math.round(opex * 0.2).toLocaleString('en-IN')}
              </span>
            </div>
            <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden border border-white/60 shadow-inner">
              <div className="bg-primary h-full rounded-full" style={{ width: '20%' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * ExecutiveWelcomeHero Component
 *
 * A premium, clean, data-driven hero banner designed specifically for the
 * Working Professional profile. Emphasizes productivity, wealth accumulation,
 * opex ratios, and tax planning.
 */
function ExecutiveWelcomeHero({ profileConfig, dashboardData, user }) {
  const shouldReduceMotion = useReducedMotion()
  const liquidCash = parseFloat(dashboardData?.net_worth?.liquid_assets || 0)
  const returnPct = parseFloat(dashboardData?.investments?.total_return_percentage || 0)

  return (
    <div className="clay-surface bg-card border-2 border-white/60 dark:border-white/5 rounded-3xl p-6 md:p-8 shadow-floating text-left flex flex-col lg:flex-row items-center justify-between gap-8 overflow-hidden relative font-sans">
      {/* Minimal clean background accents (no playful elements) */}
      <div className="absolute top-[-10%] left-[-5%] w-48 h-48 rounded-full bg-primary/5 blur-2xl pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-60 h-60 rounded-full bg-primary/5 blur-3xl pointer-events-none" />

      {/* Left side: Heading, Net Worth highlight, and CTA buttons */}
      <div className="flex-grow flex flex-col items-start gap-4 z-10 max-w-xl">
        <div className="flex items-center gap-2">
          <Badge className="text-[9px] font-black uppercase tracking-widest bg-primary/15 border-primary/20 text-primary py-0.5 px-2 rounded-md">
            Executive Summary
          </Badge>
          <div className="h-1.5 w-1.5 rounded-full bg-success shrink-0" />
          <span className="text-[9px] font-black text-text-muted uppercase tracking-widest leading-none">
            Filing Status: Active
          </span>
        </div>

        {/* Headline */}
        <h2 className="text-2xl md:text-3xl font-extrabold text-text-primary tracking-tight leading-tight">
          Track wealth accumulation and optimize taxation,{' '}
          <span className="bg-gradient-primary bg-clip-text text-transparent font-black">
            {user?.profile?.display_name ||
              user?.display_name ||
              user?.email?.split('@')[0] ||
              'Valued Member'}
          </span>
        </h2>

        {/* Description / Financial overview message */}
        <p className="text-xs md:text-sm text-text-secondary leading-relaxed font-semibold">
          Your portfolio grew by{' '}
          <span className="text-success font-bold">+{returnPct.toFixed(1)}%</span> this month.
          Increase your Section 80C contributions to optimize your tax liabilities further.
        </p>

        {/* Primary/Secondary CTAs */}
        <div className="flex flex-wrap gap-3 w-full pt-1">
          <Button
            variant="gradient"
            size="sm"
            onClick={() => alert('Add Transaction wizard placeholder')}
            className="rounded-xl font-bold shadow-button gap-1.5 shrink-0"
            iconLeft={<LucideIcons.PlusCircle className="h-4 w-4" />}
          >
            Add Transaction
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => alert('Tax optimization planner page')}
            className="rounded-xl font-bold border-border shadow-xs gap-1.5 text-text-secondary bg-card shrink-0 hover:border-primary/25"
            iconLeft={<LucideIcons.Percent className="h-4 w-4 text-primary" />}
          >
            Tax Planner
          </Button>
        </div>
      </div>

      {/* Right side: Executive Mockup Illustration Placeholder */}
      <div className="flex-shrink-0 w-full lg:w-72 flex items-center justify-center relative z-10">
        <div className="clay-surface bg-muted/20 border border-border p-4.5 rounded-2xl w-full flex flex-col gap-3.5 select-none relative overflow-hidden">
          <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase tracking-wider">
            <span>Portfolio Liquidity</span>
            <LucideIcons.Activity className="h-3 w-3 text-text-muted" />
          </div>

          {/* Simple asset indicator bars */}
          <div className="flex flex-col gap-2.5">
            <div className="flex justify-between items-center text-xs font-semibold">
              <span className="text-text-secondary">Emergency Fund</span>
              <span className="font-extrabold text-text-primary">80%</span>
            </div>
            <div className="w-full bg-muted h-2 rounded-full overflow-hidden border border-white/60 shadow-inner">
              <div className="bg-success h-full rounded-full" style={{ width: '80%' }} />
            </div>
          </div>

          <div className="flex flex-col gap-2.5 border-t border-border/40 pt-2.5 mt-1">
            <div className="flex justify-between items-center text-xs font-semibold">
              <span className="text-text-secondary">Liquid Cash</span>
              <span className="font-extrabold text-text-primary">
                ₹{liquidCash.toLocaleString('en-IN')}
              </span>
            </div>
            <div className="w-full bg-muted h-2 rounded-full overflow-hidden border border-white/60 shadow-inner">
              <div className="bg-primary h-full rounded-full" style={{ width: '35%' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * StudentWelcomeHero Component
 *
 * A premium, interactive hero banner specifically designed for the Student profile.
 * Emphasizes motivational learning, savings quotes, quick actions, and playful clay visuals.
 */
function StudentWelcomeHero({ profileConfig, dashboardData, user }) {
  const shouldReduceMotion = useReducedMotion()

  // Floating bubble animation variants for premium claymorphic background depth
  const bubbleVariants = (delay) => ({
    animate: {
      y: shouldReduceMotion ? 0 : [0, -12, 12, 0],
      x: shouldReduceMotion ? 0 : [0, 8, -8, 0],
      transition: {
        repeat: Infinity,
        duration: 8,
        delay,
        ease: 'easeInOut',
      },
    },
  })

  return (
    <div className="clay-surface bg-card border-2 border-white/60 dark:border-white/5 rounded-3xl p-6 md:p-10 shadow-floating text-left flex flex-col lg:flex-row items-center justify-between gap-10 overflow-hidden relative">
      {/* Dynamic Animated background accents */}
      <motion.div
        variants={bubbleVariants(0)}
        animate="animate"
        className="absolute top-[-10%] left-[5%] w-32 h-32 rounded-full bg-primary/10 blur-xl pointer-events-none"
      />
      <motion.div
        variants={bubbleVariants(2)}
        animate="animate"
        className="absolute bottom-[-10%] right-[30%] w-40 h-40 rounded-full bg-accent/10 blur-xl pointer-events-none"
      />
      <div className="absolute top-[20%] right-[-5%] w-52 h-52 rounded-full bg-gradient-primary opacity-[0.08] blur-3xl pointer-events-none" />

      {/* Left side: Heading copy, quote, and buttons */}
      <div className="flex-1 flex flex-col items-start gap-5 md:gap-6 z-10 max-w-xl">
        <div className="flex items-center gap-2">
          <Badge className="text-[10px] font-black uppercase tracking-widest bg-primary/10 border-primary/20 text-primary py-0.5 px-2.5 rounded-full">
            Student Hub
          </Badge>
          <div className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
          <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">
            Habits Tracking Active
          </span>
        </div>

        {/* Title greeting */}
        <h2 className="text-3xl md:text-4xl font-black text-text-primary tracking-tight leading-[1.15]">
          Make every rupee count,{' '}
          <span className="bg-gradient-primary bg-clip-text text-transparent font-black">
            {user?.profile?.display_name ||
              user?.display_name ||
              user?.email?.split('@')[0] ||
              'Valued Member'}
            !
          </span>
        </h2>

        {/* Motivational Savings Quote */}
        <div className="border-l-3 border-accent pl-4 py-1.5 bg-accent/5 rounded-r-xl w-full">
          <p className="text-xs font-black text-accent uppercase tracking-wider leading-none">
            Quote of the Day
          </p>
          <p className="text-sm font-bold text-text-secondary mt-1 leading-relaxed italic">
            "A penny saved is a penny earned."
          </p>
          <span className="text-[10px] font-bold text-text-muted block mt-0.5">
            — Benjamin Franklin
          </span>
        </div>

        {/* Primary and Secondary CTA Button elements */}
        <div className="flex flex-wrap gap-3.5 w-full pt-1">
          <Button
            variant="gradient"
            size="md"
            onClick={() => alert('Log Expense form placeholder')}
            className="rounded-2xl font-black shadow-button gap-2 group shrink-0"
            iconLeft={<LucideIcons.PlusCircle className="h-4 w-4" />}
          >
            Log Expense
          </Button>
          <Button
            variant="secondary"
            size="md"
            onClick={() => alert('AI Advisor chat page redirect')}
            className="rounded-2xl font-black border-border shadow-xs gap-2 group hover:border-primary/20 text-text-secondary bg-card shrink-0"
            iconLeft={<LucideIcons.Bot className="h-4 w-4 text-primary" />}
            iconRight={<LucideIcons.Sparkles className="h-3.5 w-3.5 text-accent animate-pulse" />}
          >
            Consult AI Advisor
          </Button>
        </div>
      </div>

      {/* Right side: Friendly Illustration Placeholder */}
      <div className="flex-1 w-full max-w-[340px] flex items-center justify-center relative min-h-[180px] z-10">
        <div className="clay-surface bg-card p-4.5 border border-white/60 shadow-md w-full relative flex items-center justify-between gap-4 overflow-hidden group hover:shadow-lg transition-shadow duration-300">
          <div className="absolute inset-0 opacity-[0.03] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:10px_10px]" />

          <div className="flex flex-col text-left gap-1">
            <span className="text-[9px] font-black text-text-muted uppercase tracking-wider leading-none">
              Daily Challenge
            </span>
            <span className="text-sm font-black text-text-primary leading-tight">
              Save ₹50 today
            </span>
            <span className="text-[10px] font-bold text-success flex items-center gap-1 mt-1 font-semibold">
              <LucideIcons.Check className="h-3 w-3 stroke-[3px]" /> Completed
            </span>
          </div>

          {/* Graphical element: Piggy bank mock */}
          <div className="relative h-20 w-20 flex items-center justify-center shrink-0">
            <div className="absolute inset-0 bg-accent/10 rounded-full border border-accent/15 flex items-center justify-center text-accent animate-pulse">
              <LucideIcons.PiggyBank className="h-10 w-10 stroke-[1.8]" />
            </div>
            {/* Animated coins floating down */}
            <motion.div
              animate={
                shouldReduceMotion
                  ? {}
                  : {
                      y: [0, 8, 0],
                      opacity: [0, 1, 0],
                    }
              }
              transition={{ repeat: Infinity, duration: 2.5, ease: 'easeInOut' }}
              className="absolute top-1 left-7 text-xs"
            >
              🪙
            </motion.div>
            <motion.div
              animate={
                shouldReduceMotion
                  ? {}
                  : {
                      y: [0, 12, 0],
                      opacity: [0, 1, 0],
                    }
              }
              transition={{ repeat: Infinity, duration: 3, delay: 1, ease: 'easeInOut' }}
              className="absolute top-3 right-6 text-[10px]"
            >
              🪙
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Inline badge helper for simple layouts
function Badge({ children, className, style }) {
  return (
    <span
      className={cn(
        'inline-flex items-center font-bold px-2 py-0.5 text-xs rounded border',
        className
      )}
      style={style}
    >
      {children}
    </span>
  )
}

/**
 * DashboardBanner Component
 *
 * Renders the welcome hero. If the active profile is "Student", it displays
 * the premium StudentWelcomeHero component; if it is "Working Professional", it
 * displays the ExecutiveWelcomeHero component; if it is "Business", it displays
 * the BusinessWelcomeHero component; otherwise, it defaults to the
 * standard profile welcome banner.
 */
export function DashboardBanner({ className, dashboardData, ...props }) {
  const { profile, profileConfig } = useProfile()
  const { user } = useAuth()
  const shouldReduceMotion = useReducedMotion()

  if (!profileConfig) return null

  // Render Student Specific Hero
  if (profile === PROFILES.STUDENT) {
    return (
      <StudentWelcomeHero profileConfig={profileConfig} dashboardData={dashboardData} user={user} />
    )
  }

  // Render Working Professional Specific Hero
  if (profile === PROFILES.PROFESSIONAL) {
    return (
      <ExecutiveWelcomeHero
        profileConfig={profileConfig}
        dashboardData={dashboardData}
        user={user}
      />
    )
  }

  // Render Business Specific Hero
  if (profile === PROFILES.BUSINESS) {
    return (
      <BusinessWelcomeHero
        profileConfig={profileConfig}
        dashboardData={dashboardData}
        user={user}
      />
    )
  }

  // Fallback Standard banner
  const bannerMessage = dashboardConfig[profile]?.bannerMessage || profileConfig.welcomeMessage

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : -15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={cn(
        'relative overflow-hidden rounded-3xl p-6 md:p-8 border border-white/20 shadow-lg text-white flex flex-col md:flex-row md:items-center justify-between gap-6 bg-gradient-primary',
        className
      )}
      {...props}
    >
      {/* Decorative glass overlay circles */}
      <div className="absolute top-[-20%] right-[-10%] w-60 h-60 rounded-full bg-white/10 blur-2xl pointer-events-none" />
      <div className="absolute bottom-[-30%] left-[-15%] w-72 h-72 rounded-full bg-accent/20 blur-2xl pointer-events-none" />

      {/* Banner message text section */}
      <div className="flex items-start gap-4 md:gap-5 z-10 max-w-2xl text-left">
        <div className="p-3.5 rounded-2xl bg-white/15 border border-white/20 shadow-md shrink-0 flex items-center justify-center text-white mt-1">
          {React.createElement(LucideIcons[profileConfig.icon] || LucideIcons.Sparkles, {
            className: 'h-6 w-6 stroke-[1.8]',
          })}
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-black text-white/70 uppercase tracking-widest leading-none">
            {profileConfig.label} Portfolio Active
          </span>
          <h2 className="text-2xl md:text-3xl font-black tracking-tight leading-tight">
            {bannerMessage}
          </h2>
          <p className="text-xs md:text-sm font-medium text-white/80 leading-relaxed">
            {profileConfig.description} Manage analytics, tracks, and configure advisor bots
            instantly.
          </p>
        </div>
      </div>

      {/* Quick dynamic banner status pill */}
      <div className="z-10 shrink-0 self-start md:self-center">
        <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white/15 border border-white/25 backdrop-blur-md shadow-sm">
          <div className="h-2 w-2 rounded-full bg-success-foreground animate-pulse" />
          <span className="text-xs font-black tracking-wider uppercase text-white/90">
            Realtime Analytics
          </span>
        </div>
      </div>
    </motion.div>
  )
}

export default DashboardBanner
