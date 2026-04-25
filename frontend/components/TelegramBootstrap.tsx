"use client";

import { useEffect } from "react";
import { applyThemeParams, waitForTelegramWebApp } from "@/lib/telegram";

export default function TelegramBootstrap() {
  useEffect(() => {
    let cleanup: (() => void) | null = null;
    let cancelled = false;

    const run = async () => {
      const webapp = await waitForTelegramWebApp(2000);
      if (cancelled || !webapp) return;

      try {
        if (webapp.themeParams) {
          applyThemeParams(webapp.themeParams);
        }

        webapp.ready?.();

        const handler = () => {
          if (!webapp.themeParams) return;
          applyThemeParams(webapp.themeParams);
        };

        if (typeof webapp.onEvent === "function" && typeof webapp.offEvent === "function") {
          webapp.onEvent("themeChanged", handler);
          cleanup = () => webapp.offEvent("themeChanged", handler);
        }
      } catch {
        // ignore bootstrap errors; app should still work in browser
      }
    };

    void run();
    return () => {
      cancelled = true;
      cleanup?.();
    };
  }, []);

  return null;
}

