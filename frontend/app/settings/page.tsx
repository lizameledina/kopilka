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
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveError, setSaveError] = useState("");

  useEffect(() => {
    if (settings) {
      setEnabled(settings.reminders_enabled);
      setTime(settings.reminder_time);
    }
  }, [settings]);

  const handleSave = async () => {
    setSaveState("saving");
    setSaveError("");
    try {
      await updateSettings.mutateAsync({ reminders_enabled: enabled, reminder_time: time });
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 2000);
    } catch {
      setSaveState("error");
      setSaveError("Не удалось сохранить настройки");
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
        <button onClick={() => router.push("/dashboard")} className="text-xl opacity-70 hover:opacity-100">
          ←
        </button>
        <h1 className="text-xl font-bold">Настройки</h1>
      </div>

      <div className="goal-card mb-6">
        <p className="text-xs font-semibold opacity-50 mb-4 uppercase tracking-wide">Напоминания</p>

        <div className="flex items-center justify-between py-1">
          <span className="text-sm">Получать напоминания</span>
          <button
            onClick={() => setEnabled((v) => !v)}
            aria-label={enabled ? "Выключить напоминания" : "Включить напоминания"}
            className={`relative shrink-0 w-11 h-6 rounded-full transition-colors duration-200 ${
              enabled
                ? "bg-[var(--tg-theme-button-color,#2AABEE)]"
                : "bg-[var(--tg-theme-hint-color,#999)]"
            }`}
          >
            <span
              className={`absolute top-[3px] w-[18px] h-[18px] bg-white rounded-full shadow transition-transform duration-200 ${
                enabled ? "translate-x-[22px]" : "translate-x-[3px]"
              }`}
            />
          </button>
        </div>

        {enabled && (
          <>
            <div className="h-px bg-white/10 my-3" />
            <div className="flex items-center justify-between py-1">
              <span className="text-sm">Время напоминания</span>
              <input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="bg-transparent text-sm text-right outline-none cursor-pointer"
                style={{ colorScheme: "auto" }}
              />
            </div>
          </>
        )}
      </div>

      {saveState === "error" && (
        <p className="text-red-500 text-sm mb-4">{saveError}</p>
      )}

      <button
        onClick={handleSave}
        disabled={saveState === "saving"}
        className="btn-primary"
      >
        {saveState === "saving"
          ? "Сохранение..."
          : saveState === "saved"
          ? "Сохранено ✓"
          : "Сохранить"}
      </button>

      <p className="text-xs opacity-40 text-center mt-6 leading-relaxed max-w-xs mx-auto">
        Напоминание придёт, если ты не открывал конверты в этот день
      </p>
    </div>
  );
}
