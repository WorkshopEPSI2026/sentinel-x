<script setup lang="ts">
import { onMounted, ref } from "vue";
import api from "@/services/api";

const healthStatus = ref("");
onMounted(async () => {
  try {
    const response = await api.get("/health");
    healthStatus.value = response.data.status;
  } catch (error) {
    console.error("Error fetching health status:", error);
    healthStatus.value = "Error";
  }
});
</script>

<template>
  <div>
    <div class="wrapper">
      <h1 class="title text-3xl font-bold">Sentinel X</h1>
      <p class="subtitle text-lg">
        A simple monitoring tool for your applications
      </p>
      <p class="health-status">Health Status: {{ healthStatus }}</p>
    </div>
  </div>
</template>
