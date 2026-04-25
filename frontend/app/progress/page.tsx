"use client";

import { Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  useProgress,
  useGoalAchievements,
  useArchiveGoal,
  useFreezeGoal,
  useUnfreezeGoal,
} from "@/lib/hooks";
import { kopecksToRubles } from "@/lib/format";
import ProgressBar from "@/components/ProgressBar";
import FrozenNotice from "@/components/FrozenNotice";
import GoalStatusBadge from "@/components/GoalStatusBadge";
import GoalActionButton from "@/components/GoalActionButton";
import { isPausedStatus } from "@/lib/goalUi";

function getGridCols(total: number): number {
  if (total <= 25) return 5;
  if (total <= 50) return 7;
  if (total <= 200) return 10;
  return 14;
}

function ProgressContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const goalId = searchParams.get("goalId");

  const archiveGoal = useArchiveGoal();
  const freezeGoal = useFreezeGoal();
  const unfreezeGoal = useUnfreezeGoal();
  const [showActions, setShowActions] = useState(false);
  const [actionError, setActionError] = useState<string>("");

  const numericGoalId = goalId ? Number(goalId) : null;

  const { data: progress, isLoading: loadingProgress, error: progressError } = useProgress(numericGoalId);
  const { data: achievementsData } = useGoalAchievements(numericGoalId);

  const goalAchievements = achievementsData?.goal_achievements || [];
  const globalAchievements = achievementsData?.global_achievements || [];
  const unlockedAchievements = useMemo(
    () => [...globalAchievements, ...goalAchievements].filter((a) => a.unlocked),
    [globalAchievements, goalAchievements]
  );

  if (!numericGoalId) {
    router.push("/dashboard");
    return null;
  }

  if (loadingProgress || !progress) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
  }

  if (progressError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6">
        <p className="text-red-500 text-sm">{progressError.message}</p>
        <button onClick={() => router.push("/dashboard")} className="btn-secondary mt-4">
          Назад
        </button>
      </div>
    );
  }

  const isActive = progress.status === "active";
  const isPaused = isPausedStatus(progress.status);
  const gridCols = getGridCols(progress.total_steps);
  const pendingSteps = progress.total_steps - progress.completed_steps - progress.skipped_steps;

  const confirmDelete = () => confirm("Удалить цель? Это действие нельзя отменить.");
  const confirmFreeze = () =>
    confirm("Заморозить цель? Ты не сможешь вносить накопления, пока не разморозишь её.");

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push("/dashboard")} className="text-xl">
          ←
        </button>
        <h1 className="text-xl font-bold flex-1 truncate">{progress.title}</h1>
        <GoalStatusBadge status={progress.status} />
        <button onClick={() => setShowActions(!showActions)} className="text-sm opacity-50">
          ⋯
        </button>
      </div>

      {actionError && !isPaused ? <p className="text-red-500 text-sm mb-4">{actionError}</p> : null}

      {showActions && (
        <div className="mb-4 goal-card">
          <div className="flex gap-2">
            {isActive && (
              <GoalActionButton
                variant="secondary"
                onClick={async () => {
                  setActionError("");
                  if (!confirmFreeze()) return;
                  try {
                    await freezeGoal.mutateAsync(numericGoalId);
                    setShowActions(false);
                    setActionError("");
                  } catch (e: any) {
                    setActionError(e?.message || "Ошибка");
                  }
                }}
                disabled={freezeGoal.isPending}
              >
                Заморозить
              </GoalActionButton>
            )}
            {isPaused && (
              <GoalActionButton
                variant="primary"
                onClick={async () => {
                  setActionError("");
                  try {
                    await unfreezeGoal.mutateAsync(numericGoalId);
                    setShowActions(false);
                    setActionError("");
                  } catch (e: any) {
                    setActionError(e?.message || "Ошибка");
                  }
                }}
                disabled={unfreezeGoal.isPending}
              >
                Разморозить
              </GoalActionButton>
            )}
            <GoalActionButton
              variant="danger"
              onClick={async () => {
                setActionError("");
                if (!confirmDelete()) return;
                try {
                  await archiveGoal.mutateAsync(numericGoalId);
                  setActionError("");
                  router.push("/dashboard");
                } catch (e: any) {
                  setActionError(e?.message || "Ошибка");
                }
              }}
              disabled={archiveGoal.isPending}
            >
              Удалить
            </GoalActionButton>
          </div>
        </div>
      )}

      {isPaused && (
        <div className="mb-4">
          <FrozenNotice
            onUnfreeze={async () => {
              setActionError("");
              try {
                await unfreezeGoal.mutateAsync(numericGoalId);
                setActionError("");
              } catch (e: any) {
                setActionError(e?.message || "Ошибка");
              }
            }}
            error={actionError}
          />
        </div>
      )}

      <ProgressBar percent={progress.percent} saved={progress.saved_amount} target={progress.target_amount} />

      {unlockedAchievements.length > 0 && (
        <div className="mt-4 goal-card">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs opacity-50">Достижения</p>
            <button
              onClick={() => router.push(`/achievements?goalId=${progress.goal_id}`)}
              className="text-xs opacity-50 hover:opacity-100"
            >
              Все →
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {unlockedAchievements.slice(0, 5).map((a) => (
              <span key={`${a.code}-${a.goal_id}`} className="text-lg" title={a.title}>
                {a.icon}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 gap-3 text-center">
        <div className="goal-card">
          <p className="text-2xl font-bold">{progress.completed_steps}</p>
          <p className="text-xs opacity-50">Выполнено</p>
        </div>
        <div className="goal-card">
          <p className="text-2xl font-bold">{pendingSteps}</p>
          <p className="text-xs opacity-50">Впереди</p>
        </div>
      </div>

      <div className={`mt-6 flex-1 overflow-y-auto ${isPaused ? "frozen-surface" : ""}`}>
        <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))` }}>
          {progress.steps.map((step) => {
            const canOpen = !isPaused && (step.status === "skipped" || step.status === "pending");
            const cellClass =
              step.status === "completed"
                ? "bg-green-500 text-white"
                : step.status === "skipped"
                  ? `bg-gray-400 text-white ${canOpen ? "cursor-pointer" : ""}`
                  : `bg-tg-secondary opacity-30 ${canOpen ? "cursor-pointer" : ""}`;
            return (
              <div
                key={step.id}
                onClick={canOpen ? () => router.push(`/step/${step.id}`) : undefined}
                className={`aspect-square rounded flex items-center justify-center text-xs ${cellClass}`}
                title={`Шаг ${step.step_number}: ${kopecksToRubles(step.planned_amount)} ₽`}
              >
                {step.step_number}
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-4 flex gap-3">
        <button
          onClick={() => router.push(`/history?goalId=${progress.goal_id}`)}
          className="flex-1 py-2 rounded-xl text-sm bg-tg-secondary text-center"
        >
          История
        </button>
        <button
          onClick={() => router.push(`/share?goalId=${progress.goal_id}`)}
          className="flex-1 py-2 rounded-xl text-sm bg-tg-secondary text-center"
        >
          Поделиться
        </button>
      </div>
    </div>
  );
}

export default function ProgressPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <p className="opacity-50">Загрузка...</p>
        </div>
      }
    >
      <ProgressContent />
    </Suspense>
  );
}
