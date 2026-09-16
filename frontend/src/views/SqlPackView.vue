<template>
  <div class="sqlpage">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 명세 확정</button>
        <span class="head-title">02 SQL 팩</span>
        <span class="mono">revision {{ sqlPack.revision }}</span>
        <span class="mono">specVersion {{ sqlPack.spec_version }}</span>
        <span class="mono">contentHash {{ sqlPack.content_hash.slice(0, 12) }}…</span>
        <span class="badge" :class="rollbackClass">{{ rollbackLabel }}</span>
      </div>
      <div class="head-right">
        <button class="btn" @click="regenerate">명세에서 다시 생성</button>
      </div>
    </div>

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
        <button class="btn">확인</button>
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
            <button class="btn small" @click="saveArtifact">저장 (revision +1)</button>
            <button class="btn small">되돌리기</button>
            <button class="btn small">복사</button>
          </div>
        </div>

        <div class="code-block sql-editor">
          <pre>{{ currentSql }}</pre>
        </div>

        <div v-if="problemCount" class="problem-bar">
          <span class="problem-count mono">문제</span>
          <span class="badge danger">오류 {{ errors }} · 경고 {{ warnings }}</span>
          <span class="problem-detail">PostgreSQL 등호 문법 오류 · 자리표시자 __id__ 잔여</span>
        </div>
      </section>

      <section class="card checklist-card">
        <div class="section-title">실행 전 확인 근거</div>
        <div class="checklist">
          <label class="check-row">
            <input type="checkbox" v-model="evidence.execution_plan_reviewed" />
            <span>실행계획 확인</span>
            <span class="check-desc">EXPLAIN 검토</span>
          </label>
          <label class="check-row">
            <input type="checkbox" v-model="evidence.index_reviewed" />
            <span>인덱스 확인</span>
            <span class="check-desc">조건 컬럼 인덱스</span>
          </label>
          <label class="check-row">
            <input type="checkbox" v-model="evidence.lock_reviewed" />
            <span>락 범위 확인</span>
            <span class="check-desc">잠금 대상·시간</span>
          </label>
          <label class="check-row">
            <input type="checkbox" v-model="evidence.concurrency_reviewed" />
            <span>동시성 확인</span>
            <span class="check-desc">동시 트래픽 영향</span>
          </label>
        </div>

        <div class="sql-actions">
          <button class="btn primary">정적 검토 실행</button>
          <button class="btn">명세에서 다시 생성</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

type RollbackStatus = 'COMPLETE' | 'TEMPLATE_REQUIRES_BACKUP_ROWS'

const route = useRoute()

type ArtifactKey = 'precheckSql' | 'backupSql' | 'executionSql' | 'verificationSql' | 'rollbackSql'

const specId = computed(() => route.params.specId as string)

const sqlPack = ref({
  precheck_sql: 'SELECT "id", "tenant_id", "status", "created_at"\nFROM "public"."orders"\nWHERE "tenant_id" = 42\n  AND "status" = \'pending\'\n  AND "created_at" < \'2026-09-01\';',
  backup_sql: '-- Save these rows outside the database before executing the change.\nSELECT "id", "tenant_id", "status", "created_at"\nFROM "public"."orders"\nWHERE "tenant_id" = 42\n  AND "status" = \'pending\'\n  AND "created_at" < \'2026-09-01\';',
  execution_sql: 'UPDATE "public"."orders"\nSET "status" = \'cancelled\'\nWHERE "created_at" < \'2026-09-01\'\n  AND "tenant_id" = 42;',
  verification_sql: 'SELECT "id"\nFROM "public"."orders"\nWHERE "tenant_id" = 42\n  AND "status" = \'cancelled\'\n  AND "created_at" < \'2026-09-01\';',
  rollback_sql: '-- TEMPLATE: replace placeholder values with rows saved by backupSql.\nUPDATE "public"."orders" AS target\nSET "status" = backup."status"\nFROM (VALUES (__id__, __tenant_id__, __status__, __created_at__)) AS backup\n  (id, tenant_id, status, created_at)\nWHERE target."id" = backup."id"\n  AND target."tenant_id" = backup."tenant_id";\n',
  rollback_status: 'TEMPLATE_REQUIRES_BACKUP_ROWS' as RollbackStatus,
  spec_id: specId.value,
  spec_version: 1,
  content_hash: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0',
  revision: 2,
  updated_at: new Date().toISOString(),
})

const artifactKey = ref<ArtifactKey>('executionSql')
const errors = ref(1)
const warnings = ref(2)
const evidence = ref({
  execution_plan_reviewed: false,
  index_reviewed: false,
  lock_reviewed: false,
  concurrency_reviewed: false,
})

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
const currentSql = computed(() => {
  const pack = sqlPack.value
  if (artifactKey.value === 'precheckSql') return pack.precheck_sql
  if (artifactKey.value === 'backupSql') return pack.backup_sql
  if (artifactKey.value === 'executionSql') return pack.execution_sql
  if (artifactKey.value === 'verificationSql') return pack.verification_sql
  return pack.rollback_sql
})
const artifactIndex = computed(() => artifactList.findIndex((a) => a.key === artifactKey.value))
const problemCount = computed(() => errors.value + warnings.value)
const rollbackLabel = computed(() => {
  if (sqlPack.value.rollback_status === 'COMPLETE') return '롤백 완료'
  return '롤백 템플릿 (백업 행 필요)'
})
const rollbackClass = computed(() => {
  if (sqlPack.value.rollback_status === 'COMPLETE') return 'ok'
  return 'warning'
})

function saveArtifact() {
  // TODO: updateSqlArtifact 호출
}

function regenerate() {
  // TODO: createSqlPack 호출
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
</style>
