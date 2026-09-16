<template>
  <div class="review-page">
    <div class="review-header">
      <div class="review-header-left">
        <span class="review-bread mono">홈</span>
        <span class="review-bread-sep">/</span>
        <span class="review-bread mono">01 명세 확정</span>
        <span class="review-bread-sep">/</span>
        <span class="review-bread mono">02 SQL 팩</span>
        <span class="review-bread-sep">/</span>
        <span class="review-bread mono">03 검토</span>
      </div>
      <div class="review-meta" v-if="review">
        <span class="review-meta-item mono">revision {{ review.sqlPackRevision }} · v{{ review.specVersion }}</span>
      </div>
    </div>

    <div v-if="!review" class="empty-state-card card">
      <div class="empty-state">검토 결과가 없습니다. 먼저 SQL 팩을 검토하세요.</div>
      <button class="btn primary" @click="router.push('/spec/' + (store.currentSpecId ?? '') + '/sql-pack')">SQL 팩으로</button>
    </div>

    <div v-else>
      <div class="review-top">
        <div class="review-verdict card">
          <div class="review-verdict-head">
            <span class="review-verdict-label">판정</span>
            <span class="review-verdict-value" :class="verdictClass">{{ review.verdict }}</span>
          </div>
          <div class="review-verdict-chips">
            <span class="chip" :class="riskClass">RISK {{ review.riskLevel }}</span>
            <span class="chip" :class="failClass">FAIL {{ failCount }}</span>
            <span class="chip" :class="reviewClass">REVIEW {{ reviewCount }}</span>
            <span class="chip" :class="passClass">PASS {{ passCount }}</span>
          </div>
        </div>
        <div class="review-disclaimer">
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
                <td v-for="col in matrixCols" :key="col" class="matrix-cell" @click="selectMatrixCell(row.label, col)">
                  <span class="cell-status" :class="matrixCellClass(row.cells[col])">
                    {{ cellIcon(row.cells[col]) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="selectedMatrix" class="matrix-detail">
            <div class="matrix-detail-head">
              <span class="matrix-detail-label">{{ selectedMatrix.row }} · {{ selectedMatrix.col }}</span>
              <span class="cell-status" :class="matrixCellClass(selectedMatrix.status)">{{ cellIcon(selectedMatrix.status) }}</span>
            </div>
            <div class="matrix-detail-body">
              <div v-if="selectedMatrix.detail">{{ selectedMatrix.detail }}</div>
              <div v-else class="matrix-detail-empty">해당 셀에는 별도 검사 결과가 없습니다.</div>
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
        </section>

        <section class="card rationale-card">
          <div class="section-title">판정 근거</div>
          <div class="rationale-list">
            <div v-for="item in rationale" :key="item.ruleId" class="rationale-item">
              <span class="rationale-status-bar" :class="rationaleStatusClass(item.status)"></span>
              <span class="chip" :class="rationaleStatusClass(item.status)">{{ item.status }}</span>
              <span class="mono">{{ item.ruleId }}</span>
              <span class="rationale-title-text">{{ item.title }}</span>
              <button v-if="item.hasDetail" class="rationale-expand" @click="item.expanded = !item.expanded">
                {{ item.expanded ? '접기' : '펼치기' }}
              </button>
              <div v-if="item.expanded" class="rationale-detail">
                <div><span class="detail-label">메시지</span><span class="detail-value">{{ item.message }}</span></div>
                <div v-if="item.expected !== null && item.expected !== undefined"><span class="detail-label">기대</span><span class="detail-value mono">{{ formatValue(item.expected) }}</span></div>
                <div v-if="item.actual !== null && item.actual !== undefined"><span class="detail-label">실제</span><span class="detail-value mono">{{ formatValue(item.actual) }}</span></div>
                <div v-if="item.suggestedFix"><span class="detail-label">제안</span><span class="detail-value">{{ item.suggestedFix }}</span></div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div v-if="review.isStale" class="stale-banner">
        <span class="mono">SQL 팩이 수정된 후 다시 검토했습니다. 이전 검토 결과는 무효입니다.</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const store = useAppStore()

const review = computed(() => store.review)

const verdictClass = computed(() => {
  if (!review.value) return ''
  if (review.value.verdict === 'BLOCK') return 'verdict-block'
  if (review.value.verdict === 'REVIEW') return 'verdict-review'
  if (review.value.verdict === 'READY') return 'verdict-ready'
  return ''
})

const riskClass = computed(() => {
  if (!review.value) return ''
  if (review.value.riskLevel === 'HIGH') return 'chip-danger'
  if (review.value.riskLevel === 'MEDIUM') return 'chip-warning'
  if (review.value.riskLevel === 'LOW') return 'chip-ok'
  return ''
})

const failClass = computed(() => (failCount.value > 0 ? 'chip-danger' : ''))
const reviewClass = computed(() => (reviewCount.value > 0 ? 'chip-warning' : ''))
const passClass = computed(() => (passCount.value > 0 ? 'chip-ok' : ''))

const failChecks = computed(() => (review.value ? review.value.checks.filter((c) => c.status === 'FAIL') : []))
const reviewChecks = computed(() => (review.value ? review.value.checks.filter((c) => c.status === 'REVIEW') : []))
const passCount = computed(() => (review.value ? review.value.checks.filter((c) => c.status === 'PASS').length : 0))
const failCount = computed(() => failChecks.value.length)
const reviewCount = computed(() => reviewChecks.value.length)

const matrixCols = ['대상', '키', '조건', '변경값', '검증', '복구', '버전'] as const

interface MatrixCell { status: string; detail: string }

interface MatrixRow { label: string; cells: Record<string, MatrixCell> }

const matrixRows = computed((): MatrixRow[] => {
  if (!review.value) return []
  const bySql = new Map<string, typeof review.value.checks>()
  const byField = new Map<string, typeof review.value.checks>()
  for (const c of review.value.checks) {
    if (c.sqlArtifact) {
      const key = c.sqlArtifact
      if (!bySql.has(key)) bySql.set(key, [])
      bySql.get(key)!.push(c)
    }
    if (c.specField) {
      const key = c.specField
      if (!byField.has(key)) byField.set(key, [])
      byField.get(key)!.push(c)
    }
  }

  const artifactOrder = ['precheckSql', 'backupSql', 'executionSql', 'verificationSql', 'rollbackSql']
  const artifactLabel = {
    precheckSql: '확인',
    backupSql: '백업',
    executionSql: '실행',
    verificationSql: '검증',
    rollbackSql: '롤백',
  }

  const rows: MatrixRow[] = []

  let worst = '·'
  for (const key of artifactOrder) {
    const checks = bySql.get(key) ?? []
    worst = worstStatus(checks)
    rows.push({
      label: artifactLabel[key] ?? key,
      cells: {
        대상: { status: '·', detail: '' },
        키: { status: '·', detail: '' },
        조건: { status: '·', detail: '' },
        변경값: { status: '·', detail: '' },
        검증: { status: '·', detail: '' },
        복구: { status: '·', detail: '' },
        버전: { status: '·', detail: '' },
      },
    })
  }

  const specFieldRows = [
    { label: 'Change Spec', field: 'predicates' },
    { label: 'Change Spec', field: 'mutations' },
    { label: 'Change Spec', field: 'identityKeyColumns' },
    { label: 'Change Spec', field: 'operation' },
    { label: 'Change Spec', field: 'expectedRowCount' },
  ]

  const seen = new Set<string>()
  for (const field of specFieldRows) {
    const key = field.field
    const checks = byField.get(key) ?? []
    const worst = worstStatus(checks)
    const detail = worst !== '·' ? bestCheckMessage(checks) : ''
    const cellKey = field.label === 'Change Spec' && field.field === 'predicates' ? '조건'
      : field.label === 'Change Spec' && field.field === 'mutations' ? '변경값'
      : field.label === 'Change Spec' && field.field === 'identityKeyColumns' ? '키'
      : field.label === 'Change Spec' && field.field === 'operation' ? '대상'
      : field.label === 'Change Spec' && field.field === 'expectedRowCount' ? '검증'
      : '대상'
    if (!seen.has(`${field.label}:${cellKey}`)) {
      rows.push({
        label: 'Change Spec',
        cells: { 대상: '조건' === cellKey ? { status: worst, detail } : { status: '·', detail: '' },
                 키: '키' === cellKey ? { status: worst, detail } : { status: '·', detail: '' },
                 조건: '조건' === cellKey ? { status: worst, detail } : { status: '·', detail: '' },
                 변경값: '변경값' === cellKey ? { status: worst, detail } : { status: '·', detail: '' },
                 검증: '검증' === cellKey ? { status: worst, detail } : { status: '·', detail: '' },
                 복구: { status: '·', detail: '' },
                 버전: { status: '·', detail: '' } },
      })
      seen.add(`${field.label}:${cellKey}`)
    }
  }

  const documentRow = {
    label: '문서',
    cells: { 대상: { status: '·', detail: '' }, 키: { status: '·', detail: '' }, 조건: { status: '·', detail: '' }, 변경값: { status: '·', detail: '' }, 검증: { status: '·', detail: '' }, 복구: { status: '·', detail: '' }, 버전: { status: '·', detail: '' } },
  }
  rows.push(documentRow)

  return rows
})

function worstStatus(checks: { status: string }[]): string {
  if (!checks.length) return '·'
  if (checks.some((c) => c.status === 'FAIL')) return '✕'
  if (checks.some((c) => c.status === 'REVIEW')) return '△'
  if (checks.some((c) => c.status === 'PASS')) return '○'
  return '·'
}

function bestCheckMessage(checks: { status: string; message: string }[]): string {
  const target = checks.find((c) => c.status !== 'PASS')
  if (!target) return ''
  return target.message
}

function matrixCellClass(status: string): string {
  if (status === '✕') return 'cell-fail'
  if (status === '△') return 'cell-review'
  if (status === '○') return 'cell-pass'
  return 'cell-none'
}

function cellIcon(status: string): string {
  if (status === '✕') return '✕'
  if (status === '△') return '△'
  if (status === '○') return '○'
  return '·'
}

const selectedMatrix = ref<{ row: string; col: string; status: string; detail: string } | null>(null)

function selectMatrixCell(row: string, col: string) {
  const rowData = matrixRows.value.find((r) => r.label === row)
  if (!rowData) return
  const cell = rowData.cells[col]
  if (!cell) return
  selectedMatrix.value = { row, col, status: cell.status, detail: cell.detail }
}

const diffTabs = ['확인', '백업', '실행', '검증', '롤백'] as const
const diffTab = ref<(typeof diffTabs)[number]>('실행')

const diffSql = computed(() => {
  if (!store.sqlPack || !store.baselineSqlPack) return ''
  const current = diffArtifactSql(store.sqlPack, diffTab.value)
  const base = diffArtifactSql(store.baselineSqlPack, diffTab.value)
  if (current === base) return ''
  return unifiedDiff(base, current, diffTab.value)
})

function diffArtifactSql(pack: Awaited<ReturnType<typeof createSqlPack>> | undefined, tab: string): string {
  if (!pack) return ''
  if (tab === '확인') return pack.precheckSql
  if (tab === '백업') return pack.backupSql
  if (tab === '실행') return pack.executionSql
  if (tab === '검증') return pack.verificationSql
  return pack.rollbackSql
}

function unifiedDiff(base: string, current: string, label: string): string {
  const baseLines = base.split('\n')
  const currentLines = current.split('\n')
  const maxLines = Math.max(baseLines.length, currentLines.length)
  const lines: string[] = []
  for (let i = 0; i < maxLines; i++) {
    const b = baseLines[i] ?? ''
    const c = currentLines[i] ?? ''
    if (b !== c) {
      if (b) lines.push(`-` + b)
      if (c) lines.push(`+` + c)
    } else if (b) {
      lines.push(' ' + b)
    }
  }
  if (lines.length === 0) return ''
  return `@@ 기준 ${label} vs 현재 ${label} @@\n` + lines.join('\n')
}

const diffCountLabel = computed(() => {
  if (!diffSql.value) return '기준 SQL과 동일'
  const lines = diffSql.value.split('\n').filter((l) => l.startsWith('-') || l.startsWith('+'))
  if (lines.length === 0) return '기준 SQL과 동일'
  return `${lines.length}줄 다름`
})

const rationale = computed(() => {
  if (!review.value) return []
  const titleMap: Record<string, string> = {
    B001: 'WHERE 존재',
    B002: '대상 테이블',
    B003: '확정 조건 누락',
    B004: '조건 추가/변형',
    B005: '변경값 불일치',
    B006: '스키마 밖 식별자',
    B007: '구문/범위',
    B008: '롤백 키',
    R001: '예상 건수',
    R002: '롤백 템플릿',
    R003: '실행 근거',
    R004: '의미 동등성',
    M001: '버전 불일치',
  }
  return review.value.checks
    .slice()
    .sort((a, b) => {
      const order = { FAIL: 0, REVIEW: 1, PASS: 2 }
      return order[a.status] - order[b.status]
    })
    .map((c) => ({
      ruleId: c.ruleId,
      status: c.status,
      title: titleMap[c.ruleId] ?? c.ruleId,
      message: c.message,
      expected: c.expected,
      actual: c.actual,
      suggestedFix: c.suggestedFix,
      hasDetail: true,
      expanded: false,
    }))
})

function rationaleStatusClass(status: string): string {
  if (status === 'FAIL') return 'chip-danger'
  if (status === 'REVIEW') return 'chip-warning'
  return 'chip-ok'
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map((v) => formatValue(v)).join(', ')
  if (typeof value === 'object') {
    return Object.entries(value)
      .map(([k, v]) => `${k}: ${formatValue(v)}`)
      .join(', ')
  }
  return String(value)
}
</script>

<style scoped>
.review-page {
  max-width: 1200px;
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  flex-wrap: wrap;
  gap: 10px;
}

.review-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.review-bread {
  font-size: 12px;
  color: var(--text-muted);
}

.review-bread-sep {
  color: var(--text-faint);
}

.review-meta {
  display: flex;
  gap: 12px;
}

.review-meta-item {
  font-size: 11px;
  color: var(--text-dim);
}

.empty-state-card {
  padding: 32px;
}

.empty-state {
  color: var(--text-dim);
  font-size: 13px;
}

.review-top {
  display: flex;
  align-items: stretch;
  gap: 12px;
  margin-bottom: 18px;
}

.review-verdict {
  flex: 1;
  padding: 18px;
}

.review-verdict-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.review-verdict-label {
  font-size: 12px;
  color: var(--text-muted);
}

.review-verdict-value {
  font-size: 28px;
  font-weight: 600;
  padding: 2px 14px;
  border-radius: 8px;
}

.verdict-block {
  background: var(--danger-bg);
  color: var(--danger-text);
}

.verdict-review {
  background: var(--warning-bg);
  color: var(--warning-text);
}

.verdict-ready {
  background: var(--ok-bg);
  color: var(--ok-text);
}

.review-verdict-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.review-disclaimer {
  font-size: 12px;
  color: var(--text-dim);
  padding: 18px;
  border-inline-start: 1px solid var(--border-soft);
}

.review-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1.2fr;
  gap: 16px;
  align-items: start;
}

.matrix-card {
  padding: 18px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.matrix {
  font-size: 12px;
}

.matrix-cell {
  text-align: center;
  cursor: default;
  padding: 6px 4px;
}

.cell-status {
  font-size: 14px;
  display: inline-block;
}

.cell-pass {
  color: var(--ok-text);
}

.cell-review {
  color: var(--warning-text);
  background: var(--warning-bg);
  padding: 0 4px;
  border-radius: 3px;
}

.cell-fail {
  color: var(--danger-text);
  background: var(--danger-bg);
  padding: 0 4px;
  border-radius: 3px;
}

.cell-none {
  color: var(--text-faint);
}

.matrix-detail {
  margin-top: 12px;
  padding: 10px 12px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: var(--bg);
}

.matrix-detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.matrix-detail-label {
  font-size: 11px;
  color: var(--text-muted);
}

.matrix-detail-body {
  font-size: 12px;
  color: var(--text);
}

.matrix-detail-empty {
  font-size: 12px;
  color: var(--text-faint);
}

.diff-card {
  padding: 18px;
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
  flex-wrap: wrap;
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
  color: var(--accent);
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
  max-height: 260px;
  overflow: auto;
  white-space: pre;
}

.rationale-card {
  padding: 18px;
}

.rationale-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rationale-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 8px 10px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: var(--panel);
}

.rationale-status-bar {
  width: 4px;
  height: 28px;
  border-radius: 2px;
  flex-shrink: 0;
}

.rationale-status-bar[class*="danger"] {
  background: var(--danger-text);
}

.rationale-status-bar[class*="warning"] {
  background: var(--warning-text);
}

.rationale-status-bar[class*="ok"] {
  background: var(--ok-text);
}

.rationale-title-text {
  flex: 1;
  color: var(--text);
}

.rationale-expand {
  border: none;
  background: none;
  color: var(--text-dim);
  font-size: 11px;
  cursor: pointer;
  padding: 0;
}

.rationale-detail {
  width: 100%;
  font-size: 11.5px;
  color: var(--text-muted);
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-soft);
  flex-direction: column;
  gap: 2px;
}

.detail-label {
  color: var(--text-faint);
  margin-right: 6px;
}

.detail-value {
  color: var(--text);
}

.stale-banner {
  margin-top: 14px;
  padding: 10px 14px;
  background: var(--warning-bg);
  color: var(--warning-text);
  border-radius: 8px;
  font-size: 12.5px;
}

.card {
  background: var(--panel);
}
</style>
