"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useCompletion } from "@/lib/hooks";
import { kopecksToRubles } from "@/lib/format";
import ProgressBar from "@/components/ProgressBar";

function CompletionContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const goalIdParam = searchParams.get("goalId");

  const { data: summary, isLoading, error } = useCompletion(goalIdParam ? Number(goalIdParam) : null);

  if (!goalIdParam) {
    router.push("/dashboard");
    return null;
  }

  if (isLoading || !summary) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6">
        <p className="text-red-500 text-sm">{error.message}</p>
        <button onClick={() => router.push("/dashboard")} className="btn-secondary mt-4">
          Назад
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push("/dashboard")} className="text-xl">←</button>
        <h1 className="text-xl font-bold">Результат</h1>
      </div>

      <div className="text-center mb-6">
        <p className="text-5xl mb-3">🎉</p>
        <h2 className="text-2xl font-bold mb-1">{summary.title}</h2>
        <p className="text-lg opacity-70">Цель достигнута!</p>
      </div>

      <ProgressBar
        percent={summary.percent}
        saved={summary.saved_amount}
        target={summary.target_amount}
      />

      <div className="mt-6 grid grid-cols-2 gap-3 text-center">
        <div className="bg-tg-secondary rounded-xl p-4">
          <p className="text-2xl font-bold">{kopecksToRubles(summary.saved_amount)} ₽</p>
          <p className="text-xs opacity-50">Накоплено</p>
        </div>
        <div className="bg-tg-secondary rounded-xl p-4">
          <p className="text-2xl font-bold">{summary.completed_steps}/{summary.total_steps}</p>
          <p className="text-xs opacity-50">Конвертов</p>
        </div>
        <div className="bg-tg-secondary rounded-xl p-4">
          <p className="text-2xl font-bold">{summary.duration_days}</p>
          <p className="text-xs opacity-50">Дней в пути</p>
        </div>
        <div className="bg-tg-secondary rounded-xl p-4">
          <p className="text-2xl font-bold">🔥 {summary.best_streak}</p>
          <p className="text-xs opacity-50">Рекорд серии</p>
        </div>
      </div>

      {summary.achievements.length > 0 && (
        <div className="mt-6">
          <p className="text-sm font-semibold mb-2 opacity-70">Достижения</p>
          <div className="flex flex-wrap gap-2">
            {summary.achievements.map((a) => (
              <span key={a.code} className="bg-tg-secondary rounded-xl px-3 py-2 text-center">
                <span className="text-lg">{a.icon}</span>
                <p className="text-xs">{a.title}</p>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-auto pt-6 flex flex-col gap-3">
        <button
          onClick={() => router.push(`/history?goalId=${summary.goal_id}`)}
          className="btn-primary"
        >
          Посмотреть историю
        </button>
        <button
          onClick={() => router.push(`/share?goalId=${summary.goal_id}`)}
          className="btn-secondary"
        >
          Поделиться результатом
        </button>
        <button
          onClick={() => router.push("/create-goal")}
          className="w-full py-2 rounded-xl text-sm opacity-70 hover:opacity-100 transition-opacity"
        >
          Создать новую цель
        </button>
      </div>
    </div>
  );
}

export default function CompletionPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><p className="opacity-50">Загрузка...</p></div>}>
      <CompletionContent />
    </Suspense>
  );
}