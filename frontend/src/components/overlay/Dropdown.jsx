import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/utils'

export function MenuGroup({ label, children }) {
  return (
    <div className="flex flex-col gap-1 py-1">
      {label && (
        <span className="px-3 py-1.5 text-xs font-bold text-text-muted select-none">{label}</span>
      )}
      {children}
    </div>
  )
}

export function MenuItem({ children, onClick, className, destructive = false, ...props }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full text-left px-3 py-2 text-sm font-semibold rounded-lg transition-colors duration-150 flex items-center gap-2 select-none cursor-pointer outline-none hover:bg-muted',
        destructive ? 'text-destructive hover:bg-destructive/10' : 'text-text-primary',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export const Dropdown = ({
  children, // Element that opens the dropdown onClick
  menuItems = [], // Array of items or customized nodes
  className,
  align = 'left', // left, right
  direction = 'down', // down, up
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef(null)

  const toggle = () => setIsOpen(!isOpen)

  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick)
    }

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick)
    }
  }, [isOpen])

  return (
    <div ref={containerRef} className="relative inline-block" {...props}>
      <div onClick={toggle} className="inline-block cursor-pointer">
        {children}
      </div>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: direction === 'up' ? -8 : 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: direction === 'up' ? -8 : 8, scale: 0.96 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className={cn(
              'absolute z-40 bg-card border border-border shadow-modal rounded-xl p-1.5 min-w-[180px] clay-surface flex flex-col gap-1',
              align === 'right' ? 'right-0' : 'left-0',
              direction === 'up' ? 'bottom-full mb-2.5' : 'mt-1.5',
              className
            )}
          >
            {React.Children.map(menuItems, (item) => {
              if (React.isValidElement(item)) {
                const orig = item.props.onClick
                return React.cloneElement(item, {
                  onClick: (e) => {
                    try {
                      if (orig) orig(e)
                    } catch (err) {
                      // swallow handler errors so menu still closes

                      console.error(err)
                    }
                    setIsOpen(false)
                  },
                })
              }

              return item
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Dropdown
