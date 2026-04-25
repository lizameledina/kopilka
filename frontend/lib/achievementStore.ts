"use client";

import { AchievementItem } from "./types";

const STORAGE_KEY = "kopilka_seen_achievements";
const LEGACY_PREFIX = "legacy:";

const seenThisSession = new Set<string>();

export function getAchievementKey(a: Pick<AchievementItem, "code" | "goal_id">): string {
  return `${a.code}:${a.goal_id ?? "global"}`;
}

function getLegacyKey(code: string): string {
  return `${LEGACY_PREFIX}${code}`;
}

export function getSeenAchievementKeys(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    const arr = Array.isArray(parsed) ? parsed : [];

    const migrated: string[] = [];
    let needsWrite = false;

    for (const item of arr) {
      if (typeof item !== "string" || item.length === 0) continue;
      if (item.startsWith(LEGACY_PREFIX) || item.includes(":")) {
        migrated.push(item);
        continue;
      }

      // Legacy format: just "code". Treat as "seen for any scope" to avoid spam after migration.
      migrated.push(getLegacyKey(item));
      needsWrite = true;
    }

    const set = new Set(migrated);
    if (needsWrite) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(set)));
      } catch {}
    }
    return set;
  } catch {
    return new Set();
  }
}

export function markAchievementsSeen(achievements: Array<Pick<AchievementItem, "code" | "goal_id">>) {
  if (typeof window === "undefined") return;
  try {
    const seen = getSeenAchievementKeys();
    achievements.forEach((a) => {
      const key = getAchievementKey(a);
      seen.add(key);
      seenThisSession.add(key);
    });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(seen)));
  } catch {}
}

export function findNewAchievements(all: AchievementItem[]): AchievementItem[] {
  const seen = getSeenAchievementKeys();
  return all.filter((a) => {
    if (!a.unlocked) return false;
    const key = getAchievementKey(a);
    if (seenThisSession.has(key)) return false;
    if (seen.has(key)) return false;
    if (seen.has(getLegacyKey(a.code))) return false;
    return true;
  });
}
