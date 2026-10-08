<script setup lang="ts">

withDefaults(
  defineProps<{
    icon: string;
    label: string;
    value: string | number;
    unit?: string;
    status?: "normal" | "warning" | "danger";
  }>(),
  {
    unit: "",
    status: "normal",
  },
);

</script>

<template>
  <div
    class="rounded-xl border border-gray-100 bg-gray-50 p-4 relative"
  >
    <div class="absolute right-4 top-4">
      <span
        v-if="status === 'normal'"
        class="rounded-full bg-green-100 px-2 py-1 text-[10px] font-semibold text-green-700"
      >
        NORMAL
      </span>

      <span
        v-else-if="status === 'warning'"
        class="rounded-full bg-orange-100 px-2 py-1 text-[10px] font-semibold text-orange-700"
      >
        ATTENTION
      </span>

      <span
        v-else
        class="rounded-full bg-red-100 px-2 py-1 text-[10px] font-semibold text-red-700"
      >
        ALERTE
      </span>
    </div>

    <p class="text-xs text-gray-500">
      {{ label }}
    </p>

    <p
      class="mt-1 text-xl font-bold"
      :class="
        status === 'danger'
          ? 'text-red-600'
          : 'text-gray-900'
      "
    >
      {{ value }}

      <span
        v-if="unit"
        class="text-sm font-medium text-gray-500"
      >
        {{ unit }}
      </span>
    </p>
  </div>
</template>