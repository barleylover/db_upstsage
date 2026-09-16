<template>
  <div class="document-page">
    <div class="document-header">
      <div class="document-header-left">
        <span class="document-bread mono">홈</span>
        <span class="document-bread-sep">/</span>
        <span class="document-bread mono">01 명세 확정</span>
        <span class="document-bread-sep">/</span>
        <span class="document-bread mono">02 SQL 팩</span>
        <span class="document-bread-sep">/</span>
        <span class="document-bread mono">03 검토</span>
        <span class="document-bread-sep">/</span>
        <span class="document-bread mono">04 변경 문서</span>
      </div>
      <div class="document-meta" v-if="documentData">
        <span class="document-meta-item mono">{{ templateName }}</span>
        <span class="document-meta-item mono">기준 v{{ specVersion }} · rev {{ sqlRevision }}</span>
        <span class="document-meta-item mono">생성 {{ formattedAt }}</span>
        <span v-if="needsRegenerate" class="chip chip-warning">재생성 필요</span>
        <span v-if="mismatchCount > 0" class="chip chip-danger">불일치 {{ mismatchCount }}</span>
      </div>
    </div>

    <div v-if="!documentData" class="empty-state-card card">
      <div class="empty-state">변경 문서가 없습니다. 문서를 먼저 생성하세요.</div>
      <button class="btn primary" @click="regenerate" :disabled="pending">문서 생성</button>
    </div>

    <div v-else>
      <div class="doc-grid">
        <section class="card form-card">
          <div class="section-title">문서 양식</div>
          <div class="field" style="margin-bottom: 12px;">
            <label>문서 양식</label>
            <select class="input" v-model="selectedTemplateId">
              <option v-for="tmpl in templates" :key="tmpl.id" :value="tmpl.id">
                {{ tmpl.name }} ({{ tmpl.itemCount }}개 항목)
              </option>
            </select>
          </div>
          <div class="doc-actions">
            <button class="btn primary" @click="regenerate" :disabled="pending || !specId">
              {{ pending ? '재생성 중…' : '선택한 양식으로 다시 생성' }}
            </button>
            <button class="btn outline" @click="reviewAgain">문서까지 다시 검토</button>
            <button class="btn" @click="goExport">내보내기 →</button>
          </div>
        </section>

        <section class="card body-card">
          <div class="section-title">변경 문서</div>
          <table class="table">
            <thead>
              <tr>
                <th style="width: 28%;">항목</th>
                <th style="width: 48%;">내용</th>
                <th style="width: 24%;">정보 출처</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in rows" :key="idx" :class="{ 'mismatch': row.mismatch }">
                <td><span class="row-label">{{ row.label }}</span></td>
                <td class="mono">
                  <template v-if="row.isSql && row.value">
                    <textarea class="sql-textarea" rows="3" :value="row.value" readonly></textarea>
                  </template>
                  <template v-else>
                    <span class="row-value">{{ row.value }}</span>
                  </template>
                </td>
                <td>
                  <span class="chip" :class="row.sourceClass">{{ row.sourceLabel }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="mismatchCount > 0" class="mismatch-note">
            <span class="mono">불일치: 사용자가 편집한 값 vs 현재 spec</span>
          </div>
        </section>
      </div>

      <div class="document-footer">
        <button class="btn outline" @click="regenerate" :disabled="pending || !specId">선택한 양식으로 다시 생성</button>
        <button class="btn primary" @click="reviewAgain" :disabled="!specId">문서까지 다시 검토</button>
        <button class="btn" @click="goExport" :disabled="!specId">내보내기 →</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { generateChangeDocument, type ChangeDocument } from '@/api/client'
import { useAppStore } from '@/stores/app'
import { documentFieldSourceLabel, isSqlField, type TemplateId } from '@/services/documentFields'

const router = useRouter()
const store = useAppStore()

const specId = computed(() => store.currentSpecId)
const documentData = computed(() => store.document)
const pending = ref(false)
const selectedTemplateId = ref<TemplateId>('default')

const templates = computed(() => store.documentTemplates)

const specVersion = computed(() => store.spec?.version ?? documentData.value?.specVersion ?? 1)
const sqlRevision = computed(() => store.sqlPack?.revision ?? documentData.value?.sqlPackRevision ?? 0)
const createdAt = computed(() => documentData.value?.generatedAt ?? '')
const formattedAt = computed(() => {
  if (!createdAt.value) return '—'
  try {
    const d = new Date(createdAt.value)
    return d.toISOString().slice(0, 10)
  } catch {
    return createdAt.value
  }
})

const templateName = computed(() => {
  if (documentData.value) return documentData.value.templateName
  const t = templates.value.find((t) => t.id === selectedTemplateId.value)
  return t?.name ?? '기본 변경 신청서'
})

const rows = computed(() => {
  if (!documentData.value) return []
  return mapDocumentToRows(documentData.value)
})

const mismatchCount = computed(() => rows.value.filter((r) => r.mismatch).length)

const needsRegenerate = computed(() => {
  if (!documentData.value) return false
  if (!store.spec) return false
  if (!store.sqlPack) return false
  if (documentData.value.specVersion !== store.spec.version) return true
  if (documentData.value.contentHash !== store.spec.contentHash) return true
  if (documentData.value.sqlPackRevision !== store.sqlPack.revision) return true
  return false
})

function mapDocumentToRows(doc: ChangeDocument) {
  return doc.fields.map((f) => {
    const isEditMismatch = isFieldMismatch(f)
    const value = formatFieldValue(f)
    return {
      label: f.label,
      value,
      rawValue: f.value,
      isSql: isSqlField(f.key),
      sourceLabel: documentFieldSourceLabel(f.source),
      sourceClass: sourceClass(f.source),
      mismatch: isEditMismatch || needsRegenerate.value,
    }
  })
}

function isFieldMismatch(f: ChangeDocument['fields'][0]): boolean {
  if (!store.editableDocumentValues) return false
  const edit = store.editableDocumentValues[f.key]
  if (edit === undefined) return false
  const current = formatFieldValue(f)
  return edit !== current
}

function formatFieldValue(f: ChangeDocument['fields'][0]): string {
  const value = f.value
  if (value === null || value === undefined) return '·'
  if (typeof value === 'string') return value
  if (f.key === 'predicates' && Array.isArray(value)) {
    return formatPredicates(value)
  }
  if (f.key === 'mutations' && Array.isArray(value)) {
    return formatMutations(value)
  }
  if (f.key === 'identityKeyColumns' && Array.isArray(value)) {
    return (value as unknown[]).join(', ')
  }
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      if (value.length && typeof value[0] === 'object') {
        return (value as Parameters<typeof formatPredicate>[0][]).map(formatPredicate).join('\n')
      }
    }
    return JSON.stringify(value)
  }
  return String(value)
}

function formatPredicate(item: unknown): string {
  const o = item as Record<string, unknown> | undefined
  if (!o) return '·'
  const column = String(o.column ?? '')
  const operator = String(o.operator ?? '')
  const value = o.value
  const valueText = formatValueText(value)
  if (operator === 'IS_NULL' || operator === 'IS_NOT_NULL') {
    return `${column} ${operator.replace('_', ' ')}`
  }
  return `${column} ${operator} ${valueText}`
}

function formatPredicates(items: unknown[]): string {
  return items.map(formatPredicate).join('\n')
}

function formatMutations(items: unknown[]): string {
  return items.map((item) => {
    const o = item as Record<string, unknown> | undefined
    if (!o) return '·'
    return `${o.column} = ${formatValueText(o.value)}`
  }).join('\n')
}

function formatValueText(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'number') return String(value)
  return JSON.stringify(value)
}

function sourceClass(source: string): string {
  if (source === 'CHANGE_SPEC') return 'chip-teal'
  if (source === 'SQL_PACK') return 'chip-teal'
  return 'chip'
}

async function regenerate() {
  if (!specId.value) return
  pending.value = true
  try {
    const doc = await generateChangeDocument(specId.value, templates.value.find((t) => t.id === selectedTemplateId.value)?.name ?? 'DEFAULT')
    store.setDocumentData(doc)
    store.editableDocumentValues = {}
  } catch (err) {
    console.error(err)
  } finally {
    pending.value = false
  }
}

function reviewAgain() {
  if (!specId.value) return
  router.push(`/spec/${specId.value}/review`)
}

function goExport() {
  if (!specId.value) return
  router.push(`/spec/${specId.value}/export`)
}

onMounted(() => {
  if (documentData.value && !documentData.value.generatedAt) {
    regenerate()
  }
})
</script>

<style scoped>
.document-page {
  max-width: 1180px;
}

.document-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  flex-wrap: wrap;
  gap: 10px;
}

.document-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.document-bread {
  font-size: 12px;
  color: var(--text-muted);
}

.document-bread-sep {
  color: var(--text-faint);
}

.document-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.document-meta-item {
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

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.row-label {
  display: block;
  font-weight: 500;
}

.row-value {
  display: block;
  word-break: break-word;
}

.sql-textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px;
  font-family: var(--mono);
  font-size: 12px;
  resize: vertical;
  margin-top: 6px;
  background: var(--bg);
  color: var(--text);
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

.mismatch {
  background: var(--danger-bg);
}

.mismatch td {
  color: var(--danger-text);
}

.mismatch-note {
  margin-top: 10px;
  font-size: 11.5px;
  color: var(--danger-text);
}

.doc-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.document-footer {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
  padding-top: 16px;
  border-top: 1px solid var(--border-soft);
}

.card {
  background: var(--panel);
}
</style>
