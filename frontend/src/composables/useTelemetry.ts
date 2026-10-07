import { onBeforeUnmount, onMounted, ref } from "vue";
import api from "../services/api";

export interface Telemetry {
  device_id: string;
  temperature: number;
  humidity: number;
  gas: number;
  presence: boolean;
  id?: number;
  created_at?: string;
}

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export function useTelemetry() {
  const telemetry = ref<Telemetry | null>(null);

  const telemetryHistory = ref<Telemetry[]>([]);

  const connected = ref(false);
  const error = ref<string | null>(null);

  let socket: WebSocket | null = null;

  /*
   * Chargement de l'historique depuis l'API REST
   */
  const loadHistory = async () => {
    try {
      const response = await api.get<Telemetry[]>(
        "/api/telemetry/history?limit=50"
      );

      // L'API renvoie les données de la plus récente à la plus ancienne.
      // Pour un graphique, on préfère l'ordre chronologique.
      telemetryHistory.value = response.data.reverse();

      if (telemetryHistory.value.length > 0) {
        telemetry.value = telemetryHistory.value[telemetryHistory.value.length - 1];
      }
    } catch (err) {
      console.error("Erreur chargement historique :", err);
      error.value = "Impossible de charger l'historique";
    }
  };

  /*
   * Connexion WebSocket
   */
  const connect = () => {
    socket = new WebSocket(`${WS_URL}/ws/telemetry`);

    socket.onopen = () => {
      connected.value = true;
      error.value = null;

      console.log("WebSocket connecté");
    };

    socket.onmessage = (event) => {
      try {
        const newTelemetry: Telemetry = JSON.parse(event.data);

        telemetry.value = newTelemetry;

        telemetryHistory.value.push(newTelemetry);

        /*
         * On conserve uniquement les 50 dernières mesures
         * dans le frontend.
         */
        if (telemetryHistory.value.length > 50) {
          telemetryHistory.value.shift();
        }
      } catch {
        error.value = "Télémétrie reçue invalide";
      }
    };

    socket.onerror = () => {
      connected.value = false;
      error.value = "Erreur WebSocket";
    };

    socket.onclose = () => {
      connected.value = false;

      console.log("WebSocket fermé");
    };
  };

  const disconnect = () => {
    socket?.close();
    socket = null;
  };

  onMounted(async () => {
    await loadHistory();
    connect();
  });

  onBeforeUnmount(() => {
    disconnect();
  });

  return {
    telemetry,
    telemetryHistory,
    connected,
    error,
    loadHistory,
    connect,
    disconnect,
  };
}