import "./globals.css";
import Script from "next/script";
import QueryProvider from "@/components/QueryProvider";
import ErrorBoundary from "@/components/ErrorBoundary";
import AchievementToast from "@/components/AchievementToast";
import TelegramBootstrap from "@/components/TelegramBootstrap";

export const metadata = {
  title: "Копилка",
  description: "Telegram Mini App для накопления денег",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <head>
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
      </head>
      <body>
        <ErrorBoundary>
          <TelegramBootstrap />
          <QueryProvider>{children}</QueryProvider>
          <AchievementToast />
        </ErrorBoundary>
      </body>
    </html>
  );
}
