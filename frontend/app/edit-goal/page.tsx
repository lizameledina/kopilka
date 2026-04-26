"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useGoals, useEditGoalPreview, useEditGoal, useResetGoal } from "@/lib/hooks";
import { kopecksToRubles, rublesToKopecks } from "@/lib/format";
import type { DistributionType, EditPreviewResponse } from "@/lib/types";

const DISTRIBUTIONS: { value: DistributionType; label: string }[] = [
  { value: "equal", label: "Равномерно" },
  { value: "random", label: "Случайно" },
  { value: "ascending", label: "По возрастанию" },
  { value: "descending", label: "По убыванию" },
];

type FormState = "idle" | "preview_loading" | "preview_shown" | "applying" | "done";

function EditGoalContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const goalIdParam = searchParams.get("goalId");
  const goalId = goalIdParam ? Number(goalIdParam) : null;

  const { data: goals } = useGoals();
  const goal = goals?.find(g => g.id === goalId);

  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [stepCount, setStepCount] = useState<string>("");
  const [distribution, setDistribution] = useState<DistributionType>("equal");
  const [formState, setFormState] = useState<FormState>("idle");
  const [preview, setPreview] = useState<EditPreviewResponse | null>(null);
  const [error, setError] = useState("");
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const editPreview = useEditGoalPreview();
  const editGoal = useEditGoal();
  const resetGoal = useResetGoal();

  useEffect(() => {
    if (goal) {
      setTitle(goal.title);
      setAmount((goal.target_amount / 100).toString());
      setStepCount(goal.total_steps.toString());
    }
  }, [goal]);

  if (!goalId || !goal) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Цель не найдена</p>
      </div>
    );
  }

  const buildRequestBody = () => {
    const body: Record<string, unknown> = {};
    if (title.trim() !== goal.title) body.title = title.trim();
    const rubles = parseFloat(amount);
    if (!isNaN(rubles)) {
      const kopecks = rublesToKopecks(rubles);
      if (kopecks !== goal.target_amount) body.target_amount = kopecks;
    }
    const count = parseInt(stepCount, 10);
    if (!isNaN(count) && count !== goal.total_steps) body.step_count = count;
    if (distribution !== (goal as any).distribution) body.distribution = distribution;
    return body;
  };

  const handlePreview = async () => {
    setError("");
    const rubles = parseFloat(amount);
    if (!title.trim()) { setError("Введите название"); return; }
    if (isNaN(rubles) || rubles < 1) { setError("Некорректная сумма"); return; }
    const count = parseInt(stepCount, 10);
    if (isNaN(count) || count < 1 || count > 365) { setError("Количество конвертов: от 1 до 365"); return; }

    setFormState("preview_loading");
    try {
      const body = buildRequestBody();
      const result = await editPreview.mutateAsync({ goalId, body });
      setPreview(result);
      setFormState("preview_shown");
    } catch (e: any) {
      setError(e.message || "Ошибка");
      setFormState("idle");
    }
  };

  const handleApply = async () => {
    if (!preview || preview.error) return;
    setFormState("applying");
    try {
      const body = buildRequestBody();
      const updated = await editGoal.mutateAsync({ goalId, body });
      router.push(`/dashboard?goalId=${updated.id}`);
    } catch (e: any) {
      setError(e.message || "Ошибка применения изменений");
      setFormState("preview_shown");
    }
  };

  const handleReset = async () => {
    setShowResetConfirm(false);
    try {
      const count = parseInt(stepCount, 10);
      const rubles = parseFloat(amount);
      const updated = await resetGoal.mutateAsync({
        goalId,
        body: {
          distribution,
          step_count: isNaN(count) ? goal.total_steps : count,
          target_amount: isNaN(rubles) ? goal.target_amount : rublesToKopecks(rubles),
        },
      });
      router.push(`/dashboard?goalId=${updated.id}`);
    } catch (e: any) {
      setError(e.message || "Ошибка сброса цели");
    }
  };

  const isLoading = formState === "preview_loading" || formState === "applying" || resetGoal.isPending;

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.back()} className="text-xl opacity-70 hover:opacity-100">←</button>
        <h1 className="text-xl font-bold">Редактировать цель</h1>
      </div>

      <div className="mb-4">
        <label className="block text-sm mb-1 opacity-70">Название</label>
        <input
          type="text"
          value={title}
          onChange={(e) => { setTitle(e.target.value); setFormState("idle"); setPreview(null); }}
          className="input-field"
          disabled={isLoading}
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm mb-1 opacity-70">Сумма цели (₽)</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => { setAmount(e.target.value); setFormState("idle"); setPreview(null); }}
          min="1"
          step="100"
          className="input-field"
          disabled={isLoading}
        />
        <p className="text-xs mt-1 opacity-40">Накоплено: {kopecksToRubles(goal.saved_amount)} ₽</p>
      </div>

      <div className="mb-4">
        <label className="block text-sm mb-1 opacity-70">Количество конвертов</label>
        <input
          type="text"
          inputMode="numeric"
          value={stepCount}
          onChange={(e) => { setStepCount(e.target.value.replace(/[^0-9]/g, "")); setFormState("idle"); setPreview(null); }}
          onBlur={() => {
            const n = parseInt(stepCount, 10);
            if (isNaN(n) || n < 1) setStepCount("1");
            else if (n > 365) setStepCount("365");
          }}
          className="input-field"
          disabled={isLoading}
        />
        <p className="text-xs mt-1 opacity-50">От 1 до 365</p>
      </div>

      <div className="mb-6">
        <label className="block text-sm mb-2 opacity-70">Распределение</label>
        <div className="grid grid-cols-2 gap-2">
          {DISTRIBUTIONS.map((d) => (
            <button
              key={d.value}
              onClick={() => { setDistribution(d.value); setFormState("idle"); setPreview(null); }}
              disabled={isLoading}
              className={distribution === d.value ? "btn-primary py-2 text-sm" : "btn-secondary py-2 text-sm"}
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {preview && formState === "preview_shown" && (
        <div className="bg-tg-secondary rounded-xl p-4 mb-4">
          <p className="text-sm font-semibold mb-3 opacity-70">Предпросмотр изменений</p>
          {preview.error ? (
            <p className="text-red-400 text-sm">{preview.error}</p>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm mb-3">
                <span className="opacity-50">Было</span>
                <span className="opacity-50">Станет</span>
                {preview.was.title !== preview.will_be.title && (
                  <>
                    <span className="line-through opacity-40">{preview.was.title}</span>
                    <span className="font-medium">{preview.will_be.title}</span>
                  </>
                )}
                {preview.was.target_amount !== preview.will_be.target_amount && (
                  <>
                    <span className="line-through opacity-40">{kopecksToRubles(preview.was.target_amount)} ₽</span>
                    <span className="font-medium">{kopecksToRubles(preview.will_be.target_amount)} ₽</span>
                  </>
                )}
                {preview.was.step_count !== preview.will_be.step_count && (
                  <>
                    <span className="line-through opacity-40">{preview.was.step_count} конв.</span>
                    <span className="font-medium">{preview.will_be.step_count} конв.</span>
                  </>
                )}
              </div>
              <p className="text-xs opacity-50">
                Осталось: {preview.will_be.remaining_steps} конвертов на {kopecksToRubles(preview.will_be.remaining_amount)} ₽
              </p>
              {preview.warnings.map((w, i) => (
                <p key={i} className="text-yellow-400 text-xs mt-1">⚠ {w}</p>
              ))}
            </>
          )}
        </div>
      )}

      {formState === "preview_shown" && !preview?.error ? (
        <button
          onClick={handleApply}
          disabled={isLoading}
          className="btn-primary mb-3"
        >
          {formState === "applying" ? "Применяем..." : "Применить изменения"}
        </button>
      ) : (
        <button
          onClick={handlePreview}
          disabled={isLoading}
          className="btn-primary mb-3"
        >
          {formState === "preview_loading" ? "Проверяем..." : "Посмотреть изменения"}
        </button>
      )}

      <div className="mt-8 border-t border-white/10 pt-6">
        <p className="text-xs opacity-50 mb-3">Опасные действия</p>
        <button
          onClick={() => setShowResetConfirm(true)}
          disabled={isLoading}
          className="w-full py-3 rounded-xl text-sm font-medium text-red-400 border border-red-400/30 hover:bg-red-400/10 transition-colors"
        >
          Начать с нуля
        </button>
        <p className="text-xs opacity-40 mt-2 text-center">
          Удалит весь прогресс и достижения этой цели
        </p>
      </div>

      {showResetConfirm && (
        <div className="fixed inset-0 bg-black/60 flex items-end z-50" onClick={() => setShowResetConfirm(false)}>
          <div className="w-full bg-tg-secondary rounded-t-2xl p-6" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-2">Начать с нуля?</h2>
            <p className="text-sm opacity-60 mb-6">
              Весь прогресс, депозиты и достижения этой цели будут удалены. Отменить нельзя.
            </p>
            <button onClick={handleReset} className="w-full py-3 rounded-xl bg-red-500 text-white font-semibold mb-3">
              Да, сбросить
            </button>
            <button onClick={() => setShowResetConfirm(false)} className="w-full py-3 rounded-xl btn-secondary">
              Отмена
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function EditGoalPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><p className="opacity-50">Загрузка...</p></div>}>
      <EditGoalContent />
    </Suspense>
  );
}
