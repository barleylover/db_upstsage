<template>
  <header class="topbar">
    <nav class="topbar-tabs">
      <button class="topbar-tab" :class="{ active: isActiveHome }" @click="go('/home')">홈</button>
      <button class="topbar-tab" :class="{ active: isActiveStep(2) }" :disabled="!canAct(2)" @click="goStep(2)">01 명세 확정</button>
      <button class="topbar-tab" :class="{ active: isActiveStep(3) }" :disabled="!canAct(3)" @click="goStep(3)">02 SQL 팩</button>
      <button class="topbar-tab" :class="{ active: isActiveStep(4) }" :disabled="!canAct(4)" @click="goStep(4)">03 검토</button>
      <button class="topbar-tab" :class="{ active: isActiveStep(5) }" :disabled="!canAct(5)" @click="goStep(5)">04 변경 문서</button>
      <button class="topbar-tab" :class="{ active: isActiveStep(6) }" :disabled="!canAct(6)" @click="goStep(6)">05 내보내기</button>
    </nav>
    <div class="topbar-right">
      <span class="pill" :class="versionPillClass" v-if="specId">CONFIRMED v{{ specVersion }}</span>
      <span class="pill pill-teal">DEMO</span>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const specId = computed(() => store.currentSpecId)
const specStatus = computed(() => store.currentSpecStatus ?? 'DRAFT')
const specVersion = computed(() => {
  if (!specId.value) return 1
  const spec = store.spec
  return spec?.version ?? 1
})

const isActiveHome = computed(() => route.path === '/home')

const currentStep = computed((): number => {
  const path = route.path
  if (path.startsWith('/spec/')) {
    const parts = path.split('/')
    const afterSpec = parts[2]
    if (!afterSpec) return 0
    if (afterSpec === 'confirm') return 2
    if (afterSpec === 'sql-pack') return 3
    if (afterSpec === 'review') return 4
    if (afterSpec === 'document') return 5
    if (afterSpec === 'export') return 6
    return 0
  }
  return 0
})

const isActiveStep = (step: number): boolean => currentStep.value === step

const canAct = (step: number): boolean => {
  if (!specId.value) return false
  if (step === 2) return true
  if (specStatus.value !== 'CONFIRMED') return false
  if (step === 3) return true
  if (step === 4) {
    const review = store.review
    if (!review) return false
    return review.verdict === 'REVIEW' || review.verdict === 'BLOCK'
  }
  if (step === 5) {
    const review = store.review
    if (!review) return false
    return review.verdict === 'READY' || review.verdict === 'BLOCK'
  }
  if (step === 6) return true
  return false
}

const versionPillClass = computed((): string => {
  if (specStatus.value === 'CONFIRMED') return 'pill-ok'
  return ''
})

const go = (path: string): void => {
  router.push(path)
}

const goStep = (step: number): void => {
  if (!specId.value) {
    router.push('/home')
    return
  }
  if (step === 2) router.push(`/spec/${specId.value}/confirm`)
  else if (step === 3) router.push(`/spec/${specId.value}/sql-pack`)
  else if (step === 4) router.push(`/spec/${specId.value}/review`)
  else if (step === 5) router.push(`/spec/${specId.value}/document`)
  else if (step === 6) router.push(`/spec/${specId.value}/export`)
}
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 28px;
  border-bottom: 1px solid var(--border);
  background: var(--panel);
  position: sticky;
  top: 0;
  z-index: 5;
}

.topbar-tabs {
  display: flex;
  gap: 4px;
}

.topbar-tab {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border-soft);
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease, color 0.12s ease;
}

.topbar-tab:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.02);
  color: var(--text);
}

.topbar-tab.active {
  background: #ffffff;
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

.topbar-tab:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.topbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
