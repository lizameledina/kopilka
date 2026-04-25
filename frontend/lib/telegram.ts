export function getTelegramWebApp() {
  if (typeof window === "undefined") return null;
  return (window as any).Telegram?.WebApp || null;
}

export async function waitForTelegramWebApp(
  timeoutMs: number = 1500,
  intervalMs: number = 50
): Promise<any | null> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const wa = getTelegramWebApp();
    if (wa) return wa;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return getTelegramWebApp();
}

export function getInitData(): string | null {
  const webapp = getTelegramWebApp();
  return webapp?.initData || null;
}

export function getTelegramUser(): {
  id: number;
  first_name?: string;
  username?: string;
} | null {
  const webapp = getTelegramWebApp();
  return webapp?.initDataUnsafe?.user || null;
}

export function getThemeParams(): Record<string, string> {
  const webapp = getTelegramWebApp();
  return webapp?.themeParams || {};
}

export function applyThemeParams(params: Record<string, string>) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;

  const map: Record<string, string> = {
    bg_color: "--tg-theme-bg-color",
    text_color: "--tg-theme-text-color",
    hint_color: "--tg-theme-hint-color",
    button_color: "--tg-theme-button-color",
    button_text_color: "--tg-theme-button-text-color",
    secondary_bg_color: "--tg-theme-secondary-bg-color",
  };

  for (const [tgKey, cssVar] of Object.entries(map)) {
    const value = params?.[tgKey];
    if (typeof value === "string" && value.length > 0) {
      root.style.setProperty(cssVar, value);
    }
  }
}

export function ready() {
  const webapp = getTelegramWebApp();
  webapp?.ready?.();
}

export function close() {
  const webapp = getTelegramWebApp();
  webapp?.close?.();
}
