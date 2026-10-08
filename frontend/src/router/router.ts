import { createRouter, createWebHistory } from "vue-router";

import AcceuilView from "../views/AcceuilView.vue";
import AuthView from "../views/AuthView.vue";
import DashboardView from "../views/DashboardView.vue";
import ProfileView from "../views/ProfileView.vue";

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

    {
      path: "/profile",
      name: "profile",
      component: ProfileView,
      meta: {
        requiresAuth: true,
      },
    },
  ],
});

router.beforeEach(async (to) => {
  const {
    isAuthenticated,
    user,
    fetchUser,
  } = useAuth();

  /*
   * Route protégée
   */
  if (to.meta.requiresAuth) {
    if (!isAuthenticated.value) {
      return {
        name: "auth",
      };
    }

    /*
     * Le token existe mais l'utilisateur
     * n'est pas encore chargé.
     */
    if (!user.value) {
      const currentUser = await fetchUser();

      if (!currentUser) {
        return {
          name: "auth",
        };
      }
    }
  }

  /*
   * Route réservée aux utilisateurs non connectés
   */
  if (to.meta.guestOnly && isAuthenticated.value) {
    return {
      name: "dashboard",
    };
  }

  return true;
});

export default router;