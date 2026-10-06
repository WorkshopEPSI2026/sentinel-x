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
    error.value =
      err.response?.data?.detail ??
      "Une erreur est survenue.";
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
  <main class="flex min-h-screen items-center justify-center bg-slate-950 px-4">
    <div
      class="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-xl"
    >
      <!-- Header -->
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-white">Sentinel-X</h1>

        <p class="mt-2 text-sm text-slate-400">
          {{ isLogin ? "Connexion à votre compte" : "Créer un compte" }}
        </p>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="mb-5 rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-sm text-red-400"
      >
        {{ error }}
      </div>

      <!-- Success -->
      <div
        v-if="success"
        class="mb-5 rounded-lg border border-green-900 bg-green-950/50 px-4 py-3 text-sm text-green-400"
      >
        {{ success }}
      </div>

      <form class="space-y-5" @submit.prevent="handleSubmit">
        <!-- Username -->
        <div v-if="!isLogin">
          <label
            for="username"
            class="mb-2 block text-sm font-medium text-slate-300"
          >
            Nom d'utilisateur
          </label>

          <input
            id="username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            class="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-white outline-none transition focus:border-blue-500"
            placeholder="john"
          />
        </div>

        <!-- Email -->
        <div>
          <label
            for="email"
            class="mb-2 block text-sm font-medium text-slate-300"
          >
            Email
          </label>

          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            class="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-white outline-none transition focus:border-blue-500"
            placeholder="john@example.com"
          />
        </div>

        <!-- Password -->
        <div>
          <label
            for="password"
            class="mb-2 block text-sm font-medium text-slate-300"
          >
            Mot de passe
          </label>

          <input
            id="password"
            v-model="password"
            type="password"
            required
            :autocomplete="isLogin ? 'current-password' : 'new-password'"
            class="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-white outline-none transition focus:border-blue-500"
            placeholder="••••••••"
          />
        </div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
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
      <div class="mt-6 text-center text-sm text-slate-400">
        <span>
          {{
            isLogin
              ? "Vous n'avez pas encore de compte ?"
              : "Vous avez déjà un compte ?"
          }}
        </span>

        <button
          type="button"
          class="ml-1 font-medium text-blue-500 hover:text-blue-400"
          @click="toggleMode"
        >
          {{ isLogin ? "Créer un compte" : "Se connecter" }}
        </button>
      </div>
    </div>
  </main>
</template>
