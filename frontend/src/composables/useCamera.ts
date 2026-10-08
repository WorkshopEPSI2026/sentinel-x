import { onMounted, onUnmounted, ref } from "vue";

import { getCameraStatus } from "../services/camera";

import type { CameraStatus } from "../types/camera";

export function useCamera() {
  const status = ref<CameraStatus | null>(null);
  const connected = ref(false);

  let interval: number | undefined;

  async function fetchStatus() {
    try {
      const data = await getCameraStatus();

      status.value = data;
      connected.value = true;
    } catch (error) {
      console.error(
        "[CAMERA] Impossible de récupérer le statut",
        error
      );

      connected.value = false;
    }
  }

  onMounted(() => {
    fetchStatus();

    interval = window.setInterval(
      fetchStatus,
      1000
    );
  });

  onUnmounted(() => {
    if (interval !== undefined) {
      window.clearInterval(interval);
    }
  });

  return {
    status,
    connected,
  };
}