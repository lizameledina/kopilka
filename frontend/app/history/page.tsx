"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useHistory, useGoalActivity } from "@/lib/hooks";
import { kopecksToRubles } from "@/lib/format";

type Tab = "steps" | "timeline";

function HistoryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState<Tab>("steps");
  const [filter, setFilter] = useState<string>("all");
  const goalId = searchParams.get("goalId");

  const statusFilter = filter === "all" ? undefined : filter === "recovered" ? "recovered" : filter;
  const { data: items = [], isLoading: histLoading, error } = useHistory(goalId ? Number(goalId) : null, "date", statusFilter);
  const { data: timeline = [], isLoading: timelineLoading } = useGoalActivity(goalId ? Number(goalId) : null);

  if (!goalId) {
    router.push("/dashboard");
    return null;
  }

  const statusLabels: Record<string, string> = {
    completed: "✓",
    skipped: "✗",
    recovered: "↩",
  };

  const statusColors: Record<string, string> = {
    completed: "text-green-500",
    skipped: "text-gray-400",
    recovered: "text-blue-400",
  };

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center gap-3 mb-4">
        <button onClick={() => router.back()} className="text-xl">←</button>
        <h1 className="text-xl font-bold">История</h1>
      </div>

      <div className="flex gap-1 mb-4 bg-tg-secondary rounded-xl p-1">
        <button
          onClick={() => setActiveTab("steps")}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "steps" ? "bg-tg-bg shadow" : "opacity-50"
          }`}
        >
          Шаги
        </button>
        <button
          onClick={() => setActiveTab("timeline")}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "timeline" ? "bg-tg-bg shadow" : "opacity-50"
          }`}
        >
          События
        </button>
      </div>

      {activeTab === "steps" && (
        <>
          <div className="flex gap-2 mb-4 overflow-x-auto">
            {[
              { key: "all", label: "Все" },
              { key: "completed", label: "Завершённые" },
              { key: "recovered", label: "Восстановленные" },
              { key: "skipped", label: "Пропущенные" },
            ].map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-opacity ${
                  filter === f.key ? "bg-tg-secondary font-semibold" : "opacity-50"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {error && <p className="text-red-500 text-sm mb-4">{error.message}</p>}

          {histLoading && items.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <p className="opacity-50">Загрузка...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-8 opacity-50">
              <p>Нет записей</p>
            </div>
          ) : (
            <div className="flex flex-col divide-y divide-gray-700">
              {items.map((item) => (
                <div key={item.id} className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-mono ${statusColors[item.label] || "text-gray-300"}`}>
                      {statusLabels[item.label] || "?"}
                    </span>
                    <div>
                      <span className="font-medium text-sm">#{item.step_number}</span>
                      <span className="text-sm opacity-70 ml-2">{kopecksToRubles(item.planned_amount)} ₽</span>
                    </div>
                  </div>
                  {item.completed_at && (
                    <span className="text-xs opacity-40">
                      {new Date(item.completed_at).toLocaleDateString("ru-RU", { day: "numeric", month: "short" })}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === "timeline" && (
        <>
          {timelineLoading && timeline.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <p className="opacity-50">Загрузка...</p>
            </div>
          ) : timeline.length === 0 ? (
            <div className="text-center py-8 opacity-50">
              <p>Нет событий</p>
            </div>
          ) : (
            <div className="flex flex-col">
              {timeline.map((item, idx) => (
                <div key={idx} className="flex gap-3 pb-4">
                  <div className="flex flex-col items-center">
                    <div className="w-2 h-2 rounded-full bg-tg-hint mt-1.5 flex-shrink-0" />
                    {idx < timeline.length - 1 && (
                      <div className="w-px flex-1 bg-tg-hint/30 mt-1" />
                    )}
                  </div>
                  <div className="flex-1 pb-2">
                    <p className="text-sm font-medium">{item.title}</p>
                    {item.description && (
                      <p className="text-xs opacity-50 mt-0.5">{item.description}</p>
                    )}
                    <p className="text-xs opacity-30 mt-1">
                      {new Date(item.created_at).toLocaleDateString("ru-RU", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function HistoryPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><p className="opacity-50">Загрузка...</p></div>}>
      <HistoryContent />
    </Suspense>
  );
}
