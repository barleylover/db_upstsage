<template>
  <button
    :class="['segmented-tab', { 'segmented-tab-active': activeTab === tab }]"
    @click="emit('select', tab)"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">

const props = defineProps<{ tab: string; activeTab: string }>()
const emit = defineEmits<{ select: [tab: string] }>()
</script>

<style scoped>
.segmented-tabs {
  display: inline-flex;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 3px;
}

.segmented-tab {
  padding: 5px 14px;
  border-radius: 18px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 12.5px;
  transition: background 0.12s ease, color 0.12s ease;
  font-weight: 500;
  cursor: pointer;
  user-select: none;
}

.segmented-tab-active {
  background: #ffffff;
  color: var(--accent);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
</style>
