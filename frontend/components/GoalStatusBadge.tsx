"use client";

import type { GoalStatus } from "@/lib/types";
import { getGoalUi } from "@/lib/goalUi";

export default function GoalStatusBadge({ status }: { status: GoalStatus }) {
  const ui = getGoalUi(status);
  if (!ui.badge) return null;
  return (
    <span className={ui.badge.className}>
      {ui.badge.icon ? <span className="mr-1">{ui.badge.icon}</span> : null}
      {ui.badge.text}
    </span>
  );
}

