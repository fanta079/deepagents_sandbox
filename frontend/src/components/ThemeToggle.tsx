"use client";

import { useEffect, useState } from "react";

export function ThemeToggle({ className }: { className?: string }) {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = stored === "dark" || (!stored && prefersDark);
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  const toggle = () => {
    const newDark = !dark;
    setDark(newDark);
    localStorage.setItem("theme", newDark ? "dark" : "light");
    document.documentElement.classList.toggle("dark", newDark);
  };

  return (
    <button
      onClick={toggle}
      className={className}
      title={dark ? "切换到亮色模式" : "切换到暗色模式"}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "0.375rem 0.5rem",
        borderRadius: "0.375rem",
        border: "1px solid hsl(var(--border))",
        background: "transparent",
        cursor: "pointer",
        fontSize: "1rem",
      }}
    >
      {dark ? "☀️" : "🌙"}
    </button>
  );
}
