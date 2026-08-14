import React, { useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'

function Selector({ label, desc, options, value, onChange }) {
  return (
    <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-3 shadow-xs">
      <div className="flex flex-col gap-0.5">
        <span className="text-xs font-black text-text-primary uppercase tracking-wider">
          {label}
        </span>
        <span className="text-[10px] font-bold text-text-muted">{desc}</span>
      </div>
      <div className="flex flex-wrap gap-2 pt-1">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className={`px-3 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer border ${
              value === opt
                ? 'bg-primary text-white border-primary shadow-xs'
                : 'bg-card border-border text-text-muted hover:text-text-primary'
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  )
}

export function PreferencesSettings() {
  const shouldReduceMotion = useReducedMotion()
  const [currency, setCurrency] = useState('INR (₹)')
  const [numberFmt, setNumberFmt] = useState('Indian (12,34,567)')
  const [dateFmt, setDateFmt] = useState('DD/MM/YYYY')
  const [defaultDash, setDefaultDash] = useState('Dashboard')

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          General Preferences
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Set default formats, currencies, and landing page behaviour.
        </p>
      </div>

      <Selector
        label="Currency Format"
        desc="Primary currency used across all modules."
        options={['INR (₹)', 'USD ($)', 'EUR (€)', 'GBP (£)']}
        value={currency}
        onChange={setCurrency}
      />
      <Selector
        label="Number Format"
        desc="Digit grouping style."
        options={['Indian (12,34,567)', 'International (1,234,567)']}
        value={numberFmt}
        onChange={setNumberFmt}
      />
      <Selector
        label="Date Format"
        desc="Date display convention."
        options={['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD']}
        value={dateFmt}
        onChange={setDateFmt}
      />
      <Selector
        label="Default Landing Page"
        desc="Page shown after login."
        options={['Dashboard', 'Finance', 'Investments', 'AI Advisor', 'Reports']}
        value={defaultDash}
        onChange={setDefaultDash}
      />
    </motion.div>
  )
}

export default PreferencesSettings
