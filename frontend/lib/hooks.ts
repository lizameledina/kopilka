"use client";

import { useQuery, useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { pushAchievements } from "@/components/AchievementToast";
import type {
  Goal,
  Progress,
  TodayStepItem,
  Streak,
  AchievementItem,
  CompletionSummary,
  ShareSummary,
  Step,
  GoalAchievementsResponse,
  EditGoalRequest,
  EditPreviewResponse,
  ReminderSettings,
} from "@/lib/types";

export function useGoals(status?: string) {
  return useQuery({
    queryKey: ["goals", status],
    queryFn: () => api.goals.list(status),
  });
}

export function useCurrentGoal() {
  return useQuery({
    queryKey: ["goals", "current"],
    queryFn: () => api.goals.current(),
  });
}

export function useProgress(goalId: number | null) {
  return useQuery({
    queryKey: ["progress", goalId],
    queryFn: () => api.goals.progress(goalId!),
    enabled: !!goalId,
  });
}

export function useTodaySteps() {
  return useQuery({
    queryKey: ["steps", "today"],
    queryFn: () => api.steps.today(),
  });
}

export function useStreak() {
  return useQuery({
    queryKey: ["streak"],
    queryFn: () => api.streak.get().catch(() => ({ current_streak: 0, best_streak: 0 })),
  });
}

export function useAchievements() {
  return useQuery({
    queryKey: ["achievements"],
    queryFn: () => api.achievements.list().catch(() => []),
  });
}

export function useGoalAchievements(goalId: number | null) {
  return useQuery({
    queryKey: ["achievements", "goal", goalId],
    queryFn: () => api.goals.achievements(goalId!),
    enabled: !!goalId,
  });
}

export function useCompletion(goalId: number | null) {
  return useQuery({
    queryKey: ["completion", goalId],
    queryFn: () => api.goals.completion(goalId!),
    enabled: !!goalId,
  });
}

export function useShareSummary(goalId: number | null) {
  return useQuery({
    queryKey: ["share", goalId],
    queryFn: () => api.goals.shareSummary(goalId!),
    enabled: !!goalId,
  });
}

export function useStep(stepId: number | null) {
  return useQuery({
    queryKey: ["step", stepId],
    queryFn: () => api.steps.get(stepId!),
    enabled: !!stepId,
  });
}

async function refreshAchievements(queryClient: QueryClient) {
  const data = await queryClient.fetchQuery({
    queryKey: ["achievements"],
    queryFn: () => api.achievements.list().catch(() => []),
  });
  pushAchievements(data);
}

export function useCreateGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ title, targetAmount, distribution, stepCount }: {
      title: string; targetAmount: number; distribution: string; stepCount: number;
    }) => api.goals.create(title, targetAmount, distribution as any, stepCount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["steps"] });
      queryClient.invalidateQueries({ queryKey: ["progress"] });
      void refreshAchievements(queryClient);
    },
  });
}

export function useCompleteStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (stepId: number) => api.steps.complete(stepId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["steps"] });
      queryClient.invalidateQueries({ queryKey: ["progress"] });
      queryClient.invalidateQueries({ queryKey: ["streak"] });
      if (data.newly_unlocked && data.newly_unlocked.length > 0) {
        pushAchievements(data.newly_unlocked);
      } else {
        void refreshAchievements(queryClient);
      }
    },
  });
}

export function useSkipStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (stepId: number) => api.steps.skip(stepId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["steps"] });
      queryClient.invalidateQueries({ queryKey: ["progress"] });
      queryClient.invalidateQueries({ queryKey: ["streak"] });
    },
  });
}

export function useArchiveGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (goalId: number) => api.goals.archive(goalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });
}

export function useFreezeGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (goalId: number) => api.goals.freeze(goalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["steps"] });
      queryClient.invalidateQueries({ queryKey: ["progress"] });
    },
  });
}

export function useUnfreezeGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (goalId: number) => api.goals.unfreeze(goalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["steps"] });
      queryClient.invalidateQueries({ queryKey: ["progress"] });
    },
  });
}

export function useEditGoalPreview() {
  return useMutation({
    mutationFn: ({ goalId, body }: { goalId: number; body: EditGoalRequest }) =>
      api.goals.editPreview(goalId, body),
  });
}

export function useEditGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ goalId, body }: { goalId: number; body: EditGoalRequest }) =>
      api.goals.edit(goalId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["steps"] });
      queryClient.invalidateQueries({ queryKey: ["progress"] });
    },
  });
}

export function useResetGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ goalId, body }: { goalId: number; body: EditGoalRequest }) =>
      api.goals.reset(goalId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      queryClient.invalidateQueries({ queryKey: ["steps"] });
      queryClient.invalidateQueries({ queryKey: ["progress"] });
      queryClient.invalidateQueries({ queryKey: ["streak"] });
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
    },
  });
}

export function useReminderSettings() {
  return useQuery({
    queryKey: ["settings", "reminders"],
    queryFn: () =>
      api.settings.getReminders().catch(() => ({
        reminders_enabled: false,
        reminder_time: "09:00",
      })),
  });
}

export function useUpdateReminderSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ReminderSettings) => api.settings.updateReminders(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", "reminders"] });
    },
  });
}
