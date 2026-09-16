<template>
  <div class="import-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 스키마 목록</button>
        <span class="head-title">새 스키마로 등록</span>
      </div>
    </div>

    <div class="import-grid">
      <section class="card">
        <div class="section-title">1. DB에서 뽑기</div>
        <div class="dbms-chips">
          <button
            class="chip"
            :class="{ active: selectedDbms === d }"
            v-for="d in supportedDbmses"
            :key="d"
            @click="selectedDbms = d"
          >
            {{ d }}
          </button>
        </div>
        <div class="code-block">
          <span class="label">{{ selectedDbms }} 기준</span>
          <pre>{{ extractExample }}</pre>
          <button class="btn small">추출 쿼리 복사</button>
          <span class="hint">psql -At -d &lt;db&gt; -f extract.sql</span>
        </div>
      </section>

      <section class="card">
        <div class="section-title">2. 붙여넣기</div>
        <div class="import-options">
          <label class="import-opt">
            <span class="opt-label">JSON 파일 선택</span>
            <input type="file" accept=".json" class="file-input" />
          </label>
          <label class="import-opt">
            <span class="opt-label">JSON 텍스트</span>
            <textarea class="textarea" rows="8" placeholder='[{ "name": "orders", ... }]'></textarea>
          </label>
        </div>

        <div class="preview">
          <div class="section-title">가져온 결과</div>
          <table class="table">
            <thead>
              <tr>
                <th>테이블</th>
                <th>컬럼</th>
                <th>기본 키</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="mono">orders</td>
                <td class="mono">2개</td>
                <td class="mono">id</td>
              </tr>
              <tr>
                <td class="mono">refunds</td>
                <td class="mono">1개</td>
                <td class="mono">id</td>
              </tr>
            </tbody>
          </table>
          <div class="preview-chip">
            <span class="mono">app.public · 2개 테이블 · 3개 컬럼</span>
          </div>
        </div>

        <div class="import-footer">
          <button class="btn primary" @click="importSchema">새 스키마로 등록</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const selectedDbms = ref('POSTGRESQL')
const supportedDbmses = store.supportedDbmses

const extractExample = `// PostgreSQL 기준\nSELECT table_name, column_name, data_type, is_nullable\nFROM information_schema.columns\nWHERE table_schema = 'public'\nORDER BY table_name, ordinal_position;`

function importSchema() {
  // TODO: 실제 스키마 등록 흐름 연결
}
</script>

<style scoped>
.import-page {
  max-width: 1200px;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
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

.import-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  align-items: start;
}

.dbms-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0 14px;
}

.chip {
  border: 1px solid var(--chip-border);
  border-radius: 8px;
  padding: 4px 10px;
  background: var(--panel);
  font-size: 12px;
  cursor: pointer;
}

.chip.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.code-block {
  background: #fafafa;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 12px 14px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text);
}

.code-block .label {
  display: block;
  color: var(--text-dim);
  margin-bottom: 6px;
  font-size: 11px;
}

.code-block pre {
  margin: 0;
  white-space: pre-wrap;
}

.code-block .hint {
  display: block;
  margin-top: 8px;
  color: var(--text-dim);
  font-size: 11px;
}

.import-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.import-opt {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.opt-label {
  font-size: 12px;
  color: var(--text-muted);
}

.file-input {
  font-size: 12px;
  color: var(--text-muted);
}

.preview-chip {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-dim);
}

.import-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
