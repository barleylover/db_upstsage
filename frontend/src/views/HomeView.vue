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
            <button class="composer-chip" :class="{ active: schemaChipActive }" @click="toggleSchemaChip">
              <span class="composer-chip-label mono">{{ schemaChipLabel }}</span>
              <span class="composer-chip-arrow">▾</span>
            </button>
            <div v-if="schemaPopoverOpen" class="composer-popover">
              <div class="composer-popover-row selected">● PostgreSQL</div>
              <div class="composer-popover-row">  MySQL — 예정</div>
              <div class="composer-popover-row">  MariaDB — 예정</div>
              <div class="composer-popover-row">  Oracle — 예정</div>
              <div class="composer-popover-row">  SQL Server — 예정</div>
            </div>
          </div>

          <div class="composer-chip-row">
            <button class="composer-chip" :class="{ active: dbmsChipActive }" @click="toggleDbmesChip">
              <span class="composer-chip-label mono">{{ dbmsChipLabel }}</span>
              <span class="composer-chip-arrow">▾</span>
            </button>
            <div v-if="dbmesPopoverOpen" class="composer-popover">
              <div class="composer-popover-row selected">● PostgreSQL</div>
              <div class="composer-popover-row muted">  MySQL — 예정</div>
              <div class="composer-popover-row muted">  MariaDB — 예정</div>
              <div class="composer-popover-row muted">  Oracle — 예정</div>
              <div class="composer-popover-row muted">  SQL Server — 예정</div>
            </div>
          </div>

          <div class="composer-chip-row">
            <button class="composer-chip" :class="{ active: detectChipActive }" @click="toggleDetectChip">
              <span class="composer-chip-label mono">자동 감지</span>
              <span class="composer-chip-arrow">▾</span>
            </button>
          </div>
        </div>

        <div class="composer-footer">
          <span class="char-count mono">{{ requestText.length }} / 10000</span>
          <button class="composer-submit btn primary tall" :disabled="!requestText.trim() || submitting" @click="submitRequest">
            전송 <span aria-hidden="true">↑</span>
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

const router = useRouter()
const store = useAppStore()

const requestText = ref('tenant_id가 42이고 status가 pending인 주문을 2026-09-01 이전에 created_at 기준으로 취소 변경해줘')
const submitting = ref(false)
const error = ref('')
const cancelled = computed(() => store.notFound)

const schemaPopoverOpen = ref(false)
const dbmesPopoverOpen = ref(false)

const activeSchema = computed(() => store.activeSchema)
const schemaChipActive = ref(false)
const schemaChipLabel = computed(() => {
  const s = activeSchema.value
  return `${s?.name ?? '기본 스키마'} · ${s?.database ?? 'app'}.${s?.schema ?? 'public'} ▾`
})

const dbmsChipActive = ref(false)
const dbmsChipLabel = ref('PostgreSQL ▾')

const detectChipActive = ref(true)

function toggleSchemaChip() {
  schemaPopoverOpen.value = !schemaPopoverOpen.value
  dbmesPopoverOpen.value = false
}

function toggleDbmesChip() {
  dbmesPopoverOpen.value = !dbmesPopoverOpen.value
  schemaPopoverOpen.value = false
}

function toggleDetectChip() {
  detectChipActive.value = !detectChipActive.value
}

async function submitRequest() {
  if (!requestText.value.trim() || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const spec = await interpretRequest(requestText.value, {
      database: activeSchema.value?.database ?? 'app',
      schema: activeSchema.value?.schema ?? 'public',
      tables: [
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

.composer-chip-arrow {
  color: var(--text-faint);
  font-size: 10px;
}

.composer-popover {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 20;
  min-width: 170px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 6px;
  box-shadow: var(--shadow);
  margin-top: 4px;
}

.composer-popover-row {
  padding: 5px 10px;
  border-radius: 6px;
  font-family: var(--mono);
  font-size: 11.5px;
  color: var(--text-muted);
  cursor: default;
}

.composer-popover-row.selected {
  background: var(--accent-bg);
  color: var(--accent);
}

.composer-popover-row.muted {
  color: var(--text-faint);
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

.composer-submit {
  min-width: 78px;
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
