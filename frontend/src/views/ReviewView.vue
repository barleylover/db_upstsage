<template>
  <div class="review-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← SQL 팩</button>
        <span class="head-title">03 검토</span>
        <span class="mono">revision {{ reviewResult.sql_pack_revision }} · v{{ reviewResult.spec_version }}</span>
      </div>
      <div class="head-right">
        <span class="verdict badge" :class="verdictClass">{{ reviewResult.verdict }}</span>
        <span class="risk badge" :class="riskClass">RISK {{ reviewResult.risk_level }}</span>
        <span class="mono">{{ checkedCount }}/{{ totalCount }}</span>
      </div>
    </div>

    <div class="summary-row">
      <div class="summary-card fail">
        <span class="count mono">{{ failCount }}</span>
        <span class="label">FAIL</span>
      </div>
      <div class="summary-card review">
        <span class="count mono">{{ reviewCount }}</span>
        <span class="label">REVIEW</span>
      </div>
      <div class="summary-card pass">
        <span class="count mono">{{ passCount }}</span>
        <span class="label">PASS</span>
      </div>
      <div class="summary-note">
        <span class="mono">{{ reviewResult.disclaimer }}</span>
      </div>
    </div>

    <div class="review-grid">
      <section class="card matrix-card">
        <div class="section-title">정합성 매트릭스</div>
        <table class="table matrix">
          <thead>
            <tr>
              <th></th>
              <th v-for="col in matrixCols" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in matrixRows" :key="row.label">
              <th>{{ row.label }}</th>
              <td v-for="col in matrixCols" :key="col" class="matrix-cell">
                <span class="cell-status" :class="matrixCellStatus(row, col)">
                  {{ cellIcon(matrixCellStatus(row, col)) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="card result-card">
        <div class="section-title">판정 요약</div>
        <div class="result-block">
          <div class="result-item">
            <span class="rlabel">판정</span>
            <span class="rvalue badge" :class="verdictClass">{{ reviewResult.verdict }}</span>
          </div>
          <div class="result-item">
            <span class="rlabel">위험도</span>
            <span class="rvalue badge" :class="riskClass">{{ reviewResult.risk_level }}</span>
          </div>
        </div>

        <div class="fail-list">
          <div v-for="check in failChecks" :key="check.rule_id" class="fail-card">
            <div class="fail-head">
              <span class="badge danger">{{ check.status }} · {{ check.category }}</span>
              <span class="mono">{{ check.rule_id }}</span>
            </div>
            <div class="fail-msg">{{ check.message }}</div>
            <div class="fail-detail">
              <div><span class="detail-label">기대</span><span class="detail-value mono">{{ formatValue(check.expected) }}</span></div>
              <div><span class="detail-label">실제</span><span class="detail-value mono">{{ formatValue(check.actual) }}</span></div>
              <div class="detail-source mono">{{ check.sql_artifact ?? '' }} · {{ check.sql_location ?? '' }}</div>
            </div>
            <div class="fail-fix">
              <span class="fix-label">제안:</span>
              <span class="fix-value">{{ check.suggested_fix ?? '—' }}</span>
            </div>
          </div>
        </div>

        <div v-if="reviewChecks.length" class="checks-list">
          <div v-for="check in reviewChecks" :key="check.rule_id" class="check-row-card">
            <span class="check-badge" :class="check.status === 'FAIL' ? 'danger' : check.status === 'REVIEW' ? 'warning' : 'ok'">
              {{ check.status }}
            </span>
            <span class="check-rule mono">{{ check.rule_id }}</span>
            <span class="check-msg">{{ check.message }}</span>
          </div>
        </div>
      </section>

      <section class="card diff-card">
        <div class="section-title">기준 SQL과의 차이</div>
        <div class="diff-summary">
          <span class="mono">2줄 다름</span>
        </div>
        <div class="diff-tabs">
          <button
            v-for="tab in diffTabs"
            :key="tab"
            class="diff-tab"
            :class="{ active: diffTab === tab }"
            @click="diffTab = tab"
          >
            {{ tab }}
          </button>
        </div>

        <div class="code-block diff-block">
          <pre>{{ diffSql }}</pre>
        </div>

        <div class="diff-rationale">
          <div class="rationale-title">판정 근거</div>
          <div class="rationale-list">
            <div v-for="item in rationale" :key="item.rule" class="rationale-item">
              <span class="badge" :class="item.badgeClass">{{ item.status }} {{ item.rule }}</span>
              <span class="rationale-msg">{{ item.msg }}</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, type Ref } from 'vue'

type CellStatus = 'pass' | 'fail' | 'review' | 'info'

const reviewResult = {
  spec_id: 'spec-001',
  spec_version: 1,
  content_hash: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0',
  sql_pack_revision: 2,
  verdict: 'BLOCK',
  risk_level: 'MEDIUM',
  is_stale: false,
  checks: [
    {
      rule_id: 'B001',
      category: 'target_scope',
      status: 'PASS',
      severity: 'INFO',
      message: 'executionSql contains a WHERE clause.',
      expected: null,
      actual: null,
      spec_field: null,
      sql_artifact: 'executionSql',
      sql_location: null,
      suggested_fix: null,
    },
    {
      rule_id: 'B003',
      category: 'predicate_consistency',
      status: 'FAIL',
      severity: 'CRITICAL',
      message: "The confirmed condition 'tenant_id = 42' is missing, so unintended rows may be changed.",
      expected: 'tenant_id = 42',
      actual: 'missing',
      spec_field: 'predicates[tenant_id]',
      sql_artifact: 'executionSql',
      sql_location: 'WHERE',
      suggested_fix: "Add 'tenant_id = 42' back to the executionSql WHERE clause.",
    },
    {
      rule_id: 'R002',
      category: 'rollback',
      status: 'REVIEW',
      severity: 'WARNING',
      message: 'Rollback is a template that still requires saved backup rows.',
      expected: 'COMPLETE',
      actual: 'TEMPLATE_REQUIRES_BACKUP_ROWS',
      spec_field: null,
      sql_artifact: 'rollbackSql',
      sql_location: null,
      suggested_fix: 'Save backupSql results and complete the rollback values before execution.',
    },
  ],
  disclaimer: '정적 검토 통과 여부이며, 실제 실행 승인 또는 무사 실행을 보장하지 않습니다.',
  reviewed_at: new Date().toISOString(),
}

const verdictClass = computed(() => ({
  'danger': reviewResult.verdict === 'BLOCK',
  'warning': reviewResult.verdict === 'REVIEW',
  'ok': reviewResult.verdict === 'READY',
}))

const riskClass = computed(() => ({
  'danger': reviewResult.risk_level === 'HIGH',
  'warning': reviewResult.risk_level === 'MEDIUM',
  'ok': reviewResult.risk_level === 'LOW',
}))

const failChecks = computed(() => reviewResult.checks.filter((c) => c.status === 'FAIL'))
const reviewChecks = computed(() => reviewResult.checks.filter((c) => c.status === 'REVIEW'))
const passCount = computed(() => reviewResult.checks.filter((c) => c.status === 'PASS').length)
const failCount = computed(() => failChecks.value.length)
const reviewCount = computed(() => reviewChecks.value.length)
const totalCount = computed(() => reviewResult.checks.length)
const checkedCount = computed(() => passCount.value + failCount.value + reviewCount.value)

const matrixCols = ['대상', '키', '조건', '변경값', '검증', '복구', '버전'] as const
const matrixRows: Array<{ label: string; cells: Record<string, CellStatus> }> = [
  {
    label: 'Change Spec',
    cells: { 대상: 'pass', 키: 'pass', 조건: 'pass', 변경값: 'pass', 검증: 'info', 복구: 'info', 버전: 'pass' },
  },
  {
    label: '확인',
    cells: { 대상: 'pass', 키: 'pass', 조건: 'pass', 변경값: 'info', 검증: 'pass', 복구: 'info', 버전: 'pass' },
  },
  {
    label: '백업',
    cells: { 대상: 'pass', 키: 'info', 조건: 'pass', 변경값: 'info', 검증: 'pass', 복구: 'pass', 버전: 'pass' },
  },
  {
    label: '실행',
    cells: { 대상: 'pass', 키: 'info', 조건: 'fail', 변경값: 'pass', 검증: 'pass', 복구: 'info', 버전: 'pass' },
  },
  {
    label: '검증',
    cells: { 대상: 'info', 키: 'info', 조건: 'info', 변경값: 'pass', 검증: 'pass', 복구: 'info', 버전: 'pass' },
  },
  {
    label: '롤백',
    cells: { 대상: 'info', 키: 'info', 조건: 'info', 변경값: 'info', 검증: 'info', 복구: 'review', 버전: 'pass' },
  },
  {
    label: '문서',
    cells: { 대상: 'info', 키: 'info', 조건: 'info', 변경값: 'info', 검증: 'info', 복구: 'info', 버전: 'pass' },
  },
]

const diffTabs = ['확인', '백업', '실행', '검증', '롤백'] as const
const diffTab: Ref<(typeof diffTabs)[number]> = ref('실행')

const diffSql = `UPDATE "public"."orders"\nSET "status" = 'cancelled'\nWHERE "created_at" < '2026-09-01'\n  AND __id__ IS NOT NULL;`

const rationale = [
  { rule: 'B003', status: 'FAIL', badgeClass: 'danger', msg: '확정 조건 누락: tenant_id = 42가 실행 SQL에서 제거됨' },
  { rule: 'R002', status: 'REVIEW', badgeClass: 'warning', msg: '롤백 템플릿이 백업 행을 요구함' },
  { rule: 'B001', status: 'PASS', badgeClass: 'ok', msg: 'WHERE 절이 존재함' },
]

function matrixCellStatus(row: { cells: Record<string, CellStatus> }, col: string): CellStatus {
  return row.cells[col] ?? 'pass'
}

function cellIcon(status: CellStatus): string {
  if (status === 'fail') return '✕'
  if (status === 'review') return '!'
  if (status === 'info') return '·'
  return '✓'
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  return JSON.stringify(value)
}
</script>

<style scoped>
.review-page {
  max-width: 1200px;
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

.verdict {
  font-weight: 600;
}

.risk {
  font-weight: 600;
}

.summary-row {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
}

.summary-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  border-radius: 10px;
  min-width: 120px;
}

.summary-card.fail {
  background: #fbe7ea;
  color: var(--danger);
}

.summary-card.review {
  background: #fbe6c8;
  color: var(--warning);
}

.summary-card.pass {
  background: #d9f0e0;
  color: var(--ok);
}

.summary-card .count {
  font-size: 32px;
  font-weight: 600;
}

.summary-card .label {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.summary-note {
  flex: 1;
  font-size: 12px;
  color: var(--text-dim);
}

.review-grid {
  display: grid;
  grid-template-columns: 1fr 1.4fr 1.4fr;
  gap: 16px;
  align-items: start;
}

.matrix {
  font-size: 12px;
}

.matrix-cell {
  text-align: center;
}

.cell-status {
  font-size: 14px;
}

.result-card {
  padding: 16px;
}

.result-block {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-item .rlabel {
  font-size: 12px;
  color: var(--text-muted);
}

.result-item .rvalue {
  font-size: 14px;
}

.fail-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.fail-card {
  background: #fbe7ea;
  border: 1px solid #f0c8ce;
  border-radius: 8px;
  padding: 10px 12px;
}

.fail-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.fail-msg {
  font-size: 13px;
  margin-bottom: 8px;
}

.fail-detail {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 8px;
}

.detail-label {
  color: var(--text-faint);
}

.detail-value {
  color: var(--text);
}

.detail-source {
  color: var(--text-dim);
}

.fail-fix {
  font-size: 12px;
  color: var(--text);
  border-top: 1px solid #f0c0c5;
  padding-top: 6px;
}

.checks-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.check-row-card {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 4px 0;
  border-bottom: 1px solid var(--border-soft);
}

.check-row-card:last-child {
  border-bottom: none;
}

.check-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 999px;
}

.check-rule {
  color: var(--text-muted);
  min-width: 60px;
}

.diff-card {
  padding: 16px;
}

.diff-summary {
  margin-bottom: 10px;
  color: var(--text-dim);
}

.diff-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border-soft);
  margin-bottom: 10px;
}

.diff-tab {
  padding: 6px 10px;
  border: none;
  border-bottom: 2px solid transparent;
  background: none;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
}

.diff-tab.active {
  color: var(--accent-2);
  border-bottom-color: var(--accent);
}

.diff-block {
  min-height: 140px;
}

.diff-rationale {
  margin-top: 12px;
}

.rationale-title {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.rationale-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rationale-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.rationale-msg {
  color: var(--text-muted);
}
</style>
