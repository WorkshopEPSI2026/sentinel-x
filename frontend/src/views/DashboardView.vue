<script setup lang="ts">
import { useTelemetry } from "../composables/useTelemetry";
import TelemetryChart from "../components/telemetry/TelemetryChart.vue";

const { telemetry, telemetryHistory, connected, error } = useTelemetry();
</script>

<template>
  <main class="p-6">
    <nav
      class="border-b border-gray-200 bg-white fixed top-0 left-0 right-0 z-50 shadow"
    >
      <div
        class="mx-auto flex h-16 max-w-7xl items-center justify-between px-6"
      >
        <!-- Logo -->
        <RouterLink to="/dashboard" class="text-xl font-bold text-gray-900">
          Sentinel-X
        </RouterLink>

        <!-- Navigation -->
        <div class="flex items-center gap-8">
          <RouterLink to="/dashboard" class="text-sm font-medium text-gray-900">
            Dashboard
          </RouterLink>

          <RouterLink
            to="/surveillance"
            class="text-sm text-gray-600 hover:text-gray-900"
          >
            Surveillance
          </RouterLink>

          <RouterLink
            to="/sensors"
            class="text-sm text-gray-600 hover:text-gray-900"
          >
            Capteurs
          </RouterLink>

          <RouterLink
            to="/alerts"
            class="text-sm text-gray-600 hover:text-gray-900"
          >
            Alertes
            <span
              class="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600"
            >
              3
            </span>
          </RouterLink>

          <RouterLink
            to="/history"
            class="text-sm text-gray-600 hover:text-gray-900"
          >
            Historique
          </RouterLink>
        </div>

        <!-- User -->
        <button
          class="rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-100"
        >
          Jules
        </button>
      </div>
    </nav>

    <div class="px-2 md:px-6 lg-8 py-8">
      <p class="mt-2">
        WebSocket :

        <span :class="connected ? 'text-green-500' : 'text-red-500'">
          {{ connected ? "Connecté" : "Déconnecté" }}
        </span>
      </p>

      <p v-if="error" class="text-red-500">
        {{ error }}
      </p>

      <div class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- États actuels du site (température, humidité, etc.) -->
        <div v-if="telemetry" class="grid grid-cols-2 gap-4">
          <div class="p-4 rounded-lg bg-gray-100">
            <p class="text-sm text-gray-500">Température</p>

            <p class="text-2xl font-bold">{{ telemetry.temperature }} °C</p>
          </div>

          <div class="p-4 rounded-lg bg-gray-100">
            <p class="text-sm text-gray-500">Humidité</p>

            <p class="text-2xl font-bold">{{ telemetry.humidity }} %</p>
          </div>

          <div class="p-4 rounded-lg bg-gray-100">
            <p class="text-sm text-gray-500">Gaz</p>

            <p class="text-2xl font-bold">
              {{ telemetry.gas }}
            </p>
          </div>
          

          <div class="p-4 rounded-lg bg-gray-100">
            <p class="text-sm text-gray-500">Présence</p>

            <p class="text-2xl font-bold">
              {{ telemetry.presence ? "Détectée" : "Aucune" }}
            </p>
          </div>
        </div>

        <!-- Caméra -->
        <div class="p-4 rounded-lg bg-gray-100 w-full h-100">
          <p class="text-sm text-gray-500">Caméra</p>
          <img src="" alt="Caméra" class="mt-2" />
        </div>

      </div>

      <p class="mt-6 text-sm text-gray-500">
        {{ telemetryHistory.length }} mesures chargées
      </p>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <div class="p-4 rounded-lg bg-white shadow">
          <h2 class="font-semibold mb-4">Température</h2>

          <TelemetryChart
            :telemetry-history="telemetryHistory"
            label="Température"
            data-key="temperature"
            unit="°C"
          />
        </div>

        <div class="p-4 rounded-lg bg-white shadow">
          <h2 class="font-semibold mb-4">Humidité</h2>

          <TelemetryChart
            :telemetry-history="telemetryHistory"
            label="Humidité"
            data-key="humidity"
            unit="%"
          />
        </div>

        <div class="p-4 rounded-lg bg-white shadow lg:col-span-2">
          <h2 class="font-semibold mb-4">Gaz</h2>

          <TelemetryChart
            :telemetry-history="telemetryHistory"
            label="Gaz"
            data-key="gas"
            unit="ppm"
          />
        </div>
      </div>
    </div>
  </main>
</template>
