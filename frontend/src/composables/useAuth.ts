import { computed, ref } from "vue";

import {
  getMe,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
} from "../services/auth";

import type {
  LoginRequest,
  RegisterRequest,
  User,
} from "../types/auth";

import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "../services/tokens";


const accessToken = ref<string | null>(
  getAccessToken(),
);

const refreshToken = ref<string | null>(
  getRefreshToken(),
);

const user = ref<User | null>(null);

const isAuthenticated = computed(
  () => accessToken.value !== null,
);


async function login(
  data: LoginRequest,
): Promise<void> {
  const response = await loginRequest(data);

  setTokens(
    response.access_token,
    response.refresh_token,
  );

  accessToken.value = response.access_token;
  refreshToken.value = response.refresh_token;

  user.value = await getMe();
}


async function register(
  data: RegisterRequest,
) {
  return registerRequest(data);
}


async function logout(): Promise<void> {
  const currentRefreshToken =
    getRefreshToken();

  if (currentRefreshToken) {
    try {
      await logoutRequest(
        currentRefreshToken,
      );
    } catch {
      // La session locale sera quand même supprimée.
    }
  }

  clearTokens();

  accessToken.value = null;
  refreshToken.value = null;
  user.value = null;
}


async function fetchUser(): Promise<User | null> {
  if (!getAccessToken()) {
    return null;
  }

  try {
    user.value = await getMe();

    return user.value;
  } catch {
    await logout();

    return null;
  }
}


export function useAuth() {
  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUser,
  };
}