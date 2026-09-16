<template>
  <div class="document-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 검토</button>
        <span class="head-title">04 변경 문서</span>
        <span class="mono">양식 {{ templateName ?? '기본 변경 신청서' }}</span>
        <span class="mono">기준: v{{ specVersion }} · rev {{ sqlRevision }}</span>
        <span class="mono">생성일: {{ createdAt ?? '—' }}</span>
        <span class="badge" :class="regenerateBadgeClass">{{ regenerateBadgeLabel }}</span>
        <span class="badge" :class="mismatchBadgeClass">불일치 {{ mismatchCount }}</span>
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
                  <template v-if="editableRowId === idx">
                    <textarea class="field-textarea mono" rows="3" v-model="editingValue" @blur="commitEdit(idx)" @keydown.enter.prevent="commitEdit(idx)"></textarea>
                  </template>
                  <template v-else>
                    <span class="row-value mono">{{ row.value }}</span>
                    <button class="btn small" @click="startEdit(idx)">편집</button>
                  </template>
                </td>
                <td><span class="source-label">{{ row.source }}</span></td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>

      <div class="export-bar">
        <button class="btn primary" @click="copyMarkdown">Markdown</button>
        <button class="btn primary" @click="copyJson">JSON</button>
        <button class="btn primary" @click="copyAll">전체 복사</button>
      </div>

      <div v-if="previewOpen" class="preview-card card">
        <div class="preview-head">
          <span class="preview-title">미리보기</span>
          <button class="btn small" @click="previewOpen = false">닫기</button>
        </div>
        <pre class="preview-body mono">{{ previewText }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { generateChangeDocument, type ChangeDocument } from '@/api/client'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const store = useAppStore()

const specId = computed(() => store.currentSpecId)
const documentData = computed(() => store.document)
const pending = ref(false)
const previewOpen = ref(false)
const previewText = ref('')
const editingValue = ref('')
const editableRowId = ref<number | null>(null)

const specVersion = computed(() => store.spec?.version ?? documentData.value?.specVersion ?? 1)
const sqlRevision = computed(() => store.sqlPack?.revision ?? documentData.value?.sqlPackRevision ?? 0)
const createdAt = computed(() => documentData.value?.generatedAt ?? '—')
const templateName = computed(() => documentData.value?.templateName ?? store.documentTemplates.find((t) => t.id === selectedTemplateId.value)?.name ?? '기본 변경 신청서')

const selectedTemplateId = ref('default')
const templates = computed(() => store.documentTemplates)

const rows = computed(() => {
  if (!documentData.value) return []
  return mapDocumentToRows(documentData.value)
})

const mismatchCount = computed(() => rows.value.filter((r) => r.mismatch).length)

const regenerateBadgeClass = computed(() => {
  if (mismatchCount.value > 0) return 'badge-danger'
  if (!documentData.value?.generatedAt) return 'badge-warning'
  return ''
})
const regenerateBadgeLabel = computed(() => {
  if (mismatchCount.value > 0) return '불일치 있음'
  if (!documentData.value?.generatedAt) return '생성 필요'
  return '정상'
})
const mismatchBadgeClass = computed(() => (mismatchCount.value > 0 ? 'badge-danger' : ''))

function mapDocumentToRows(doc: ChangeDocument) {
  return doc.fields.map((f) => {
    const mismatch = detectMismatch(f)
    return {
      label: f.label,
      value: f.value ?? '·',
      source: f.source ?? '—',
      mismatch,
    }
  })
}

function detectMismatch(f: ChangeDocument['fields'][0]): boolean {
  if (!store.spec) return false
  if (f.key === 'targetTable' && f.value !== store.spec.targetTable) return true
  if (f.key === 'operation' && f.value !== store.spec.operation) return true
  if (f.key === 'database' && f.value !== store.spec.database) return true
  if (f.key === 'schema' && f.value !== store.spec.schema) return true
  return false
}

function startEdit(idx: number) {
  const row = rows.value[idx]
  if (!row) return
  editingValue.value = row.value
  editableRowId.value = idx
}

function commitEdit(idx: number) {
  if (editableRowId.value !== idx) return
  const row = rows.value[idx]
  if (!row) return
  // 문서 재생성 없이 편집 표시를 유지하는 용도. 실제 저장은 regenerate로.
  editableRowId.value = null
}

async function regenerate() {
  if (!specId.value) return
  pending.value = true
  try {
    const doc = await generateChangeDocument(specId.value, selectedTemplateId.value)
    store.setDocumentData(doc)
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

function copyMarkdown() {
  previewText.value = buildMarkdown()
  previewOpen.value = true
}

function copyJson() {
  previewText.value = JSON.stringify(documentData.value ?? {}, null, 2)
  previewOpen.value = true
}

function copyAll() {
  previewText.value = buildMarkdown() + '\n\n---\n\n' + JSON.stringify(documentData.value ?? {}, null, 2)
  previewOpen.value = true
}

function buildMarkdown(): string {
  if (!documentData.value) return ''
  const lines = ['# 변경 문서', '', `**생성일:** ${documentData.value.generatedAt}`, `**양식:** ${documentData.value.templateName}`, `**기준:** v${specVersion.value} · rev ${sqlRevision.value}`, '', '## 항목', '']
  for (const f of documentData.value.fields) {
    lines.push(`### ${f.label}`)
    lines.push(f.value ?? '·')
    lines.push('')
  }
  lines.push('## 출처', '')
  for (const f of documentData.value.fields) {
    lines.push(`- ${f.label}: ${f.source ?? '—'}`)
  }
  return lines.join('\n')
}

watch(
  () => documentData.value,
  () => {
    if (documentData.value && !documentData.value.generatedAt) {
      regenerate()
    }
  },
  { immediate: true },
)
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
  background: var(--panel);
}

.body-card {
  padding: 18px;
  background: var(--panel);
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

.field-textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px;
  font-family: var(--mono);
  font-size: 12px;
  resize: vertical;
  margin-top: 6px;
}

.row-value {
  display: block;
  margin-right: 8px;
}

.doc-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.export-bar {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.preview-card {
  margin-top: 16px;
  padding: 16px;
  background: var(--panel);
}

.preview-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.preview-title {
  font-size: 14px;
  font-weight: 600;
}

.preview-body {
  background: var(--bg);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 14px;
  max-height: 400px;
  overflow: auto;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.card {
  background: var(--panel);
}
</style>
