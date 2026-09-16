<template>
  <div class="setup-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 스키마 목록</button>
        <span class="head-title">Setup</span>
        <span class="head-sub mono">스키마 {{ schemaList.length }}개</span>
        <button class="btn primary small" @click="importMode = true">JSON 가져오기</button>
        <button class="btn small" @click="showNewSchema = true">+ 새 스키마</button>
      </div>
    </div>

    <div class="tabs">
      <router-link to="/setup/schemas" class="tab" :class="{ active: true }">DBMS · 스키마</router-link>
      <router-link to="/setup/templates" class="tab">문서 양식</router-link>
    </div>

    <section class="search-row">
      <input class="input" placeholder="스키마 이름·테이블 이름" />
      <select class="input">
        <option>정렬 · 이름순</option>
      </select>
    </section>

    <table class="table">
      <thead>
        <tr>
          <th>스키마</th>
          <th>DBMS</th>
          <th>database.schema</th>
          <th>테이블</th>
          <th>컬럼</th>
          <th>상태</th>
          <th></th>
        </tr>
      </thead>
      <tbody v-if="schemaList.length">
        <tr v-for="schema in schemaList" :key="schema.id">
          <td>
            <button class="schema-name" @click="openSchema(schema)">
              {{ schema.name }}
            </button>
          </td>
          <td class="mono">{{ schema.dbms }}</td>
          <td class="mono">{{ schema.database }}.{{ schema.schema }}</td>
          <td class="mono">{{ schema.tableCount }}개</td>
          <td class="mono">{{ schema.columnCount }}개</td>
          <td>
            <span class="badge" :class="{ 'ok': schema.used }">
              {{ schema.used ? '사용 중' : '미사용' }}
            </span>
          </td>
          <td>
            <button class="btn small" @click="useSchema(schema)">사용</button>
            <button class="btn small">복제</button>
          </td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr>
          <td colspan="7" class="empty-state">스키마가 없습니다.</td>
        </tr>
      </tbody>
    </table>

    <div class="empty-hint">행을 클릭하면 상세 편집으로 들어갑니다.</div>

    <Transition name="fade">
      <div v-if="importMode" class="overlay" @click.self="importMode = false">
        <div class="modal card">
          <h3>JSON 가져오기</h3>
          <div class="modal-actions">
            <button class="btn" @click="importMode = false">취소</button>
            <button class="btn primary" @click="importMode = false">새 스키마로 등록</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import type { SchemaCatalogEntry } from '@/types'

const router = useRouter()
const store = useAppStore()

const schemaList = store.schemaList
const importMode = ref(false)
const showNewSchema = ref(false)

function openSchema(schema: SchemaCatalogEntry) {
  router.push(`/setup/schemas/${schema.id}`)
}

function useSchema(schema: SchemaCatalogEntry) {
  store.activeSchemaId = schema.id
}
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
  flex: 1;
  max-width: 320px;
}

.schema-name {
  background: none;
  border: none;
  padding: 0;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.empty-hint {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-dim);
}

.overlay {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 20, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

.modal {
  width: 90%;
  max-width: 560px;
  padding: 24px;
}

.modal-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
