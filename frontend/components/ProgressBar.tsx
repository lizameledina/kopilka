"use client";

import { kopecksToRubles } from "@/lib/format";

interface ProgressBarProps {
  percent: number;
  saved: number;
  target: number;
}

export default function ProgressBar({ percent, saved, target }: ProgressBarProps) {
  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span>Накоплено: {kopecksToRubles(saved)} ₽</span>
        <span>Цель: {kopecksToRubles(target)} ₽</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-4 overflow-hidden">
        <div
          className="h-full bg-[var(--tg-theme-button-color,#2AABEE)] rounded-full transition-all duration-500"
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
      <p className="text-center text-sm mt-1">{percent.toFixed(1)}%</p>
    </div>
  );
}