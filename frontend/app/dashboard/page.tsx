"use client";

import React, { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useGoals, useTodaySteps, useStreak, useAchievements, useUnfreezeGoal } from "@/lib/hooks";
import { kopecksToRubles } from "@/lib/format";
import ProgressBar from "@/components/ProgressBar";
import FrozenNotice from "@/components/FrozenNotice";
import GoalStatusBadge from "@/components/GoalStatusBadge";
import { isPausedStatus } from "@/lib/goalUi";
import GoalCard from "@/components/GoalCard";
import GoalActionButton from "@/components/GoalActionButton";

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const { data: allGoals = [], isLoading: goalsLoading, isFetching: goalsFetching } = useGoals();
  const { data: todaySteps = [], isLoading: stepsLoading } = useTodaySteps();
  const { data: streak } = useStreak();
  const { data: achievements = [] } = useAchievements();
  const unfreezeGoal = useUnfreezeGoal();

  const goals = useMemo(
    () => allGoals.filter((g) => g.status === "active" || isPausedStatus(g.status)),
    [allGoals]
  );
  const activeGoals = useMemo(() => goals.filter((g) => g.status === "active"), [goals]);
  const pausedGoals = useMemo(() => goals.filter((g) => isPausedStatus(g.status)), [goals]);

  const goalIdFromUrl = searchParams.get("goalId");
  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(
    goalIdFromUrl ? Number(goalIdFromUrl) : null
  );
  const [showGoalList, setShowGoalList] = useState(false);
  const [actionError, setActionError] = useState<string>("");

  useEffect(() => {
    if (goals.length > 0 && !selectedGoalId) {
      const preferred = goals.find((g) => g.status === "active") || goals[0];
      setSelectedGoalId(preferred.id);
    }
  }, [goals, selectedGoalId]);

  if (goalsLoading || goalsFetching) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
  }

  if (goals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6">
        <p className="text-2xl mb-4">🪙</p>
        <p className="text-lg font-bold mb-2">Нет целей в работе</p>
        <p className="text-sm opacity-70 mb-6 text-center">
          Создай цель, чтобы начать формировать привычку накопления.
        </p>
        <button onClick={() => router.push("/create-goal")} className="btn-primary max-w-xs">
          Создать цель
        </button>
      </div>
    );
  }

  if (activeGoals.length === 0) {
    return (
      <div className="flex flex-col min-h-screen px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold">Нет активных целей</h1>
          <button onClick={() => router.push("/goals")} className="text-sm opacity-70 hover:opacity-100">
            Все цели
          </button>
        </div>

        {actionError ? <p className="text-red-500 text-sm mb-4">{actionError}</p> : null}

        <div className="goal-card mb-6 text-center">
          <p className="text-sm opacity-70">
            Создай новую цель или разморозь одну из замороженных.
          </p>
          <button onClick={() => router.push("/create-goal")} className="btn-primary mt-4">
            Создать цель
          </button>
        </div>

        {pausedGoals.length > 0 ? (
          <div className="flex flex-col gap-3">
            {pausedGoals.map((goal) => (
              <GoalCard
                key={goal.id}
                goal={goal}
                onOpen={() => router.push(`/progress?goalId=${goal.id}`)}
                actions={
                  <div className="flex gap-2">
                    <GoalActionButton
                      variant="primary"
                      onClick={async () => {
                        setActionError("");
                        try {
                          await unfreezeGoal.mutateAsync(goal.id);
                        } catch (e: any) {
                          setActionError(e?.message || "Ошибка");
                        }
                      }}
                      disabled={unfreezeGoal.isPending}
                    >
                      Разморозить
                    </GoalActionButton>
                    <GoalActionButton
                      variant="secondary"
                      onClick={() => router.push(`/progress?goalId=${goal.id}`)}
                    >
                      Открыть
                    </GoalActionButton>
                  </div>
                }
              />
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  const selectedGoal = goals.find((g) => g.id === selectedGoalId) || activeGoals[0];
  const isActive = selectedGoal.status === "active";
  const isPaused = isPausedStatus(selectedGoal.status);

  const todayItem = isActive
    ? todaySteps.find((t) => t.goal_id === selectedGoal.id)
    : undefined;
  const step = todayItem?.step;

  const percent =
    selectedGoal.target_amount > 0
      ? Math.round((selectedGoal.saved_amount / selectedGoal.target_amount) * 1000) / 10
      : 0;

  const unlockedAchievements = achievements.filter(
    (a) => a.unlocked && (a.goal_id === null || a.goal_id === selectedGoal.id)
  );
  const recentAchievements = unlockedAchievements.slice(-3).reverse();

  const loading = stepsLoading || (isActive && !todayItem);

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center justify-between mb-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold truncate">{selectedGoal.title}</h1>
            <GoalStatusBadge status={selectedGoal.status} />
          </div>
        </div>

        {goals.length > 1 && (
          <button onClick={() => setShowGoalList(!showGoalList)} className="shrink-0 text-lg opacity-70 hover:opacity-100 ml-2">
            ▾
          </button>
        )}
      </div>

      <div className="bg-tg-secondary rounded-2xl flex mb-4">
        <button
          onClick={() => router.push(`/progress?goalId=${selectedGoal.id}`)}
          className="flex-1 flex flex-col items-center gap-1 py-3 rounded-2xl opacity-70 hover:opacity-100 transition-opacity"
        >
          <span className="text-base">📊</span>
          <span className="text-xs font-medium">Прогресс</span>
        </button>
        <button
          onClick={() => router.push("/goals")}
          className="flex-1 flex flex-col items-center gap-1 py-3 rounded-2xl opacity-70 hover:opacity-100 transition-opacity"
        >
          <span className="text-base">🎯</span>
          <span className="text-xs font-medium">Все цели</span>
        </button>
        <button
          onClick={() => router.push(selectedGoal ? `/achievements?goalId=${selectedGoal.id}` : "/achievements")}
          className="flex-1 flex flex-col items-center gap-1 py-3 rounded-2xl opacity-70 hover:opacity-100 transition-opacity"
        >
          <span className="text-base">⭐</span>
          <span className="text-xs font-medium">Достижения</span>
        </button>
      </div>

      {streak && streak.current_streak > 0 && (
        <div className="bg-tg-secondary rounded-xl p-3 mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">🔥</span>
            <span className="text-sm font-semibold">Серия: {streak.current_streak} {streak.current_streak === 1 ? "день" : streak.current_streak >= 2 && streak.current_streak <= 4 ? "дня" : "дней"}</span>
          </div>
          {streak.best_streak > streak.current_streak && (
            <span className="text-xs opacity-50">Рекорд: {streak.best_streak}</span>
          )}
        </div>
      )}

      {showGoalList && goals.length > 1 && (
        <div className="mb-4 goal-card">
          <div className="flex flex-col gap-2">
            {goals.map((g) => (
              <button
                key={g.id}
                onClick={() => {
                  setSelectedGoalId(g.id);
                  setShowGoalList(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-xl ${
                  g.id === selectedGoal.id ? "bg-black/10" : "opacity-80 hover:opacity-100"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate">{g.title}</span>
                  <span className="text-xs opacity-60 whitespace-nowrap">
                    {kopecksToRubles(g.saved_amount)}/{kopecksToRubles(g.target_amount)} ₽
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className={isPaused ? "frozen-surface" : ""}>
        <ProgressBar percent={percent} saved={selectedGoal.saved_amount} target={selectedGoal.target_amount} />
      </div>

      {actionError && !isPaused ? <p className="text-red-500 text-sm mt-3">{actionError}</p> : null}

      <div className="mt-6 flex-1">
        {selectedGoal.status === "completed" ? (
          <div className="goal-card text-center">
            <p className="text-3xl mb-2">🎉</p>
            <p className="text-lg font-bold">Цель достигнута!</p>
            <button onClick={() => router.push(`/completion?goalId=${selectedGoal.id}`)} className="btn-primary mt-4">
              Посмотреть результат
            </button>
          </div>
        ) : isPaused ? (
          <FrozenNotice
            onUnfreeze={async () => {
              setActionError("");
              try {
                await unfreezeGoal.mutateAsync(selectedGoal.id);
              } catch (e: any) {
                setActionError(e?.message || "Ошибка");
              }
            }}
            error={actionError}
          />
        ) : loading ? (
          <div className="goal-card text-center">
            <p className="opacity-50">Загрузка...</p>
          </div>
        ) : step ? (
          <div className="goal-card">
            {step.status === "skipped" ? (
              <>
                <p className="text-sm opacity-50 mb-1">
                  Пропущенный конверт #{step.step_number} из {step.total_steps}
                </p>
                <p className="text-sm opacity-70 mt-2">Верни пропущенный конверт и внеси накопление</p>
              </>
            ) : (
              <>
                <p className="text-sm opacity-50 mb-1">
                  Конверт #{step.step_number} из {step.total_steps}
                </p>
                <p className="text-sm opacity-70 mt-2">Открой, чтобы узнать сумму</p>
              </>
            )}
            <div className="mt-4">
              <button onClick={() => router.push(`/step/${step.id}`)} className="btn-primary">
                {step.status === "skipped" ? "Вернуть конверт" : "Открыть конверт"}
              </button>
            </div>
          </div>
        ) : (
          <div className="goal-card text-center">
            <p className="text-3xl mb-2">✅</p>
            <p className="text-lg font-bold">Все шаги пройдены!</p>
          </div>
        )}
      </div>

      {isActive && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs opacity-50">Достижения</span>
            {recentAchievements.length > 0 && (
              <button
                onClick={() => router.push(selectedGoal ? `/achievements?goalId=${selectedGoal.id}` : "/achievements")}
                className="text-xs opacity-50 hover:opacity-100"
              >
                Все →
              </button>
            )}
          </div>
          {recentAchievements.length > 0 ? (
            <div className="flex gap-2">
              {recentAchievements.map((a) => (
                <div key={a.code} className="bg-tg-secondary rounded-xl px-3 py-2 text-center flex-1">
                  <span className="text-lg">{a.icon}</span>
                  <p className="text-xs mt-0.5 truncate">{a.title}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs opacity-40 text-center py-2">Открывай конверты — появятся достижения</p>
          )}
        </div>
      )}

    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <p className="opacity-50">Загрузка...</p>
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
