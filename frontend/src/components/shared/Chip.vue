<template>
  <span :class="['chip', variantClass]">
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type ChipVariant = 'neutral' | 'teal' | 'ok' | 'warning' | 'danger'

const props = defineProps<{ variant?: ChipVariant }>()

const variantClass = computed(() => {
  switch (props.variant ?? 'neutral') {
    case 'teal':
      return 'chip-teal'
    case 'ok':
      return 'chip-ok'
    case 'warning':
      return 'chip-warning'
    case 'danger':
      return 'chip-danger'
    default:
      return ''
  }
})
</script>

<style scoped>
.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--chip-bg);
  border: 1px solid var(--chip-border);
  color: var(--text-muted);
  font-size: 11.5px;
  white-space: nowrap;
}

.chip.active {
  background: var(--panel);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.chip-teal {
  background: var(--accent-bg);
  border-color: var(--accent);
  color: var(--accent);
}

.chip-ok {
  background: var(--ok-bg);
  border-color: var(--ok-bg);
  color: var(--ok-text);
}

.chip-warning {
  background: var(--warning-bg);
  border-color: var(--warning-bg);
  color: var(--warning-text);
}

.chip-danger {
  background: var(--danger-bg);
  border-color: var(--danger-bg);
  color: var(--danger-text);
}
</style>
