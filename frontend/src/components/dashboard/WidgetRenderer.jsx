import React from 'react';
import { getWidget } from '@/config';
import WidgetPlaceholder from './WidgetPlaceholder';
import {
  StudentAllowanceWidget,
  StudentSavingsWidget,
  StudentEducationWidget,
  StudentBudgetWidget,
  StudentGoalsWidget,
  ProfessionalSalaryWidget,
  ProfessionalExpensesWidget,
  ProfessionalNetworthWidget,
  ProfessionalInvestmentsWidget,
  ProfessionalAssetsWidget,
  BusinessRevenueWidget,
  BusinessProfitWidget,
  BusinessCashFlowWidget,
  BusinessPayrollWidget,
  BusinessInventoryWidget,
} from './widgets';

// Map design token sizes to responsive grid column spans
const SIZE_MAP = {
  sm: 'lg:col-span-4 md:col-span-2 col-span-1',
  md: 'lg:col-span-6 md:col-span-2 col-span-1',
  lg: 'lg:col-span-8 md:col-span-2 col-span-1',
  xl: 'lg:col-span-12 md:col-span-2 col-span-1',
};

// Map widget IDs to their actual rich UI React components
const WIDGET_COMPONENTS = {
  // Student Widgets
  'student-allowance': StudentAllowanceWidget,
  'student-savings': StudentSavingsWidget,
  'student-education': StudentEducationWidget,
  'student-budget': StudentBudgetWidget,
  'student-goals': StudentGoalsWidget,

  // Working Professional Widgets
  'professional-salary': ProfessionalSalaryWidget,
  'professional-expenses': ProfessionalExpensesWidget,
  'professional-networth': ProfessionalNetworthWidget,
  'professional-investments': ProfessionalInvestmentsWidget,
  'professional-assets': ProfessionalAssetsWidget,

  // Business Widgets
  'business-revenue': BusinessRevenueWidget,
  'business-profit': BusinessProfitWidget,
  'business-cashflow': BusinessCashFlowWidget,
  'business-payroll': BusinessPayrollWidget,
  'business-inventory': BusinessInventoryWidget,
};

/**
 * WidgetRenderer Component
 *
 * Resolves widget configurations dynamically from the centralized widget registry
 * and maps the size parameters to CSS 12-column grid spans.
 * Mounts the actual rich UI components if registered; otherwise,
 * falls back to WidgetPlaceholder.
 */
export function WidgetRenderer({ widgetId, size = 'md', ...props }) {
  const widget = getWidget(widgetId);

  if (!widget) {
    console.error(`Widget with ID "${widgetId}" is not registered in widgetRegistry.`);
    return null;
  }

  // Resolve responsive grid class
  const sizeClass = SIZE_MAP[size] || SIZE_MAP.md;

  // Resolve actual component if defined
  const ActualWidgetComponent = WIDGET_COMPONENTS[widgetId];

  if (ActualWidgetComponent) {
    return (
      <ActualWidgetComponent
        widget={widget}
        sizeClass={sizeClass}
        {...props}
      />
    );
  }

  // Fallback to stylized Coming Soon placeholder card
  return (
    <WidgetPlaceholder
      widget={widget}
      sizeClass={sizeClass}
      {...props}
    />
  );
}

export default WidgetRenderer;
