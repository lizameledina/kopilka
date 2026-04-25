"use client";

import { useEffect, useState } from "react";
import { getThemeParams } from "@/lib/telegram";

export function useTelegramTheme() {
  const [theme, setTheme] = useState<Record<string, string>>({});

  useEffect(() => {
    setTheme(getThemeParams());
  }, []);

  return theme;
}