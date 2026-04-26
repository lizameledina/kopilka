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
  const [stepCount, setStepCount] = useState<string>("100");
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
    const parsedStepCount = parseInt(stepCount, 10);
    if (!parsedStepCount || parsedStepCount < 1 || parsedStepCount > 365) {
      setError("Количество конвертов: от 1 до 365");
      return;
    }

    setError("");
    try {
      const goal = await createGoal.mutateAsync({
        title: title.trim(),
        targetAmount: rublesToKopecks(targetRubles),
        distribution,
        stepCount: parsedStepCount,
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
        <label className="block text-sm mb-1 opacity-70">Количество конвертов</label>
        <input
          type="text"
          inputMode="numeric"
          value={stepCount}
          onChange={(e) => setStepCount(e.target.value.replace(/[^0-9]/g, ""))}
          onBlur={() => {
            const n = parseInt(stepCount, 10);
            if (isNaN(n) || n < 1) setStepCount("1");
            else if (n > 365) setStepCount("365");
          }}
          className="input-field"
        />
        <p className="text-xs mt-1 opacity-50">От 1 до 365</p>
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