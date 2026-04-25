"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useShareSummary } from "@/lib/hooks";
import { kopecksToRubles } from "@/lib/format";
import ProgressBar from "@/components/ProgressBar";
import { isPausedStatus } from "@/lib/goalUi";

function ShareContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const goalIdParam = searchParams.get("goalId");

  const { data: summary, isLoading, error } = useShareSummary(goalIdParam ? Number(goalIdParam) : null);

  if (!goalIdParam) {
    router.push("/dashboard");
    return null;
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6">
        {error && <p className="text-red-500 text-sm">{error.message}</p>}
        <button onClick={() => router.push("/dashboard")} className="btn-secondary mt-4">
          Назад
        </button>
      </div>
    );
  }

  const isCompleted = summary.status === "completed";
  const isPaused = isPausedStatus(summary.status);

  const stateIcon = isCompleted ? "🏆" : isPaused ? "❄️" : "🪙";
  const stateText = isCompleted ? "Цель достигнута!" : isPaused ? "На паузе" : "В процессе";

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.back()} className="text-xl">
          ←
        </button>
        <h1 className="text-xl font-bold">Поделиться</h1>
      </div>

      <div id="share-card" className="bg-gradient-to-br from-purple-900 to-indigo-900 rounded-2xl p-6 text-white shadow-lg">
        <div className="text-center mb-4">
          <p className="text-3xl mb-2">{stateIcon}</p>
          <h2 className="text-xl font-bold">{summary.title}</h2>
          <p className="text-sm opacity-70 mt-1">{stateText}</p>
        </div>

        <ProgressBar percent={summary.percent} saved={summary.saved_amount} target={summary.target_amount} />

        <div className="mt-4 grid grid-cols-2 gap-3 text-center text-sm">
          <div className="bg-white/10 rounded-xl p-3">
            <p className="font-bold text-lg">{kopecksToRubles(summary.saved_amount)} ₽</p>
            <p className="opacity-60">Накоплено</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3">
            <p className="font-bold text-lg">
              {summary.completed_steps}/{summary.total_steps}
            </p>
            <p className="opacity-60">Конвертов</p>
          </div>
          {isCompleted && summary.duration_days != null && (
            <div className="bg-white/10 rounded-xl p-3">
              <p className="font-bold text-lg">{summary.duration_days}</p>
              <p className="opacity-60">Дней</p>
            </div>
          )}
          {summary.best_streak > 0 && (
            <div className="bg-white/10 rounded-xl p-3">
              <p className="font-bold text-lg">🔥 {summary.best_streak}</p>
              <p className="opacity-60">Рекорд серии</p>
            </div>
          )}
        </div>
      </div>

      <div className="mt-auto pt-6 flex flex-col gap-3">
        <button
          onClick={() => {
            const header = isCompleted ? "🏆 Цель достигнута!" : isPaused ? "❄️ На паузе" : "🪙 В процессе";
            const text =
              `${header}\n` +
              `${summary.title}\n` +
              `${kopecksToRubles(summary.saved_amount)} / ${kopecksToRubles(summary.target_amount)} ₽ (${summary.percent}%)\n` +
              `Конвертов: ${summary.completed_steps}/${summary.total_steps}` +
              (isCompleted && summary.duration_days != null ? `\nДней: ${summary.duration_days}` : "") +
              (summary.best_streak > 0 ? `\nРекорд серии: ${summary.best_streak} дней` : "");

            if (navigator.share) {
              navigator.share({ text }).catch(() => {});
            } else {
              navigator.clipboard.writeText(text).then(() => alert("Скопировано!"));
            }
          }}
          className="btn-primary"
        >
          Поделиться
        </button>
        <button
          onClick={() => router.back()}
          className="w-full py-2 rounded-xl text-sm opacity-70 hover:opacity-100 transition-opacity"
        >
          Назад
        </button>
      </div>
    </div>
  );
}

export default function SharePage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <p className="opacity-50">Загрузка...</p>
        </div>
      }
    >
      <ShareContent />
    </Suspense>
  );
}

