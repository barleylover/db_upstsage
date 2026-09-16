<template>
  <Card :class="['card', { 'card-ghost': ghost }]">
    <div v-if="$slots.header" class="card-header">
      <slot name="header" />
    </div>
    <div class="card-body">
      <slot />
    </div>
  </Card>
</template>

<script setup lang="ts">
defineProps<{ ghost?: boolean }>()
</script>

<style scoped>
.card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 16px;
}

.card-ghost {
  background: transparent;
  border-color: transparent;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-soft);
}

.card-header-title {
  font-size: 15px;
  font-weight: 600;
}

.card-header-meta {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text-dim);
}

.card-body {
  padding: 18px;
}
</style>
