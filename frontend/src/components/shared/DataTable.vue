<template>
  <table class="data-table">
    <thead>
      <tr>
        <th v-for="h in headers" :key="h" scope="col">{{ h }}</th>
      </tr>
    </thead>
    <tbody>
      <slot />
    </tbody>
  </table>
</template>

<script setup lang="ts">
const props = defineProps<{ headers: string[] }>()
</script>

<style scoped>
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  text-align: left;
  padding: 8px 10px;
  background: var(--bg);
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.03em;
  border-bottom: 1px solid var(--border-soft);
}

.data-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-soft);
  vertical-align: top;
}

.data-table tr:last-child td {
  border-bottom: none;
}
</style>
