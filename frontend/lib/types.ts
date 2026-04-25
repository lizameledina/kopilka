export type DistributionType = "equal" | "random" | "ascending" | "descending";
export type GoalStatus = "active" | "frozen" | "completed" | "abandoned" | "archived";

export interface User {
  id: number;
  telegram_id: number;
  first_name: string | null;
  username: string | null;
  timezone: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface Goal {
  id: number;
  title: string;
  target_amount: number;
  saved_amount: number;
  status: GoalStatus;
  total_steps: number;
  completed_at: string | null;
}

export interface Step {
  id: number;
  step_number: number;
  planned_amount: number;
  status: string;
  total_steps: number;
  goal_title?: string;
  goal_saved?: number;
  goal_target?: number;
}

export interface StepAction {
  id: number;
  status: string;
}

export interface TodayStepItem {
  goal_id: number;
  goal_title: string;
  step: Step | null;
  total_steps: number;
}

export interface Progress {
  goal_id: number;
  title: string;
  target_amount: number;
  saved_amount: number;
  percent: number;
  completed_steps: number;
  skipped_steps: number;
  total_steps: number;
  status: GoalStatus;
  steps: StepListItem[];
}

export interface StepListItem {
  id: number;
  step_number: number;
  planned_amount: number;
  status: string;
}

export interface Streak {
  current_streak: number;
  best_streak: number;
}

export interface AchievementItem {
  code: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlocked_at: string | null;
  goal_id: number | null;
  goal_title: string | null;
}

export interface ActivityItem {
  id: number;
  event_type: string;
  created_at: string;
  payload: Record<string, unknown> | null;
}

export interface CompletionSummary {
  goal_id: number;
  title: string;
  target_amount: number;
  saved_amount: number;
  percent: number;
  completed_steps: number;
  skipped_steps: number;
  total_steps: number;
  status: GoalStatus;
  completed_at: string | null;
  created_at: string;
  duration_days: number;
  current_streak: number;
  best_streak: number;
  achievements: AchievementItem[];
}

export interface ShareSummary {
  goal_id: number;
  title: string;
  target_amount: number;
  saved_amount: number;
  percent: number;
  completed_steps: number;
  total_steps: number;
  status: GoalStatus;
  completed_at: string | null;
  duration_days: number | null;
  current_streak: number;
  best_streak: number;
}

export interface GoalAchievementsResponse {
  goal_achievements: AchievementItem[];
  global_achievements: AchievementItem[];
  other_goal_achievements: AchievementItem[];
}

export interface HistoryItem {
  id: number;
  step_number: number;
  planned_amount: number;
  status: string;
  label: string;
  completed_at: string | null;
}
