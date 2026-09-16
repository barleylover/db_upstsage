<template>
  <div class="home-page">
    <div class="home-title">
      <h1 class="home-title-main">ChangeSpec</h1>
      <span class="home-title-sub">Reviewer</span>
    </div>

    <div class="home-composer-wrap">
      <div class="composer-card card">
        <textarea
          class="composer-textarea"
          placeholder="바꾸려는 내용을 여기에 적습니다 …"
          v-model="requestText"
          :disabled="submitting"
          maxlength="10000"
          rows="4"
        ></textarea>

        <div class="composer-chips">
          <div class="composer-chip-row">
            <button class="composer-chip" :class="{ active: schemaPopoverOpen }" @click="toggleSchemaPopover">
              <span class="composer-chip-label mono">{{ schemaChipLabel }}</span>
            </button>
            <div v-if="schemaPopoverOpen" class="composer-popover" @click.stop>
              <div class="composer-popover-head">스키마</div>
              <div
                v-for="schema in schemaList"
                :key="schema.id"
                class="composer-popover-row"
                :class="{ selected: activeSchema?.id === schema.id }"
                @click="selectSchema(schema)"
              >
                <span>●</span>
                <span class="mono">{{ schema.name }}</span>
                <span class="mono popover-meta">{{ schema.database }}.{{ schema.schema }}</span>
              </div>
              <div class="composer-popover-divider"></div>
              <div class="composer-popover-row" @click="selectSchemaAutoDetect">
                <span>●</span>
                <span>자동 감지</span>
              </div>
            </div>
          </div>

          <div class="composer-chip-row">
            <button class="composer-chip" :class="{ active: dbmsPopoverOpen }" @click="toggleDbmesPopover">
              <span class="composer-chip-label mono">{{ dbmsChipLabel }}</span>
            </button>
            <div v-if="dbmsPopoverOpen" class="composer-popover" @click.stop>
              <div class="composer-popover-head">DBMS</div>
              <div
                v-for="dbms in supportedDbmses"
                :key="dbms"
                class="composer-popover-row"
                :class="{ selected: activeSchema?.dbms === dbms }"
                @click="selectDbms(dbms)"
              >
                <span>●</span>
                <span>{{ dbmsLabel(dbms) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="composer-footer">
          <span class="char-count mono">{{ requestText.length }} / 10000</span>
          <button class="composer-submit composer-submit-icon" :disabled="!requestText.trim() || submitting" @click="submitRequest" aria-label="요청 전송">
            <span class="composer-submit-icon-mark">→</span>
          </button>
        </div>

        <div v-if="error" class="composer-error">{{ error }}</div>
      </div>

      <div v-if="cancelled" class="home-cancelled">
        <div class="card" style="max-width: 420px;">
          <div class="card-body">
            <div class="empty-state">서버에 이 검토가 없습니다. 새 검토를 시작하세요.</div>
            <button class="btn primary" style="margin-top: 12px;" @click="cancelDone">새 검토</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { interpretRequest } from '@/api/client'
import type { SchemaCatalogEntry } from '@/types'

const router = useRouter()
const store = useAppStore()

const requestText = ref('tenant_id가 42이고 status가 pending인 주문을 2026-09-01 이전에 created_at 기준으로 취소 변경해줘')
const submitting = ref(false)
const error = ref('')
const cancelled = computed(() => store.notFound)

const schemaPopoverOpen = ref(false)
const dbmsPopoverOpen = ref(false)

const schemaList = computed(() => store.schemaList)
const activeSchema = computed(() => store.activeSchema)
const supportedDbmses = computed(() => store.supportedDbmses)

const schemaChipLabel = computed(() => {
  const s = activeSchema.value
  if (!s) return '기본 스키마 · app.public'
  return `${s.name} · ${s.database}.${s.schema}`
})

const dbmsChipLabel = computed(() => {
  const s = activeSchema.value
  if (!s) return 'PostgreSQL'
  return dbmsLabel(s.dbms)
})

function dbmsLabel(dbms: string): string {
  const map: Record<string, string> = {
    POSTGRESQL: 'PostgreSQL',
    MYSQL: 'MySQL',
    MARIADB: 'MariaDB',
    ORACLE: 'Oracle',
    SQL_SERVER: 'SQL Server',
    SQLITE: 'SQLite',
    BIGQUERY: 'BigQuery',
    SNOWFLAKE: 'Snowflake',
  }
  return map[dbms] ?? dbms
}

function toggleSchemaPopover() {
  schemaPopoverOpen.value = !schemaPopoverOpen.value
  dbmsPopoverOpen.value = false
}

function toggleDbmesPopover() {
  dbmsPopoverOpen.value = !dbmsPopoverOpen.value
  schemaPopoverOpen.value = false
}

function selectSchema(schema: SchemaCatalogEntry) {
  store.activeSchemaId = schema.id
  schemaPopoverOpen.value = false
}

function selectSchemaAutoDetect() {
  schemaPopoverOpen.value = false
}

function selectDbms(dbms: string) {
  const current = activeSchema.value
  if (!current) {
    store.activeSchemaId = store.schemaList[0]?.id ?? null
    const next = store.activeSchema
    if (next) {
      next.dbms = dbms as typeof next.dbms
      store.persistSchemaCatalog()
    }
  } else {
    current.dbms = dbms as typeof current.dbms
    store.persistSchemaCatalog()
  }
  dbmsPopoverOpen.value = false
}

async function submitRequest() {
  if (!requestText.value.trim() || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const spec = await interpretRequest(requestText.value, {
      database: activeSchema.value?.database ?? 'app',
      schema: activeSchema.value?.schema ?? 'public',
      tables: activeSchema.value?.tables ?? [
        {
          name: 'orders',
          columns: [
            { name: 'id', data_type: 'bigint', nullable: false },
            { name: 'tenant_id', data_type: 'bigint', nullable: false },
            { name: 'status', data_type: 'varchar', nullable: false },
            { name: 'created_at', data_type: 'timestamp', nullable: false },
          ],
          primary_key_columns: ['id'],
        },
      ],
    })
    store.setSpec(spec.specId, spec.status)
    router.push(`/spec/${spec.specId}/confirm`)
  } catch (err: unknown) {
    const e = err as { status?: number; message?: string; code?: string }
    error.value = e.message ?? `요청에 실패했습니다: ${String(err)}`
  } finally {
    submitting.value = false
  }
}

function cancelDone() {
  store.setNotFound()
  router.push('/home')
}
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 40px 24px;
}

.home-title {
  text-align: center;
  margin-bottom: 36px;
}

.home-title-main {
  font-size: 48px;
  font-weight: 600;
  color: var(--accent-2);
  margin: 0;
  letter-spacing: 0;
}

.home-title-sub {
  font-size: 48px;
  font-weight: 600;
  color: var(--accent);
  margin-left: 6px;
}

.home-composer-wrap {
  width: 100%;
  max-width: 720px;
}

.composer-card {
  width: 100%;
}

.composer-textarea {
  width: 100%;
  min-height: 110px;
  margin-bottom: 14px;
}

.composer-chips {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  position: relative;
}

.composer-chip-row {
  position: relative;
}

.composer-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: auto;
  padding: 6px 10px;
  border: 1px solid var(--chip-border);
  border-radius: 10px;
  background: var(--chip-bg);
  color: var(--text-muted);
  font-size: 11.5px;
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease, color 0.12s ease;
}

.composer-chip:hover {
  background: rgba(0, 0, 0, 0.03);
  color: var(--text);
}

.composer-chip.active {
  background: rgba(0, 0, 0, 0.04);
  border-color: var(--accent);
  color: var(--text);
}

.composer-chip-label {
  color: var(--text-muted);
}

.composer-chip.active .composer-chip-label {
  color: var(--text);
}

.composer-popover {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 20;
  min-width: 220px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 6px;
  box-shadow: var(--shadow);
  margin-top: 4px;
}

.composer-popover-head {
  font-size: 10px;
  color: var(--text-faint);
  padding: 4px 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.composer-popover-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 11.5px;
  color: var(--text-muted);
  cursor: pointer;
}

.composer-popover-row:hover {
  background: var(--bg);
}

.composer-popover-row.selected {
  background: var(--accent-bg);
  color: var(--accent);
}

.composer-popover-row .mono {
  font-family: var(--mono);
  font-size: 11px;
}

.popover-meta {
  color: var(--text-faint);
  margin-left: auto;
}

.composer-popover-divider {
  height: 1px;
  background: var(--border-soft);
  margin: 4px 10px;
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.char-count {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text-dim);
}

.composer-submit-icon {
  width: 38px;
  height: 38px;
  padding: 0;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  border: 1px solid var(--accent);
  font-size: 16px;
  min-width: 0;
  flex: none;
}

.composer-submit-icon:hover {
  background: var(--accent-3);
  border-color: var(--accent-3);
}

.composer-submit-icon-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.composer-error {
  margin-top: 10px;
  color: var(--danger-text);
  font-size: 12.5px;
}

.home-cancelled {
  margin-top: 18px;
}
</style>
