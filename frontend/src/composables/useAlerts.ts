import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import api from "../services/api";

export interface Alert {
  id: number;
  device_id: string;
  source: "esp" | "ml" | "vision" | string;
  type: "PIR" | "GAS" | "ANOMALY" | "INTRUSION" | string;
  state: "TRIGGERED" | "CLEARED" | string;
  value: number | null;
  detail: Record<string, unknown> | null;
  created_at: string;
}

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
const MAX_ALERTS = 50;

export function useAlerts() {
  const alerts = ref<Alert[]>([]); // la plus récente en premier
  const connected = ref(false);

  let socket: WebSocket | null = null;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  let stopped = false;

  /*
   * Alertes "en cours" : pour chaque (appareil, type), la dernière alerte
   * reçue est TRIGGERED (pas encore de CLEARED après elle).
   */
  const activeAlerts = computed(() => {
    const last = new Map<string, Alert>();

    // alerts est trié du plus récent au plus ancien : on garde la 1re vue
    for (const alert of alerts.value) {
      const key = `${alert.device_id}:${alert.type}`;
      if (!last.has(key)) {
        last.set(key, alert);
      }
    }

    return [...last.values()].filter((a) => a.state === "TRIGGERED");
  });

  const loadHistory = async () => {
    try {
      const response = await api.get<Alert[]>("/api/alerts?limit=" + MAX_ALERTS);
      alerts.value = response.data;
    } catch (err) {
      console.error("Erreur chargement des alertes :", err);
    }
  };

  const connect = () => {
    socket = new WebSocket(`${WS_URL}/ws/alerts`);

    socket.onopen = () => {
      connected.value = true;
    };

    socket.onmessage = (event) => {
      try {
        const alert: Alert = JSON.parse(event.data);
        alerts.value = [alert, ...alerts.value].slice(0, MAX_ALERTS);
      } catch {
        console.error("Alerte reçue invalide");
      }
    };

    socket.onclose = () => {
      connected.value = false;

      // Reconnexion automatique (backend redémarré, coupure réseau...)
      if (!stopped) {
        retryTimer = setTimeout(async () => {
          await loadHistory(); // récupère ce qui a été manqué
          connect();
        }, 3000);
      }
    };
  };

  onMounted(async () => {
    await loadHistory();
    connect();
  });

  onBeforeUnmount(() => {
    stopped = true;
    if (retryTimer) clearTimeout(retryTimer);
    socket?.close();
  });

  return { alerts, activeAlerts, connected, loadHistory };
}
