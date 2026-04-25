"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6">
      <p className="text-4xl mb-4">😵</p>
      <h2 className="text-xl font-bold mb-2">Что-то пошло не так</h2>
      <p className="text-sm opacity-70 mb-6">{error.message}</p>
      <button onClick={reset} className="btn-primary">
        Попробовать снова
      </button>
    </div>
  );
}