"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useStep, useCompleteStep, useSkipStep } from "@/lib/hooks";
import { kopecksToRubles } from "@/lib/format";

export default function StepPage() {
  const router = useRouter();
  const params = useParams();
  const stepId = Number(params.id);

  const { data: step, isLoading, error: fetchError } = useStep(isNaN(stepId) ? null : stepId);
  const completeStep = useCompleteStep();
  const skipStep = useSkipStep();
  const [actionError, setActionError] = useState("");
  const isSubmitting = completeStep.isPending || skipStep.isPending;

  useEffect(() => {
    if (fetchError && !isNaN(stepId)) {
      router.push("/dashboard");
    }
  }, [fetchError, router, stepId]);

  if (isNaN(stepId) || isLoading || !step) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
  }

  const isSkipped = step.status === "skipped";
  const isCompleted = step.status === "completed";

  const handleComplete = async () => {
    try {
      setActionError("");
      await completeStep.mutateAsync(step.id);
      router.push("/dashboard");
    } catch (e: any) {
      setActionError(e.message || "Ошибка");
    }
  };

  const handleSkip = async () => {
    try {
      setActionError("");
      await skipStep.mutateAsync(step.id);
      router.push("/dashboard");
    } catch (e: any) {
      setActionError(e.message || "Ошибка");
    }
  };

  return (
    <div className="flex flex-col items-center min-h-screen px-6 py-8">
      <button onClick={() => router.push("/dashboard")} className="self-start text-xl mb-4 opacity-70 hover:opacity-100">
        ←
      </button>

      {isSkipped ? (
        <h1 className="text-xl font-bold mb-2">Пропущенный конверт #{step.step_number}</h1>
      ) : isCompleted ? (
        <h1 className="text-xl font-bold mb-2">Конверт #{step.step_number} ✓</h1>
      ) : (
        <h1 className="text-xl font-bold mb-2">Конверт #{step.step_number}</h1>
      )}

      <p className="text-sm opacity-50 mb-6">из {step.total_steps}</p>

      <div className="bg-tg-secondary rounded-2xl p-8 text-center w-full max-w-sm mb-8">
        <p className="text-sm opacity-50 mb-2">Отложи сегодня</p>
        <p className="text-5xl font-bold mb-2">
          {kopecksToRubles(step.planned_amount)} ₽
        </p>
      </div>

      {actionError && <p className="text-red-500 text-sm mb-4">{actionError}</p>}

      {!isCompleted && (
        <div className="flex flex-col gap-3 w-full max-w-sm">
          <button
            onClick={handleComplete}
            disabled={isSubmitting}
            className="btn-primary"
          >
            {completeStep.isPending ? "Внесение..." : "Внесено"}
          </button>
          {!isSkipped && (
            <button
              onClick={handleSkip}
              disabled={isSubmitting}
              className="btn-ghost"
            >
              {skipStep.isPending ? "Пропуск..." : "Пропустить на сегодня"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}