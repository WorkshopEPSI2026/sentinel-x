<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'

interface Recording {
  filename: string
  size: number
  created_at: number
  url: string
}

const recordings = ref<Recording[]>([])
const selectedRecording = ref<Recording | null>(null)
const loading = ref(true)
const error = ref('')

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function fetchRecordings() {
  loading.value = true
  error.value = ''

  try {
    const response = await axios.get<Recording[]>(
      `${API_URL}/api/recordings`,
    )
    recordings.value = response.data

    if (
      selectedRecording.value &&
      !recordings.value.some(
        (item) => item.filename === selectedRecording.value?.filename,
      )
    ) {
      selectedRecording.value = null
    }
  } catch {
    error.value = 'Impossible de charger les enregistrements.'
  } finally {
    loading.value = false
  }
}

function formatDate(timestamp: number) {
  return new Date(timestamp * 1000).toLocaleString('fr-FR')
}

function formatSize(bytes: number) {
  return `${(bytes / (1024 * 1024)).toFixed(2)} Mo`
}

function videoUrl(recording: Recording) {
  return `${API_URL}${recording.url}`
}

onMounted(fetchRecordings)
</script>

<template>
  <section class="space-y-6">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-900">
          Enregistrements des incidents
        </h2>
        <p class="mt-1 text-sm text-gray-500">
          Historique des vidéos capturées automatiquement.
        </p>
      </div>

      <button
        type="button"
        class="rounded-lg border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
        @click="fetchRecordings"
      >
        Actualiser
      </button>
    </div>

    <p v-if="loading" class="text-sm text-gray-500">
      Chargement des vidéos...
    </p>

    <p v-else-if="error" class="text-sm text-red-600">
      {{ error }}
    </p>

    <p
      v-else-if="recordings.length === 0"
      class="rounded-xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500"
    >
      Aucun enregistrement disponible.
    </p>

    <div v-else class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div class="space-y-3">
        <button
          v-for="recording in recordings"
          :key="recording.filename"
          type="button"
          class="w-full rounded-xl border p-4 text-left transition"
          :class="
            selectedRecording?.filename === recording.filename
              ? 'border-red-500 bg-red-50'
              : 'border-gray-200 bg-white hover:bg-gray-50'
          "
          @click="selectedRecording = recording"
        >
          <p class="break-all text-sm font-medium text-gray-900">
            {{ recording.filename }}
          </p>
          <p class="mt-2 text-xs text-gray-500">
            {{ formatDate(recording.created_at) }}
          </p>
          <p class="mt-1 text-xs text-gray-500">
            {{ formatSize(recording.size) }}
          </p>
        </button>
      </div>

      <div class="min-w-0">
        <div
          v-if="selectedRecording"
          class="overflow-hidden rounded-xl border border-gray-200 bg-black"
        >
          <video
            :key="selectedRecording.filename"
            :src="videoUrl(selectedRecording)"
            controls
            preload="metadata"
            class="aspect-video w-full"
          >
            Votre navigateur ne prend pas en charge la lecture vidéo.
          </video>

          <div class="bg-white p-4">
            <p class="break-all text-sm font-medium text-gray-900">
              {{ selectedRecording.filename }}
            </p>
            <p class="mt-1 text-xs text-gray-500">
              {{ formatDate(selectedRecording.created_at) }}
            </p>
          </div>
        </div>

        <div
          v-else
          class="flex aspect-video items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500"
        >
          Sélectionne un incident pour visionner la vidéo.
        </div>
      </div>
    </div>
  </section>
</template>