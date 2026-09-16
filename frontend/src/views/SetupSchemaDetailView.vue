<template>
  <div class="detail-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 스키마 목록</button>
        <span class="head-title">{{ schema?.name ?? '스키마 상세' }}</span>
        <span class="badge" :class="{ 'ok': true }">사용 중</span>
      </div>
      <div class="head-right">
        <span class="mono">{{ tableCount }}개 테이블 · {{ columnCount }}개 컬럼</span>
        <span class="badge warning" v-if="!saved">저장 안 됨</span>
        <button class="btn primary" @click="save">저장</button>
      </div>
    </div>

    <section class="card" style="padding: 20px;">
      <div class="section-title">연결 정보</div>
      <div class="field-grid">
        <div class="field">
          <label>스키마 이름</label>
          <input class="input" :value="schema?.name ?? ''" @input="set('name', ($event.target as HTMLInputElement).value)" />
        </div>
        <div class="field">
          <label>DBMS</label>
          <select class="input" :value="schema?.dbms ?? 'POSTGRESQL'" @change="setDbms(($event.target as HTMLSelectElement).value)">
            <option v-for="d in supportedDbmses" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>
        <div class="field">
          <label>DATABASE</label>
          <input class="input mono" :value="schema?.database ?? ''" @input="set('database', ($event.target as HTMLInputElement).value)" />
        </div>
        <div class="field">
          <label>SCHEMA</label>
          <input class="input mono" :value="schema?.schema ?? ''" @input="set('schema', ($event.target as HTMLInputElement).value)" />
        </div>
      </div>
    </section>

    <section class="card" style="margin-top: 16px; padding: 20px;">
      <div class="section-title">테이블 #1</div>
      <div class="field-grid">
        <div class="field">
          <label>테이블명</label>
          <input class="input mono" v-model="tableName" />
        </div>
        <div class="field">
          <label>기본 키 컬럼</label>
          <input class="input mono" v-model="primaryKey" />
        </div>
      </div>

      <table class="table" style="margin-top: 14px;">
        <thead>
          <tr>
            <th>컬럼명</th>
            <th>데이터 타입</th>
            <th>Nullable</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(col, idx) in columns" :key="idx">
            <td class="mono">{{ col.name }}</td>
            <td class="mono">{{ col.data_type }}</td>
            <td>
              <label class="check">
                <input type="checkbox" v-model="col.nullable" />
                허용
              </label>
            </td>
            <td>
              <button class="btn small">삭제</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="table-actions">
        <button class="btn small" @click="addColumn">+ 컬럼</button>
        <button class="btn small">+ 테이블</button>
        <button class="btn small">JSON 가져오기</button>
        <button class="btn small">예시 스키마로 되돌리기</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import type { SchemaCatalogEntry } from '@/types'

const route = useRoute()
const store = useAppStore()

const schema = computed<SchemaCatalogEntry | null>(() => store.schemaList.find((s) => s.id === route.params.schemaId) ?? null)

const tableName = ref('orders')
const primaryKey = ref('id')
const columns = ref([
  { name: 'id', data_type: 'bigint', nullable: false },
  { name: 'tenant_id', data_type: 'bigint', nullable: false },
  { name: 'status', data_type: 'varchar', nullable: false },
  { name: 'created_at', data_type: 'timestamp', nullable: false },
])

const tableCount = computed(() => 1)
const columnCount = computed(() => columns.value.length)
const saved = ref(false)
const supportedDbmses = store.supportedDbmses

function addColumn() {
  columns.value.push({ name: '', data_type: 'varchar', nullable: true })
}

function save() {
  saved.value = true
}

function set(key: string, value: string) {
  if (!schema.value) return
  Object.assign(schema.value, { [key]: value })
}

function setDbms(value: string) {
  if (!schema.value) return
  schema.value.dbms = value as SchemaCatalogEntry['dbms']
}
</script>

<style scoped>
.detail-page {
  max-width: 1180px;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.head-left,
.head-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.head-title {
  font-size: 20px;
  font-weight: 600;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 12px;
  color: var(--text-muted);
}

.table-actions {
  margin-top: 14px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  cursor: pointer;
  user-select: none;
}
</style>
