import api from "./api";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from "../types/auth";

export async function register(
  data: RegisterRequest,
): Promise<User> {
  const response = await api.post<User>(
    "/api/auth/register",
    data,
  );

  return response.data;
}

export async function login(
  data: LoginRequest,
): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>(
    "/api/auth/login",
    data,
  );

  return response.data;
}

export async function getMe(): Promise<User> {
  const response = await api.get<User>(
    "/api/auth/me",
  );

  return response.data;
}

export async function logout(
  refreshToken: string,
): Promise<void> {
  await api.post("/api/auth/logout", {
    refresh_token: refreshToken,
  });
}

export async function refresh(
  refreshToken: string,
): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>(
    "/api/auth/refresh",
    {
      refresh_token: refreshToken,
    },
  );

  return response.data;
}