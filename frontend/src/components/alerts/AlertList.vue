<script setup lang="ts">
import type { Alert } from "../../composables/useAlerts";

defineProps<{
  alerts: Alert[];
}>();

const LABELS: Record<string, string> = {
  PIR: "Mouvement (PIR)",
  GAS: "Gaz",
  ANOMALY: "Anomalie (IA)",
  INTRUSION: "Intrusion (caméra)",
};

const SOURCES: Record<string, string> = {
  esp: "Boîtier",
  ml: "IA anomalies",
  vision: "IA vision",
};

const label = (alert: Alert) => LABELS[alert.type] ?? alert.type;
const source = (alert: Alert) => SOURCES[alert.source] ?? alert.source;
const time = (alert: Alert) => new Date(alert.created_at).toLocaleTimeString();

function valueText(alert: Alert): string {
  if (alert.value === null) return "";
  if (alert.type === "ANOMALY") return `score ${alert.value.toFixed(3)}`;
  if (alert.type === "GAS") return `gaz ${Math.round(alert.value)}`;
  return "";
}
</script>

<template>
  <div>
    <p v-if="alerts.length === 0" class="text-sm text-gray-500">
      Aucune alerte pour le moment.
    </p>

    <ul v-else class="divide-y divide-gray-100 max-h-80 overflow-y-auto">
      <li
        v-for="alert in alerts"
        :key="alert.id"
        class="flex items-center justify-between gap-4 py-2"
      >
        <div class="flex items-center gap-3">
          <span
            class="rounded-full px-2 py-0.5 text-xs font-semibold"
            :class="
              alert.state === 'TRIGGERED'
                ? 'bg-red-100 text-red-700'
                : 'bg-green-100 text-green-700'
            "
          >
            {{ alert.state === "TRIGGERED" ? "ALERTE" : "FIN" }}
          </span>

          <div>
            <p class="text-sm font-medium text-gray-900">{{ label(alert) }}</p>
            <p class="text-xs text-gray-500">
              {{ source(alert) }} · {{ alert.device_id }}
              <span v-if="valueText(alert)"> · {{ valueText(alert) }}</span>
            </p>
          </div>
        </div>

        <span class="text-xs text-gray-500 whitespace-nowrap">{{ time(alert) }}</span>
      </li>
    </ul>
  </div>
</template>
