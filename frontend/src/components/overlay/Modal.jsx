import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/utils';

export function CloseButton({ onClick, className, ...props }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn('rounded-full p-1 text-text-muted hover:bg-muted outline-none focus:ring-2 focus:ring-primary/40 cursor-pointer', className)}
      {...props}
    >
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  );
}

export function ModalHeader({ children, className, onClose, ...props }) {
  return (
    <div className={cn('flex items-center justify-between border-b border-border pb-4', className)} {...props}>
      <div className="flex flex-col gap-0.5">{children}</div>
      {onClose && <CloseButton onClick={onClose} />}
    </div>
  );
}

export function ModalBody({ children, className, ...props }) {
  return (
    <div className={cn('py-4 overflow-y-auto max-h-[60vh] scrollbar-none', className)} {...props}>
      {children}
    </div>
  );
}

export function ModalFooter({ children, className, ...props }) {
  return (
    <div className={cn('flex items-center justify-end gap-3 border-t border-border pt-4 mt-auto', className)} {...props}>
      {children}
    </div>
  );
}

export const Modal = ({
  children,
  isOpen = false,
  onClose,
  className,
  size = 'md', // sm, md, lg, xl, full
  drawer = false, // If true, render as slide-out drawer
  drawerSide = 'right', // left, right
  ...props
}) => {
  const modalRef = useRef(null);

  // Close on ESC key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && onClose) onClose();
    };

    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (typeof document === 'undefined') return null;

  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    full: 'max-w-full m-0 h-screen rounded-none',
  };

  const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  };

  const modalVariants = drawer
    ? {
        hidden: { x: drawerSide === 'right' ? '100%' : '-100%' },
        visible: { x: 0, transition: { type: 'spring', stiffness: 350, damping: 40 } },
        exit: { x: drawerSide === 'right' ? '100%' : '-100%' },
      }
    : {
        hidden: { scale: 0.95, opacity: 0 },
        visible: { scale: 1, opacity: 1, transition: { type: 'spring', stiffness: 350, damping: 30 } },
        exit: { scale: 0.95, opacity: 0 },
      };

  const containerClasses = drawer
    ? cn(
        'fixed top-0 bottom-0 bg-card z-50 p-6 flex flex-col border-border',
        drawerSide === 'right' ? 'right-0 border-l shadow-2xl h-full w-full max-w-md' : 'left-0 border-r shadow-2xl h-full w-full max-w-md',
        className
      )
    : cn(
        'w-full bg-card rounded-modal shadow-modal p-6 border border-border flex flex-col relative z-50 clay-surface',
        sizes[size] || sizes.md,
        className
      );

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm"
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={backdropVariants}
            onClick={onClose}
          />
          {/* Modal Container */}
          <motion.div
            ref={modalRef}
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={modalVariants}
            className={containerClasses}
            role="dialog"
            aria-modal="true"
            {...props}
          >
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body
  );
};

export const Dialog = ({ children, ...props }) => <Modal size="md" {...props}>{children}</Modal>;

export const Drawer = ({ children, side = 'right', ...props }) => (
  <Modal drawer drawerSide={side} {...props}>
    {children}
  </Modal>
);

export const ConfirmationDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title = 'Are you sure?',
  description = 'This action cannot be undone.',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'destructive', // primary, destructive
  ...props
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="sm" {...props}>
      <ModalHeader onClose={onClose}>
        <span className="text-lg font-bold text-text-primary">{title}</span>
      </ModalHeader>
      <ModalBody>
        <p className="text-sm text-text-secondary">{description}</p>
      </ModalBody>
      <ModalFooter>
        <button
          onClick={onClose}
          className="px-4 py-2 border border-border rounded-button text-sm font-semibold hover:bg-muted"
        >
          {cancelText}
        </button>
        <button
          onClick={onConfirm}
          className={cn(
            'px-4 py-2 rounded-button text-sm font-semibold text-white shadow-sm',
            variant === 'destructive' ? 'bg-destructive hover:bg-destructive/90' : 'bg-primary hover:bg-primary-hover'
          )}
        >
          {confirmText}
        </button>
      </ModalFooter>
    </Modal>
  );
};

export default Modal;
