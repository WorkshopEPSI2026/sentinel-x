import "vue-router";

declare module "vue-router" {
  interface RouteMeta {
    guestOnly?: boolean;
    requestAuth?: boolean;
  }
}