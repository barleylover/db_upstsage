<template>
  <div class="home-page">
    <div class="title-row">
      <h1 class="title-main">ChangeSpec</h1>
      <span class="title-sub">Reviewer</span>
    </div>

    <section class="intro">
      <div class="intro-card card">
        <h2>변경 검토 프로세스</h2>
        <div class="flow-steps">
          <div class="flow-step">1. 변경 요청을 자연어로 입력</div>
          <div class="flow-arrow">→</div>
          <div class="flow-step">2. 대상·조건·변경값을 확정</div>
          <div class="flow-arrow">→</div>
          <div class="flow-step">3. SQL 팩 생성·확인</div>
          <div class="flow-arrow">→</div>
          <div class="flow-step">4. 정적 검토(안전성)</div>
          <div class="flow-arrow">→</div>
          <div class="flow-step">5. 변경 문서 생성·내보내기</div>
        </div>
        <p class="intro-note">명세 확정 → SQL 팩 → 검토 → 변경 문서 → 내보내기 순서로 진행됩니다.</p>
      </div>
    </section>

    <section class="composer">
      <div class="composer-card card">
        <div class="composer-label mono">컴포저</div>
        <textarea
          class="composer-input textarea"
          placeholder="바꾸려는 내용을 여기에 적습니다 …"
          v-model="requestText"
          maxlength="10000"
          rows="4"
        ></textarea>

        <div class="composer-options">
          <div class="chip-option">
            <span class="chip-label mono">기본 스키마 · app.public · orders</span>
          </div>
          <div class="chip-option">
            <span class="chip-label mono">PostgreSQL</span>
          </div>
          <div class="chip-option">
            <span class="chip-label mono">자동 감지</span>
          </div>
        </div>

        <div class="composer-footer">
          <span class="char-count mono">{{ requestText.length }} / 10000</span>
          <button class="btn primary" @click="submitRequest" :disabled="!requestText.trim()">
            전송 <span aria-hidden="true">↑</span>
          </button>
        </div>
      </div>

      <div class="db-selector card">
        <div class="selector-head">선택 창 (드롭다운)</div>
        <div class="selector-list">
          <div class="selector-item selected">● PostgreSQL</div>
          <div class="selector-item">  MySQL — 예정</div>
          <div class="selector-item">  MariaDB — 예정</div>
          <div class="selector-item">  Oracle — 예정</div>
          <div class="selector-item">  SQL Server — 예정</div>
        </div>
        <div class="selector-hint">드래그해서 훑어보고 클릭해 선택</div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { interpretRequest } from '@/api/client'

const router = useRouter()
const requestText = ref('tenant_id가 42이고 status가 pending인 주문을 2026-09-01 이전에 created_at 기준으로 취소 변경해줘')

async function submitRequest() {
  if (!requestText.value.trim()) return
  try {
    const spec = await interpretRequest(requestText.value, {
      database: 'app',
      schema: 'public',
      tables: [
        { name: 'orders', columns: [{ name: 'id', data_type: 'bigint', nullable: false }, { name: 'tenant_id', data_type: 'bigint', nullable: false }, { name: 'status', data_type: 'varchar', nullable: false }, { name: 'created_at', data_type: 'timestamp', nullable: false }], primary_key_columns: ['id'] },
      ],
    })
    router.push(`/spec/${spec.specId}/confirm`)
  } catch (err) {
    console.error(err)
  }
}
</script>

<style scoped>
.home-page {
  max-width: 1180px;
}

.title-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 28px;
}

.title-main {
  font-size: 40px;
  font-weight: 600;
  color: var(--accent-2);
  margin: 0;
  letter-spacing: 0;
}

.title-sub {
  font-size: 40px;
  font-weight: 600;
  color: var(--text-muted);
  margin: 0;
}

.intro {
  margin-bottom: 28px;
}

.intro-card {
  padding: 20px 24px;
}

.intro-card h2 {
  margin: 0 0 12px;
  font-size: 18px;
}

.flow-steps {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 8px;
}

.flow-step {
  color: var(--text-muted);
  font-size: 13px;
}

.flow-arrow {
  color: var(--text-faint);
  font-size: 14px;
}

.intro-note {
  margin: 12px 0 0;
  color: var(--text-dim);
  font-size: 13px;
}

.composer {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 18px;
  align-items: start;
}

.composer-card {
  padding: 20px;
}

.composer-label {
  color: var(--text-muted);
  font-size: 12px;
  margin-bottom: 12px;
  display: block;
}

.composer-input {
  min-height: 96px;
}

.composer-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0 16px;
}

.chip-option {
  border: 1px solid var(--chip-border);
  border-radius: 15px;
  padding: 4px 10px;
  background: var(--chip-bg);
}

.chip-label {
  color: var(--text-ghost);
  font-size: 11.5px;
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.char-count {
  color: var(--text-dim);
  font-size: 11px;
}

.db-selector {
  padding: 16px;
}

.selector-head {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 10px;
}

.selector-list {
  background: var(--panel);
  border: 1px solid var(--border-soft);
  border-radius: 10px;
  padding: 8px;
}

.selector-item {
  padding: 6px 10px;
  border-radius: 6px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11.5px;
  color: var(--text-muted);
}

.selector-item.selected {
  background: rgba(10, 107, 114, 0.08);
  color: var(--accent-2);
}

.selector-hint {
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-dim);
}
</style>
