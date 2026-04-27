"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useReminderSettings, useUpdateReminderSettings } from "@/lib/hooks";

export default function SettingsPage() {
  const router = useRouter();
  const { data: settings, isLoading } = useReminderSettings();
  const updateSettings = useUpdateReminderSettings();

  const [enabled, setEnabled] = useState(false);
  const [time, setTime] = useState("09:00");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (settings) {
      setEnabled(settings.reminders_enabled);
      setTime(settings.reminder_time);
    }
  }, [settings]);

  const handleSave = async () => {
    try {
      setError("");
      await updateSettings.mutateAsync({ reminders_enabled: enabled, reminder_time: time });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e: any) {
      setError(e.message || "Ошибка сохранения");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => router.push("/dashboard")} className="text-xl">
          ←
        </button>
        <h1 className="text-xl font-bold">Настройки</h1>
      </div>

      <div className="goal-card mb-6">
        <h2 className="text-sm font-semibold mb-4 opacity-70">Напоминания</h2>

        <div className="flex items-center justify-between mb-4">
          <span className="text-sm">Получать напоминания</span>
          <button
            onClick={() => setEnabled((v) => !v)}
            className={`relative w-12 h-6 rounded-full transition-colors duration-200 ${
              enabled
                ? "bg-[var(--tg-theme-button-color,#2AABEE)]"
                : "bg-[var(--tg-theme-hint-color,#999)]"
            }`}
          >
            <span
              className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 ${
                enabled ? "translate-x-7" : "translate-x-1"
              }`}
            />
          </button>
        </div>

        {enabled && (
          <div className="flex items-center justify-between">
            <span className="text-sm">Время напоминания</span>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="bg-tg-secondary rounded-lg px-3 py-1.5 text-sm text-[var(--tg-theme-text-color,#000)] border-0 outline-none"
            />
          </div>
        )}
      </div>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      <button
        onClick={handleSave}
        disabled={updateSettings.isPending}
        className="btn-primary"
      >
        {saved ? "Сохранено ✓" : updateSettings.isPending ? "Сохранение..." : "Сохранить"}
      </button>

      <p className="text-xs opacity-40 text-center mt-4 leading-relaxed">
        Напоминание придёт, если ты не открывал конверты в этот день
      </p>
    </div>
  );
}
