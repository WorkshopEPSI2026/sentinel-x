import api from "./api";

import type { CameraStatus } from "../types/camera";

const cameraApi = "http://localhost:9000";

export async function getCameraStatus(): Promise<CameraStatus> {
  const response = await fetch(`${cameraApi}/status`);

  if (!response.ok) {
    throw new Error("Impossible de récupérer l'état de la caméra.");
  }

  return response.json();
}