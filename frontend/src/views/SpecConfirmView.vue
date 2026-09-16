<template>
  <div class="confirm-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 홈</button>
        <span class="head-title">01 명세 확정</span>
        <span class="mono">specId: <strong>{{ specId }}</strong></span>
        <span class="badge" :class="statusClass">{{ status }}</span>
        <span class="mono">version {{ version }}</span>
        <span class="mono">contentHash {{ contentHash.slice(0, 12) }}…</span>
      </div>
      <div class="head-right">
        <span class="mono">{{ stepLabel }}</span>
      </div>
    </div>

    <div class="steps">
      <button
        v-for="(s, idx) in steps"
        :key="s.key"
        class="step chip"
        :class="{ active: activeStep === idx, done: idx < activeStep }"
        @click="goStep(idx)"
      >
        <span class="step-num">{{ idx + 1 }}</span>
        {{ s.label }}
      </button>
    </div>

    <div class="confirm-grid">
      <section class="card">
        <div class="section-title">대상</div>
        <div class="field-grid">
          <div class="field">
            <label>환경</label>
            <input class="input mono" :value="draft.environment" disabled />
          </div>
          <div class="field">
            <label>데이터베이스</label>
            <input class="input mono" :value="draft.database" disabled />
          </div>
          <div class="field">
            <label>스키마</label>
            <input class="input mono" :value="draft.schema" disabled />
          </div>
          <div class="field">
            <label>테이블</label>
            <input class="input mono" :value="draft.target_table" disabled />
          </div>
          <div class="field">
            <label>작업</label>
            <input class="input mono" :value="draft.operation" disabled />
          </div>
          <div class="field">
            <label>키</label>
            <input class="input mono" :value="draft.identity_key_columns.join(', ')" disabled />
          </div>
        </div>
      </section>

      <section v-if="activeStep === 1" class="card">
        <div class="section-title">조건</div>
        <div class="condition-head">
          <span class="mono">대상 조건 {{ draft.predicates.length }} / {{ maxPredicates }}</span>
          <span class="badge">최소 1개</span>
        </div>

        <table class="table">
          <thead>
            <tr>
              <th>컬럼</th>
              <th>연산자</th>
              <th>값</th>
              <th>타입</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(p, idx) in draft.predicates" :key="idx">
              <td class="mono">{{ p.column }}</td>
              <td class="mono">{{ p.operator }}</td>
              <td class="mono">{{ formatValue(p.value) }}</td>
              <td class="mono">{{ p.value_type }}</td>
              <td>
                <button class="btn small">삭제</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="condition-actions">
          <button class="btn small">+ 조건</button>
        </div>
      </section>

      <section v-if="activeStep === 2" class="card">
        <div class="section-title">변경값</div>
        <div class="field" style="margin-bottom: 14px;">
          <label>변경할 컬럼과 값</label>
        </div>

        <table class="table">
          <thead>
            <tr>
              <th>컬럼</th>
              <th>값</th>
              <th>타입</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(m, idx) in draft.mutations" :key="idx">
              <td class="mono">{{ m.column }}</td>
              <td class="mono">{{ formatValue(m.value) }}</td>
              <td class="mono">{{ m.value_type }}</td>
              <td>
                <button class="btn small">삭제</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="condition-actions">
          <button class="btn small">+ 변경값</button>
        </div>
      </section>

      <section v-if="activeStep === 3" class="card">
        <div class="section-title">마무리</div>
        <div class="field" style="margin-bottom: 14px;">
          <label>예상 영향 건수</label>
          <input class="input mono" :value="draft.expected_row_count" @input="draft.expected_row_count = ($event.target as HTMLInputElement).valueAsNumber" placeholder="예: 77" />
        </div>
        <div class="field" style="margin-bottom: 14px;">
          <label>가정</label>
          <textarea class="textarea" rows="3" placeholder="예: 동시성 영향이 적은 배치 시간에만 실행"></textarea>
        </div>
        <div class="field">
          <label> unresolved 질문</label>
          <textarea class="textarea" rows="2" placeholder="해결 전에는 확정이 불가능합니다"></textarea>
        </div>
      </section>
    </div>

    <div class="confirm-footer">
      <button class="btn" @click="prev" :disabled="activeStep === 0">← 이전</button>
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
        :disabled="draft.unresolved_questions.length > 0"
      >
        확정
      </button>
    </div>

    <div class="summary-bar">
      <span class="summary-label mono">변경 필드 {{ draft.mutations.length }}개</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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

const activeStep = ref(1)
const maxPredicates = 4

interface Predicate {
  column: string
  operator: string
  value: unknown
  value_type: ValueType
}

interface Mutation {
  column: string
  value: unknown
  value_type: ValueType
}

const draft = ref<{
  environment: string
  database: string
  schema: string
  target_table: string
  operation: string
  identity_key_columns: string[]
  predicates: Predicate[]
  mutations: Mutation[]
  expected_row_count: number | null
  assumptions: string[]
  unresolved_questions: string[]
}>({
  environment: 'production',
  database: 'app',
  schema: 'public',
  target_table: 'orders',
  operation: 'UPDATE',
  identity_key_columns: ['id'],
  predicates: [
    { column: 'tenant_id', operator: 'EQ', value: 42, value_type: 'NUMBER' },
    { column: 'status', operator: 'EQ', value: 'pending', value_type: 'STRING' },
    { column: 'created_at', operator: 'LT', value: '2026-09-01T00:00:00+09:00', value_type: 'TIMESTAMP' },
  ],
  mutations: [
    { column: 'status', value: 'cancelled', value_type: 'STRING' },
  ],
  expected_row_count: 77,
  assumptions: [],
  unresolved_questions: [],
})

const status: 'DRAFT' | 'CONFIRMED' | 'SUPERSEDED' = 'DRAFT'
const version = 1
const contentHash = 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0'

const statusClass = computed(() => {
  const s = status as string
  if (s === 'CONFIRMED') return { 'ok': true }
  if (s === 'DRAFT') return { 'warning': true }
  return { 'danger': true }
})

const stepLabel = computed(() => steps[activeStep.value]?.label ?? '')
const stepButtonLabel = computed(() => {
  if (activeStep.value === 0) return '조건으로'
  if (activeStep.value === 1) return '변경값으로'
  if (activeStep.value === 2) return '마무리로'
  return '확정'
})

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

function confirm() {
  if (draft.value.unresolved_questions.length > 0) return
  router.push(`/spec/${specId.value}/sql-pack`)
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return 'NULL'
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

.step.active .step-num {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
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

.condition-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
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
