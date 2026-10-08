<script setup lang="ts">
import AlertList from "../alerts/AlertList.vue";

import type { Alert } from "../../types/alert";

defineProps<{
  alerts: Alert[];
  activeAlerts: Alert[];
}>();
</script>

<template>
  <div
    class="rounded-2xl border border-gray-200 bg-white shadow-sm"
  >
    <div
      class="flex items-center justify-between border-b border-gray-200 px-5 py-4"
    >
      <div>
        <p class="text-sm font-semibold text-gray-900">
          Alertes en cours
        </p>

        <p class="mt-0.5 text-xs text-gray-500">
          Événements nécessitant une attention
        </p>
      </div>

      <span
        v-if="activeAlerts.length > 0"
        class="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-600"
      >
        {{ activeAlerts.length }}
        alerte{{ activeAlerts.length > 1 ? "s" : "" }}
      </span>

      <span
        v-else
        class="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700"
      >
        Site sécurisé
      </span>
    </div>

    <div class="p-5">
      <div
        v-if="activeAlerts.length === 0"
        class="flex items-center gap-4 rounded-xl border border-green-100 bg-green-50 p-4"
      >
        <div
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-green-100"
        >
          <span class="text-lg">
            ✓
          </span>
        </div>

        <div>
          <p class="text-sm font-semibold text-green-800">
            Aucune alerte active
          </p>

          <p class="mt-0.5 text-xs text-green-700">
            Les systèmes de surveillance fonctionnent normalement.
          </p>
        </div>
      </div>

      <AlertList
        v-else
        :alerts="activeAlerts"
      />
    </div>
  </div>
</template>