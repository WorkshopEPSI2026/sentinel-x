<script setup lang="ts">
import { useRouter } from "vue-router";

import { useTelemetry } from "../composables/useTelemetry";
import { useAlerts } from "../composables/useAlerts";
import { useAuth } from "../composables/useAuth";

import SystemStatus from "../components/dashboard/SystemStatus.vue";
import CameraCard from "../components/dashboard/CameraCard.vue";
import SensorOverview from "../components/dashboard/SensorOverview.vue";
import ActiveAlerts from "../components/dashboard/ActiveAlerts.vue";

import TelemetryChart from "../components/telemetry/TelemetryChart.vue";
import AlertList from "../components/alerts/AlertList.vue";

import { useCamera } from "../composables/useCamera";

const router = useRouter();
const { status: cameraStatus, connected: cameraConnected } = useCamera();

const { telemetry, telemetryHistory, connected, error } = useTelemetry();

const { alerts, activeAlerts } = useAlerts();

const { user, logout } = useAuth();

async function handleLogout() {
  await logout();

  await router.push({
    name: "auth",
  });
}
</script>

<template>
  <main class="min-h-screen bg-gray-100 text-gray-900 pt-16">
    <!-- ====================================================== -->
    <!-- NAVBAR                                                  -->
    <!-- ====================================================== -->

    <nav
      class="fixed left-0 right-0 top-0 z-50 border-b border-gray-200 bg-white"
    >
      <div class="mx-auto flex h-16 items-center justify-between px-6 md:px-15">
        <!-- Logo -->
        <RouterLink to="/dashboard" class="text-xl font-bold tracking-tight">
          Sentinel-X
        </RouterLink>

        <!-- Navigation -->
        <div class="hidden items-center gap-8 md:flex">
          <RouterLink to="/dashboard" class="text-sm font-medium text-gray-900">
            Dashboard
          </RouterLink>

          <RouterLink
            to="/surveillance"
            class="text-sm text-gray-600 transition hover:text-gray-900"
          >
            Surveillance
          </RouterLink>

          <RouterLink
            to="/sensors"
            class="text-sm text-gray-600 transition hover:text-gray-900"
          >
            Capteurs
          </RouterLink>

          <RouterLink
            to="/alerts"
            class="flex items-center gap-2 text-sm text-gray-600 transition hover:text-gray-900"
          >
            Alertes

            <span
              v-if="activeAlerts.length > 0"
              class="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600"
            >
              {{ activeAlerts.length }}
            </span>
          </RouterLink>

          <RouterLink
            to="/history"
            class="text-sm text-gray-600 transition hover:text-gray-900"
          >
            Historique
          </RouterLink>
        </div>

        <!-- User -->
        <div class="flex items-center gap-2">
          <RouterLink
            to="/profile"
            class="rounded-lg px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-100"
          >
            {{ user?.username ?? "Utilisateur" }}
          </RouterLink>

          <button
            type="button"
            class="hidden rounded-lg px-3 py-2 text-sm text-red-600 transition hover:bg-red-50 sm:block"
            @click="handleLogout"
          >
            Déconnexion
          </button>
        </div>
      </div>
    </nav>

    <!-- ====================================================== -->
    <!-- CONTENT                                                 -->
    <!-- ====================================================== -->

    <div class="mx-auto px-6 md:px-15 py-5">
      <!-- Header -->
      <div
        class="mb-10 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between"
      >
        <div>
          <span
            class="inline-flex rounded-full bg-gray-200 px-3 py-1 text-sm font-medium text-gray-700"
          >
            Edge Security & IoT
          </span>

          <h1 class="mt-5 text-4xl font-bold tracking-tight text-gray-900">
            Centre de supervision
          </h1>

          <p class="mt-3 max-w-2xl text-gray-600">
            Surveillez en temps réel l'état de votre infrastructure Sentinel-X.
          </p>
        </div>

        <SystemStatus :connected="connected" />
      </div>

      <!-- Erreur -->
      <div
        v-if="error"
        class="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        {{ error }}
      </div>

      <!-- ==================================================== -->
      <!-- SURVEILLANCE PRINCIPALE                              -->
      <!-- ==================================================== -->

      <section class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CameraCard />
        
        <SensorOverview
          :telemetry="telemetry"
          :connected="connected"
          :camera-status="cameraStatus"
          :camera-connected="cameraConnected"
        />

      </section>

      <!-- ==================================================== -->
      <!-- ALERTES                                               -->
      <!-- ==================================================== -->

      <section class="mt-8">
        <ActiveAlerts :alerts="alerts" :active-alerts="activeAlerts" />
      </section>

      <!-- ==================================================== -->
      <!-- GRAPHIQUES                                            -->
      <!-- ==================================================== -->

      <section class="mt-10">
        <div class="mb-6">
          <h2 class="text-2xl font-bold tracking-tight text-gray-900">
            Télémétrie
          </h2>

          <p class="mt-2 text-gray-600">
            Évolution des données environnementales collectées par l'ESP8266.
          </p>
        </div>

        <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <!-- Température -->
          <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h3 class="mb-5 font-semibold text-gray-900">Température</h3>

            <TelemetryChart
              :telemetry-history="telemetryHistory"
              label="Température"
              data-key="temperature"
              unit="°C"
            />
          </div>

          <!-- Humidité -->
          <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h3 class="mb-5 font-semibold text-gray-900">Humidité</h3>

            <TelemetryChart
              :telemetry-history="telemetryHistory"
              label="Humidité"
              data-key="humidity"
              unit="%"
            />
          </div>

          <!-- Gaz -->
          <div
            class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm lg:col-span-2"
          >
            <h3 class="mb-5 font-semibold text-gray-900">Gaz</h3>

            <TelemetryChart
              :telemetry-history="telemetryHistory"
              label="Gaz"
              data-key="gas"
              unit="ppm"
            />
          </div>
        </div>
      </section>

      <!-- ==================================================== -->
      <!-- HISTORIQUE DES ALERTES                                -->
      <!-- ==================================================== -->

      <section class="mt-10">
        <div class="mb-6">
          <h2 class="text-2xl font-bold tracking-tight text-gray-900">
            Historique des alertes
          </h2>

          <p class="mt-2 text-gray-600">
            Événements détectés par le système de supervision.
          </p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <AlertList :alerts="alerts" />
        </div>
      </section>

      <!-- ==================================================== -->
      <!-- FOOTER                                                -->
      <!-- ==================================================== -->

      <footer
        class="mt-12 flex flex-col gap-2 border-t border-gray-200 py-6 text-sm text-gray-500 md:flex-row md:items-center md:justify-between"
      >
        <p>© 2026 Sentinel-X</p>

        <p>Edge Security & IoT</p>
      </footer>
    </div>
  </main>
</template>
