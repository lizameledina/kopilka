"use client";

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmModal({
  isOpen,
  title,
  message,
  confirmLabel = "Подтвердить",
  cancelLabel = "Отмена",
  danger = false,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-end z-50"
      onClick={onCancel}
    >
      <div
        className="w-full bg-[var(--tg-theme-secondary-bg-color,#f0f0f0)] rounded-t-2xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-bold mb-2">{title}</h2>
        <p className="text-sm opacity-60 mb-6 leading-relaxed">{message}</p>
        <button
          onClick={onConfirm}
          className={`w-full py-3 rounded-xl font-semibold mb-3 text-sm ${
            danger
              ? "bg-red-500 text-white"
              : "bg-[var(--tg-theme-button-color,#2AABEE)] text-[var(--tg-theme-button-text-color,#fff)]"
          }`}
        >
          {confirmLabel}
        </button>
        <button
          onClick={onCancel}
          className="w-full py-3 rounded-xl text-sm bg-[var(--tg-theme-bg-color,#fff)] opacity-70"
        >
          {cancelLabel}
        </button>
      </div>
    </div>
  );
}
