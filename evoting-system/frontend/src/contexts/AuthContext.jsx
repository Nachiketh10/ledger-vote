import { createContext, useContext, useEffect, useState, useCallback } from "react";
import * as authService from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    authService.restoreSession().then((restoredUser) => {
      setUser(restoredUser);
      setIsLoading(false);
    });

    const handleExpired = () => setUser(null);
    window.addEventListener("evoting:session-expired", handleExpired);
    return () => window.removeEventListener("evoting:session-expired", handleExpired);
  }, []);

  const login = useCallback(async (email, password, role) => {
    const loggedInUser = await authService.login(email, password, role);
    setUser(loggedInUser);
    return loggedInUser;
  }, []);

  const register = useCallback(async (payload) => {
    const registeredUser = await authService.registerVoter(payload);
    setUser(registeredUser);
    return registeredUser;
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  // Re-fetches the current user from the server and updates the cached
  // copy everywhere the app reads `user` from — used right after face
  // registration so has_face_registered reflects immediately, without
  // needing a page refresh.
  const refreshUser = useCallback(async () => {
    const freshUser = await authService.fetchCurrentUser();
    setUser(freshUser);
    return freshUser;
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, role: user?.role ?? null, isLoading, login, register, logout, refreshUser, setUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
