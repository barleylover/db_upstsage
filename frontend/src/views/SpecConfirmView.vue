<template>
  <div class="confirm-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 홈</button>
        <span class="head-title">01 명세 확정</span>
        <span class="mono">specId: <strong>{{ specId }}</strong></span>
        <span class="badge" :class="statusBadgeClass">{{ specStatus }}</span>
        <span class="mono">version {{ specVersion }}</span>
        <span class="mono">contentHash {{ specContentHash.slice(0, 12) }}…</span>
      </div>
    </div>

    <div v-if="loading" class="loading-bar">
      <span class="mono">명세 읽는 중…</span>
    </div>

    <div v-else-if="!spec" class="empty-state-card card">
      <div class="empty-state">명세를 불러오지 못했습니다.</div>
      <button class="btn primary" @click="refreshSpec">다시 불러오기</button>
    </div>

    <div v-else>
      <div class="steps">
        <button
          v-for="(s, idx) in steps"
          :key="s.key"
          class="step chip"
          :class="stepClass(idx)"
          @click="goStep(idx)"
        >
          <span class="step-num">{{ idx + 1 }}</span>
          {{ s.label }}
        </button>
      </div>

      <div class="confirm-grid">
        <section class="card">
          <div class="card-header">
            <span class="card-header-title">대상</span>
            <button class="btn small" @click="goStep(0)">수정</button>
          </div>
          <div class="field-grid">
            <div class="field">
              <label>환경</label>
              <input class="input mono" :value="(spec as any)?.environment ?? '·'" :disabled="!editable" />
            </div>
            <div class="field">
              <label>데이터베이스</label>
              <input class="input mono" :value="spec.database" :disabled="!editable" />
            </div>
            <div class="field">
              <label>스키마</label>
              <input class="input mono" :value="spec.schema" :disabled="!editable" />
            </div>
            <div class="field">
              <label>테이블</label>
              <input class="input mono" :value="spec.targetTable" :disabled="!editable" />
            </div>
            <div class="field">
              <label>작업</label>
              <input class="input mono" :value="spec.operation" :disabled="!editable" />
            </div>
            <div class="field">
              <label>식별 키</label>
              <input class="input mono" :value="spec.identityKeyColumns.join(', ')" :disabled="!editable" />
            </div>
          </div>
        </section>

        <section v-show="activeStep === 1" class="card">
          <div class="card-header">
            <span class="card-header-title">조건</span>
            <span class="card-header-meta">대상 조건 {{ predicates.length }} / {{ maxPredicates }} · predicates · 최소 1개</span>
          </div>

          <table class="data-table">
            <thead>
              <tr>
                <th>COLUMN</th>
                <th>OPERATOR</th>
                <th>VALUE</th>
                <th>VALUETYPE</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, idx) in predicates" :key="idx">
                <td class="mono">{{ p.column }}</td>
                <td class="mono">{{ p.operator }}</td>
                <td class="mono">{{ formatValue(p.value) }}</td>
                <td class="mono">{{ p.valueType }}</td>
                <td>
                  <button class="btn small" @click="removePredicate(idx)" :disabled="predicates.length <= 1">삭제</button>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="condition-actions">
            <button class="btn small" @click="addPredicate">+ 조건</button>
          </div>
        </section>

        <section v-show="activeStep === 2" class="card">
          <div class="card-header">
            <span class="card-header-title">변경값</span>
            <span class="card-header-meta">mutations · {{ mutations.length }}개</span>
          </div>

          <table class="data-table">
            <thead>
              <tr>
                <th>COLUMN</th>
                <th>VALUE</th>
                <th>VALUETYPE</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(m, idx) in mutations" :key="idx">
                <td class="mono">{{ m.column }}</td>
                <td class="mono">{{ formatValue(m.value) }}</td>
                <td class="mono">{{ m.valueType }}</td>
                <td>
                  <button class="btn small" @click="removeMutation(idx)" :disabled="mutations.length <= 1">삭제</button>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="condition-actions">
            <button class="btn small" @click="addMutation">+ 변경값</button>
          </div>
        </section>

        <section v-show="activeStep === 3" class="card">
          <div class="card-header">
            <span class="card-header-title">마무리</span>
          </div>

          <div class="field" style="margin-bottom: 14px;">
            <span class="field-label">예상 영향 건수</span>
            <input class="input mono" v-model.number="draft.expectedRowCount" placeholder="예: 77" :disabled="!editable" />
          </div>
          <div class="field" style="margin-bottom: 14px;">
            <span class="field-label">가정</span>
            <textarea class="textarea" rows="3" placeholder="예: 동시성 영향이 적은 배치 시간에만 실행" v-model="draft.assumptionsText" :disabled="!editable"></textarea>
          </div>
          <div class="field">
            <span class="field-label">미해결 질문</span>
            <textarea class="textarea" rows="2" placeholder="해결 전에는 확정이 불가능합니다" v-model="draft.unresolvedQuestionsText" :disabled="!editable"></textarea>
          </div>
        </section>
      </div>

      <div class="confirm-footer">
        <button class="btn outline" @click="prev" :disabled="activeStep === 0">← 이전</button>
        <button
          v-if="activeStep < steps.length - 1"
          class="btn primary"
          @click="next"
        >
          {{ stepButtonLabel }}
        </button>
        <button
          v-else
          class="btn primary"
          @click="confirm"
          :disabled="!editable || draft.unresolvedQuestionsText.length > 0"
        >
          {{ confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSpec, confirmSpec, type ChangeSpec } from '@/api/client'
import type { ValueType } from '@/types'

const route = useRoute()
const router = useRouter()

const specId = computed(() => route.params.specId as string)

const steps = [
  { key: 'target', label: '대상' },
  { key: 'predicates', label: '조건' },
  { key: 'mutations', label: '변경값' },
  { key: 'finalize', label: '마무리' },
]

const loading = ref(false)
const spec = ref<ChangeSpec | null>(null)

const activeStep = ref(1)
const maxPredicates = 4

interface Predicate {
  column: string
  operator: string
  value: unknown
  valueType: ValueType
}

interface Mutation {
  column: string
  value: unknown
  valueType: ValueType
}

const draft = ref<{
  environment: string
  database: string
  schema: string
  targetTable: string
  operation: string
  identityKeyColumns: string[]
  predicates: Predicate[]
  mutations: Mutation[]
  expectedRowCount: number | null
  assumptionsText: string
  unresolvedQuestionsText: string
}>({
  environment: 'production',
  database: 'app',
  schema: 'public',
  targetTable: 'orders',
  operation: 'UPDATE',
  identityKeyColumns: ['id'],
  predicates: [
    { column: 'tenant_id', operator: 'EQ', value: 42, valueType: 'NUMBER' },
    { column: 'status', operator: 'EQ', value: 'pending', valueType: 'STRING' },
    { column: 'created_at', operator: 'LT', value: '2026-09-01T00:00:00+09:00', valueType: 'TIMESTAMP' },
  ],
  mutations: [
    { column: 'status', value: 'cancelled', valueType: 'STRING' },
  ],
  expectedRowCount: 77,
  assumptionsText: '',
  unresolvedQuestionsText: '',
})

const specStatus = computed(() => spec.value?.status ?? 'DRAFT')
const specVersion = computed(() => spec.value?.version ?? 1)
const specContentHash = computed(() => spec.value?.contentHash ?? '')
const predicates = computed(() => draft.value.predicates)
const mutations = computed(() => draft.value.mutations)

const statusBadgeClass = computed(() => {
  const s = specStatus.value
  if (s === 'CONFIRMED') return 'badge-ok'
  if (s === 'DRAFT') return 'badge-warning'
  return 'badge-danger'
})

const stepClass = (idx: number) => {
  if (idx < activeStep.value) return 'step-done'
  if (idx === activeStep.value) return 'step-active'
  return ''
}

const stepButtonLabel = computed(() => {
  if (activeStep.value === 0) return '조건으로'
  if (activeStep.value === 1) return '변경값으로'
  if (activeStep.value === 2) return '마무리로'
  return ''
})

const confirmLabel = computed(() => {
  if (specStatus.value === 'CONFIRMED') return '확정됨'
  if (draft.value.unresolvedQuestionsText.trim()) return '미해결 질문이 있습니다'
  return '확정'
})

const editable = computed(() => specStatus.value === 'DRAFT')

watch(
  () => activeStep.value,
  () => {
    syncDraftFromSpec()
  },
  { immediate: true },
)

function syncDraftFromSpec() {
  if (!spec.value) return
  const s = spec.value
  draft.value = {
    environment: 'production',
    database: s.database,
    schema: s.schema,
    targetTable: s.targetTable,
    operation: s.operation,
    identityKeyColumns: s.identityKeyColumns,
    predicates: s.predicates.map((p) => ({
      column: p.column,
      operator: p.operator,
      value: p.value,
      valueType: p.valueType as ValueType,
    })),
    mutations: s.mutations.map((m) => ({
      column: m.column,
      value: m.value,
      valueType: m.valueType as ValueType,
    })),
    expectedRowCount: s.expectedRowCount,
    assumptionsText: s.assumptions.join(' '),
    unresolvedQuestionsText: s.unresolvedQuestions.join(' '),
  }
}

async function refreshSpec() {
  loading.value = true
  try {
    const data = await getSpec(specId.value)
    spec.value = data
    syncDraftFromSpec()
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

function goStep(idx: number) {
  activeStep.value = idx
}

function next() {
  if (activeStep.value < steps.length - 1) {
    activeStep.value++
  }
}

function prev() {
  if (activeStep.value > 0) {
    activeStep.value--
  }
}

function addPredicate() {
  if (predicates.value.length >= maxPredicates) return
  draft.value.predicates.push({ column: '', operator: 'EQ', value: null, valueType: 'STRING' })
}

function removePredicate(idx: number) {
  if (predicates.value.length <= 1) return
  draft.value.predicates.splice(idx, 1)
}

function addMutation() {
  if (mutations.value.length >= 5) return
  draft.value.mutations.push({ column: '', value: null, valueType: 'STRING' })
}

function removeMutation(idx: number) {
  if (mutations.value.length <= 1) return
  draft.value.mutations.splice(idx, 1)
}

async function confirm() {
  if (!editable.value) return
  if (draft.value.unresolvedQuestionsText.trim()) return
  try {
    const payload = {
      environment: draft.value.environment,
      database: draft.value.database,
      schema: draft.value.schema,
      targetTable: draft.value.targetTable,
      operation: draft.value.operation,
      identityKeyColumns: draft.value.identityKeyColumns,
      predicates: draft.value.predicates
        .filter((p) => p.column && p.operator)
        .map((p) => ({
          column: p.column,
          operator: p.operator,
          value: p.value,
          valueType: p.valueType,
        })),
      mutations: draft.value.mutations
        .filter((m) => m.column)
        .map((m) => ({
          column: m.column,
          value: m.value,
          valueType: m.valueType,
        })),
      expectedRowCount: draft.value.expectedRowCount,
      assumptions: draft.value.assumptionsText
        ? draft.value.assumptionsText.split(/\s+/).filter(Boolean)
        : [],
      unresolvedQuestions: draft.value.unresolvedQuestionsText
        ? draft.value.unresolvedQuestionsText.split(/\s+/).filter(Boolean)
        : [],
    }
    const updated = await confirmSpec(specId.value, payload)
    spec.value = updated
    await router.push(`/spec/${specId.value}/sql-pack`)
  } catch (err: unknown) {
    const e = err as { status?: number; message?: string; code?: string }
    if (e.status === 409 && (e.code === 'SPEC_NOT_DRAFT' || e.code === 'UNRESOLVED_QUESTIONS')) {
      return
    }
    console.error(err)
  }
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  return String(value)
}
</script>

<style scoped>
.confirm-page {
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

.head-right {
  color: var(--text-muted);
  font-size: 12px;
}

.loading-bar {
  margin-bottom: 18px;
  color: var(--text-muted);
}

.empty-state-card {
  padding: 32px;
}

.empty-state {
  color: var(--text-dim);
  font-size: 13px;
}

.steps {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--chip-bg);
  border: 1px solid var(--chip-border);
  font-size: 11px;
  color: var(--text-muted);
}

.step-active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.step-done .step-num {
  background: var(--accent-bg);
  border-color: var(--accent);
  color: var(--accent);
}

.confirm-grid {
  display: grid;
  gap: 16px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
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

.condition-actions {
  margin-top: 12px;
}

.confirm-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border-soft);
}

.summary-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.summary-label {
  font-size: 12px;
  color: var(--text-dim);
}
</style>
