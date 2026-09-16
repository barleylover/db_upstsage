import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },
  {
    path: '/home',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    path: '/spec/:specId/confirm',
    name: 'spec-confirm',
    component: () => import('@/views/SpecConfirmView.vue'),
  },
  {
    path: '/spec/:specId/sql-pack',
    name: 'spec-sql-pack',
    component: () => import('@/views/SqlPackView.vue'),
  },
  {
    path: '/spec/:specId/review',
    name: 'spec-review',
    component: () => import('@/views/ReviewView.vue'),
  },
  {
    path: '/spec/:specId/document',
    name: 'spec-document',
    component: () => import('@/views/DocumentView.vue'),
  },
  {
    path: '/spec/:specId/export',
    name: 'spec-export',
    component: () => import('@/views/ExportView.vue'),
  },
  {
    path: '/setup/schemas',
    name: 'setup-schemas',
    component: () => import('@/views/SetupSchemasView.vue'),
  },
  {
    path: '/setup/schemas/:schemaId',
    name: 'setup-schema-detail',
    component: () => import('@/views/SetupSchemaDetailView.vue'),
  },
  {
    path: '/setup/schemas/import',
    name: 'setup-schema-import',
    component: () => import('@/views/SetupSchemaImportView.vue'),
  },
  {
    path: '/setup/templates',
    name: 'setup-templates',
    component: () => import('@/views/SetupTemplatesView.vue'),
  },
  {
    path: '/setup/templates/:templateId',
    name: 'setup-template-detail',
    component: () => import('@/views/SetupTemplateDetailView.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
  },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})
