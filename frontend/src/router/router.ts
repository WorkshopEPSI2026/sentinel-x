import { createRouter, createWebHistory } from "vue-router";

import AcceuilView from "../views/AcceuilView.vue";
import AuthView from "../views/AuthView.vue";
import DashboardView from "../views/DashboardView.vue";

import { useAuth } from "../composables/useAuth";

const router = createRouter({
  history: createWebHistory(),

  routes: [
    {
      path: "/",
      name: "Acceuil",
      component: AcceuilView,
    },
    {
      path: "/auth",
      name: "auth",
      component: AuthView,
      meta: {
        guestOnly: true,
      },
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: DashboardView,
      meta: {
        requiresAuth: true,
      },
    },
  ],
});

router.beforeEach(async (to) => {
  const { isAuthenticated, fetchUser } = useAuth();

  if (to.meta.requiresAuth) {
    if (!isAuthenticated.value) {
      return {
        name: "auth",
      };
    }

    if (!useAuth().user.value) {
      const user = await fetchUser();

      if (!user) {
        return {
          name: "auth",
        };
      }
    }
  }

  if (to.meta.guestOnly && isAuthenticated.value) {
    return {
      name: "dashboard",
    };
  }

  return true;
});

export default router;