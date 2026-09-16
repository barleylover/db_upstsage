<template>
  <div class="setup-page">
    <div class="page-head">
      <div class="head-left">
        <span class="head-title">Setup</span>
        <span class="head-sub mono">문서 양식 {{ documentTemplates.length }}개</span>
        <button class="btn primary small">+ 새 문서 양식</button>
      </div>
    </div>

    <div class="tabs">
      <router-link to="/setup/schemas" class="tab">DBMS · 스키마</router-link>
      <router-link to="/setup/templates" class="tab" :class="{ active: true }">문서 양식</router-link>
    </div>

    <section class="search-row">
      <input class="input" placeholder="양식 이름·항목 이름" />
      <select class="input">
        <option>필터 · 전체</option>
      </select>
      <select class="input">
        <option>정렬 · 이름순</option>
      </select>
    </section>

    <div class="template-grid">
      <router-link
        v-for="tmpl in documentTemplates"
        :key="tmpl.id"
        :to="`/setup/templates/${tmpl.id}`"
        class="template-card card"
      >
        <div class="template-thumb"></div>
        <div class="template-info">
          <div class="template-name">{{ tmpl.name }}</div>
          <div class="template-meta mono">{{ tmpl.itemCount }}개 항목</div>
          <span class="badge" v-if="tmpl.isDefault">기본</span>
        </div>
      </router-link>

      <div class="template-card card new">
        <div class="template-thumb new-thumb"></div>
        <div class="template-info">
          <div class="template-name">새 문서 양식</div>
          <div class="template-meta mono">빈 양식으로 시작</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const documentTemplates = store.documentTemplates
</script>

<style scoped>
.setup-page {
  max-width: 1180px;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.head-title {
  font-size: 20px;
  font-weight: 600;
}

.head-sub {
  color: var(--text-dim);
  font-size: 13px;
}

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border-soft);
  margin-bottom: 18px;
}

.tab {
  padding: 8px 12px;
  border-radius: 6px 6px 0 0;
  font-size: 13px;
  color: var(--text-muted);
  text-decoration: none;
  background: var(--panel);
  border-bottom: 2px solid transparent;
}

.tab.active {
  color: var(--text);
  border-bottom-color: var(--accent);
}

.search-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.search-row .input {
  max-width: 240px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.template-card {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-decoration: none;
  color: inherit;
}

.template-card.new {
  border-style: dashed;
}

.template-thumb {
  height: 110px;
  border-radius: 8px;
  background: linear-gradient(180deg, #f2f2f2 0%, #e6e6e6 100%);
}

.new-thumb {
  background: repeating-linear-gradient(45deg, #f2f2f2, #f2f2f2 6px, #ececec 6px, #ececec 12px);
}

.template-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.template-name {
  font-size: 14px;
  font-weight: 500;
}

.template-meta {
  font-size: 11.5px;
  color: var(--text-dim);
}
</style>
