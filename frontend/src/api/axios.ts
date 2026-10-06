import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "../services/tokens";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});


/*
 * Ajoute automatiquement l'access token
 * aux requêtes protégées.
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = getAccessToken();

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
);


/*
 * Gestion des access tokens expirés.
 */
api.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (
      error.response?.status !== 401 ||
      !originalRequest
    ) {
      return Promise.reject(error);
    }

    /*
     * Empêche une boucle infinie.
     */
    if (
      (originalRequest as InternalAxiosRequestConfig & {
        _retry?: boolean;
      })._retry
    ) {
      clearTokens();

      window.location.href = "/auth";

      return Promise.reject(error);
    }

    (
      originalRequest as InternalAxiosRequestConfig & {
        _retry?: boolean;
      }
    )._retry = true;

    const refreshToken = getRefreshToken();

    if (!refreshToken) {
      clearTokens();

      window.location.href = "/auth";

      return Promise.reject(error);
    }

    try {
      /*
       * Attention :
       * on utilise axios directement et non `api`
       * pour éviter que l'intercepteur intercepte
       * lui-même la requête /refresh.
       */
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/auth/refresh`,
        {
          refresh_token: refreshToken,
        },
      );

      const {
        access_token,
        refresh_token,
      } = response.data;

      /*
       * Le backend effectue une rotation :
       * l'ancien refresh token est donc remplacé.
       */
      setTokens(
        access_token,
        refresh_token,
      );

      originalRequest.headers.Authorization =
        `Bearer ${access_token}`;

      return api(originalRequest);
    } catch (refreshError) {
      clearTokens();

      window.location.href = "/auth";

      return Promise.reject(refreshError);
    }
  },
);

export default api;