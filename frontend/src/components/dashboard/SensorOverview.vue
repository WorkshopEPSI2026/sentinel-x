<script setup lang="ts">
import SensorCard from "./SensorCard.vue";

import type { Telemetry } from "../../types/telemetry";
import type { CameraStatus } from "../../types/camera";

defineProps<{
  telemetry: Telemetry | null;
  connected: boolean;
  cameraStatus: CameraStatus | null;
  cameraConnected: boolean;
}>();
</script>

<template>
  <div
    class="rounded-2xl border border-gray-200 bg-white shadow-sm"
  >
    <!-- Header -->
    <div
      class="border-b border-gray-200 px-5 py-4"
    >
      <p class="text-sm font-semibold text-gray-900">
        État des capteurs
      </p>

      <p class="mt-0.5 text-xs text-gray-500">
        Données reçues en temps réel
      </p>
    </div>

    <!-- Capteurs -->
    <div class="grid grid-cols-2 gap-3 p-4">

      <SensorCard
        icon="🌡️"
        label="Température"
        :value="telemetry?.temperature ?? '--'"
        unit="°C"
        status="normal"
      />

      <SensorCard
        icon="💧"
        label="Humidité"
        :value="telemetry?.humidity ?? '--'"
        unit="%"
        status="normal"
      />

      <SensorCard
        icon="☁️"
        label="Niveau de gaz"
        :value="telemetry?.gas ?? '--'"
        status="normal"
      />

      <SensorCard
        icon="👤"
        label="Présence"
        :value="telemetry?.presence ? 'Détectée' : 'Aucune'"
        :status="
          telemetry?.presence
            ? 'danger'
            : 'normal'
        "
      />

    </div>

    <!-- Connexion ESP8266 -->
    <div
      class="mx-4 mb-3 flex items-center justify-between rounded-xl border border-gray-100 bg-gray-50 px-4 py-3"
    >
      <div class="flex items-center gap-3">

        <span
          class="h-2.5 w-2.5 rounded-full"
          :class="
            connected
              ? 'bg-green-500'
              : 'bg-red-500'
          "
        />

        <div>
          <p class="text-xs font-semibold text-gray-900">
            ESP8266
          </p>

          <p class="text-[11px] text-gray-500">
            Transmission MQTT
          </p>
        </div>

      </div>

      <span
        class="text-xs font-medium"
        :class="
          connected
            ? 'text-green-600'
            : 'text-red-600'
        "
      >
        {{ connected ? "Connecté" : "Déconnecté" }}
      </span>
    </div>

    <!-- Surveillance IA -->
    <div
      class="mx-4 mb-4 rounded-xl border border-gray-200 bg-gray-50 p-4"
    >
      <div class="flex items-center justify-between">

        <div>
          <p class="text-xs font-semibold text-gray-900">
            Surveillance IA
          </p>

          <p class="mt-0.5 text-[11px] text-gray-500">
            Détection de présence par YOLO
          </p>
        </div>

        <div class="flex items-center gap-2">

          <span
            class="h-2 w-2 rounded-full"
            :class="
              cameraConnected && cameraStatus?.ai_available
                ? 'bg-green-500'
                : 'bg-red-500'
            "
          />

          <span
            class="text-xs font-medium"
            :class="
              cameraConnected && cameraStatus?.ai_available
                ? 'text-green-600'
                : 'text-red-600'
            "
          >
            {{
              cameraConnected && cameraStatus?.ai_available
                ? "Active"
                : "Indisponible"
            }}
          </span>

        </div>
      </div>

      <div class="mt-3 grid grid-cols-2 gap-3">

        <!-- Détection -->
        <div
          class="rounded-lg border border-gray-200 bg-white px-3 py-2.5"
        >
          <p class="text-[11px] text-gray-500">
            Présence visuelle
          </p>

          <p
            class="mt-1 text-sm font-semibold"
            :class="
              cameraStatus?.person_detected
                ? 'text-red-600'
                : 'text-green-600'
            "
          >
            {{
              cameraStatus?.person_detected
                ? "Détectée"
                : "Aucune"
            }}
          </p>
        </div>

        <!-- Nombre -->
        <div
          class="rounded-lg border border-gray-200 bg-white px-3 py-2.5"
        >
          <p class="text-[11px] text-gray-500">
            Personnes détectées
          </p>

          <p class="mt-1 text-sm font-semibold text-gray-900">
            {{ cameraStatus?.persons_count ?? "--" }}
          </p>
        </div>

      </div>
    </div>
  </div>
</template>