"use client";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-6xl font-bold text-gray-900 dark:text-white">404</h1>
      <p className="text-xl text-gray-600 dark:text-gray-400 mt-4">
        页面不存在
      </p>
      <a href="/" className="mt-6 text-blue-500 hover:text-blue-600">
        返回首页
      </a>
    </div>
  );
}
