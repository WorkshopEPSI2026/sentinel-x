<template>
  <div class="min-h-screen bg-gray-100 text-gray-900">
    <!-- Navbar -->
    <nav class="border-b border-gray-200 bg-white">
      <div
        class="mx-auto flex h-16 max-w-7xl items-center justify-between px-6"
      >
        <!-- Logo -->
        <RouterLink
          to="/"
          class="text-xl font-bold tracking-tight"
        >
          Sentinel-X
        </RouterLink>

        <!-- Navigation -->
        <div class="hidden items-center gap-8 md:flex">
          <a
            href="#solution"
            class="text-sm text-gray-600 transition hover:text-gray-900"
          >
            Solution
          </a>

          <a
            href="#fonctionnalites"
            class="text-sm text-gray-600 transition hover:text-gray-900"
          >
            Fonctionnalités
          </a>

          <a
            href="#architecture"
            class="text-sm text-gray-600 transition hover:text-gray-900"
          >
            Architecture
          </a>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-3">
          <RouterLink
            to="/auth"
            class="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-100"
          >
            Connexion
          </RouterLink>

          <RouterLink
            to="/auth"
            class="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-800"
          >
            Commencer
          </RouterLink>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <main>
      <section
        id="solution"
        class="mx-auto max-w-7xl px-6 py-24"
      >
        <div class="max-w-3xl">
          <span
            class="inline-flex rounded-full bg-gray-200 px-3 py-1 text-sm font-medium text-gray-700"
          >
            Edge Security & IoT
          </span>

          <h1
            class="mt-6 text-5xl font-bold tracking-tight text-gray-900 md:text-6xl"
          >
            Sécurisez vos infrastructures.
            <span class="text-gray-500">
              Surveillez-les intelligemment.
            </span>
          </h1>

          <p
            class="mt-6 max-w-2xl text-lg leading-8 text-gray-600"
          >
            Sentinel-X est une plateforme de supervision
            cyber-physique permettant de surveiller en temps réel
            l'environnement et la sécurité de vos infrastructures
            isolées.
          </p>

          <div class="mt-8 flex flex-wrap gap-4">
            <RouterLink
              to="/auth"
              class="rounded-lg bg-gray-900 px-6 py-3 font-medium text-white transition hover:bg-gray-800"
            >
              Accéder à la plateforme
            </RouterLink>

            <a
              href="#fonctionnalites"
              class="rounded-lg border border-gray-300 bg-white px-6 py-3 font-medium text-gray-700 transition hover:bg-gray-50"
            >
              Découvrir Sentinel-X
            </a>
          </div>
        </div>
      </section>

      <!-- Fonctionnalités -->
      <section
        id="fonctionnalites"
        class="border-y border-gray-200 bg-white"
      >
        <div class="mx-auto max-w-7xl px-6 py-20">
          <div class="max-w-2xl">
            <h2 class="text-3xl font-bold">
              Une supervision centralisée
            </h2>

            <p class="mt-3 text-gray-600">
              Toutes les informations essentielles de votre
              infrastructure réunies au même endroit.
            </p>
          </div>

          <div
            class="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-4"
          >
            <!-- IoT -->
            <div class="rounded-xl border border-gray-200 p-6 hover:shadow-lg transition">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 font-bold"
              >
                01
              </div>

              <h3 class="mt-5 font-semibold">
                Capteurs IoT
              </h3>

              <p class="mt-2 text-sm leading-6 text-gray-600">
                Collecte des données environnementales et détection
                des événements physiques en temps réel.
              </p>
            </div>

            <!-- Temps réel -->
            <div class="rounded-xl border border-gray-200 p-6 hover:shadow-lg transition">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 font-bold"
              >
                02
              </div>

              <h3 class="mt-5 font-semibold">
                Supervision temps réel
              </h3>

              <p class="mt-2 text-sm leading-6 text-gray-600">
                Visualisation instantanée des données grâce à une
                communication temps réel.
              </p>
            </div>

            <!-- IA -->
            <div class="rounded-xl border border-gray-200 p-6 hover:shadow-lg transition">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 font-bold"
              >
                03
              </div>

              <h3 class="mt-5 font-semibold">
                Intelligence locale
              </h3>

              <p class="mt-2 text-sm leading-6 text-gray-600">
                Analyse locale des événements et détection
                intelligente des comportements suspects.
              </p>
            </div>

            <!-- Sécurité -->
            <div class="rounded-xl border border-gray-200 p-6 hover:shadow-lg transition">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 font-bold"
              >
                04
              </div>

              <h3 class="mt-5 font-semibold">
                Cybersécurité
              </h3>

              <p class="mt-2 text-sm leading-6 text-gray-600">
                Une infrastructure locale conçue pour limiter
                l'exposition des données sensibles.
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Architecture -->
      <section
        id="architecture"
        class="mx-auto max-w-7xl px-6 py-20"
      >
        <div class="grid gap-12 lg:grid-cols-2 lg:items-center">
          <div>
            <h2 class="text-3xl font-bold">
              Une architecture Edge pensée pour le terrain
            </h2>

            <p class="mt-4 leading-7 text-gray-600">
              Sentinel-X traite les données au plus près de
              l'infrastructure surveillée afin de permettre une
              supervision réactive et résiliente.
            </p>

            <div class="mt-8 space-y-4">
              <div class="flex gap-4">
                <div
                  class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-900 text-sm font-bold text-white"
                >
                  1
                </div>

                <div>
                  <h3 class="font-semibold">
                    Collecte
                  </h3>

                  <p class="text-sm text-gray-600">
                    Les capteurs transmettent leurs données au
                    système local.
                  </p>
                </div>
              </div>

              <div class="flex gap-4">
                <div
                  class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-900 text-sm font-bold text-white"
                >
                  2
                </div>

                <div>
                  <h3 class="font-semibold">
                    Analyse
                  </h3>

                  <p class="text-sm text-gray-600">
                    Les données sont stockées et analysées localement.
                  </p>
                </div>
              </div>

              <div class="flex gap-4">
                <div
                  class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-900 text-sm font-bold text-white"
                >
                  3
                </div>

                <div>
                  <h3 class="font-semibold">
                    Supervision
                  </h3>

                  <p class="text-sm text-gray-600">
                    L'opérateur visualise les événements et l'état
                    de l'infrastructure.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Architecture card -->
          <div
            class="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm"
          >
            <div class="space-y-4">
              <div
                class="rounded-lg bg-gray-100 p-4 text-center font-medium"
              >
                Capteurs IoT
              </div>

              <div class="text-center text-gray-400">
                ↓
              </div>

              <div
                class="rounded-lg bg-gray-900 p-4 text-center font-medium text-white"
              >
                Sentinel-X Edge
              </div>

              <div class="text-center text-gray-400">
                ↓
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div
                  class="rounded-lg bg-gray-100 p-4 text-center text-sm"
                >
                  PostgreSQL
                </div>

                <div
                  class="rounded-lg bg-gray-100 p-4 text-center text-sm"
                >
                  Dashboard
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="bg-gray-900">
        <div
          class="mx-auto max-w-7xl px-6 py-20 text-center text-white"
        >
          <h2 class="text-3xl font-bold">
            Prenez le contrôle de votre infrastructure.
          </h2>

          <p class="mx-auto mt-4 max-w-xl text-gray-400">
            Accédez à votre espace de supervision et visualisez
            l'état de votre système en temps réel.
          </p>

          <RouterLink
            to="/auth"
            class="mt-8 inline-block rounded-lg bg-white px-6 py-3 font-medium text-gray-900 transition hover:bg-gray-100"
          >
            Accéder à Sentinel-X
          </RouterLink>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="border-t border-gray-200 bg-white">
      <div
        class="mx-auto flex max-w-7xl flex-col gap-2 px-6 py-6 text-sm text-gray-500 md:flex-row md:items-center md:justify-between"
      >
        <p>
          © 2026 Sentinel-X
        </p>

        <p>
          Edge Security & IoT
        </p>
      </div>
    </footer>
  </div>
</template>