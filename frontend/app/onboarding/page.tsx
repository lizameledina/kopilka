"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const ONBOARDING_KEY = "kopilka_onboarding_done";
const markDone = () => localStorage.setItem(ONBOARDING_KEY, "1");

const SCREENS = [
  {
    icon: "🪙",
    title: "Копи в конвертах",
    body: "Разбей большую сумму на маленькие шаги и двигайся к цели каждый день",
  },
  {
    icon: null,
    title: "Открывай конверты",
    body: "Каждый раз ты открываешь конверт и видишь сумму, которую нужно отложить",
  },
  {
    icon: "🏦",
    title: "Куда откладывать деньги?",
    body: "Ты сам откладываешь деньги — наличными, на карту или отдельный счёт.\n\nПриложение подсказывает сумму и помогает отслеживать прогресс.",
  },
  {
    icon: "🎯",
    title: "Начнём?",
    body: "Создай первую цель и попробуй",
  },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [envelopeOpen, setEnvelopeOpen] = useState(false);

  const handleSkip = () => {
    markDone();
    router.push("/dashboard");
  };

  const handleNext = () => {
    setEnvelopeOpen(false);
    setStep((s) => s + 1);
  };

  const handleFinish = () => {
    markDone();
    router.push("/dashboard");
  };

  const screen = SCREENS[step];
  const isLast = step === SCREENS.length - 1;

  return (
    <div className="relative flex flex-col min-h-screen px-6 pb-8 text-center">
      <button
        onClick={handleSkip}
        className="absolute top-6 right-6 text-sm opacity-40 hover:opacity-70 transition-opacity z-10"
      >
        Пропустить
      </button>

      <div className="flex-1 flex flex-col items-center justify-center px-2">
        {step === 1 ? (
          <div
            onClick={() => setEnvelopeOpen(true)}
            className={`text-6xl mb-6 w-24 h-24 flex items-center justify-center rounded-2xl bg-tg-secondary cursor-pointer select-none transition-all duration-300 ${
              envelopeOpen ? "scale-105" : "active:scale-95"
            }`}
          >
            {envelopeOpen ? "📭" : "📬"}
          </div>
        ) : (
          <div className="text-6xl mb-6">{screen.icon}</div>
        )}

        {step === 1 && envelopeOpen && (
          <p className="text-2xl font-bold mb-2 transition-all duration-300">1 000 ₽</p>
        )}
        {step === 1 && !envelopeOpen && (
          <p className="text-xs opacity-40 mb-2">Нажми, чтобы открыть</p>
        )}

        <h1 className="text-2xl font-bold mb-3">{screen.title}</h1>
        <p className="text-sm opacity-70 leading-relaxed max-w-xs whitespace-pre-line">
          {screen.body}
        </p>
      </div>

      <div className="flex gap-2 justify-center mb-6">
        {SCREENS.map((_, i) => (
          <div
            key={i}
            className={`h-2 rounded-full transition-all duration-300 ${
              i === step
                ? "bg-[var(--tg-theme-button-color,#2AABEE)] w-4"
                : "bg-[var(--tg-theme-hint-color,#999)] w-2"
            }`}
          />
        ))}
      </div>

      <button
        onClick={isLast ? handleFinish : handleNext}
        className="btn-primary w-full"
      >
        {isLast ? "Начать" : "Дальше"}
      </button>
    </div>
  );
}
