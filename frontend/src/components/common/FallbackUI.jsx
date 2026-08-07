export default function FallbackUI({ error, resetError }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 text-center">
      <div className="max-w-md rounded-2xl bg-white p-8 shadow-md">
        <h1 className="text-2xl font-bold text-slate-800">Something went wrong</h1>
        <p className="mt-4 text-slate-600">
          {error?.message || 'An unexpected application error occurred.'}
        </p>
        <button
          onClick={resetError}
          className="mt-6 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700 transition"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}
