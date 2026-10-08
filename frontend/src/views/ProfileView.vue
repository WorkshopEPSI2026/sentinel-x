<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth";

const router = useRouter();

const {
  user,
  logout,
} = useAuth();

async function handleLogout() {
  await logout();

  await router.push({
    name: "auth",
  });
}
</script>

<template>
  <main class="min-h-screen bg-gray-50 pt-16">
    <!-- Navbar -->
    <nav
      class="fixed top-0 left-0 right-0 z-50 border-b border-gray-200 bg-white shadow"
    >
      <div
        class="mx-auto flex h-16 max-w-7xl items-center justify-between px-6"
      >
        <RouterLink
          to="/dashboard"
          class="text-xl font-bold text-gray-900"
        >
          Sentinel-X
        </RouterLink>

        <div class="flex items-center gap-8">
          <RouterLink
            to="/dashboard"
            class="text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            Dashboard
          </RouterLink>

          <RouterLink
            to="/profile"
            class="text-sm font-medium text-gray-900"
          >
            Profil
          </RouterLink>

          <button
            type="button"
            class="rounded-lg px-3 py-2 text-sm text-red-600 hover:bg-red-50"
            @click="handleLogout"
          >
            Déconnexion
          </button>
        </div>
      </div>
    </nav>

    <!-- Contenu -->
    <div class="mx-auto max-w-4xl px-6 py-10">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">
          Mon profil
        </h1>

        <p class="mt-2 text-gray-500">
          Informations de votre compte Sentinel-X.
        </p>
      </div>

      <div
        v-if="user"
        class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm"
      >
        <!-- En-tête profil -->
        <div class="border-b border-gray-200 px-6 py-6">
          <div class="flex items-center gap-4">
            <div
              class="flex h-14 w-14 items-center justify-center rounded-full bg-gray-900 text-xl font-bold text-white"
            >
              {{ user.username.charAt(0).toUpperCase() }}
            </div>

            <div>
              <h2 class="text-xl font-semibold text-gray-900">
                {{ user.username }}
              </h2>

              <p class="text-sm text-gray-500">
                {{ user.email }}
              </p>
            </div>
          </div>
        </div>

        <!-- Informations -->
        <div class="divide-y divide-gray-100">
          <div class="flex items-center justify-between px-6 py-4">
            <span class="text-sm text-gray-500">
              Nom d'utilisateur
            </span>

            <span class="text-sm font-medium text-gray-900">
              {{ user.username }}
            </span>
          </div>

          <div class="flex items-center justify-between px-6 py-4">
            <span class="text-sm text-gray-500">
              Adresse email
            </span>

            <span class="text-sm font-medium text-gray-900">
              {{ user.email }}
            </span>
          </div>

          <div class="flex items-center justify-between px-6 py-4">
            <span class="text-sm text-gray-500">
              Statut
            </span>

            <span
              class="rounded-full px-3 py-1 text-xs font-medium"
              :class="
                user.is_active
                  ? 'bg-green-100 text-green-700'
                  : 'bg-red-100 text-red-700'
              "
            >
              {{ user.is_active ? "Actif" : "Désactivé" }}
            </span>
          </div>

          <div class="flex items-center justify-between px-6 py-4">
            <span class="text-sm text-gray-500">
              Rôle
            </span>

            <span class="text-sm font-medium text-gray-900">
              {{ user.is_admin ? "Administrateur" : "Utilisateur" }}
            </span>
          </div>

          <div class="flex items-center justify-between px-6 py-4">
            <span class="text-sm text-gray-500">
              Compte créé le
            </span>

            <span class="text-sm font-medium text-gray-900">
              {{ new Date(user.created_at).toLocaleDateString("fr-FR") }}
            </span>
          </div>
        </div>

        <!-- Actions -->
        <div
          class="flex justify-end border-t border-gray-200 bg-gray-50 px-6 py-4"
        >
          <button
            type="button"
            class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            @click="handleLogout"
          >
            Se déconnecter
          </button>
        </div>
      </div>

      <div
        v-else
        class="rounded-xl border border-gray-200 bg-white p-8 text-center shadow-sm"
      >
        <p class="text-gray-500">
          Impossible de récupérer les informations du profil.
        </p>
      </div>
    </div>
  </main>
</template>