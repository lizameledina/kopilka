"use client";

import { useEffect, useState } from "react";
import { AchievementItem } from "@/lib/types";
import { findNewAchievements, markAchievementsSeen } from "@/lib/achievementStore";

interface ToastItem {
  key: string;
  achievement: AchievementItem;
}

class AchievementQueue {
  private items: AchievementItem[] = [];
  private listeners = new Set<(items: AchievementItem[]) => void>();

  push(newItems: AchievementItem[]): void {
    this.items.push(...newItems);
    this._notify();
  }

  shift(): AchievementItem | undefined {
    return this.items.shift();
  }

  get size(): number {
    return this.items.length;
  }

  subscribe(listener: (items: AchievementItem[]) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private _notify(): void {
    const snapshot = [...this.items];
    for (const l of this.listeners) l(snapshot);
  }
}

const achievementQueue = new AchievementQueue();

export function pushAchievements(achievements: AchievementItem[]) {
  const newOnes = findNewAchievements(achievements);
  if (newOnes.length === 0) return;
  markAchievementsSeen(newOnes.map((a) => ({ code: a.code, goal_id: a.goal_id })));
  achievementQueue.push(newOnes);
}

export default function AchievementToast() {
  const [current, setCurrent] = useState<ToastItem | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    return achievementQueue.subscribe((items) => {
      if (!current && items.length > 0) {
        const next = achievementQueue.shift()!;
        setCurrent({ key: `${next.code}-${Date.now()}`, achievement: next });
        setVisible(true);
      }
    });
  }, [current]);

  useEffect(() => {
    if (!visible || !current) return;
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => {
        setCurrent(null);
        if (achievementQueue.size > 0) {
          const next = achievementQueue.shift()!;
          setCurrent({ key: `${next.code}-${Date.now()}`, achievement: next });
          setVisible(true);
        }
      }, 300);
    }, 3000);
    return () => clearTimeout(timer);
  }, [visible, current]);

  if (!current) return null;

  const a = current.achievement;

  return (
    <div
      className={`fixed top-4 left-4 right-4 z-50 transition-all duration-300 ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"
      }`}
    >
      <div className="bg-[var(--tg-theme-bg-color,#1a1a2e)] border border-[var(--tg-theme-secondary-bg-color,#2a2a3e)] rounded-xl p-4 flex items-center gap-3 shadow-lg">
        <span className="text-3xl">{a.icon}</span>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm">{a.title}</p>
          <p className="text-xs opacity-60">{a.description}</p>
        </div>
      </div>
    </div>
  );
}
