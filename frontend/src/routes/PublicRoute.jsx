import React from 'react';
import { Navigate } from 'react-router-dom';
import { STORAGE_KEYS } from '@/constants';

export function PublicRoute({ children }) {
  // Real implementation:
  // const token = localStorage.getItem(STORAGE_KEYS.AUTH);
  // if (token) return <Navigate to="/dashboard" replace />;
  
  return children;
}

export default PublicRoute;
