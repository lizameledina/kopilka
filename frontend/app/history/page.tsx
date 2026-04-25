"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useHistory } from "@/lib/hooks";
import { kopecksToRubles } from "@/lib/format";

function HistoryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [filter, setFilter] = useState<string>("all");
  const goalId = searchParams.get("goalId");

  const statusFilter = filter === "all" ? undefined : filter === "recovered" ? "recovered" : filter;
  const { data: items = [], isLoading, error } = useHistory(goalId ? Number(goalId) : null, "date", statusFilter);

  if (!goalId) {
    router.push("/dashboard");
    return null;
  }

  const handleFilter = (newFilter: string) => {
    setFilter(newFilter);
  };

  if (isLoading && items.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="opacity-50">Загрузка...</p>
      </div>
    );
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

      <div className="flex gap-2 mb-4">
        {[
          { key: "all", label: "Все" },
          { key: "completed", label: "Завершённые" },
          { key: "recovered", label: "Восстановленные" },
          { key: "skipped", label: "Пропущенные" },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => handleFilter(f.key)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-opacity ${
              filter === f.key ? "bg-tg-secondary font-semibold" : "opacity-50"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <p className="text-red-500 text-sm mb-4">{error.message}</p>}

      <div className="flex-1 overflow-y-auto">
        {items.length === 0 ? (
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
      </div>
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