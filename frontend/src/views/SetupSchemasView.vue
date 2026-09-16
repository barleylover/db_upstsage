<template>
  <div class="setup-page">
    <div class="page-head">
      <div class="head-left">
        <span class="setup-bread mono">홈</span>
        <span class="setup-bread-sep">/</span>
        <span class="setup-bread mono">스키마 목록</span>
      </div>
      <div class="head-right">
        <button class="btn primary small" @click="handleNewSchema">+ 새 스키마</button>
      </div>
    </div>

    <div class="tabs">
      <RouterLink to="/setup/schemas" class="tab" :class="{ active: true }">DBMS · 스키마</RouterLink>
      <RouterLink to="/setup/templates" class="tab">문서 양식</RouterLink>
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
          <th>수정한 날짜</th>
          <th>상태</th>
          <th></th>
        </tr>
      </thead>
      <tbody v-if="schemaList.length">
        <tr v-for="schema in schemaList" :key="schema.id" :class="{ 'schema-in-use': schema.used }">
          <td>
            <button class="schema-name" @click="openSchema(schema)">
              {{ schema.name }}
            </button>
          </td>
          <td class="mono">{{ schema.dbms }}</td>
          <td class="mono">{{ schema.database }}.{{ schema.schema }}</td>
          <td class="mono">{{ schema.tableCount }}개</td>
          <td class="mono">{{ schema.columnCount }}개</td>
          <td class="mono">{{ schema.updatedAt.slice(0, 10) }}</td>
          <td>
            <span class="chip" :class="schema.used ? 'chip-ok' : 'chip'">
              {{ schema.used ? '사용 중' : '사용' }}
            </span>
          </td>
          <td>
            <button class="btn small" @click="handleUseSchema(schema)">{{ schema.used ? '사용 안 함' : '사용' }}</button>
            <button class="btn small">복제</button>
          </td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr>
          <td colspan="8" class="empty-state">스키마가 없습니다.</td>
        </tr>
      </tbody>
    </table>

    <div class="empty-hint">행을 클릭하면 상세 편집으로 들어갑니다.</div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import type { SchemaCatalogEntry } from '@/types'

const router = useRouter()
const store = useAppStore()

const schemaList = store.schemaList

function openSchema(schema: SchemaCatalogEntry) {
  router.push(`/setup/schemas/${schema.id}`)
}

function handleUseSchema(schema: SchemaCatalogEntry) {
  if (schema.used) {
    schema.used = false
  } else {
    schema.used = true
    store.activeSchemaId = schema.id
  }
  store.persistSchemaCatalog()
}

function handleNewSchema() {
  const newId = 'schema_' + Date.now()
  const entry: SchemaCatalogEntry = {
    id: newId,
    name: '새 스키마',
    dbms: 'POSTGRESQL',
    database: 'app',
    schema: 'public',
    tables: [],
    updatedAt: new Date().toISOString(),
    tableCount: 0,
    columnCount: 0,
    used: false,
  }
  schemaList.push(entry)
  store.persistSchemaCatalog()
  router.push(`/setup/schemas/${newId}`)
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
  flex-wrap: wrap;
  gap: 10px;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.setup-bread {
  font-size: 12px;
  color: var(--text-muted);
}

.setup-bread-sep {
  color: var(--text-faint);
}

.head-right {
  display: flex;
  gap: 8px;
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
  display: block;
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

.schema-in-use {
  background: var(--accent-bg);
}

.empty-hint {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-dim);
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.table th {
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

.table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-soft);
  vertical-align: top;
}

.table tr:last-child td {
  border-bottom: none;
}

.empty-state {
  color: var(--text-dim);
  font-size: 13px;
  padding: 8px 10px;
}
</style>
