import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "./tokens";

type RetryableConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/*
 * Endpoints qui gèrent eux-mêmes leurs erreurs :
 * pas de refresh, pas de redirection.
 */
const AUTH_ENDPOINTS = [
  "/auth/login",
  "/auth/register",
  "/auth/refresh",
];

function isAuthEndpoint(url?: string): boolean {
  return AUTH_ENDPOINTS.some((path) => url?.includes(path));
}

/*
 * Termine la session sans recharger la page.
 * Imports dynamiques pour éviter les cycles.
 */
async function endSession(): Promise<void> {
  clearTokens();

  const { useAuth } = await import("../composables/useAuth");
  const { accessToken, refreshToken, user } = useAuth();

  accessToken.value = null;
  refreshToken.value = null;
  user.value = null;

  const { default: router } = await import("../router/router");

  if (router.currentRoute.value.name !== "auth") {
    await router.push({ name: "auth" });
  }
}

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = getAccessToken();

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
);

api.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableConfig | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      isAuthEndpoint(originalRequest.url)
    ) {
      return Promise.reject(error);
    }

    // Empêche une boucle infinie.
    if (originalRequest._retry) {
      await endSession();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    const refreshToken = getRefreshToken();

    if (!refreshToken) {
      await endSession();
      return Promise.reject(error);
    }

    try {
      // axios direct (pas `api`) pour ne pas repasser dans l'intercepteur.
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/auth/refresh`,
        { refresh_token: refreshToken },
      );

      const { access_token, refresh_token } = response.data;

      // Rotation : l'ancien refresh token est remplacé.
      setTokens(access_token, refresh_token);

      // Garde l'état réactif de useAuth synchronisé.
      const { useAuth } = await import("../composables/useAuth");
      const auth = useAuth();
      auth.accessToken.value = access_token;
      auth.refreshToken.value = refresh_token;

      originalRequest.headers.Authorization = `Bearer ${access_token}`;

      return api(originalRequest);
    } catch (refreshError) {
      await endSession();
      return Promise.reject(refreshError);
    }
  },
);

export default api;