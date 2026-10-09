<script setup lang="ts">
import { computed } from "vue";
import { useAnomaly } from "../../composables/useAnomaly";

/*
 * Carte "IA - Détection d'anomalies"
 * - état du modèle (entraîné / en préparation / normal / anomalie)
 * - courbe du score en direct avec le seuil
 * - évaluation : IA vs seuil fixe "gaz > 600"
 * - bouton pour (ré)entraîner le modèle
 */
const { status, device, deviceId, history, error, training, trainMessage, train } = useAnomaly();

const trained = computed(() => status.value?.trained === true);
const windowSize = computed(() => status.value?.window ?? 30);
const threshold = computed(() => status.value?.threshold ?? 0);

type State = "offline" | "untrained" | "waiting" | "normal" | "anomaly";

const state = computed<State>(() => {
  if (error.value || !status.value) return "offline";
  if (!trained.value) return "untrained";
  if (!device.value || device.value.buffer < windowSize.value) return "waiting";
  return device.value.in_anomaly ? "anomaly" : "normal";
});

const BADGES: Record<State, { text: string; cls: string }> = {
  offline: { text: "Hors ligne", cls: "bg-gray-100 text-gray-600" },
  untrained: { text: "Non entraîné", cls: "bg-amber-100 text-amber-700" },
  waiting: { text: "Analyse en préparation", cls: "bg-blue-100 text-blue-700" },
  normal: { text: "Comportement normal", cls: "bg-green-100 text-green-700" },
  anomaly: { text: "Anomalie détectée", cls: "bg-red-100 text-red-600" },
};
const badge = computed(() => BADGES[state.value]);

const score = computed(() => device.value?.last_score ?? null);

/* ---------- graphique SVG du score ---------- */
const W = 300;
const H = 110;

const range = computed(() => {
  const values = [...history.value.map((p) => p.score), threshold.value];
  const min = Math.min(...values) - 0.03;
  const max = Math.max(...values) + 0.03;
  return { min, max };
});

const y = (v: number) => H - ((v - range.value.min) / (range.value.max - range.value.min)) * H;

const linePoints = computed(() => {
  const pts = history.value;
  if (pts.length < 2) return "";
  return pts.map((p, i) => `${(i / (pts.length - 1)) * W},${y(p.score).toFixed(1)}`).join(" ");
});

const thresholdY = computed(() => y(threshold.value));

/* ---------- évaluation ---------- */
const evalDrift = computed(() => status.value?.eval_drift_detected_after_s ?? null);
const evalFixed = computed(() => status.value?.eval_fixed_threshold_600_after_s ?? null);
const gain = computed(() =>
  evalDrift.value !== null && evalFixed.value !== null && evalDrift.value > 0
    ? Math.round(evalFixed.value / evalDrift.value)
    : null,
);

const trainedAt = computed(() =>
  status.value?.trained_at ? new Date(status.value.trained_at).toLocaleString() : "—",
);
</script>

<template>
  <div class="rounded-2xl border border-gray-200 bg-white shadow-sm">
    <!-- En-tête -->
    <div class="flex items-center justify-between border-b border-gray-200 px-5 py-4">
      <div>
        <p class="text-sm font-semibold text-gray-900">IA · Détection d'anomalies</p>
        <p class="mt-0.5 text-xs text-gray-500">
          Isolation Forest · apprend le comportement normal du boîtier
        </p>
      </div>

      <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="badge.cls">
        {{ badge.text }}
      </span>
    </div>

    <div class="p-5">
      <!-- Service injoignable -->
      <p v-if="state === 'offline'" class="text-sm text-gray-500">
        Le service IA (ai/anomaly, port 8002) ne répond pas.
      </p>

      <!-- Pas encore de modèle -->
      <div
        v-else-if="state === 'untrained'"
        class="rounded-xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-800"
      >
        Aucun modèle entraîné. Laissez le boîtier mesurer au calme quelques minutes
        (150 mesures minimum), puis lancez l'entraînement.
      </div>

      <div v-else class="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <!-- Courbe du score -->
        <div class="lg:col-span-2">
          <div class="mb-2 flex items-baseline justify-between">
            <p class="text-xs font-medium text-gray-500">
              Score d'anomalie en direct · {{ deviceId ?? "—" }}
            </p>
            <p class="text-xs text-gray-400">plus bas = plus anormal</p>
          </div>

          <div class="rounded-xl border border-gray-100 bg-gray-50 p-3">
            <svg
              v-if="history.length >= 2"
              :viewBox="`0 0 ${W} ${H}`"
              preserveAspectRatio="none"
              class="h-32 w-full"
            >
              <!-- zone anormale sous le seuil -->
              <rect
                x="0"
                :y="thresholdY"
                :width="W"
                :height="Math.max(0, H - thresholdY)"
                class="fill-red-100"
              />
              <line
                x1="0"
                :x2="W"
                :y1="thresholdY"
                :y2="thresholdY"
                class="stroke-red-400"
                stroke-width="1"
                stroke-dasharray="4 3"
                vector-effect="non-scaling-stroke"
              />
              <polyline
                :points="linePoints"
                fill="none"
                :class="state === 'anomaly' ? 'stroke-red-600' : 'stroke-gray-900'"
                stroke-width="2"
                stroke-linejoin="round"
                vector-effect="non-scaling-stroke"
              />
            </svg>

            <div v-else class="flex h-32 items-center justify-center text-xs text-gray-500">
              <span v-if="state === 'waiting'">
                Remplissage de la fenêtre d'analyse : {{ device?.buffer ?? 0 }} / {{ windowSize }} mesures
              </span>
              <span v-else>En attente des premières mesures…</span>
            </div>
          </div>

          <div class="mt-2 flex justify-between text-xs text-gray-500">
            <span>
              Score : <b class="text-gray-900">{{ score !== null ? score.toFixed(3) : "—" }}</b>
            </span>
            <span class="text-red-500">--- seuil {{ threshold.toFixed(3) }}</span>
          </div>
        </div>

        <!-- Infos modèle + évaluation -->
        <div class="flex flex-col gap-3 text-sm">
          <div class="rounded-xl border border-gray-100 p-3">
            <p class="text-xs text-gray-500">Détection d'une dérive lente (test)</p>
            <div class="mt-2 flex items-end justify-between">
              <div>
                <p class="text-xl font-bold text-gray-900">
                  {{ evalDrift !== null ? evalDrift + " s" : "—" }}
                </p>
                <p class="text-xs text-gray-500">IA</p>
              </div>
              <div class="text-right">
                <p class="text-xl font-bold text-gray-400">
                  {{ evalFixed !== null ? evalFixed + " s" : "—" }}
                </p>
                <p class="text-xs text-gray-500">seuil fixe gaz &gt; 600</p>
              </div>
            </div>
            <p v-if="gain" class="mt-2 text-xs font-medium text-green-700">
              ≈ {{ gain }}× plus rapide qu'un seuil fixe
            </p>
          </div>

          <dl class="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
            <dt class="text-gray-500">Fausses alertes (test)</dt>
            <dd class="text-right font-medium text-gray-900">{{ status?.eval_false_alerts ?? "—" }}</dd>
            <dt class="text-gray-500">Mesures d'apprentissage</dt>
            <dd class="text-right font-medium text-gray-900">{{ status?.samples ?? "—" }}</dd>
            <dt class="text-gray-500">Fenêtre</dt>
            <dd class="text-right font-medium text-gray-900">{{ windowSize }} mesures</dd>
            <dt class="text-gray-500">Alerte après</dt>
            <dd class="text-right font-medium text-gray-900">{{ status?.consecutive }} fenêtres</dd>
            <dt class="text-gray-500">Entraîné le</dt>
            <dd class="text-right font-medium text-gray-900">{{ trainedAt }}</dd>
          </dl>
        </div>
      </div>

      <!-- Entraînement -->
      <div
        v-if="state !== 'offline'"
        class="mt-5 flex flex-col gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <p class="text-xs text-gray-500">
          {{ trainMessage ?? "À relancer après avoir déplacé le boîtier (nouvelle « normale »)." }}
        </p>
        <button
          type="button"
          class="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
          :disabled="training"
          @click="train"
        >
          {{ training ? "Entraînement…" : trained ? "Réentraîner le modèle" : "Entraîner le modèle" }}
        </button>
      </div>
    </div>
  </div>
</template>
