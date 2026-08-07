import React from 'react';
import { cn, format } from '@/utils';

export const NumericValue = ({
  value,
  className,
  type = 'currency', // currency, number, percent
  locale = 'en-IN',
  currency = 'INR',
  ...props
}) => {
  let formattedValue = value;

  if (type === 'currency') {
    formattedValue = format.currency(value, locale, currency);
  } else if (type === 'number') {
    formattedValue = format.number(value, locale);
  } else if (type === 'percent') {
    formattedValue = format.percent(value, locale);
  }

  return (
    <span
      className={cn('text-numeric font-semibold tabular-nums', className)}
      {...props}
    >
      {formattedValue}
    </span>
  );
};

export default NumericValue;
