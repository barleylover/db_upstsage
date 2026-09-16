<template>
  <span :class="['pill', variantClass]">
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type PillVariant = 'neutral' | 'teal' | 'ok' | 'warning' | 'danger'

const props = defineProps<{ variant?: PillVariant }>()

const variantClass = computed(() => {
  switch (props.variant ?? 'neutral') {
    case 'teal':
      return 'pill-teal'
    case 'ok':
      return 'pill-ok'
    case 'warning':
      return 'pill-warning'
    case 'danger':
      return 'pill-danger'
    default:
      return ''
  }
})
</script>

<style scoped>
.pill {
  display: inline-flex;
  align-items: center;
  padding: 1px 8px;
  border-radius: 999px;
  font-family: var(--mono);
  font-size: 10.5px;
  background: var(--chip-bg);
  color: var(--text-muted);
}

.pill-teal {
  background: var(--accent-bg);
  color: var(--accent);
}

.pill-ok {
  background: var(--ok-bg);
  color: var(--ok-text);
}

.pill-warning {
  background: var(--warning-bg);
  color: var(--warning-text);
}

.pill-danger {
  background: var(--danger-bg);
  color: var(--danger-text);
}
</style>
