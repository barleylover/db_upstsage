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
import { useRoute } from 'vue-router'

const route = useRoute()

const steps = [
  { num: '01', label: '명세 확정', to: '/spec/new' },
  { num: '02', label: 'SQL 팩', to: (specId: string) => `/spec/${specId}/sql-pack` },
  { num: '03', label: '검토', to: (specId: string) => `/spec/${specId}/review` },
  { num: '04', label: '변경 문서', to: (specId: string) => `/spec/${specId}/document` },
  { num: '05', label: '내보내기', to: (specId: string) => `/spec/${specId}/export` },
]

const specStatus = 'CONFIRMED'
const specVersion = 1

const currentSpecId = 'placeholder'

function resolveStepTo(step: { to: string | ((specId: string) => string) }) {
  if (typeof step.to === 'function') {
    return currentSpecId ? step.to(currentSpecId) : '/spec/new'
  }
  return step.to
}

function isActive(step: { to: string | ((specId: string) => string) }) {
  const target = resolveStepTo(step)
  return route.path === target || route.path.startsWith(target)
}

function isDone(_step: { to: string | ((specId: string) => string) }) {
  return false
}
</script>
