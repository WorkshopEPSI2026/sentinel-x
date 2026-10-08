export interface CameraStatus {
  ai_available: boolean;
  person_detected: boolean;
  persons_count: number;
  detections: CameraDetection[];
}

export interface CameraDetection {
  object: string;
  confidence: number;
  box: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
}