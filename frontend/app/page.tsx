"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authenticate, isAuthenticated } from "@/lib/auth";
import { getInitData, ready, waitForTelegramWebApp } from "@/lib/telegram";

const ONBOARDING_KEY = "kopilka_onboarding_done";
const isOnboardingDone = () => typeof window !== "undefined" && !!localStorage.getItem(ONBOARDING_KEY);

export default function WelcomePage() {
  const router = useRouter();
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const boot = async () => {
      ready();

      if (isAuthenticated()) {
        router.push(isOnboardingDone() ? "/dashboard" : "/onboarding");
        return;
      }

      await waitForTelegramWebApp(1200);
      if (cancelled) return;

      if (!getInitData()) {
        setError("Откройте приложение через Telegram бот");
        return;
      }

      try {
        const success = await authenticate();
        if (cancelled) return;
        if (success) {
          router.push(isOnboardingDone() ? "/dashboard" : "/onboarding");
        } else {
          setError("Ошибка авторизации. Откройте приложение через Telegram бот.");
        }
      } catch (e: any) {
        if (cancelled) return;
        setError(e.message || "Произошла ошибка");
      }
    };

    void boot();
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 text-center">
      {error ? (
        <>
          <p className="text-red-500 text-sm mb-3">{error}</p>
          <p className="text-sm opacity-40">Откройте приложение через Telegram бот</p>
        </>
      ) : (
        <p className="opacity-50">Загрузка...</p>
      )}
    </div>
  );
}
