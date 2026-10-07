<script setup lang="ts">
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";

import { Line } from "vue-chartjs";

import type { Telemetry } from "../../composables/useTelemetry";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
);

const props = defineProps<{
  telemetryHistory: Telemetry[];
  label: string;
  dataKey: "temperature" | "humidity" | "gas";
  unit: string;
}>();

const chartData = () => ({
  labels: props.telemetryHistory.map((telemetry) =>
    telemetry.created_at
      ? new Date(telemetry.created_at).toLocaleTimeString()
      : "",
  ),

  datasets: [
    {
      label: props.label,

      data: props.telemetryHistory.map(
        (telemetry) => telemetry[props.dataKey],
      ),

      tension: 0.3,
      pointRadius: 2,
    },
  ],
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,

  plugins: {
    legend: {
      display: true,
    },
  },

  scales: {
    y: {
      beginAtZero: false,
      title: {
        display: true,
        text: props.unit,
      },
    },
  },
};
</script>

<template>
  <div class="h-64">
    <Line
      :data="chartData()"
      :options="chartOptions"
    />
  </div>
</template>