import { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { authService } from "@/services/api/auth";
import { setUser, setToken, clearAuth } from "@/state/slices/auth";
import type { RootState } from "@/state/store";
import type { User, LoginRequest, RegisterRequest } from "@/types/api";

export function useAuth() {
  const dispatch = useDispatch();
  const auth = useSelector((state: RootState) => state.auth);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      try {
        const response = await authService.login(credentials);
        if (response.access_token) {
          dispatch(setToken(response.access_token));
          if (response.user) {
            dispatch(setUser(response.user));
          }
        }
        return response;
      } catch (error) {
        console.error("Login error:", error);
        throw error;
      }
    },
    [dispatch]
  );

  const register = useCallback(
    async (data: RegisterRequest) => {
      try {
        const user = await authService.register(data);
        return user;
      } catch (error) {
        console.error("Register error:", error);
        throw error;
      }
    },
    []
  );

  const logout = useCallback(() => {
    authService.logout();
    dispatch(clearAuth());
  }, [dispatch]);

  const checkAuth = useCallback(async () => {
    try {
      const token = authService.getToken();
      if (!token) {
        dispatch(clearAuth());
        return null;
      }
      const user = await authService.getCurrentUser();
      dispatch(setUser(user));
      dispatch(setToken(token));
      return user;
    } catch (error) {
      console.error("Auth check error:", error);
      dispatch(clearAuth());
      if (typeof window !== "undefined") {
        document.cookie = "auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      }
      return null;
    }
  }, [dispatch]);

  return {
    ...auth,
    login,
    register,
    logout,
    checkAuth,
    isAuthenticated: !!auth.token,
    isAdmin: auth.user?.role === "admin",
  };
}
