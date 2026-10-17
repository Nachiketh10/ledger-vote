import api from "./api";
import { setAccessToken } from "./tokenStore";

const REFRESH_KEY = "evoting-refresh-token";

export async function login(email, password, role) {
  const { data } = await api.post("/auth/login", { email, password, role });
  setAccessToken(data.data.access_token);
  window.localStorage.setItem(REFRESH_KEY, data.data.refresh_token);
  return data.data.user;
}

export async function registerVoter(payload) {
  const { data } = await api.post("/auth/register", payload);
  setAccessToken(data.data.access_token);
  window.localStorage.setItem(REFRESH_KEY, data.data.refresh_token);
  return data.data.user;
}

export async function logout() {
  const refreshToken = window.localStorage.getItem(REFRESH_KEY);
  try {
    if (refreshToken) {
      await api.post(
        "/auth/logout",
        {},
        { headers: { Authorization: `Bearer ${refreshToken}` } }
      );
    }
  } finally {
    setAccessToken(null);
    window.localStorage.removeItem(REFRESH_KEY);
  }
}

export async function fetchCurrentUser() {
  const { data } = await api.get("/auth/me");
  return data.data;
}

/** Called once on app load to silently restore a session from the
 * stored refresh token, so a page reload doesn't force a re-login. */
export async function restoreSession() {
  const refreshToken = window.localStorage.getItem(REFRESH_KEY);
  if (!refreshToken) return null;

  try {
    const { data } = await api.post(
      "/auth/refresh",
      {},
      { headers: { Authorization: `Bearer ${refreshToken}` } }
    );
    setAccessToken(data.data.access_token);
    window.localStorage.setItem(REFRESH_KEY, data.data.refresh_token);
    return await fetchCurrentUser();
  } catch {
    window.localStorage.removeItem(REFRESH_KEY);
    return null;
  }
}
