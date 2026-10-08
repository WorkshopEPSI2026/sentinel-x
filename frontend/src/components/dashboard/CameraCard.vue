<script setup lang="ts">

const cameraUrl = "http://localhost:9000/video_feed";

</script>

<template>
  <div
    class="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm"
  >
    <!-- Header -->
    <div
      class="flex items-center justify-between border-b border-gray-200 px-5 py-4"
    >
      <div>
        <p class="text-sm font-semibold text-gray-900">
          Surveillance vidéo
        </p>

        <p class="mt-0.5 text-xs text-gray-500">
          Analyse locale par intelligence artificielle
        </p>
      </div>

      <div class="flex items-center gap-2">
        <span
          class="h-2.5 w-2.5 rounded-full bg-red-500"
        />

        <span
          class="text-xs font-semibold uppercase tracking-wide text-red-600"
        >
          Live
        </span>
      </div>
    </div>

    <!-- Vidéo -->
    <div class="relative bg-black">
      <img
        :src="cameraUrl"
        alt="Flux vidéo de surveillance Sentinel-X"
        class="aspect-video w-full object-cover"
      />

      <div
        class="absolute bottom-0 left-0 right-0 flex items-center justify-between bg-gradient-to-t from-black/80 to-transparent px-5 pb-4 pt-10"
      >
        <div class="flex items-center gap-2 text-white">
          <span
            class="h-2 w-2 rounded-full bg-green-400"
          />

          <span class="text-xs font-medium">
            Caméra connectée
          </span>
        </div>

        <span
          class="rounded-md bg-black/50 px-2 py-1 text-xs text-white"
        >
          YOLO
        </span>
      </div>
    </div>
  </div>
</template>