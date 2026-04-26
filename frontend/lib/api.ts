import { AuthResponse, Goal, Step, StepAction, Progress, TodayStepItem, DistributionType, Streak, AchievementItem, ActivityItem, CompletionSummary, ShareSummary, HistoryItem, GoalAchievementsResponse, EditGoalRequest, EditPreviewResponse, GoalActivityItem } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const IS_BROWSER = typeof window !== "undefined";
const REQUEST_TIMEOUT = 15000;

function getBaseUrl(): string {
  if (IS_BROWSER && window.location.protocol === "https:") {
    return "/backend";
  }
  return API_URL;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const method = options.method || "GET";
    const url = `${getBaseUrl()}${path}`;

    const res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    if (!res.ok) {
      const contentType = res.headers.get("content-type") || "";
      const isJson = contentType.includes("application/json");

      let detail = "";
      if (isJson) {
        const data = await res.json().catch(() => ({}));
        detail = data?.detail || "";
      } else {
        const text = await res.text().catch(() => "");
        const compact = text.replace(/\s+/g, " ").trim();
        detail = compact ? `HTTP ${res.status} (non-json): ${compact.slice(0, 120)}` : "";
      }

      const message = detail || `HTTP ${res.status}`;
      if (process.env.NODE_ENV !== "production") {
        // eslint-disable-next-line no-console
        console.warn("[api]", method, url, "->", res.status, message);
      }
      throw new Error(message);
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  } catch (e: any) {
    if (e.name === "AbortError") {
      throw new Error("Запрос превышен по времени. Попробуйте снова.");
    }
    throw e;
  } finally {
    clearTimeout(timeoutId);
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

export function detectTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return "UTC";
  }
}

export const api = {
  auth: {
    telegram: (initData: string, timezone?: string) =>
      request<AuthResponse>("/auth/telegram", {
        method: "POST",
        body: JSON.stringify({
          init_data: initData,
          timezone: timezone || detectTimezone(),
        }),
      }),
  },
  me: () => request<import("./types").User>("/me"),
  goals: {
    create: (title: string, targetAmount: number, distribution: DistributionType, stepCount: number = 100) =>
      request<Goal>("/goals", {
        method: "POST",
        body: JSON.stringify({
          title,
          target_amount: targetAmount,
          distribution,
          step_count: stepCount,
        }),
      }),
    list: (status?: string) =>
      request<Goal[]>(status ? `/goals?status=${status}` : "/goals"),
    current: () => request<Goal | null>("/goals/current"),
    get: (goalId: number) => request<Goal>(`/goals/${goalId}`),
    archive: (goalId: number) =>
      request<Goal>(`/goals/${goalId}`, { method: "DELETE" }),
    freeze: (goalId: number) =>
      request<Goal>(`/goals/${goalId}/freeze`, { method: "POST" }),
    unfreeze: (goalId: number) =>
      request<Goal>(`/goals/${goalId}/unfreeze`, { method: "POST" }),
    progress: (goalId: number) => request<Progress>(`/goals/${goalId}/progress`),
    achievements: (goalId: number) =>
      request<GoalAchievementsResponse>(`/goals/${goalId}/achievements`),
    completion: (goalId: number) =>
      request<CompletionSummary>(`/goals/${goalId}/completion`),
    shareSummary: (goalId: number) =>
      request<ShareSummary>(`/goals/${goalId}/share-summary`),
    history: (goalId: number, sort?: string, status?: string) => {
      const params = new URLSearchParams();
      if (sort) params.set("sort_by", sort);
      if (status) params.set("status", status);
      const qs = params.toString();
      return request<HistoryItem[]>(`/goals/${goalId}/history${qs ? `?${qs}` : ""}`);
    },
    edit: (goalId: number, body: EditGoalRequest) =>
      request<Goal>(`/goals/${goalId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    editPreview: (goalId: number, body: EditGoalRequest) =>
      request<EditPreviewResponse>(`/goals/${goalId}/edit-preview`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    reset: (goalId: number, body: EditGoalRequest) =>
      request<Goal>(`/goals/${goalId}/reset`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    activity: (goalId: number) =>
      request<GoalActivityItem[]>(`/goals/${goalId}/activity`),
  },
  steps: {
    today: () => request<TodayStepItem[]>("/steps/today"),
    get: (stepId: number) => request<Step>(`/steps/${stepId}`),
    complete: (stepId: number) =>
      request<StepAction>(`/steps/${stepId}/complete`, { method: "POST" }),
    skip: (stepId: number) =>
      request<StepAction>(`/steps/${stepId}/skip`, { method: "POST" }),
  },
  streak: {
    get: () => request<Streak>("/streak"),
  },
  achievements: {
    list: () => request<AchievementItem[]>("/achievements"),
  },
  activity: {
    list: (limit: number = 20) => request<ActivityItem[]>(`/activity?limit=${limit}`),
  },
};
