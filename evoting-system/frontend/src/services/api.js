import axios from "axios";
import { getAccessToken, setAccessToken } from "./tokenStore";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;

    // Don't try to refresh the refresh call itself, or requests that
    // have already been retried once.
    if (!response || response.status !== 401 || config._retried || config.url === "/auth/refresh") {
      return Promise.reject(error);
    }

    const refreshToken = window.localStorage.getItem("evoting-refresh-token");
    if (!refreshToken) {
      return Promise.reject(error);
    }

    config._retried = true;

    try {
      // Multiple simultaneous 401s should trigger only ONE refresh call,
      // not one per failed request — share the in-flight promise.
      if (!refreshPromise) {
        refreshPromise = axios
          .post("/api/auth/refresh", null, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          })
          .finally(() => {
            refreshPromise = null;
          });
      }
      const refreshResponse = await refreshPromise;
      const { access_token, refresh_token } = refreshResponse.data.data;

      setAccessToken(access_token);
      window.localStorage.setItem("evoting-refresh-token", refresh_token);

      config.headers.Authorization = `Bearer ${access_token}`;
      return api(config);
    } catch (refreshError) {
      setAccessToken(null);
      window.localStorage.removeItem("evoting-refresh-token");
      window.dispatchEvent(new CustomEvent("evoting:session-expired"));
      return Promise.reject(refreshError);
    }
  }
);

export default api;
