"use client";

import type { Goal } from "@/lib/types";
import { kopecksToRubles } from "@/lib/format";
import { getGoalUi } from "@/lib/goalUi";
import GoalStatusBadge from "@/components/GoalStatusBadge";

export default function GoalCard({
  goal,
  onOpen,
  actions,
}: {
  goal: Goal;
  onOpen?: () => void;
  actions?: React.ReactNode;
}) {
  const ui = getGoalUi(goal.status);
  const percent =
    goal.target_amount > 0 ? Math.min((goal.saved_amount / goal.target_amount) * 100, 100) : 0;

  return (
    <div className={ui.cardClassName}>
      <div className="goal-card__content">
        <div className="flex items-start justify-between gap-3">
          <button
            type="button"
            onClick={onOpen}
            className="text-left flex-1 min-w-0"
          >
            <p className="font-semibold truncate">{goal.title}</p>
            <p className="text-sm opacity-70 mt-1">
              {kopecksToRubles(goal.saved_amount)} / {kopecksToRubles(goal.target_amount)} ₽
            </p>
          </button>

          <GoalStatusBadge status={goal.status} />
        </div>

        <div className="mt-3">
          <div className="w-full goal-progress-track">
            <div className="goal-progress-fill" style={{ width: `${percent}%` }} />
          </div>
        </div>

        {actions ? <div className="mt-3">{actions}</div> : null}
      </div>
    </div>
  );
}

