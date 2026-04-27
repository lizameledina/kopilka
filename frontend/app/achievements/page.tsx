"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAchievements, useGoalAchievements } from "@/lib/hooks";
import type { AchievementItem } from "@/lib/types";

function AchievementCard({ a, locked }: { a: AchievementItem; locked: boolean }) {
  return (
    <div className={`bg-tg-secondary rounded-xl p-4 flex items-center gap-3 min-h-[60px] ${locked ? "opacity-40" : ""}`}>
      <span className={`text-2xl shrink-0 ${locked ? "grayscale" : ""}`}>{a.icon}</span>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm line-clamp-1">{a.title}</p>
        <p className="text-xs opacity-50 line-clamp-2">{a.description}</p>
      </div>
      {a.unlocked_at && !locked && (
        <span className="text-xs opacity-30 whitespace-nowrap">
          {new Date(a.unlocked_at).toLocaleDateString("ru-RU")}
        </span>
      )}
    </div>
  );
}

function AchievementSection({ title, items }: { title: string; items: AchievementItem[] }) {
  if (items.length === 0) return null;
  const unlocked = items.filter(a => a.unlocked);
  const locked = items.filter(a => !a.unlocked);
  return (
    <div className="mb-6">
      <h2 className="text-sm font-semibold mb-3 opacity-70">{title}</h2>
      {unlocked.length > 0 && (
        <div className="flex flex-col gap-2 mb-4">
          {unlocked.map(a => <AchievementCard key={a.code} a={a} locked={false} />)}
        </div>
      )}
      {locked.length > 0 && (
        <div className="flex flex-col gap-2">
          {locked.map(a => <AchievementCard key={a.code} a={a} locked />)}
        </div>
      )}
    </div>
  );
}

function AchievementsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const goalIdParam = searchParams.get("goalId");
  const goalId = goalIdParam ? Number(goalIdParam) : null;
  const isScoped = goalId !== null;

  const globalResult = useAchievements();
  const scopedResult = useGoalAchievements(goalId);

  if (isScoped) {
    const loading = scopedResult.isLoading;
    if (loading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <p className="opacity-50">Загрузка...</p>
        </div>
      );
    }

    const goalAchievements = scopedResult.data?.goal_achievements || [];
    const globalAchievements = scopedResult.data?.global_achievements || [];

    return (
      <div className="flex flex-col min-h-screen px-6 py-8">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => router.back()} className="text-xl">←</button>
          <h1 className="text-xl font-bold">Достижения</h1>
        </div>

        <AchievementSection title="Цель" items={goalAchievements} />
        <AchievementSection title="Общие" items={globalAchievements} />
      </div>
    );
  }

  const loading = globalResult.isLoading;
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
  }

  const achievements = globalResult.data || [];
  const userAchievements = achievements.filter(a => a.goal_id === null);
  const goalIdsMap: Record<number, boolean> = {};
  achievements.forEach(a => {
    if (a.goal_id !== null) goalIdsMap[a.goal_id] = true;
  });
  const goalIds = Object.keys(goalIdsMap).map(Number);
  const goalSections = goalIds.map(gid => {
    const items = achievements.filter(a => a.goal_id === gid);
    const title = items[0]?.goal_title || `Цель #${gid}`;
    return { goalId: gid, title, items };
  });

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push("/dashboard")} className="text-xl">←</button>
        <h1 className="text-xl font-bold">Достижения</h1>
        <span className="text-sm opacity-50 ml-auto">
          {achievements.filter(a => a.unlocked).length}/{achievements.length}
        </span>
      </div>

      <AchievementSection title="Общие" items={userAchievements} />
      {goalSections.map(section => (
        <AchievementSection key={section.goalId} title={section.title} items={section.items} />
      ))}
    </div>
  );
}

export default function AchievementsPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><p className="opacity-50">Загрузка...</p></div>}>
      <AchievementsContent />
    </Suspense>
  );
}