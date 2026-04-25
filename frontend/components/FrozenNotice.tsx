"use client";

import { useState } from "react";

export default function FrozenNotice({
  onUnfreeze,
  unfreezeLabel = "Разморозить",
  error,
}: {
  onUnfreeze: () => Promise<void> | void;
  unfreezeLabel?: string;
  error?: string;
}) {
  const [busy, setBusy] = useState(false);

  const handle = async () => {
    setBusy(true);
    try {
      await onUnfreeze();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="frozen-banner">
      <div className="flex items-start gap-3">
        <div className="text-2xl leading-none">❄️</div>
        <div className="min-w-0">
          <p className="font-semibold">Эта цель заморожена</p>
          <p className="text-sm opacity-80 mt-1">
            Чтобы продолжить накопление — разморозь её.
          </p>
        </div>
      </div>
      <div className="mt-3">
        <button onClick={handle} disabled={busy} className="btn-primary frozen-primary">
          {busy ? "Разморозка..." : unfreezeLabel}
        </button>
      </div>
      {error ? <p className="text-sm text-red-500 mt-3">{error}</p> : null}
    </div>
  );
}
