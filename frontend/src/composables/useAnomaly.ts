import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import axios from "axios";
import type { AnomalyStatus, ScorePoint } from "../types/anomaly";

/*
 * Le service IA d'anomalies tourne à part (dossier ai/anomaly, port 8002).
 * URL modifiable avec VITE_ANOMALY_URL.
 */
const ANOMALY_URL =
  (import.meta.env as unknown as Record<string, string | undefined>).VITE_ANOMALY_URL ||
  "http://localhost:8002";

const api = axios.create({ baseURL: ANOMALY_URL });

const POLL_MS = 3000;
const MAX_POINTS = 60; // ~3 min d'historique du score

/*
 * État du modèle IA d'anomalies : interroge le service IA toutes les 3 s
 * et garde l'historique du score pour le graphique.
 * Les alertes ANOMALY elles-mêmes arrivent déjà par useAlerts (WebSocket).
 */
export function useAnomaly() {
  const status = ref<AnomalyStatus | null>(null);
  const history = ref<ScorePoint[]>([]);
  const error = ref<string | null>(null);
  const training = ref(false);
  const trainMessage = ref<string | null>(null);

  let timer: ReturnType<typeof setInterval> | null = null;

  // Appareil suivi : celui du modèle, sinon le premier vu
  const deviceId = computed(() => {
    const s = status.value;
    if (!s) return null;
    if (s.device_id && s.devices[s.device_id]) return s.device_id;
    return Object.keys(s.devices)[0] ?? s.device_id ?? null;
  });

  const device = computed(() =>
    status.value && deviceId.value ? status.value.devices[deviceId.value] ?? null : null,
  );

  const fetchStatus = async () => {
    try {
      const response = await api.get<AnomalyStatus>("/api/anomaly/status");
      status.value = response.data;
      error.value = null;

      const score = device.value?.last_score;
      if (score !== null && score !== undefined) {
        history.value = [...history.value, { time: Date.now(), score }].slice(-MAX_POINTS);
      }
    } catch {
      error.value = "Service IA injoignable (" + ANOMALY_URL + ")";
    }
  };

  const train = async () => {
    training.value = true;
    trainMessage.value = null;
    try {
      await api.post("/api/anomaly/train");
      history.value = [];
      trainMessage.value = "Modèle entraîné sur les dernières mesures.";
      await fetchStatus();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      trainMessage.value = detail ?? "Échec de l'entraînement.";
    } finally {
      training.value = false;
    }
  };

  onMounted(() => {
    fetchStatus();
    timer = setInterval(fetchStatus, POLL_MS);
  });

  onBeforeUnmount(() => {
    if (timer) clearInterval(timer);
  });

  return { status, device, deviceId, history, error, training, trainMessage, train, fetchStatus };
}
