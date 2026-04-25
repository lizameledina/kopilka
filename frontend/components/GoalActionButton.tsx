"use client";

import React from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";

export default function GoalActionButton({
  variant,
  children,
  onClick,
  disabled,
}: {
  variant: Variant;
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  const base =
    "px-3 py-2 rounded-xl text-sm font-semibold transition-opacity active:scale-95";
  const styles: Record<Variant, string> = {
    primary:
      "bg-[var(--tg-theme-button-color,#2AABEE)] text-[var(--tg-theme-button-text-color,#fff)]",
    secondary:
      "bg-[var(--tg-theme-secondary-bg-color,#f0f0f0)] text-[var(--tg-theme-text-color,#000)]",
    danger: "bg-red-500 text-white",
    ghost: "bg-transparent text-[var(--tg-theme-hint-color,#999)]",
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${styles[variant]} ${disabled ? "opacity-60" : "hover:opacity-100 opacity-90"}`}
    >
      {children}
    </button>
  );
}

