"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { messages, Locale, MessageSchema } from "./messages";

type NestedKeyOf<T> = T extends object
  ? {
      [K in keyof T]: K extends string
        ? T[K] extends object
          ? `${K}.${NestedKeyOf<T[K]>}`
          : K
        : never;
    }[keyof T]
  : never;

type TranslationKey = NestedKeyOf<MessageSchema>;

function getNestedValue(obj: any, path: string): string {
  return path.split(".").reduce((acc, part) => acc && acc[part], obj) ?? path;
}

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("zh");

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("locale", newLocale);
    }
  }, []);

  // 从 localStorage 恢复
  React.useEffect(() => {
    if (typeof localStorage !== "undefined") {
      const saved = localStorage.getItem("locale") as Locale | null;
      if (saved && (saved === "zh" || saved === "en")) {
        setLocaleState(saved);
      }
    }
  }, []);

  const t = useCallback(
    (key: TranslationKey): string => {
      const dict = messages[locale];
      return getNestedValue(dict, key as string);
    },
    [locale]
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useTranslation() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useTranslation must be used within I18nProvider");
  return ctx;
}
