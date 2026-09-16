<template>
  <header class="topbar">
    <nav class="stepper">
      <template v-for="(step, idx) in steps" :key="step.label">
        <router-link
          :to="resolveStepTo(step)"
          class="step"
          :class="{ active: isActive(step), done: isDone(step) }"
        >
          <span class="step-num">{{ step.num }}</span>
          <span class="step-label">{{ step.label }}</span>
        </router-link>
        <span v-if="idx < steps.length - 1" class="step-sep"></span>
      </template>
    </nav>
    <div class="topbar-right">
      <span class="pill confirmed mono" v-if="specStatus === 'CONFIRMED'">CONFIRMED v{{ specVersion }}</span>
      <span class="pill demo mono">DEMO</span>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const store = useAppStore()

const steps = [
  { num: '01', label: '명세 확정', to: '/home' },
  { num: '02', label: 'SQL 팩', to: (specId: string) => `/spec/${specId}/sql-pack` },
  { num: '03', label: '검토', to: (specId: string) => `/spec/${specId}/review` },
  { num: '04', label: '변경 문서', to: (specId: string) => `/spec/${specId}/document` },
  { num: '05', label: '내보내기', to: (specId: string) => `/spec/${specId}/export` },
]

const specStatus = computed(() => store.currentSpecStatus ?? 'DRAFT')
const specVersion = computed(() => {
  const id = store.currentSpecId
  if (!id) return 1
  return 1
})

const currentSpecId = computed(() => store.currentSpecId ?? null)

function resolveStepTo(step: { to: string | ((specId: string) => string) }) {
  if (typeof step.to === 'function') {
    return currentSpecId.value ? step.to(currentSpecId.value) : '/home'
  }
  return step.to
}

function isActive(step: { to: string | ((specId: string) => string) }) {
  const target = resolveStepTo(step)
  if (!target) return false
  if (typeof target === 'string') {
    return route.path === target || (target.endsWith('/') ? route.path.startsWith(target) : route.path.startsWith(target + '/'))
  }
  return false
}

function isDone(_step: { to: string | ((specId: string) => string) }) {
  return false
}
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  border-bottom: 1px solid var(--border);
  background: var(--panel);
  position: sticky;
  top: 0;
  z-index: 5;
}

.topbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.stepper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.step {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 6px;
  text-decoration: none;
  color: var(--text-muted);
  font-size: 11.5px;
  transition: background 0.12s ease, color 0.12s ease;
}

.step:hover {
  background: rgba(0, 0, 0, 0.03);
  color: var(--text);
}

.step.active {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text);
}

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--chip-bg);
  border: 1px solid var(--chip-border);
  font-size: 10px;
  color: var(--text-muted);
}

.step.active .step-num {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.step-label {
  white-space: nowrap;
}

.step-sep {
  width: 1px;
  height: 14px;
  background: var(--border);
  margin: 0 2px;
}
</style>
