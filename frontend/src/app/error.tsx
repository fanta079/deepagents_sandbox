"use client";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-6xl font-bold text-red-500">500</h1>
      <p className="text-xl text-gray-600 dark:text-gray-400 mt-4">
        服务器错误
      </p>
      <button onClick={reset} className="mt-6 text-blue-500 hover:text-blue-600">
        重试
      </button>
    </div>
  );
}
