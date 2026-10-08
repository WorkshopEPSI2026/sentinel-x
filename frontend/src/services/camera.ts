import type { CameraStatus } from "../types/camera";

const CAMERA_API_URL = "http://localhost:9000";

export async function getCameraStatus(): Promise<CameraStatus> {
  const response = await fetch(
    `${CAMERA_API_URL}/status`
  );

  if (!response.ok) {
    throw new Error(
      `Erreur caméra : ${response.status}`
    );
  }

  return response.json();
}