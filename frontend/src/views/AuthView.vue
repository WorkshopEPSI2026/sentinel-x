<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth";

const router = useRouter();

const {
  login,
  register,
} = useAuth();

const isLogin = ref(true);

const email = ref("");
const username = ref("");
const password = ref("");

const loading = ref(false);
const error = ref("");
const success = ref("");

function getAuthErrorMessage(err: any): string {
  /*
   * Pas de réponse du serveur :
   * problème réseau, backend arrêté, mauvaise URL, etc.
   */
  if (!err?.response) {
    return "Impossible de contacter le serveur. Vérifiez que le serveur est disponible.";
  }

  const status = err.response.status;
  const detail = err.response.data?.detail;

  /*
   * Identifiants incorrects
   */
  if (status === 401) {
    return "Email ou mot de passe incorrect.";
  }

  /*
   * Compte désactivé
   */
  if (status === 403) {
    return "Votre compte est désactivé. Contactez un administrateur.";
  }

  /*
   * Ressource déjà existante
   * Exemple :
   * "Email or username already registered"
   */
  if (status === 409) {
    return "Cet email ou nom d'utilisateur est déjà utilisé.";
  }

  /*
   * Erreur de validation FastAPI
   *
   * FastAPI peut renvoyer :
   *
   * detail: [
   *   {
   *     loc: ["body", "email"],
   *     msg: "...",
   *     type: "..."
   *   }
   * ]
   */
  if (status === 422) {
    if (Array.isArray(detail)) {
      const fields = detail
        .map((item: any) => item?.loc?.at(-1))
        .filter(Boolean);

      if (fields.includes("email")) {
        return "Veuillez saisir une adresse email valide.";
      }

      if (fields.includes("username")) {
        return "Le nom d'utilisateur n'est pas valide.";
      }

      if (fields.includes("password")) {
        return "Le mot de passe ne respecte pas les règles requises.";
      }

      return "Certaines informations saisies sont invalides.";
    }

    return "Certaines informations saisies sont invalides.";
  }

  /*
   * Erreur serveur
   */
  if (status >= 500) {
    return "Une erreur interne du serveur est survenue. Veuillez réessayer plus tard.";
  }

  /*
   * Cas où le backend nous renvoie une erreur
   * connue mais différente.
   */
  if (typeof detail === "string") {
    switch (detail) {
      case "Invalid credentials":
        return "Email ou mot de passe incorrect.";

      case "Email or username already registered":
        return "Cet email ou nom d'utilisateur est déjà utilisé.";

      case "User account is disabled":
        return "Votre compte est désactivé. Contactez un administrateur.";

      case "Invalid refresh token":
        return "Votre session a expiré. Veuillez vous reconnecter.";

      case "Refresh token already revoked":
        return "Votre session a expiré. Veuillez vous reconnecter.";

      default:
        break;
    }
  }

  /*
   * Erreur inconnue
   */
  return "Une erreur est survenue. Veuillez réessayer.";
}

async function handleSubmit() {
  loading.value = true;

  // On efface l'ancien message uniquement
  // lorsqu'une nouvelle tentative commence.
  error.value = "";
  success.value = "";

  try {
    if (isLogin.value) {
      await login({
        email: email.value,
        password: password.value,
      });

      await router.push({
        name: "dashboard",
      });

      return;
    }

    await register({
      email: email.value,
      username: username.value,
      password: password.value,
    });

    success.value =
      "Compte créé avec succès. Vous pouvez maintenant vous connecter.";

    isLogin.value = true;

    username.value = "";
    password.value = "";
  } catch (err: any) {
    error.value = getAuthErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

function toggleMode() {
  isLogin.value = !isLogin.value;

  error.value = "";
  success.value = "";
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-gray-100 px-4">
    <div class="relative w-full max-w-md rounded-xl bg-white p-8 shadow">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-2xl font-bold text-gray-900">
          Sentinel-X
        </h1>

        <!-- Retour à l'accueil -->
        <RouterLink
          to="/"
          aria-label="Retour à l'accueil"
          title="Retour à l'accueil"
          class="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 transition hover:bg-gray-100 hover:text-gray-900"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </RouterLink>

        <p class="mt-1 text-sm text-gray-500">
          {{ isLogin ? "Connexion à votre compte" : "Créer un compte" }}
        </p>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
        role="alert"
      >
        {{ error }}
      </div>

      <!-- Success -->
      <div
        v-if="success"
        class="mb-5 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-600"
        role="status"
      >
        {{ success }}
      </div>

      <form
        class="space-y-5"
        @submit.prevent="handleSubmit"
      >
        <!-- Username -->
        <div v-if="!isLogin">
          <label
            for="username"
            class="mb-2 block text-sm font-medium text-gray-700"
          >
            Nom d'utilisateur
          </label>

          <input
            id="username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            placeholder="john"
            class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 outline-none transition focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
          />
        </div>

        <!-- Email -->
        <div>
          <label
            for="email"
            class="mb-2 block text-sm font-medium text-gray-700"
          >
            Email
          </label>

          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            placeholder="john@example.com"
            class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 outline-none transition focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
          />
        </div>

        <!-- Password -->
        <div>
          <label
            for="password"
            class="mb-2 block text-sm font-medium text-gray-700"
          >
            Mot de passe
          </label>

          <input
            id="password"
            v-model="password"
            type="password"
            required
            :autocomplete="
              isLogin
                ? 'current-password'
                : 'new-password'
            "
            placeholder="••••••••"
            class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 outline-none transition focus:border-gray-500 focus:ring-1 focus:ring-gray-500"
          />
        </div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-lg bg-gray-900 px-4 py-3 font-medium text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {{
            loading
              ? "Chargement..."
              : isLogin
                ? "Se connecter"
                : "Créer mon compte"
          }}
        </button>
      </form>

      <!-- Toggle -->
      <div class="mt-6 text-center text-sm text-gray-500">
        <span>
          {{
            isLogin
              ? "Vous n'avez pas encore de compte ?"
              : "Vous avez déjà un compte ?"
          }}
        </span>

        <button
          type="button"
          class="ml-1 font-medium text-gray-900 hover:underline"
          @click="toggleMode"
        >
          {{ isLogin ? "Créer un compte" : "Se connecter" }}
        </button>
      </div>
    </div>
  </main>
</template>