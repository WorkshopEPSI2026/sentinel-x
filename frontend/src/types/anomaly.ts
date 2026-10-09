/*
 * IA - Détection d'anomalies (Isolation Forest côté backend)
 * Réponse de GET /api/anomaly/status
 */
export interface AnomalyDeviceState {
  buffer: number; // mesures dans la fenêtre (0..window)
  last_score: number | null; // plus c'est bas, plus c'est anormal
  in_anomaly: boolean;
}

export interface AnomalyStatus {
  trained: boolean;
  device_id?: string;
  samples?: number;
  windows?: number;
  threshold?: number;
  trained_at?: string;
  eval_false_alerts?: number;
  eval_drift_detected_after_s?: number | null;
  eval_fixed_threshold_600_after_s?: number | null;
  model_path: string;
  window: number;
  consecutive: number;
  devices: Record<string, AnomalyDeviceState>;
}

export interface ScorePoint {
  time: number; // timestamp ms
  score: number;
}
