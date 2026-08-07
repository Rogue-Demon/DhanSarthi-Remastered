import React from 'react';
import PieChartCard from './PieChartCard';

/**
 * DonutChartCard Component
 * Reusable Donut chart wrapper setting innerRadius for hollow center visual style.
 */
export function DonutChartCard(props) {
  return <PieChartCard innerRadius={50} outerRadius={80} {...props} />;
}

export default DonutChartCard;
