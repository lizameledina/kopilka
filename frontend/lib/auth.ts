import { getInitData } from "./telegram";
import { api, setToken, clearToken, getToken, detectTimezone } from "./api";

export async function authenticate(): Promise<boolean> {
  const initData = getInitData();
  if (!initData) {
    return !!getToken();
  }

  try {
    const data = await api.auth.telegram(initData, detectTimezone());
    setToken(data.token);
    return true;
  } catch {
    clearToken();
    return false;
  }
}

export function isAuthenticated(): boolean {
  if (typeof window === "undefined") return false;
  return !!getToken();
}