<script setup lang="ts">
import { computed } from "vue";

/*
 * Explication lisible d'une alerte IA (ANOMALY).
 * Le service IA envoie dans `detail` les 7 indicateurs de la dernière minute :
 *   temp, hum, gas            valeurs actuelles
 *   temp_slope, gas_slope     pente par mesure (1 mesure = 2 s)
 *   gas_std                   agitation du gaz sur la minute
 *   corr_tg                   corrélation température / gaz (-1..1)
 */
const props = defineProps<{
  detail: Record<string, unknown> | null;
}>();

const PER_MIN = 30; // 30 mesures par minute

// Seuils d'affichage (au-delà, on considère que l'indicateur "parle")
const TEMP_RATE = 0.3; // °C / min
const GAS_RATE = 5; // unités / min
const GAS_STD = 5;
const CORR = 0.6;

const num = (key: string): number | null => {
  const v = props.detail?.[key];
  return typeof v === "number" && Number.isFinite(v) ? v : null;
};

const fmt = (v: number, digits = 1) => (v > 0 ? "+" : "") + v.toFixed(digits);

const reasons = computed(() => {
  if (!props.detail) return [];

  const tempRate = (num("temp_slope") ?? 0) * PER_MIN;
  const gasRate = (num("gas_slope") ?? 0) * PER_MIN;
  const gasStd = num("gas_std") ?? 0;
  const corr = num("corr_tg") ?? 0;

  // [importance, phrase]
  const list: [number, string][] = [];

  if (corr >= CORR && tempRate > TEMP_RATE / 2 && gasRate > GAS_RATE / 2) {
    list.push([10, "température et gaz montent ensemble"]);
  }
  if (Math.abs(tempRate) >= TEMP_RATE) {
    list.push([
      Math.abs(tempRate) / TEMP_RATE,
      `la température ${tempRate > 0 ? "monte" : "baisse"} vite (${fmt(tempRate)} °C/min)`,
    ]);
  }
  if (Math.abs(gasRate) >= GAS_RATE) {
    list.push([
      Math.abs(gasRate) / GAS_RATE,
      `le gaz ${gasRate > 0 ? "monte" : "baisse"} vite (${fmt(gasRate, 0)}/min)`,
    ]);
  }
  if (gasStd >= GAS_STD) {
    list.push([gasStd / GAS_STD, `le gaz est instable (±${gasStd.toFixed(0)})`]);
  }

  return list
    .sort((a, b) => b[0] - a[0])
    .slice(0, 2)
    .map(([, text]) => text);
});

// Valeurs au moment de l'alerte
const values = computed(() => {
  const parts: string[] = [];
  const t = num("temp");
  const h = num("hum");
  const g = num("gas");
  if (t !== null) parts.push(`${t.toFixed(1)} °C`);
  if (h !== null) parts.push(`${h.toFixed(0)} %`);
  if (g !== null) parts.push(`gaz ${g.toFixed(0)}`);
  return parts.join(" · ");
});
</script>

<template>
  <p v-if="detail" class="mt-0.5 text-xs text-gray-700">
    <span class="font-medium">
      {{
        reasons.length
          ? reasons.join(" et ")
          : "combinaison de valeurs inhabituelle"
      }}
    </span>
    <span v-if="values" class="text-gray-500"> — {{ values }}</span>
  </p>
</template>
