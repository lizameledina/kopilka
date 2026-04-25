"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCreateGoal } from "@/lib/hooks";
import { rublesToKopecks } from "@/lib/format";
import type { DistributionType } from "@/lib/types";

const DISTRIBUTIONS: { value: DistributionType; label: string; hint: string }[] = [
  { value: "equal", label: "Равномерно", hint: "Каждый шаг одинаковая сумма" },
  { value: "random", label: "Случайно", hint: "Сумма каждого шага случайная" },
  { value: "ascending", label: "По возрастанию", hint: "Сумма растёт с каждым шагом" },
  { value: "descending", label: "По убыванию", hint: "Сумма уменьшается с каждым шагом" },
];

export default function CreateGoalPage() {
  const router = useRouter();
  const createGoal = useCreateGoal();
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [distribution, setDistribution] = useState<DistributionType>("equal");
  const [stepCount, setStepCount] = useState(100);
  const [error, setError] = useState("");

  const isSubmitting = createGoal.isPending;
  const hasFormData = title.trim() || amount.trim();

  const handleSubmit = async () => {
    const targetRubles = parseFloat(amount);
    if (!title.trim()) {
      setError("Введите название цели");
      return;
    }
    if (!targetRubles || targetRubles < 1) {
      setError("Минимальная сумма — 1 рубль");
      return;
    }
    if (stepCount < 1 || stepCount > 500) {
      setError("Количество шагов: от 1 до 500");
      return;
    }

    setError("");
    try {
      const goal = await createGoal.mutateAsync({
        title: title.trim(),
        targetAmount: rublesToKopecks(targetRubles),
        distribution,
        stepCount,
      });
      router.push(`/dashboard?goalId=${goal.id}`);
    } catch (e: any) {
      setError(e.message || "Ошибка создания цели");
    }
  };

  const handleCancel = () => {
    if (hasFormData) {
      if (!confirm("Выйти без сохранения?")) return;
    }
    router.push("/dashboard");
  };

  const selectedHint = DISTRIBUTIONS.find((d) => d.value === distribution)?.hint;

  return (
    <div className="flex flex-col min-h-screen px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={handleCancel} className="text-xl opacity-70 hover:opacity-100">←</button>
        <h1 className="text-xl font-bold">Новая цель</h1>
      </div>

      <div className="mb-4">
        <label className="block text-sm mb-1 opacity-70">Название цели</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Например: На отпуск"
          className="input-field"
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm mb-1 opacity-70">Сумма цели (₽)</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="10000"
          min="1"
          step="100"
          className="input-field"
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm mb-1 opacity-70">Количество шагов</label>
        <input
          type="number"
          value={stepCount}
          onChange={(e) => {
            const v = parseInt(e.target.value);
            if (!isNaN(v)) setStepCount(v);
          }}
          min={1}
          max={500}
          className="input-field"
        />
        <p className="text-xs mt-1 opacity-50">От 1 до 500</p>
      </div>

      <div className="mb-6">
        <label className="text-sm font-semibold mb-2 opacity-70">Распределение шагов</label>
        <div className="grid grid-cols-2 gap-2">
          {DISTRIBUTIONS.map((d) => (
            <button
              key={d.value}
              onClick={() => setDistribution(d.value)}
              className={distribution === d.value ? "btn-primary py-2 text-sm" : "btn-secondary py-2 text-sm"}
            >
              {d.label}
            </button>
          ))}
        </div>
        <p className="text-xs mt-1 opacity-50">{selectedHint}</p>
      </div>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={isSubmitting}
        className="btn-primary mt-auto"
      >
        {isSubmitting ? "Создание..." : "Создать цель"}
      </button>
    </div>
  );
}