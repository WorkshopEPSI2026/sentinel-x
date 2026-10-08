export interface Telemetry {
  id: number;
  device_id: string;
  temperature: number;
  humidity: number;
  gas: number;
  presence: boolean;
  created_at: string;
}