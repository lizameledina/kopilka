"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useGoals, useArchiveGoal, useFreezeGoal, useUnfreezeGoal } from "@/lib/hooks";
import GoalCard from "@/components/GoalCard";
import GoalActionButton from "@/components/GoalActionButton";
import { isPausedStatus } from "@/lib/goalUi";

export default function GoalsPage() {
  const router = useRouter();
  const { data: goals = [], isLoading, error } = useGoals();
  const archiveGoal = useArchiveGoal();
  const freezeGoal = useFreezeGoal();
  const unfreezeGoal = useUnfreezeGoal();
  const [actionError, setActionError] = useState<string>("");

  const activeGoals = goals.filter((g) => g.status === "active");
  const pausedGoals = goals.filter((g) => isPausedStatus(g.status));
  const completedGoals = goals.filter((g) => g.status === "completed");

  const canCreate = activeGoals.length < 3;

  const confirmDelete = () =>
    confirm("Удалить цель? Это действие нельзя отменить.");

  const confirmFreeze = () =>
    confirm("Заморозить цель? Ты не сможешь вносить накопления, пока не разморозишь её.");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push("/dashboard")} className="text-xl">
          ←
        </button>
        <h1 className="text-xl font-bold">Мои цели</h1>
      </div>

      {error && <p className="text-red-500 text-sm mb-4">{error.message}</p>}
      {actionError ? <p className="text-red-500 text-sm mb-4">{actionError}</p> : null}

      <button
        onClick={() => router.push("/create-goal")}
        className="btn-primary mb-6"
        disabled={!canCreate}
      >
        {canCreate ? "+ Новая цель" : "Максимум 3 активные цели"}
      </button>

      {goals.length === 0 && (
        <div className="text-center py-12 opacity-60">
          <p>У тебя пока нет целей</p>
          <p className="text-sm mt-2">Создай первую, чтобы начать.</p>
        </div>
      )}

      {activeGoals.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold mb-3 opacity-70">Активные</h2>
          <div className="flex flex-col gap-3">
            {activeGoals.map((goal) => (
              <GoalCard
                key={goal.id}
                goal={goal}
                onOpen={() => {
                  setActionError("");
                  router.push(`/progress?goalId=${goal.id}`);
                }}
                actions={
                  <div className="flex flex-col gap-2">
                    <GoalActionButton
                      variant="secondary"
                      className="w-full"
                      onClick={() => router.push(`/edit-goal?goalId=${goal.id}`)}
                    >
                      Редактировать
                    </GoalActionButton>
                    <GoalActionButton
                      variant="secondary"
                      className="w-full"
                      onClick={async () => {
                        setActionError("");
                        if (!confirmFreeze()) return;
                        try {
                          await freezeGoal.mutateAsync(goal.id);
                          setActionError("");
                        } catch (e: any) {
                          setActionError(e?.message || "Ошибка");
                        }
                      }}
                      disabled={freezeGoal.isPending}
                    >
                      Заморозить
                    </GoalActionButton>
                    <GoalActionButton
                      variant="danger"
                      className="w-full"
                      onClick={async () => {
                        setActionError("");
                        if (!confirmDelete()) return;
                        try {
                          await archiveGoal.mutateAsync(goal.id);
                          setActionError("");
                        } catch (e: any) {
                          setActionError(e?.message || "Ошибка");
                        }
                      }}
                      disabled={archiveGoal.isPending}
                    >
                      Удалить
                    </GoalActionButton>
                  </div>
                }
              />
            ))}
          </div>
        </div>
      )}

      {pausedGoals.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold mb-3 opacity-70">На паузе</h2>
          <div className="flex flex-col gap-3">
            {pausedGoals.map((goal) => (
              <GoalCard
                key={goal.id}
                goal={goal}
                onOpen={() => {
                  setActionError("");
                  router.push(`/progress?goalId=${goal.id}`);
                }}
                actions={
                  <div className="flex flex-col gap-2">
                    <GoalActionButton
                      variant="secondary"
                      className="w-full"
                      onClick={() => router.push(`/edit-goal?goalId=${goal.id}`)}
                    >
                      Редактировать
                    </GoalActionButton>
                    <GoalActionButton
                      variant="primary"
                      className="w-full"
                      onClick={async () => {
                        setActionError("");
                        try {
                          await unfreezeGoal.mutateAsync(goal.id);
                          setActionError("");
                        } catch (e: any) {
                          setActionError(e?.message || "Ошибка");
                        }
                      }}
                      disabled={unfreezeGoal.isPending}
                    >
                      Разморозить
                    </GoalActionButton>
                    <GoalActionButton
                      variant="danger"
                      className="w-full"
                      onClick={async () => {
                        setActionError("");
                        if (!confirmDelete()) return;
                        try {
                          await archiveGoal.mutateAsync(goal.id);
                          setActionError("");
                        } catch (e: any) {
                          setActionError(e?.message || "Ошибка");
                        }
                      }}
                      disabled={archiveGoal.isPending}
                    >
                      Удалить
                    </GoalActionButton>
                  </div>
                }
              />
            ))}
          </div>
        </div>
      )}

      {completedGoals.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold mb-3 opacity-70">Завершённые</h2>
          <div className="flex flex-col gap-3">
            {completedGoals.map((goal) => (
              <GoalCard
                key={goal.id}
                goal={goal}
                onOpen={() => {
                  setActionError("");
                  router.push(`/completion?goalId=${goal.id}`);
                }}
                actions={
                  <div className="flex gap-2">
                    <GoalActionButton
                      variant="danger"
                      onClick={async () => {
                        setActionError("");
                        if (!confirmDelete()) return;
                        try {
                          await archiveGoal.mutateAsync(goal.id);
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
                }
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
