<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { useAuth } from "../composables/useAuth";

const router = useRouter();

const { login, register } = useAuth();

const isLogin = ref(true);

const email = ref("");
const username = ref("");
const password = ref("");

const loading = ref(false);
const error = ref("");
const success = ref("");

async function handleSubmit() {
  loading.value = true;
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
    error.value = err.response?.data?.detail ?? "Une erreur est survenue.";
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
        <h1 class="text-2xl font-bold text-gray-900">Sentinel-X</h1>

        <!-- bouton de fermeture -->
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
        class="mb-5 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600"
      >
        {{ error }}
      </div>

      <!-- Success -->
      <div
        v-if="success"
        class="mb-5 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-600"
      >
        {{ success }}
      </div>

      <form class="space-y-5" @submit.prevent="handleSubmit">
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
            :autocomplete="isLogin ? 'current-password' : 'new-password'"
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
