import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 text-center">
      <h1 className="text-4xl font-bold text-slate-800">404</h1>
      <p className="mt-2 text-xl font-semibold text-slate-600">Page Not Found</p>
      <p className="mt-2 text-slate-500">The page you are looking for does not exist.</p>
      <Link
        to="/dashboard"
        className="mt-6 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700 transition"
      >
        Go to Dashboard
      </Link>
    </div>
  );
}
