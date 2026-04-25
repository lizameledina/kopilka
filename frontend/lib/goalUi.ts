import type { GoalStatus } from "@/lib/types";

export type GoalUiBadge = {
  text: string;
  icon?: string;
  className: string;
};

export type GoalUi = {
  cardClassName: string;
  badge?: GoalUiBadge;
  isPaused: boolean;
};

export function isPausedStatus(status: GoalStatus): boolean {
  return status === "frozen" || status === "abandoned";
}

export function getGoalUi(status: GoalStatus): GoalUi {
  if (isPausedStatus(status)) {
    return {
      cardClassName: "goal-card goal-card--frozen",
      badge: {
        text: "Заморожена",
        icon: "❄️",
        className: "status-badge status-badge--frozen",
      },
      isPaused: true,
    };
  }

  if (status === "completed") {
    return {
      cardClassName: "goal-card",
      badge: {
        text: "Завершена",
        icon: "🏁",
        className: "status-badge status-badge--completed",
      },
      isPaused: false,
    };
  }

  if (status === "archived") {
    return {
      cardClassName: "goal-card",
      badge: {
        text: "Удалена",
        className: "status-badge status-badge--archived",
      },
      isPaused: false,
    };
  }

  return {
    cardClassName: "goal-card",
    badge: undefined,
    isPaused: false,
  };
}

