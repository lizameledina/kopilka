"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authenticate, isAuthenticated } from "@/lib/auth";
import { getInitData, ready, waitForTelegramWebApp } from "@/lib/telegram";

export default function WelcomePage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const boot = async () => {
      // Prefer Telegram boot, but remain functional in browser.
      ready();

      if (isAuthenticated()) {
        router.push("/dashboard");
        return;
      }

      // Wait a bit for Telegram WebApp/initData to become available.
      await waitForTelegramWebApp(1200);
      if (cancelled) return;
      setChecking(false);

      // If we're not inside Telegram (no initData), do not auto-auth. Keep "Начать" as manual fallback.
      if (!getInitData()) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");
      try {
        const success = await authenticate();
        if (cancelled) return;
        if (success) {
          router.push("/dashboard");
        } else {
          setError("Ошибка авторизации. Откройте приложение через Telegram бот.");
        }
      } catch (e: any) {
        if (cancelled) return;
        setError(e.message || "Произошла ошибка");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void boot();
    return () => {
      cancelled = true;
    };
  }, [router]);

  const handleStart = async () => {
    setLoading(true);
    setError("");
    try {
      const success = await authenticate();
      if (success) {
        router.push("/dashboard");
      } else {
        setError("Ошибка авторизации. Откройте приложение через Telegram бот.");
      }
    } catch (e: any) {
      setError(e.message || "Произошла ошибка");
    } finally {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6">
      <div className="text-6xl mb-6">🪙</div>
      <h1 className="text-2xl font-bold mb-2 text-center">Копилка</h1>
      <p className="text-center text-sm mb-8 opacity-70">
        Формируй привычку накопления шаг за шагом
      </p>
      {error && (
        <p className="text-red-500 text-sm mb-4 text-center">{error}</p>
      )}
      <button
        onClick={handleStart}
        disabled={loading}
        className="btn-primary max-w-xs"
      >
        {loading ? "Загрузка..." : "Начать"}
      </button>
    </div>
  );
}
