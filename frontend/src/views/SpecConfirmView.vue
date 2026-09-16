<template>
  <div class="confirm-page">
    <div class="confirm-header">
      <div class="confirm-header-left">
        <span class="confirm-bread mono">홈</span>
        <span class="confirm-bread-sep">/</span>
        <span class="confirm-bread mono">01 명세 확정</span>
      </div>
      <div class="confirm-meta">
        <span class="confirm-meta-item mono">specId {{ specId }}</span>
        <span class="confirm-meta-item mono">status {{ specStatus }}</span>
        <span class="confirm-meta-item mono">version {{ specVersion }}</span>
        <span class="confirm-meta-item mono">contentHash {{ specContentHash.slice(0, 12) }}…</span>
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
      <div class="sub-steps">
        <button
          v-for="(s, idx) in steps"
          :key="s.key"
          class="sub-step"
          :class="subStepClass(idx)"
        >
          {{ s.label }}
        </button>
      </div>

      <div v-if="activeStep === 0" class="target-summary card">
        <div class="target-summary-row">
          <span class="target-summary-label">대상</span>
          <span class="target-summary-value mono">
            {{ draft.environment ? `[${draft.environment}] environment` : '·' }}
            {{ draft.environment ? '|' : '' }}
            {{ draft.database ? `[${draft.database}] database` : '·' }}
            {{ draft.database ? '|' : '' }}
            {{ draft.schema ? `[${draft.schema}] schema` : '·' }}
            {{ draft.schema ? '|' : '' }}
            {{ draft.targetTable ? `[${draft.targetTable}] table` : '·' }}
            {{ draft.targetTable ? '|' : '' }}
            {{ draft.identityKeyColumns.length ? `[${draft.identityKeyColumns.join(', ')}] identityKey` : '·' }}
          </span>
          <button v-if="editable" class="btn small" @click="startEditTarget">수정</button>
        </div>
      </div>

      <div class="confirm-grid">
        <section v-show="activeStep === 0" class="card">
          <div class="card-header">
            <span class="card-header-title">01 대상</span>
            <span v-if="editable" class="card-header-meta">수정 가능</span>
          </div>
          <div v-if="editingTarget" class="field-grid">
            <div class="field">
              <label>환경</label>
              <input class="input mono" v-model="draft.environment" />
            </div>
            <div class="field">
              <label>데이터베이스</label>
              <input class="input mono" v-model="draft.database" />
            </div>
            <div class="field">
              <label>스키마</label>
              <input class="input mono" v-model="draft.schema" />
            </div>
            <div class="field">
              <label>테이블</label>
              <input class="input mono" v-model="draft.targetTable" />
            </div>
            <div class="field">
              <label>작업</label>
              <select class="input mono" v-model="draft.operation">
                <option value="UPDATE">UPDATE</option>
                <option value="DELETE">DELETE</option>
              </select>
            </div>
            <div class="field">
              <label>식별 키</label>
              <input class="input mono" v-model="draft.identityKeyColumnsText" placeholder="예: id" />
            </div>
          </div>
          <div v-else class="field-grid">
            <div class="field">
              <label>환경</label>
              <span class="mono field-value">{{ spec.environment ?? '·' }}</span>
            </div>
            <div class="field">
              <label>데이터베이스</label>
              <span class="mono field-value">{{ spec.database ?? '·' }}</span>
            </div>
            <div class="field">
              <label>스키마</label>
              <span class="mono field-value">{{ spec.schema ?? '·' }}</span>
            </div>
            <div class="field">
              <label>테이블</label>
              <span class="mono field-value">{{ spec.targetTable ?? '·' }}</span>
            </div>
            <div class="field">
              <label>작업</label>
              <span class="mono field-value">{{ spec.operation ?? '·' }}</span>
            </div>
            <div class="field">
              <label>식별 키</label>
              <span class="mono field-value">{{ spec.identityKeyColumns.join(', ') ?? '·' }}</span>
            </div>
          </div>
        </section>

        <section v-show="activeStep === 1" class="card">
          <div class="card-header">
            <span class="card-header-title">02 조건</span>
            <span class="card-header-meta">{{ subStepIndex + 1 }} / 4 · predicates · 최소 1개</span>
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
              <tr v-for="(p, idx) in draft.predicates" :key="idx">
                <td>
                  <select class="input mono" v-model="p.column" style="padding: 6px 8px;">
                    <option value="">—</option>
                    <option v-for="col in availableColumns" :key="col" :value="col">{{ col }}</option>
                  </select>
                </td>
                <td>
                  <select class="input mono" v-model="p.operator" style="padding: 6px 8px;">
                    <option value="EQ">EQ</option>
                    <option value="NEQ">NEQ</option>
                    <option value="LT">LT</option>
                    <option value="LTE">LTE</option>
                    <option value="GT">GT</option>
                    <option value="GTE">GTE</option>
                    <option value="IS_NULL">IS_NULL</option>
                    <option value="IS_NOT_NULL">IS_NOT_NULL</option>
                  </select>
                </td>
                <td>
                  <input
                    class="input mono"
                    v-model="p.valueText"
                    :placeholder="isNullOperator(p.operator) ? '값 불필요' : '값'"
                    :disabled="isNullOperator(p.operator)"
                  />
                </td>
                <td>
                  <select class="input mono" v-model="p.valueType" style="padding: 6px 8px;">
                    <option value="STRING">STRING</option>
                    <option value="NUMBER">NUMBER</option>
                    <option value="BOOLEAN">BOOLEAN</option>
                    <option value="TIMESTAMP">TIMESTAMP</option>
                  </select>
                </td>
                <td>
                  <button class="btn small" @click="removePredicate(idx)" :disabled="draft.predicates.length <= 1">삭제</button>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="condition-actions">
            <button class="btn small" @click="addPredicate" :disabled="draft.predicates.length >= 8">+ 조건</button>
          </div>
        </section>

        <section v-show="activeStep === 2" class="card">
          <div class="card-header">
            <span class="card-header-title">03 변경값</span>
            <span class="card-header-meta">mutations · {{ draft.mutations.length }}개</span>
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
              <tr v-for="(m, idx) in draft.mutations" :key="idx">
                <td>
                  <select class="input mono" v-model="m.column" style="padding: 6px 8px;">
                    <option value="">—</option>
                    <option v-for="col in availableColumns" :key="col" :value="col">{{ col }}</option>
                  </select>
                </td>
                <td>
                  <input class="input mono" v-model="m.valueText" placeholder="값" />
                </td>
                <td>
                  <select class="input mono" v-model="m.valueType" style="padding: 6px 8px;">
                    <option value="STRING">STRING</option>
                    <option value="NUMBER">NUMBER</option>
                    <option value="BOOLEAN">BOOLEAN</option>
                    <option value="TIMESTAMP">TIMESTAMP</option>
                  </select>
                </td>
                <td>
                  <button class="btn small" @click="removeMutation(idx)" :disabled="draft.mutations.length <= 1">삭제</button>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="condition-actions">
            <button class="btn small" @click="addMutation" :disabled="draft.mutations.length >= 8">+ 변경값</button>
          </div>
        </section>

        <section v-show="activeStep === 3" class="card">
          <div class="card-header">
            <span class="card-header-title">04 마무리</span>
          </div>

          <div class="field" style="margin-bottom: 14px;">
            <span class="field-label">예상 영향 건수</span>
            <input class="input mono" v-model.number="draft.expectedRowCount" placeholder="예: 77" />
          </div>
          <div class="field" style="margin-bottom: 14px;">
            <span class="field-label">가정</span>
            <textarea class="textarea" rows="3" placeholder="예: 동시성 영향이 적은 배치 시간에만 실행" v-model="draft.assumptionsText"></textarea>
          </div>
          <div class="field">
            <span class="field-label">미해결 질문</span>
            <textarea class="textarea" rows="2" placeholder="해결 전에는 확정이 불가능합니다" v-model="draft.unresolvedQuestionsText"></textarea>
          </div>
        </section>
      </div>

      <div class="confirm-footer">
        <button class="btn outline" @click="prev" :disabled="activeStep === 0">← 이전</button>
        <span v-if="activeStep === 0" class="footer-chip mono">변경 필드 {{ mutationFieldCount }}개</span>
        <span v-else-if="activeStep === 1" class="footer-chip mono">변경 필드 {{ mutationFieldCount }}개</span>
        <span v-else-if="activeStep === 2" class="footer-chip mono">변경 필드 {{ mutationFieldCount }}개</span>
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
          :disabled="!editable || !!draft.unresolvedQuestionsText.trim()"
        >
          {{ confirmLabel }}
        </button>
      </div>

      <div v-if="errorMessage" class="confirm-errors">
        <div class="error-item">{{ errorMessage }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getSpec, confirmSpec } from '@/api/client'
import { useAppStore } from '@/stores/app'
import type { ValueType } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const specId = computed(() => route.params.specId as string)

const steps = [
  { key: 'target', label: '대상' },
  { key: 'predicates', label: '조건' },
  { key: 'mutations', label: '변경값' },
  { key: 'finalize', label: '마무리' },
]

const loading = ref(false)
const spec = ref<Awaited<ReturnType<typeof getSpec>> | null>(null)
const errorMessage = ref('')

const activeStep = ref(0)
const editingTarget = ref(false)

const storeSpec = computed(() => store.spec)

interface Predicate {
  column: string
  operator: string
  value: unknown
  valueType: ValueType
  valueText: string
}

interface Mutation {
  column: string
  value: unknown
  valueType: ValueType
  valueText: string
}

const draft = ref<{
  environment: string
  database: string
  schema: string
  targetTable: string
  operation: string
  identityKeyColumns: string[]
  identityKeyColumnsText: string
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
  identityKeyColumnsText: 'id',
  predicates: [
    { column: 'tenant_id', operator: 'EQ', value: 42, valueType: 'NUMBER', valueText: '42' },
    { column: 'status', operator: 'EQ', value: 'pending', valueType: 'STRING', valueText: 'pending' },
    { column: 'created_at', operator: 'LT', value: '2026-09-01T00:00:00+09:00', valueType: 'TIMESTAMP', valueText: '2026-09-01T00:00:00+09:00' },
  ],
  mutations: [
    { column: 'status', value: 'cancelled', valueType: 'STRING', valueText: 'cancelled' },
  ],
  expectedRowCount: 77,
  assumptionsText: '',
  unresolvedQuestionsText: '',
})

const specStatus = computed(() => {
  if (spec.value) return spec.value.status
  if (storeSpec.value) return storeSpec.value.status
  return 'DRAFT'
})
const specVersion = computed(() => {
  if (spec.value) return spec.value.version
  if (storeSpec.value) return storeSpec.value.version
  return 1
})
const specContentHash = computed(() => {
  if (spec.value) return spec.value.contentHash
  if (storeSpec.value) return storeSpec.value.contentHash
  return ''
})
const editable = computed(() => specStatus.value === 'DRAFT')
const subStepIndex = computed(() => activeStep.value)
const mutationFieldCount = computed(() => draft.value.mutations.length)
const availableColumns = computed(() => {
  const candidate = spec.value ?? storeSpec.value
  if (!candidate) {
    const s = store.activeSchema
    if (s && s.tables.length) {
      return s.tables.flatMap((t) => t.columns.map((c) => c.name))
    }
    return []
  }
  const schemaInput = store.schemaList.find((s) => s.id === store.activeSchemaId)
  if (schemaInput && schemaInput.tables.length) {
    const target = schemaInput.tables.find((t) => t.name.toLowerCase() === candidate.targetTable.toLowerCase())
    if (target) return target.columns.map((c) => c.name)
  }
  return []
})

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

function subStepClass(idx: number) {
  if (idx < activeStep.value) return 'sub-step-done'
  if (idx === activeStep.value) return 'sub-step-active'
  return 'sub-step-pending'
}

function isNullOperator(op: string): boolean {
  return op === 'IS_NULL' || op === 'IS_NOT_NULL'
}

watch(
  () => activeStep.value,
  () => {
    syncDraftFromSpec()
  },
  { immediate: true },
)

onMounted(async () => {
  await refreshSpec()
  store.loadFlowState(specId.value)
})

watch(
  () => specId.value,
  async () => {
    await refreshSpec()
    store.loadFlowState(specId.value)
  },
)

function syncDraftFromSpec() {
  const s = spec.value ?? storeSpec.value
  if (!s) return
  const existingPredicates = draft.value.predicates
  const existingMutations = draft.value.mutations
  draft.value = {
    environment: s.environment ?? draft.value.environment,
    database: s.database ?? draft.value.database,
    schema: s.schema ?? draft.value.schema,
    targetTable: s.targetTable ?? draft.value.targetTable,
    operation: s.operation ?? draft.value.operation,
    identityKeyColumns: s.identityKeyColumns ?? draft.value.identityKeyColumns,
    identityKeyColumnsText: (s.identityKeyColumns ?? draft.value.identityKeyColumns).join(', '),
    predicates: s.predicates.map((p, idx) => {
      const existing = existingPredicates[idx]
      return {
        column: p.column,
        operator: p.operator,
        value: p.value,
        valueType: p.valueType as ValueType,
        valueText: existing?.valueText ?? formatValue(p.value),
      }
    }),
    mutations: s.mutations.map((m, idx) => {
      const existing = existingMutations[idx]
      return {
        column: m.column,
        value: m.value,
        valueType: m.valueType as ValueType,
        valueText: existing?.valueText ?? formatValue(m.value),
      }
    }),
    expectedRowCount: s.expectedRowCount ?? draft.value.expectedRowCount,
    assumptionsText: s.assumptions.join('\n') ?? draft.value.assumptionsText,
    unresolvedQuestionsText: s.unresolvedQuestions.join('\n') ?? draft.value.unresolvedQuestionsText,
  }
}

async function refreshSpec() {
  if (!specId.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await getSpec(specId.value)
    spec.value = data
    store.setSpecData(data)
  } catch (err) {
    errorMessage.value = '명세를 불러오지 못했습니다.'
    console.error(err)
  } finally {
    loading.value = false
  }
}

function startEditTarget() {
  editingTarget.value = true
}

function syncIdentityKeyColumns() {
  if (!draft.value.identityKeyColumnsText.trim()) {
    draft.value.identityKeyColumns = []
    return
  }
  draft.value.identityKeyColumns = draft.value.identityKeyColumnsText
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

function next() {
  if (activeStep.value < steps.length - 1) {
    if (activeStep.value === 0) syncIdentityKeyColumns()
    activeStep.value++
  }
}

function prev() {
  if (activeStep.value > 0) {
    activeStep.value--
  }
}

function addPredicate() {
  draft.value.predicates.push({ column: '', operator: 'EQ', value: null, valueType: 'STRING', valueText: '' })
}

function removePredicate(idx: number) {
  if (draft.value.predicates.length <= 1) return
  draft.value.predicates.splice(idx, 1)
}

function addMutation() {
  if (specStatus.value === 'CONFIRMED' && draft.value.mutations.length >= 1) return
  draft.value.mutations.push({ column: '', value: null, valueType: 'STRING', valueText: '' })
}

function removeMutation(idx: number) {
  if (draft.value.mutations.length <= 1 && specStatus.value === 'CONFIRMED') return
  draft.value.mutations.splice(idx, 1)
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  return String(value)
}

async function confirm() {
  if (!editable.value) return
  if (draft.value.unresolvedQuestionsText.trim()) return
  errorMessage.value = ''
  try {
    const payload = {
      environment: draft.value.environment,
      database: draft.value.database,
      schema: draft.value.schema,
      targetTable: draft.value.targetTable,
      operation: draft.value.operation as 'UPDATE' | 'DELETE',
      identityKeyColumns: draft.value.identityKeyColumns,
      predicates: draft.value.predicates
        .filter((p) => p.column && p.operator)
        .map((p) => ({
          column: p.column,
          operator: p.operator as 'EQ' | 'NEQ' | 'LT' | 'LTE' | 'GT' | 'GTE' | 'IS_NULL' | 'IS_NOT_NULL',
          value: p.value,
          valueType: p.valueType as 'STRING' | 'NUMBER' | 'BOOLEAN' | 'TIMESTAMP',
        })),
      mutations: draft.value.mutations
        .filter((m) => m.column)
        .map((m) => ({
          column: m.column,
          value: m.value,
          valueType: m.valueType as 'STRING' | 'NUMBER' | 'BOOLEAN' | 'TIMESTAMP',
        })),
      expectedRowCount: draft.value.expectedRowCount,
      assumptions: draft.value.assumptionsText
        ? draft.value.assumptionsText.split('\n').map((s) => s.trim()).filter(Boolean)
        : [],
      unresolvedQuestions: draft.value.unresolvedQuestionsText
        ? draft.value.unresolvedQuestionsText.split('\n').map((s) => s.trim()).filter(Boolean)
        : [],
    }
    const updated = await confirmSpec(specId.value, payload)
    spec.value = updated
    store.setSpecData(updated)
    store.loadFlowState(specId.value)
    router.push(`/spec/${specId.value}/sql-pack`)
  } catch (err: unknown) {
    const e = err as { status?: number; message?: string; code?: string }
    if (e.status === 409 && (e.code === 'SPEC_NOT_DRAFT' || e.code === 'UNRESOLVED_QUESTIONS')) {
      errorMessage.value = e.message ?? '확정할 수 없습니다.'
      return
    }
    errorMessage.value = e.message ?? '확정에 실패했습니다.'
    console.error(err)
  }
}
</script>

<style scoped>
.confirm-page {
  max-width: 1180px;
}

.confirm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  flex-wrap: wrap;
  gap: 10px;
}

.confirm-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confirm-bread {
  font-size: 12px;
  color: var(--text-muted);
}

.confirm-bread-sep {
  color: var(--text-faint);
}

.confirm-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.confirm-meta-item {
  font-size: 11px;
  color: var(--text-dim);
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

.sub-steps {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.sub-step {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border-soft);
  background: var(--panel);
  color: var(--text-muted);
  font-size: 13px;
  cursor: default;
}

.sub-step-done {
  background: var(--accent-bg);
  border-color: var(--accent);
  color: var(--accent);
}

.sub-step-active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  font-weight: 600;
}

.target-summary {
  margin-bottom: 16px;
  padding: 14px 18px;
}

.target-summary-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.target-summary-label {
  font-weight: 600;
}

.target-summary-value {
  font-size: 13px;
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

.field-value {
  font-size: 13px;
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
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border-soft);
  flex-wrap: wrap;
  gap: 10px;
}

.footer-chip {
  font-size: 11px;
  color: var(--text-dim);
}

.confirm-errors {
  margin-top: 12px;
}

.error-item {
  color: var(--danger-text);
  font-size: 12.5px;
}
</style>
