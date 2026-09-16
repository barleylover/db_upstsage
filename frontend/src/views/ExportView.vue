<template>
  <div class="export-page">
    <div class="export-header">
      <div class="export-header-left">
        <span class="export-bread mono">홈</span>
        <span class="export-bread-sep">/</span>
        <span class="export-bread mono">01 명세 확정</span>
        <span class="export-bread-sep">/</span>
        <span class="export-bread mono">02 SQL 팩</span>
        <span class="export-bread-sep">/</span>
        <span class="export-bread mono">03 검토</span>
        <span class="export-bread-sep">/</span>
        <span class="export-bread mono">04 변경 문서</span>
        <span class="export-bread-sep">/</span>
        <span class="export-bread mono">05 내보내기</span>
      </div>
      <div class="export-meta" v-if="packageSpec">
        <span class="chip" :class="verdictClass">{{ verdictLabel }}</span>
        <span class="mono">app.public.orders</span>
      </div>
    </div>

    <div v-if="!packageSpec" class="empty-state-card card">
      <div class="empty-state">내보낼 패키지가 없습니다. 검토 결과를 먼저 확인하세요.</div>
      <button class="btn primary" @click="router.push('/spec/' + (store.currentSpecId ?? '') + '/review')">검토로 이동</button>
    </div>

    <div v-else>
      <section class="card package-card">
        <div class="section-title">패키지 구성</div>
        <table class="table">
          <thead>
            <tr>
              <th>항목</th>
              <th>상태</th>
              <th>내용</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in packageItems" :key="idx">
              <td><span class="item-name">{{ item.name }}</span></td>
              <td>
                <span class="chip" :class="item.badgeClass">{{ item.status }}</span>
              </td>
              <td class="mono">{{ item.note }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <div class="export-actions">
        <button class="btn primary" @click="downloadMarkdown">Markdown 내려받기</button>
        <button class="btn" @click="downloadJson">JSON 내려받기</button>
        <button class="btn" @click="copyAll">전체 복사</button>
      </div>

      <section class="card preview-card">
        <div class="section-title">미리보기</div>
        <div class="preview-head">
          <span class="mono">{{ previewLineCount }}줄</span>
        </div>
        <div class="code-block preview-body">
          <pre>{{ preview }}</pre>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import type { ChangeDocument, ChangeSpec, ReviewResult, SqlPack } from '@/api/client'

const router = useRouter()
const store = useAppStore()

interface ReviewPackage {
  spec: ChangeSpec
  sqlPack: SqlPack
  review: ReviewResult
  document: ChangeDocument
}

const packageSpec = computed((): ReviewPackage | null => {
  if (!store.spec || !store.sqlPack || !store.review || !store.document) return null
  return {
    spec: store.spec as ChangeSpec,
    sqlPack: store.sqlPack as SqlPack,
    review: store.review,
    document: store.document,
  }
})

const verdictLabel = computed(() => {
  if (!store.review) return ''
  return store.review.verdict
})

const verdictClass = computed(() => {
  if (!store.review) return ''
  if (store.review.verdict === 'BLOCK') return 'chip-danger'
  if (store.review.verdict === 'REVIEW') return 'chip-warning'
  if (store.review.verdict === 'READY') return 'chip-ok'
  return ''
})

const packageItems = computed(() => {
  if (!packageSpec.value) return []
  const s = packageSpec.value
  const evidenceChecked = [
    store.evidence.executionPlanReviewed,
    store.evidence.indexReviewed,
    store.evidence.lockReviewed,
    store.evidence.concurrencyReviewed,
  ].filter(Boolean).length

  return [
    {
      name: '확정 Change Spec',
      status: '포함',
      badgeClass: 'chip-ok',
      note: `v${s.spec.version} · ${s.spec.specId.slice(0, 8)}…`,
    },
    {
      name: '5종 SQL',
      status: '포함',
      badgeClass: 'chip-ok',
      note: `revision ${s.sqlPack.revision}`,
    },
    {
      name: '영향도·위험 분석',
      status: '포함',
      badgeClass: 'chip-ok',
      note: `위험 ${s.review.riskLevel}`,
    },
    {
      name: '테스트·검증 증거',
      status: evidenceChecked >= 4 ? '포함' : '확인 필요',
      badgeClass: evidenceChecked >= 4 ? 'chip-ok' : 'chip-warning',
      note: `${evidenceChecked} / 4`,
    },
    {
      name: '롤백 계획',
      status: s.sqlPack.rollbackStatus === 'COMPLETE' ? '포함' : '확인 필요',
      badgeClass: s.sqlPack.rollbackStatus === 'COMPLETE' ? 'chip-ok' : 'chip-warning',
      note: s.sqlPack.rollbackStatus,
    },
    {
      name: '변경관리 신청서',
      status: '포함',
      badgeClass: 'chip-ok',
      note: s.document.templateName,
    },
    {
      name: '최종 판정과 근거',
      status: s.review.verdict,
      badgeClass: verdictClass.value,
      note: `${s.review.checks.filter((c) => c.status === 'FAIL').length} FAIL · ${s.review.checks.filter((c) => c.status === 'REVIEW').length} REVIEW`,
    },
  ]
})

const preview = computed(() => buildPackageMarkdown(packageSpec.value))

const previewLineCount = computed(() => {
  if (!preview.value) return 0
  return preview.value.split('\n').length
})

function buildPackageMarkdown(spec: ReviewPackage | null): string {
  if (!spec) return ''
  const s = spec
  const lines: string[] = []
  lines.push(`# 변경 리뷰 패키지 — ${s.sqlPack.executionSql.match(/"([^"]+)"\."([^"]+)"/)?.[2] ?? 'table'}`)
  lines.push('')
  lines.push(`- specId: ${s.spec.specId}`)
  lines.push(`- 버전: v${s.spec.version}`)
  lines.push(`- 상태: ${s.spec.status}`)
  lines.push(`- contentHash: ${s.spec.contentHash}`)
  lines.push('')
  lines.push('## 1. 확정 Change Spec')
  lines.push('')
  lines.push(`- 환경: ${s.spec.environment}`)
  lines.push(`- 데이터베이스: ${s.spec.database}`)
  lines.push(`- 스키마: ${s.spec.schema}`)
  lines.push(`- 테이블: ${s.spec.targetTable}`)
  lines.push(`- 작업: ${s.spec.operation}`)
  lines.push(`- 식별 키: ${(s.spec.identityKeyColumns ?? []).join(', ')}`)
  lines.push(`- predicates:`)
  for (const p of s.spec.predicates) {
    lines.push(`  - ${formatPredicate(p)}`)
  }
  lines.push(`- mutations:`)
  for (const m of s.spec.mutations) {
    lines.push(`  - ${m.column} = ${m.value} (${m.valueType})`)
  }
  lines.push(`- 예상 영향 건수: ${s.spec.expectedRowCount ?? '미입력'}`)
  lines.push(`- 가정: ${(s.spec.assumptions ?? []).join('; ') ?? '없음'}`)
  lines.push(`- 미해결 질문: ${(s.spec.unresolvedQuestions ?? []).join('; ') ?? '없음'}`)
  lines.push('')
  lines.push('## 2. 5종 SQL')
  lines.push('')
  lines.push('### 확인 SQL')
  lines.push('```sql')
  lines.push(s.sqlPack.precheckSql)
  lines.push('```')
  lines.push('')
  lines.push('### 백업 SQL')
  lines.push('```sql')
  lines.push(s.sqlPack.backupSql)
  lines.push('```')
  lines.push('')
  lines.push('### 실행 SQL')
  lines.push('```sql')
  lines.push(s.sqlPack.executionSql)
  lines.push('```')
  lines.push('')
  lines.push('### 검증 SQL')
  lines.push('```sql')
  lines.push(s.sqlPack.verificationSql)
  lines.push('```')
  lines.push('')
  lines.push('### 롤백 SQL')
  lines.push('```sql')
  lines.push(s.sqlPack.rollbackSql)
  lines.push('```')
  lines.push('')
  lines.push('## 3. 영향도·위험 분석')
  lines.push('')
  lines.push(`- 위험도: ${s.review.riskLevel}`)
  lines.push('')
  lines.push('## 4. 테스트·검증 증거')
  lines.push('')
  lines.push(`- 실행계획 확인: ${store.evidence.executionPlanReviewed}`)
  lines.push(`- 인덱스 확인: ${store.evidence.indexReviewed}`)
  lines.push(`- 락 범위 확인: ${store.evidence.lockReviewed}`)
  lines.push(`- 동시성 확인: ${store.evidence.concurrencyReviewed}`)
  lines.push('')
  lines.push('## 5. 롤백 계획')
  lines.push('')
  lines.push(`- 상태: ${s.sqlPack.rollbackStatus}`)
  lines.push('')
  lines.push('## 6. 변경관리 신청서')
  lines.push('')
  lines.push(`- 양식: ${s.document.templateName}`)
  lines.push('- 항목:')
  for (const f of s.document.fields) {
    lines.push(`  - ${f.label}: ${formatDocumentField(f)}`)
    lines.push(`    출처: ${f.source}`)
  }
  lines.push('')
  lines.push('## 7. 최종 판정과 근거')
  lines.push('')
  lines.push('| 규칙 | 상태 | 내용 |')
  lines.push('| --- | --- | --- |')
  for (const c of s.review.checks) {
    lines.push(`| ${c.ruleId} | ${c.status} | ${c.message} |`)
  }
  lines.push('')
  lines.push(`- 판정: ${s.review.verdict}`)
  lines.push(`- 검토 시점: ${s.review.reviewedAt}`)
  lines.push(`- 면책: ${s.review.disclaimer}`)
  lines.push('')
  return lines.join('\n')
}

function formatPredicate(p: { column: string; operator: string; value: unknown; valueType: string }): string {
  if (p.operator === 'IS_NULL' || p.operator === 'IS_NOT_NULL') {
    return `${p.column} ${p.operator.replace('_', ' ')}`
  }
  return `${p.column} ${p.operator} ${formatPredicateValue(p.value)}`
}

function formatPredicateValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return `'${value}'`
  return String(value)
}

function formatDocumentField(f: ChangeDocument['fields'][0]): string {
  const value = f.value
  if (value === null || value === undefined) return '·'
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    return (value as Parameters<typeof formatPredicate>[0][]).map(formatPredicate).join('; ')
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

function downloadMarkdown() {
  const content = preview.value
  if (!content) return
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `changespec-package-${store.currentSpecId ?? 'export'}.md`
  a.click()
  URL.revokeObjectURL(url)
}

function downloadJson() {
  const payload = {
    spec: store.spec,
    sqlPack: store.sqlPack,
    review: store.review,
    document: store.document,
    evidence: store.evidence,
    confirmedArtifacts: Array.from(store.confirmedArtifacts),
  }
  const content = JSON.stringify(payload, null, 2)
  const blob = new Blob([content], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `changespec-package-${store.currentSpecId ?? 'export'}.json`
  a.click()
  URL.revokeObjectURL(url)
}

async function copyAll() {
  const content = preview.value
  if (!content) return
  try {
    await navigator.clipboard.writeText(content)
  } catch {
    // clipboard unavailable
  }
}
</script>

<style scoped>
.export-page {
  max-width: 1180px;
}

.export-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  flex-wrap: wrap;
  gap: 10px;
}

.export-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.export-bread {
  font-size: 12px;
  color: var(--text-muted);
}

.export-bread-sep {
  color: var(--text-faint);
}

.export-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.empty-state-card {
  padding: 32px;
}

.empty-state {
  color: var(--text-dim);
  font-size: 13px;
}

.package-card {
  padding: 18px;
  margin-bottom: 18px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.export-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.preview-card {
  padding: 18px;
}

.preview-head {
  margin-bottom: 10px;
  color: var(--text-dim);
}

.preview-body {
  min-height: 200px;
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

.item-name {
  font-weight: 500;
}

.code-block {
  background: var(--bg);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 12px 14px;
  font-family: var(--mono);
  font-size: 12.5px;
  line-height: 1.6;
  overflow: auto;
  white-space: pre;
  color: var(--text);
}

.card {
  background: var(--panel);
}
</style>
