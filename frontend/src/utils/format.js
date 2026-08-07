export const formatCurrency = (value, locale = 'en-IN', currency = 'INR') => {
  if (isNaN(value)) return '₹0';
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value);
};

export const formatNumber = (value, locale = 'en-IN') => {
  if (isNaN(value)) return '0';
  return new Intl.NumberFormat(locale).format(value);
};

export const formatDate = (date, options = { month: 'short', day: 'numeric', year: 'numeric' }) => {
  if (!date) return '';
  const d = new Date(date);
  return isNaN(d.getTime()) ? '' : d.toLocaleDateString('en-IN', options);
};

export const formatPercent = (value, locale = 'en-IN') => {
  if (isNaN(value)) return '0%';
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 2,
  }).format(value / 100);
};

export default {
  currency: formatCurrency,
  number: formatNumber,
  date: formatDate,
  percent: formatPercent,
};
