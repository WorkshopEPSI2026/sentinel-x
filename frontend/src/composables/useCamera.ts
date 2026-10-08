import { onMounted, onUnmounted, ref } from "vue";

import { getCameraStatus } from "../services/camera";

import type { CameraStatus } from "../types/camera";

export function useCamera() {
  const status = ref<CameraStatus | null>(null);
  const connected = ref(false);

  let interval: number | undefined;

  async function fetchStatus() {
    try {
      status.value = await getCameraStatus();
      connected.value = true;
    } catch {
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
    if (interval) {
      clearInterval(interval);
    }
  });

  return {
    status,
    connected,
  };
}