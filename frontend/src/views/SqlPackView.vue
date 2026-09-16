<template>
  <div class="sqlpage">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 명세 확정</button>
        <span class="head-title">02 SQL 팩</span>
        <span class="mono">revision {{ pack?.revision ?? '·' }}</span>
        <span class="mono">specVersion {{ pack?.specVersion ?? '·' }}</span>
        <span class="mono">contentHash {{ pack?.contentHash?.slice(0, 12) ?? '·' }}…</span>
        <span class="badge" :class="rollbackClass">{{ rollbackLabel }}</span>
      </div>
      <div class="head-right">
        <button class="btn outline" @click="regenerate" :disabled="!specId">명세에서 다시 생성</button>
      </div>
    </div>

    <div v-if="loading" class="loading-bar">
      <span class="mono">SQL 팩 생성 중…</span>
    </div>

    <div v-else-if="!pack" class="empty-state-card card">
      <div class="empty-state">SQL 팩이 없습니다. 먼저 명세를 확정하세요.</div>
      <button class="btn primary" @click="regenerate">SQL 팩 생성</button>
    </div>

    <div v-else>
      <div class="progress">
        <div class="progress-item" :class="{ active: artifactKey === 'precheckSql' }">
          <span class="pnum">1</span><span>확인</span>
        </div>
        <div class="progress-sep"></div>
        <div class="progress-item" :class="{ active: artifactKey === 'backupSql' }">
          <span class="pnum">2</span><span>백업</span>
        </div>
        <div class="progress-sep"></div>
        <div class="progress-item" :class="{ active: artifactKey === 'executionSql' }">
          <span class="pnum">3</span><span>실행</span>
        </div>
        <div class="progress-sep"></div>
        <div class="progress-item" :class="{ active: artifactKey === 'verificationSql' }">
          <span class="pnum">4</span><span>검증</span>
        </div>
        <div class="progress-sep"></div>
        <div class="progress-item" :class="{ active: artifactKey === 'rollbackSql' }">
          <span class="pnum">5</span><span>롤백</span>
        </div>
        <div class="progress-right">
          <span class="mono">SQL 확인 {{ artifactIndex + 1 }} / 5</span>
          <button class="btn" @click="confirmArtifact" :disabled="saving">확인</button>
        </div>
      </div>

      <div class="sql-grid">
        <section class="card sql-card">
          <div class="card-head">
            <div class="card-title">
              <span class="artifact-badge mono">{{ currentArtifactLabel }}</span>
              <span class="artifact-name">{{ currentArtifactTitle }}</span>
            </div>
            <div class="card-actions">
              <button class="btn small" @click="saveArtifact" :disabled="saving || !editableSql">저장 (revision +1)</button>
              <button class="btn small">되돌리기</button>
              <button class="btn small">복사</button>
            </div>
          </div>

          <div class="code-block sql-editor">
            <textarea
              class="sql-textarea mono"
              :value="currentSql"
              @input="onSqlInput"
              :disabled="saving"
              rows="14"
              spellcheck="false"
            ></textarea>
          </div>

          <div v-if="problemCount" class="problem-bar">
            <span class="problem-count mono">문제</span>
            <span class="badge danger">오류 {{ errors }} · 경고 {{ warnings }}</span>
            <span class="problem-detail">PostgreSQL 등호 문법 오류 · 자리표시자 잔여</span>
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
            <button class="btn primary" @click="runReview" :disabled="!canReview">정적 검토 실행</button>
            <button class="btn outline" @click="regenerate" :disabled="!specId">명세에서 다시 생성</button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createSqlPack, updateSqlArtifact, reviewSpec } from '@/api/client'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const specId = computed(() => route.params.specId as string)

type ArtifactKey = 'precheckSql' | 'backupSql' | 'executionSql' | 'verificationSql' | 'rollbackSql'

const loading = ref(false)
const saving = ref(false)
const errors = ref(1)
const warnings = ref(2)

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
const currentSql = computed(() => sqlText.value || artifactSql(artifactKey.value))
const artifactIndex = computed(() => artifactList.findIndex((a) => a.key === artifactKey.value))
const editableSql = computed(() => artifactKey.value !== 'precheckSql')
const problemCount = computed(() => errors.value + warnings.value)
const rollbackLabel = computed(() => {
  if (pack.value?.rollbackStatus === 'COMPLETE') return '롤백 완료'
  return '롤백 템플릿 (백업 행 필요)'
})
const rollbackClass = computed(() => {
  if (pack.value?.rollbackStatus === 'COMPLETE') return 'badge-ok'
  return 'badge-warning'
})
const canReview = computed(() => {
  if (!pack.value) return false
  const checked = [store.evidence.executionPlanReviewed, store.evidence.indexReviewed, store.evidence.lockReviewed, store.evidence.concurrencyReviewed]
  return checked.every(Boolean)
})

watch(
  () => pack.value,
  () => {
    if (pack.value) {
      syncSqlText()
    }
  },
  { immediate: true },
)

function artifactSql(key: ArtifactKey): string {
  const p = pack.value
  if (!p) return ''
  if (key === 'precheckSql') return p.precheckSql
  if (key === 'backupSql') return p.backupSql
  if (key === 'executionSql') return p.executionSql
  if (key === 'verificationSql') return p.verificationSql
  return p.rollbackSql
}

function syncSqlText() {
  if (!pack.value) return
  sqlText.value = artifactSql(artifactKey.value)
}

function onSqlInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  sqlText.value = target.value
}

async function regenerate() {
  if (!specId.value) return
  loading.value = true
  saving.value = true
  try {
    const data = await createSqlPack(specId.value)
    store.setSqlPackData(data)
    store.setBaselineSqlPack(data)
    syncSqlText()
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
    saving.value = false
  }
}

async function saveArtifact() {
  if (saving.value || !specId.value || !editableSql.value) return
  saving.value = true
  try {
    const data = await updateSqlArtifact(specId.value, artifactKey.value, sqlText.value)
    store.setSqlPackData(data)
    syncSqlText()
  } catch (err) {
    console.error(err)
  } finally {
    saving.value = false
  }
}

async function confirmArtifact() {
  await saveArtifact()
}

async function runReview() {
  if (!specId.value || !canReview.value) return
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

</script>

<style scoped>
.sqlpage {
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

.progress {
  display: flex;
  align-items: center;
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 18px;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-muted);
}

.progress-item.active {
  color: var(--accent-2);
  font-weight: 600;
}

.pnum {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--chip-bg);
  border: 1px solid var(--chip-border);
  font-size: 10px;
}

.progress-item.active .pnum {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.progress-sep {
  width: 1px;
  height: 14px;
  background: var(--border);
  margin: 0 8px;
}

.progress-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.sql-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  align-items: start;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.card-title {
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

.card-actions {
  display: flex;
  gap: 6px;
}

.sql-editor {
  min-height: 220px;
}

.sql-textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
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

.problem-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-dim);
  flex-wrap: wrap;
}

.problem-count {
  color: var(--text-muted);
}

.problem-detail {
  color: var(--text-dim);
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
