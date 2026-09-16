<template>
  <div class="settings-page">
    <div class="page-head">
      <div class="head-left">
        <span class="head-title">설정</span>
      </div>
      <div class="head-right">
        <button class="btn small">기본값으로</button>
      </div>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: true }">SQL 편집기 · 토크나이저</button>
    </div>

    <div class="settings-grid">
      <section class="card">
        <div class="section-title">미리보기</div>
        <div class="code-block">
          <pre>{{ previewSql }}</pre>
        </div>
      </section>

      <section class="card">
        <div class="section-title">토큰 색상</div>
        <div class="token-grid">
          <div class="token-item"><span class="token-dot keyword"></span> 키워드 .kw</div>
          <div class="token-item"><span class="token-dot string"></span> 문자열 .str</div>
          <div class="token-item"><span class="token-dot number"></span> 숫자 .num</div>
          <div class="token-item"><span class="token-dot identifier"></span> 식별자 ".id</div>
          <div class="token-item"><span class="token-dot comment"></span> 주석 .com</div>
          <div class="token-item"><span class="token-dot ph"></span> 자리표시자 .ph</div>
          <div class="token-item"><span class="token-dot fn"></span> 함수 .fn</div>
        </div>
      </section>

      <section class="card">
        <div class="section-title">편집 동작</div>
        <div class="field">
          <label>탭 크기</label>
          <select class="input" v-model="tabSize">
            <option>2칸</option>
            <option :selected="true">4칸</option>
            <option>8칸</option>
          </select>
        </div>
        <div class="toggle-list">
          <label class="check"><input type="checkbox" v-model="lintOnType" /> 실시간 문법 검사</label>
          <label class="check"><input type="checkbox" v-model="autoComplete" /> 자동완성</label>
          <label class="check"><input type="checkbox" v-model="autoIndent" /> 자동 들여쓰기</label>
        </div>
      </section>

      <section class="card">
        <div class="section-title">검사 규칙</div>
        <div class="rule-list">
          <div class="rule-item"><span class="rule-status warn">⚠</span> 닫히지 않은 따옴표</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> 괄호 짝</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> 쉼표 뒤 빈 항목</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> ==, != 같은 잘못된 연산자</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> 지원하지 않는 문장</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> SET절 형식</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> WHERE절 없음</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> 세미콜론 누락</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> 자리표시자 잔존</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> 스키마에 없는 식별자</div>
          <div class="rule-item"><span class="rule-status warn">⚠</span> 쓸 수 없는 문자</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const tabSize = ref(4)
const lintOnType = ref(true)
const autoComplete = ref(true)
const autoIndent = ref(true)

const previewSql = [
  `UPDATE "public"."orders"`,
  `SET "status" = 'cancelled'`,
  `WHERE "tenant_id" = 42 AND`,
  `"created_at" < '2026-09-01'`,
  `AND __id__ IS NOT NULL;`,
].join('\n')
</script>

<style scoped>
.settings-page {
  max-width: 1180px;
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

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border-soft);
  margin-bottom: 18px;
}

.tab {
  padding: 8px 12px;
  border-radius: 6px 6px 0 0;
  font-size: 13px;
  color: var(--text-muted);
  background: var(--panel);
  border-bottom: 2px solid transparent;
  border: none;
  cursor: pointer;
}

.tab.active {
  color: var(--text);
  border-bottom-color: var(--accent);
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.token-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.token-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.token-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  display: inline-block;
}

.token-dot.keyword { background: #0a6b72; }
.token-dot.string { background: #5a8a3a; }
.token-dot.number { background: #b06a00; }
.token-dot.identifier { background: #6b6b6b; }
.token-dot.comment { background: #999999; }
.token-dot.ph { background: #b00020; }
.token-dot.fn { background: #141414; }

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.field label {
  font-size: 12px;
  color: var(--text-muted);
}

.toggle-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  cursor: pointer;
  user-select: none;
}

.rule-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: var(--text-muted);
}

.rule-status {
  font-size: 14px;
  color: var(--warning);
}
</style>
