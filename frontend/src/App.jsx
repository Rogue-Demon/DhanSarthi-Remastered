import React from 'react';
import { AppProviders, AppRouter } from '@/app/index';

export default function App() {
  return (
    <AppProviders>
      <AppRouter />
    </AppProviders>
  );
}
