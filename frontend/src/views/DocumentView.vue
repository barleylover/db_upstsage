<template>
  <div class="document-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 검토</button>
        <span class="head-title">04 변경 문서</span>
        <span class="mono">양식 기본 변경 신청서</span>
        <span class="mono">기준: v{{ specVersion }} · rev {{ sqlRevision }}</span>
        <span class="mono">생성일: {{ createdAt }}</span>
        <span class="badge warning">재생성 필요</span>
        <span class="badge danger">불일치 1</span>
      </div>
    </div>

    <div class="doc-grid">
      <section class="card form-card">
        <div class="section-title">양식 선택</div>
        <div class="field" style="margin-bottom: 12px;">
          <label>문서 양식</label>
          <select class="input" v-model="selectedTemplate">
            <option v-for="tmpl in templates" :key="tmpl.id" :value="tmpl.id">
              {{ tmpl.name }} ({{ tmpl.itemCount }}개 항목)
            </option>
          </select>
        </div>
        <div class="doc-actions">
          <button class="btn primary" @click="regenerateDoc" :disabled="pending">
            {{ pending ? '재생성 중…' : '선택한 양식으로 다시 생성' }}
          </button>
          <button class="btn" @click="reviewAgain">문서까지 다시 검토</button>
          <button class="btn" @click="goExport">내보내기 →</button>
        </div>
      </section>

      <section class="card body-card">
        <div class="section-title">변경 문서</div>
        <table class="table">
          <thead>
            <tr>
              <th>항목</th>
              <th>내용</th>
              <th>정보 출처</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in documentRows" :key="idx" :class="{ 'mismatch': row.mismatch }">
              <td><span class="row-label">{{ row.name }}</span></td>
              <td class="mono">{{ row.value }}</td>
              <td><span class="source-label">{{ row.source }}</span></td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const store = useAppStore()

const selectedTemplate = ref('default')
const pending = ref(false)
const specVersion = 1
const sqlRevision = 2
const createdAt = '2026-09-16'

const templates = computed(() => store.documentTemplates)

interface DocumentRow {
  name: string
  value: string
  source: string
  mismatch?: boolean
}

const documentRows = ref<DocumentRow[]>([
  { name: '변경 요청 원문', value: 'tenant_id가 42이고 status가 pending인 주문을 취소 변경해줘', source: '변경 요청 원문' },
  { name: '대상 테이블', value: 'refunds', source: '대상 테이블', mismatch: true },
  { name: '변경 작업', value: 'UPDATE', source: '변경 작업' },
  { name: '대상 조건', value: 'tenant_id = 42, status = pending', source: '대상 조건' },
  { name: '실행 SQL', value: 'UPDATE "public"."orders" SET "status" = \'cancelled\' WHERE ...', source: '실행 SQL' },
  { name: '승인자', value: '직접 입력', source: '승인자' },
])

function regenerateDoc() {
  pending.value = true
  setTimeout(() => {
    pending.value = false
    documentRows.value = documentRows.value.map((row) =>
      row.name === '대상 테이블' ? { ...row, value: 'orders', mismatch: false } : row,
    )
  }, 600)
}

function reviewAgain() {
  // TODO: 다시 검토
}

function goExport() {
  router.push(`/spec/placeholder/export`)
}
</script>

<style scoped>
.document-page {
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
  gap: 12px;
}

.head-title {
  font-size: 20px;
  font-weight: 600;
}

.doc-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  align-items: start;
}

.form-card {
  padding: 18px;
}

.body-card {
  padding: 18px;
}

.row-label {
  display: block;
  font-weight: 500;
}

.source-label {
  color: var(--text-muted);
  font-size: 12px;
}

.mismatch {
  background: #fbe7ea;
}

.mismatch td {
  color: var(--danger);
}

.doc-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}
</style>
