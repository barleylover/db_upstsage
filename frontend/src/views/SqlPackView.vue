<template>
  <div class="sqlpage">
    <div class="sql-header">
      <div class="sql-header-left">
        <span class="sql-bread mono">홈</span>
        <span class="sql-bread-sep">/</span>
        <span class="sql-bread mono">01 명세 확정</span>
        <span class="sql-bread-sep">/</span>
        <span class="sql-bread mono">02 SQL 팩</span>
      </div>
      <div class="sql-meta">
        <span class="sql-meta-item mono">revision {{ pack?.revision ?? '·' }}</span>
        <span class="sql-meta-item mono">specVersion {{ pack?.specVersion ?? '·' }}</span>
        <span class="sql-meta-item mono">contentHash {{ pack?.contentHash?.slice(0, 12) ?? '·' }}…</span>
        <span class="badge" :class="rollbackClass">{{ rollbackLabel }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading-bar">
      <span class="mono">SQL 팩 생성 중…</span>
    </div>

    <div v-else-if="!pack" class="empty-state-card card">
      <div class="empty-state">SQL 팩이 없습니다. 먼저 명세를 확정하세요.</div>
      <button class="btn primary" @click="regenerate" :disabled="loading">SQL 팩 생성</button>
    </div>

    <div v-else>
      <div class="artifact-tabs">
        <button
          v-for="artifact in artifactList"
          :key="artifact.key"
          class="artifact-tab"
          :class="{ active: artifactKey === artifact.key }"
          @click="switchArtifact(artifact.key)"
        >
          <span class="artifact-status" :class="artifactStatusClass(artifact.key)"></span>
          {{ artifact.title }}
        </button>
        <button class="btn primary" style="margin-left: auto;" @click="confirmCurrent" :disabled="saving">
          확인
        </button>
      </div>
      <div class="sql-meta-row">
        <span class="mono">SQL 확인 {{ confirmedCount }} / 5</span>
      </div>

      <div class="sql-grid">
        <section class="card sql-card">
          <div class="sql-card-head">
            <div class="sql-card-title">
              <span class="artifact-badge mono">{{ currentArtifactLabel }}</span>
              <span class="artifact-name">{{ currentArtifactTitle }}</span>
            </div>
            <div class="sql-card-actions">
              <button class="btn small" @click="saveArtifact" :disabled="saving || !editableSql">저장 (revision +1)</button>
              <button class="btn small" @click="revertArtifact" :disabled="saving">되돌리기</button>
              <button class="btn small" @click="copyArtifact" :disabled="saving">복사</button>
            </div>
          </div>

          <div class="sql-editor-wrap">
            <div class="sql-editor-gutter">
              <span v-for="(line, idx) in currentLines" :key="idx" class="sql-line-num">{{ idx + 1 }}</span>
            </div>
            <textarea
              class="sql-textarea mono"
              :value="currentSqlText"
              @input="onSqlInput"
              :disabled="saving"
              rows="16"
              spellcheck="false"
              ref="sqlEditorRef"
            ></textarea>
          </div>

          <div class="sql-card-foot">
            <button class="btn small" @click="regenerate" :disabled="loading">명세에서 다시 생성</button>
          </div>
        </section>

        <section class="card checklist-card">
          <div class="section-title">실행 전 확인 근거</div>
          <div class="checklist">
            <label class="check-row">
              <input type="checkbox" v-model="evidence.executionPlanReviewed" />
              <span>실행계획 확인</span>
              <span class="check-desc">EXPLAIN 검토</span>
            </label>
            <label class="check-row">
              <input type="checkbox" v-model="evidence.indexReviewed" />
              <span>인덱스 확인</span>
              <span class="check-desc">조건 컬럼 인덱스</span>
            </label>
            <label class="check-row">
              <input type="checkbox" v-model="evidence.lockReviewed" />
              <span>락 범위 확인</span>
              <span class="check-desc">잠금 대상·시간</span>
            </label>
            <label class="check-row">
              <input type="checkbox" v-model="evidence.concurrencyReviewed" />
              <span>동시성 확인</span>
              <span class="check-desc">동시 트래픽 영향</span>
            </label>
          </div>

          <div class="sql-actions">
            <button class="btn primary" @click="runReview" :disabled="!specId">정적 검토 실행</button>
            <button class="btn outline" @click="clearConfirmedAndRegenerate" :disabled="loading">명세에서 다시 생성</button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { createSqlPack, updateSqlArtifact, reviewSpec } from '@/api/client'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const specId = computed(() => route.params.specId as string)

type ArtifactKey = 'precheckSql' | 'backupSql' | 'executionSql' | 'verificationSql' | 'rollbackSql'

const loading = ref(false)
const saving = ref(false)
const sqlEditorRef = ref<HTMLTextAreaElement | null>(null)

const pack = computed(() => store.sqlPack)
const evidence = computed(() => store.evidence)

const artifactKey = ref<ArtifactKey>('executionSql')
const sqlText = ref('')

const artifactList: Array<{ key: ArtifactKey; label: string; title: string }> = [
  { key: 'precheckSql', label: 'precheckSql', title: '확인 SQL' },
  { key: 'backupSql', label: 'backupSql', title: '백업 SQL' },
  { key: 'executionSql', label: 'executionSql', title: '실행 SQL' },
  { key: 'verificationSql', label: 'verificationSql', title: '검증 SQL' },
  { key: 'rollbackSql', label: 'rollbackSql', title: '롤백 SQL' },
]

const currentArtifactLabel = computed(() => {
  const item = artifactList.find((a) => a.key === artifactKey.value)
  return item?.label ?? ''
})
const currentArtifactTitle = computed(() => {
  const item = artifactList.find((a) => a.key === artifactKey.value)
  return item?.title ?? ''
})
const currentSqlText = computed(() => sqlText.value || artifactSql(artifactKey.value))
const currentLines = computed(() => currentSqlText.value.split('\n'))
const editableSql = computed(() => true)
const confirmedCount = computed(() => store.confirmedArtifacts.size)
const rollbackLabel = computed(() => {
  if (pack.value?.rollbackStatus === 'COMPLETE') return '롤백 완료'
  return '롤백 템플릿 (백업 행 필요)'
})
const rollbackClass = computed(() => {
  if (pack.value?.rollbackStatus === 'COMPLETE') return 'badge-ok'
  return 'badge-warning'
})

function artifactSql(key: ArtifactKey): string {
  const p = pack.value
  if (!p) return ''
  if (key === 'precheckSql') return p.precheckSql
  if (key === 'backupSql') return p.backupSql
  if (key === 'executionSql') return p.executionSql
  if (key === 'verificationSql') return p.verificationSql
  return p.rollbackSql
}

function artifactStatusClass(key: ArtifactKey): string {
  if (store.confirmedArtifacts.has(key)) return 'artifact-status-confirmed'
  return 'artifact-status-none'
}

function switchArtifact(key: ArtifactKey) {
  artifactKey.value = key
  sqlText.value = ''
}

watch(
  () => pack.value,
  () => {
    if (pack.value) {
      sqlText.value = ''
    }
  },
  { immediate: true },
)

function onSqlInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  sqlText.value = target.value
}

function syncSqlText() {
  if (!pack.value) return
  sqlText.value = artifactSql(artifactKey.value)
}

async function regenerate() {
  if (!specId.value) return
  loading.value = true
  try {
    const data = await createSqlPack(specId.value)
    store.setSqlPackData(data)
    store.setBaselineSqlPack(data)
    sqlText.value = ''
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function saveArtifact() {
  if (saving.value || !specId.value) return
  saving.value = true
  try {
    const data = await updateSqlArtifact(specId.value, artifactKey.value, sqlText.value)
    store.setSqlPackData(data)
    sqlText.value = ''
  } catch (err) {
    console.error(err)
  } finally {
    saving.value = false
  }
}

function confirmCurrent() {
  if (!specId.value) return
  if (store.confirmedArtifacts.has(artifactKey.value)) return
  store.markArtifactConfirmed(artifactKey.value)
}

function revertArtifact() {
  sqlText.value = artifactSql(artifactKey.value)
}

async function copyArtifact() {
  const sql = sqlText.value || artifactSql(artifactKey.value)
  if (!sql) return
  try {
    await navigator.clipboard.writeText(sql)
  } catch {
    // clipboard unavailable
  }
}

async function runReview() {
  if (!specId.value) return
  try {
    const data = await reviewSpec(specId.value, {
      executionPlanReviewed: store.evidence.executionPlanReviewed,
      indexReviewed: store.evidence.indexReviewed,
      lockReviewed: store.evidence.lockReviewed,
      concurrencyReviewed: store.evidence.concurrencyReviewed,
    })
    store.setReviewData(data)
    router.push(`/spec/${specId.value}/review`)
  } catch (err) {
    console.error(err)
  }
}

async function clearConfirmedAndRegenerate() {
  if (!specId.value) return
  store.clearConfirmedArtifacts()
  await regenerate()
}
</script>

<style scoped>
.sqlpage {
  max-width: 1180px;
}

.sql-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  flex-wrap: wrap;
  gap: 10px;
}

.sql-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sql-bread {
  font-size: 12px;
  color: var(--text-muted);
}

.sql-bread-sep {
  color: var(--text-faint);
}

.sql-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.sql-meta-item {
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

.artifact-tabs {
  display: flex;
  align-items: center;
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  padding: 8px 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 4px;
}

.artifact-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  border-radius: 18px;
  background: var(--bg);
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease;
}

.artifact-tab:hover {
  background: var(--border-soft);
  color: var(--text);
}

.artifact-tab.active {
  background: var(--accent-bg);
  color: var(--accent);
  font-weight: 600;
}

.artifact-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--border);
}

.artifact-status-confirmed {
  background: var(--ok-text);
}

.artifact-status-none {
  background: var(--border);
}

.sql-meta-row {
  margin-bottom: 12px;
  color: var(--text-dim);
  font-size: 12px;
}

.sql-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 16px;
  align-items: start;
}

.sql-card {
  padding: 18px;
}

.sql-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.sql-card-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.artifact-badge {
  background: var(--chip-bg);
  border: 1px solid var(--chip-border);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--text-muted);
}

.artifact-name {
  font-size: 15px;
  font-weight: 600;
}

.sql-card-actions {
  display: flex;
  gap: 6px;
}

.sql-editor-wrap {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  overflow: hidden;
}

.sql-editor-gutter {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding: 12px 8px 12px 12px;
  background: var(--bg);
  border-inline-end: 1px solid var(--border-soft);
  min-width: 44px;
  user-select: none;
}

.sql-line-num {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text-faint);
  line-height: 1.5;
}

.sql-textarea {
  flex: 1;
  border: none;
  border-radius: 0;
  padding: 12px;
  font-family: var(--mono);
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
  background: var(--bg);
  color: var(--text);
}

.sql-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sql-card-foot {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.checklist-card {
  padding: 18px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  cursor: pointer;
}

.check-row span:first-of-type {
  min-width: 16px;
}

.check-desc {
  color: var(--text-dim);
  font-size: 11.5px;
}

.sql-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.card {
  background: var(--panel);
}

.checklist-card {
  background: var(--panel);
}
</style>
