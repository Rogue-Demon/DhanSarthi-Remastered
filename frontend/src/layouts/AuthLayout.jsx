import React from 'react';
import { Outlet } from 'react-router-dom';

export default function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="w-full max-w-md bg-card p-8 rounded-2xl shadow-md border border-border">
        <Outlet />
      </div>
    </div>
  );
}
