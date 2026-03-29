"use client";

import { useTranslation } from "@/i18n/I18nProvider";
import { Globe } from "lucide-react";
import { cn } from "@/lib/utils";

export function LanguageSwitcher({ className }: { className?: string }) {
  const { locale, setLocale } = useTranslation();

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <Globe className="h-4 w-4 text-muted-foreground" />
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as "zh" | "en")}
        className="bg-transparent text-sm text-muted-foreground border-none outline-none cursor-pointer hover:text-foreground transition-colors"
      >
        <option value="zh">中文</option>
        <option value="en">EN</option>
      </select>
    </div>
  );
}
