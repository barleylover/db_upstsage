/// <reference types="vite/client" />

export {}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'vue-router' {
  export * from 'vue-router'
  export { useRoute, useRouter, createRouter, createWebHistory, RouterLink, RouterView }
}
