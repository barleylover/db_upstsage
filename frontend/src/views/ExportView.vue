<template>
  <div class="export-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 변경 문서</button>
        <span class="head-title">05 내보내기</span>
        <span class="badge danger">BLOCK</span>
      </div>
    </div>

    <section class="card package-card">
      <div class="section-title">패키지 구성</div>
      <table class="table">
        <thead>
          <tr>
            <th>항목</th>
            <th>상태</th>
            <th>비고</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, idx) in packageItems" :key="idx">
            <td><span class="item-name">{{ item.name }}</span></td>
            <td>
              <span class="badge" :class="item.badgeClass">{{ item.status }}</span>
            </td>
            <td class="mono">{{ item.note }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <div class="export-grid">
      <section class="card action-card">
        <div class="section-title">내려받기 / 복사</div>
        <div class="export-actions">
          <button class="btn primary" @click="downloadMarkdown">Markdown 내려받기</button>
          <button class="btn" @click="downloadJson">JSON 내려받기</button>
          <button class="btn" @click="copyAll">전체 복사</button>
        </div>
      </section>

      <section class="card preview-card">
        <div class="section-title">미리보기</div>
        <div class="preview-head">
          <span class="mono">미리보기 {{ previewLines }}줄</span>
          <span class="badge warning">BLOCK</span>
        </div>
        <div class="code-block preview-body">
          <pre>{{ preview }}</pre>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const previewLines = 114

const packageItems = ref([
  { name: '확정 Change Spec', status: '포함', badgeClass: 'ok', note: 'v1' },
  { name: '5종 SQL', status: '포함', badgeClass: 'ok', note: 'revision 2' },
  { name: '영향도·위험 분석', status: '포함', badgeClass: 'ok', note: '위험 MEDIUM' },
  { name: '테스트·검증 증거', status: '확인 필요', badgeClass: 'warning', note: '2 / 4' },
  { name: '롤백 계획', status: '확인 필요', badgeClass: 'warning', note: 'TEMPLATE_REQUIRES_BACKUP_ROWS' },
  { name: '변경관리 신청서', status: '포함', badgeClass: 'ok', note: '기본 변경 신청서' },
  { name: '최종 판정과 근거', status: '포함', badgeClass: 'danger', note: 'BLOCK' },
])

const preview = `## 변경 검토 패키지

- 대상: app.public.orders
- 조건: tenant_id = 42, status = pending
- 작업: UPDATE
- 변경값: status → cancelled

### SQL 초안 (revision 2)

\`\`\`sql
UPDATE "public"."orders"
SET "status" = 'cancelled'
WHERE "created_at" < '2026-09-01'
  AND "tenant_id" = 42;
\`\`\`

### 최종 판정

- B003 | FAIL | 확정 조건 누락
- R002 | REVIEW | 롤백 템플릿
- B001 | PASS | WHERE 존재
`

function downloadMarkdown() {
  // TODO: markdown 다운로드
}

function downloadJson() {
  // TODO: json 다운로드
}

function copyAll() {
  // TODO: 전체 복사
}
</script>

<style scoped>
.export-page {
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

.package-card {
  padding: 18px;
  margin-bottom: 18px;
}

.export-grid {
  display: grid;
  grid-template-columns: 1fr 1.6fr;
  gap: 16px;
  align-items: start;
}

.action-card {
  padding: 18px;
}

.export-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.preview-card {
  padding: 18px;
}

.preview-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  color: var(--text-dim);
}

.item-name {
  font-weight: 500;
}
</style>
