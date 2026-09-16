<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="brand-mark"></span>
      <span class="brand-text">ChangeSpec</span>
    </div>

    <nav class="sidebar-nav">
      <button class="sidebar-section-btn" @click="$emit('newReview')">
        <span class="plus">+</span> 새 검토
      </button>
      <button class="sidebar-section-btn" :class="{ active: activeRoute.startsWith('/setup/schemas') }" @click="$router.push('/setup/schemas')">
        스키마
      </button>
      <button class="sidebar-section-btn" :class="{ active: activeRoute.startsWith('/setup/templates') }" @click="$router.push('/setup/templates')">
        양식
      </button>
    </nav>

    <div class="sidebar-tools">
      <div class="sidebar-tools-row">
        <button class="sidebar-tool-btn">검색</button>
        <button class="sidebar-tool-btn">필터</button>
        <button class="sidebar-tool-btn">정렬</button>
      </div>
      <div class="sidebar-tools-divider"></div>

      <div class="sidebar-section-label">북마크</div>
      <div class="sidebar-chat-list">
        <div class="sidebar-chat-item">
          <span class="sidebar-chat-dot"></span>
          <div class="sidebar-chat-content">
            <div class="sidebar-chat-title">폴더 +</div>
          </div>
        </div>
      </div>

      <div class="sidebar-section-label">최근 대화 내역</div>
      <div class="sidebar-chat-list">
        <div class="sidebar-chat-item active" @click="onSelectChat">
          <span class="sidebar-chat-dot"></span>
          <div class="sidebar-chat-content">
            <div class="sidebar-chat-title">tenant_id가 42이고 status가…</div>
            <div class="sidebar-chat-meta">UPDATE · orders · REVIEW</div>
          </div>
        </div>
        <div class="sidebar-date-group">
          <div class="sidebar-date-label">오늘</div>
        </div>
        <div class="sidebar-chat-item" @click="onSelectChat">
          <span class="sidebar-chat-dot"></span>
          <div class="sidebar-chat-content">
            <div class="sidebar-chat-title">status가 draft인 주문을 삭제…</div>
            <div class="sidebar-chat-meta">DELETE · orders · DRAFT</div>
          </div>
        </div>
        <div class="sidebar-date-group">
          <div class="sidebar-date-label">어제</div>
        </div>
        <div class="sidebar-chat-item" @click="onSelectChat">
          <span class="sidebar-chat-dot"></span>
          <div class="sidebar-chat-content">
            <div class="sidebar-chat-title">created_at이 비어 있는 주문…</div>
            <div class="sidebar-chat-meta">UPDATE · orders · BLOCK</div>
          </div>
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <button class="sidebar-footer-btn" :class="{ active: activeRoute === '/settings' }" @click="$router.push('/settings')">
        설정   ·   SQL 편집기 · 토크나이저
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const emit = defineEmits<{ newReview: [] }>()

const activeRoute = computed(() => route.path)

function onSelectChat() {
  // 최근 대화 항목 클릭 시 해당 spec의 마지막 단계로 이동
  // 백엔드에 목록 API가 없어서 지금은 홈으로 돌아가기만 하되, 추후 Pinia/ローカステストデータ 연동
  emit('newReview')
}
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
  background: var(--accent);
}

.brand-text {
  font-size: 14px;
  font-weight: 600;
}

.sidebar-nav {
  padding: 12px 12px 8px;
}

.sidebar-section-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 232px;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: #fff;
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease, color 0.12s ease;
}

.sidebar-section-btn:hover {
  background: rgba(0, 0, 0, 0.02);
}

.sidebar-section-btn.active {
  background: var(--accent-bg);
  border-color: var(--accent);
  color: var(--accent);
}

.sidebar-section-btn .plus {
  font-weight: 600;
}

.sidebar-tools {
  padding: 8px 12px;
}

.sidebar-tools-row {
  display: flex;
  gap: 4px;
}

.sidebar-tool-btn {
  flex: 1;
  padding: 4px 6px;
  border: none;
  background: transparent;
  border-radius: 6px;
  color: var(--text-dim);
  font-size: 11px;
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease;
}

.sidebar-tool-btn:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-muted);
}

.sidebar-tools-divider {
  height: 1px;
  background: var(--border-soft);
  margin: 8px 0;
}

.sidebar-section-label {
  font-size: 11px;
  color: var(--text-faint);
  margin: 12px 4px 6px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sidebar-chat-list {
  flex: 1;
  overflow: auto;
  margin: 0 4px;
}

.sidebar-chat-item {
  display: flex;
  gap: 8px;
  padding: 7px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s ease;
}

.sidebar-chat-item:hover {
  background: rgba(0, 0, 0, 0.03);
}

.sidebar-chat-item.active {
  background: var(--accent-bg);
}

.sidebar-chat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-faint);
  flex-shrink: 0;
  margin-top: 4px;
}

.sidebar-chat-content {
  min-width: 0;
}

.sidebar-chat-title {
  font-size: 12px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-chat-meta {
  font-family: var(--mono);
  font-size: 9.5px;
  color: var(--text-dim);
  margin-top: 2px;
}

.sidebar-date-group {
  margin: 6px 4px;
}

.sidebar-date-label {
  font-size: 11px;
  color: var(--text-faint);
  margin-bottom: 4px;
}

.sidebar-footer {
  border-top: 1px solid var(--border);
  padding: 12px 16px 14px;
}

.sidebar-footer-btn {
  display: block;
  width: 100%;
  text-align: left;
  padding: 6px 4px;
  border: none;
  background: transparent;
  border-radius: 6px;
  color: var(--text-dim);
  font-size: 11px;
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease;
}

.sidebar-footer-btn:hover {
  background: rgba(0, 0, 0, 0.03);
  color: var(--text-muted);
}

.sidebar-footer-btn.active {
  background: var(--accent-bg);
  color: var(--accent);
}
</style>
