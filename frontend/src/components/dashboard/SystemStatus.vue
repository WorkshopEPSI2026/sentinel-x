<script setup lang="ts">

defineProps<{
  connected: boolean;
}>();

</script>

<template>
  <div
    class="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm"
  >
    <span class="relative flex h-3 w-3">
      <span
        v-if="connected"
        class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"
      />

      <span
        class="relative inline-flex h-3 w-3 rounded-full"
        :class="
          connected
            ? 'bg-green-500'
            : 'bg-red-500'
        "
      />
    </span>

    <div>
      <p class="text-sm font-semibold text-gray-900">
        {{ connected ? "Système opérationnel" : "Connexion interrompue" }}
      </p>

      <p class="text-xs text-gray-500">
        WebSocket :
        {{ connected ? "Connecté" : "Déconnecté" }}
      </p>
    </div>
  </div>
</template>