<template>
  <div class="review-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← SQL 팩</button>
        <span class="head-title">03 검토</span>
        <span class="mono">revision {{ review?.sqlPackRevision ?? '·' }} · v{{ review?.specVersion ?? '·' }}</span>
      </div>
      <div class="head-right" v-if="review">
        <span class="badge" :class="verdictBadgeClass">{{ review.verdict }}</span>
        <span class="badge" :class="riskBadgeClass">RISK {{ review.riskLevel }}</span>
        <span class="mono">{{ checkedCount }}/{{ totalCount }}</span>
      </div>
    </div>

    <div v-if="!review" class="empty-state-card card">
      <div class="empty-state">검토 결과가 없습니다. 먼저 SQL 팩을 검토하세요.</div>
      <button class="btn primary" @click="$router.back()">SQL 팩으로</button>
    </div>

    <div v-else>
      <div class="summary-row">
        <div class="summary-card" :class="failCardClass">
          <span class="count mono">{{ failCount }}</span>
          <span class="label">FAIL</span>
        </div>
        <div class="summary-card" :class="reviewCardClass">
          <span class="count mono">{{ reviewCount }}</span>
          <span class="label">REVIEW</span>
        </div>
        <div class="summary-card" :class="passCardClass">
          <span class="count mono">{{ passCount }}</span>
          <span class="label">PASS</span>
        </div>
        <div class="summary-note">
          <span class="mono">{{ review.disclaimer }}</span>
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
                  <span class="cell-status" :class="matrixCellClass(row.cells[col])">
                    {{ cellIcon(matrixCellClass(row.cells[col])) }}
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
              <span class="rvalue badge" :class="verdictBadgeClass">{{ review.verdict }}</span>
            </div>
            <div class="result-item">
              <span class="rlabel">위험도</span>
              <span class="rvalue badge" :class="riskBadgeClass">{{ review.riskLevel }}</span>
            </div>
            <div class="result-item">
              <span class="rlabel">판독 시점</span>
              <span class="rvalue mono">{{ formatDate(review.reviewedAt) }}</span>
            </div>
          </div>

          <div class="fail-list">
            <div v-for="check in failChecks" :key="check.ruleId" class="fail-card">
              <div class="fail-head">
                <span class="badge danger">{{ check.status }} · {{ check.category }}</span>
                <span class="mono">{{ check.ruleId }}</span>
              </div>
              <div class="fail-msg">{{ check.message }}</div>
              <div class="fail-detail">
                <div><span class="detail-label">기대</span><span class="detail-value mono">{{ formatValue(check.expected) }}</span></div>
                <div><span class="detail-label">실제</span><span class="detail-value mono">{{ formatValue(check.actual) }}</span></div>
                <div class="detail-source mono">{{ check.sqlArtifact ?? '—' }} · {{ check.sqlLocation ?? '—' }}</div>
              </div>
              <div class="fail-fix">
                <span class="fix-label">제안:</span>
                <span class="fix-value">{{ check.suggestedFix ?? '—' }}</span>
              </div>
            </div>
          </div>

          <div v-if="reviewChecks.length" class="checks-list">
            <div v-for="check in reviewChecks" :key="check.ruleId" class="check-row-card">
              <span class="check-badge" :class="check.status === 'FAIL' ? 'check-badge-danger' : check.status === 'REVIEW' ? 'check-badge-warning' : 'check-badge-ok'">
                {{ check.status }}
              </span>
              <span class="check-rule mono">{{ check.ruleId }}</span>
              <span class="check-msg">{{ check.message }}</span>
            </div>
          </div>
        </section>

        <section class="card diff-card">
          <div class="section-title">기준 SQL과의 차이</div>
          <div class="diff-summary">
            <span class="mono">{{ diffCountLabel }}</span>
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
            <pre class="diff-pre mono">{{ diffSql }}</pre>
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
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAppStore } from '@/stores/app'

const store = useAppStore()

const review = computed(() => store.review)

const verdictBadgeClass = computed(() => {
  if (!review.value) return ''
  if (review.value.verdict === 'BLOCK') return 'badge-danger'
  if (review.value.verdict === 'REVIEW') return 'badge-warning'
  if (review.value.verdict === 'READY') return 'badge-ok'
  return ''
})

const riskBadgeClass = computed(() => {
  if (!review.value) return ''
  if (review.value.riskLevel === 'HIGH') return 'badge-danger'
  if (review.value.riskLevel === 'MEDIUM') return 'badge-warning'
  if (review.value.riskLevel === 'LOW') return 'badge-ok'
  return ''
})

const failChecks = computed(() => (review.value ? review.value.checks.filter((c) => c.status === 'FAIL') : []))
const reviewChecks = computed(() => (review.value ? review.value.checks.filter((c) => c.status === 'REVIEW') : []))
const passCount = computed(() => (review.value ? review.value.checks.filter((c) => c.status === 'PASS').length : 0))
const failCount = computed(() => failChecks.value.length)
const reviewCount = computed(() => reviewChecks.value.length)
const totalCount = computed(() => (review.value ? review.value.checks.length : 0))
const checkedCount = computed(() => passCount.value + failCount.value + reviewCount.value)

const failCardClass = computed(() => (failCount.value > 0 ? 'summary-card-fail' : 'summary-card-empty'))
const reviewCardClass = computed(() => (reviewCount.value > 0 ? 'summary-card-review' : 'summary-card-empty'))
const passCardClass = computed(() => (passCount.value > 0 ? 'summary-card-pass' : 'summary-card-empty'))

const matrixCols = ['대상', '키', '조건', '변경값', '검증', '복구', '버전'] as const
const matrixRows: Array<{ label: string; cells: Record<string, string> }> = [
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
const diffTab = ref<(typeof diffTabs)[number]>('실행')

const diffSql = `UPDATE "public"."orders"\nSET "status" = 'cancelled'\nWHERE "created_at" < '2026-09-01'\n  AND __id__ IS NOT NULL;`

const rationale = computed(() => {
  if (!review.value) return []
  return review.value.checks.slice(0, 5).map((c) => ({
    rule: c.ruleId,
    status: c.status,
    badgeClass: c.status === 'FAIL' ? 'badge-danger' : c.status === 'REVIEW' ? 'badge-warning' : 'badge-ok',
    msg: c.status === 'FAIL' ? `확정 조건 누락: ${c.message}` : c.status === 'REVIEW' ? `검토 필요: ${c.message}` : `확인: ${c.message}`,
  }))
})

const diffCountLabel = computed(() => {
  if (!review.value) return '—'
  const total = review.value.checks.length
  const fail = failCount.value
  if (fail > 0) return `${fail}건 FAIL`
  const localReviewCount = reviewCount.value
  if (localReviewCount > 0) return `${localReviewCount}건 REVIEW`
  return `${total}건 PASS`
})

function matrixCellClass(status: string): string {
  if (status === 'fail') return 'cell-fail'
  if (status === 'review') return 'cell-review'
  if (status === 'info') return 'cell-info'
  return 'cell-pass'
}

function cellIcon(status: string): string {
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

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
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

.empty-state-card {
  padding: 32px;
}

.empty-state {
  color: var(--text-dim);
  font-size: 13px;
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

.summary-card-fail {
  background: #fbe7ea;
  color: var(--danger);
}

.summary-card-review {
  background: #fbe6c8;
  color: var(--warning);
}

.summary-card-pass {
  background: #d9f0e0;
  color: var(--ok);
}

.summary-card-empty {
  background: var(--panel);
  color: var(--text-dim);
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

.cell-pass {
  color: var(--ok);
}

.cell-review {
  color: var(--warning);
}

.cell-fail {
  color: var(--danger);
}

.cell-info {
  color: var(--text-dim);
}

.result-card {
  padding: 16px;
  background: var(--panel);
}

.result-block {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
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

.check-badge-danger {
  background: #f6dada;
  color: var(--danger);
}

.check-badge-warning {
  background: #f3e6cc;
  color: var(--warning);
}

.check-badge-ok {
  background: #ddefE3;
  color: var(--ok);
}

.check-rule {
  color: var(--text-muted);
  min-width: 60px;
}

.diff-card {
  padding: 16px;
  background: var(--panel);
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

.diff-pre {
  background: var(--bg);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 12px;
  min-height: 120px;
  max-height: 220px;
  overflow: auto;
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

.card {
  background: var(--panel);
}
</style>
