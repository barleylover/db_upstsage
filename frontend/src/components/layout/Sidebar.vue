<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="brand-mark"></span>
      <span class="brand-text">ChangeSpec</span>
    </div>
    <nav class="sidebar-nav">
      <button class="sidebar-btn" @click="$emit('newReview')">
        <span class="plus">+</span> 새 검토
      </button>
      <button class="sidebar-btn" @click="$router.push('/setup/schemas')">스키마</button>
      <button class="sidebar-btn" @click="$router.push('/setup/templates')">양식</button>
    </nav>
    <div class="sidebar-tools">
      <div class="tool-group-label mono">검색 필터 정렬</div>
      <div class="tool-row"><span>북마크</span></div>
      <div class="tool-row"><span>폴더</span> +</div>
      <div class="tool-row"><span>최근 대화 내역</span></div>
      <div class="tool-row"><span>오늘</span></div>
      <div class="tool-row"><span>어제</span></div>
    </div>
    <div class="sidebar-footer">
      <span class="mono">설정   ·   SQL 편집기 · 토크나이저</span>
    </div>
  </aside>
</template>

<script setup lang="ts">
defineEmits<{ newReview: [] }>()
</script>

<style scoped>
.sidebar {
  width: 264px;
  flex-shrink: 0;
  background: #f2f2f2;
  border-inline-end: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 16px 12px;
}

.brand-mark {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--accent-2);
}

.brand-text {
  font-size: 14px;
  font-weight: 600;
}

.sidebar-nav {
  padding: 0 12px;
}

.sidebar-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: none;
  background: transparent;
  border-radius: 9px;
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.12s ease;
}

.sidebar-btn:hover {
  background: rgba(0, 0, 0, 0.04);
}

.sidebar-btn .plus {
  font-weight: 600;
}

.sidebar-tools {
  flex: 1;
  padding: 12px 12px 0;
  overflow: auto;
}

.tool-group-label {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text-ghost);
  margin-bottom: 6px;
}

.tool-row {
  font-size: 11px;
  color: var(--text-dim);
  padding: 2px 0;
}

.sidebar-footer {
  border-top: 1px solid var(--border);
  padding: 12px 16px 16px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text-ghost);
}
</style>
