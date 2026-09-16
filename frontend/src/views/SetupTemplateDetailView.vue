<template>
  <div class="detail-page">
    <div class="page-head">
      <div class="head-left">
        <button class="btn" @click="$router.back()">← 양식 목록</button>
        <span class="head-title">{{ template?.name ?? '문서 양식 상세' }}</span>
        <span class="badge" v-if="template?.isDefault">기본 양식</span>
        <span class="mono">{{ template?.itemCount ?? 0 }}개 항목</span>
      </div>
    </div>

    <div class="detail-grid">
      <section class="preview-card card">
        <div class="section-title">문서 미리보기</div>
        <div class="preview-doc">
          <div class="preview-title">기본 변경 신청서</div>
          <div class="preview-row"><span>작성자</span><span class="mono">—</span></div>
          <div class="preview-row"><span>대상 테이블</span><span class="mono">orders</span></div>
          <div class="preview-row"><span>변경 작업</span><span class="mono">UPDATE</span></div>
          <div class="preview-row"><span>대상 조건</span><span class="mono">tenant_id = 42, status...</span></div>
          <div class="preview-row"><span>변경 값</span><span class="mono">status → cancelled</span></div>
          <div class="preview-row"><span>식별 키</span><span class="mono">id</span></div>
          <div class="preview-row"><span>예상 영향 건수</span><span class="mono">18</span></div>
          <div class="preview-row"><span>실행 SQL</span><span class="mono">UPDATE "public"...</span></div>
          <div class="preview-row"><span>롤백 계획</span><span class="mono">-- TEMPLATE ...</span></div>
          <div class="preview-row"><span>검토 판정</span><span class="mono">REVIEW</span></div>
          <div class="preview-row"><span>위험 등급</span><span class="mono">MEDIUM</span></div>
          <div class="preview-row"><span>승인자</span><span class="mono">—</span></div>
        </div>
      </section>

      <section class="edit-card card">
        <div class="section-title">항목 편집</div>
        <div class="field" style="margin-bottom: 14px;">
          <label>양식명</label>
          <input class="input" :value="template?.name" />
        </div>
        <div class="field" style="margin-bottom: 14px;">
          <span class="badge" v-if="template?.isDefault">기본 양식</span>
          <span class="mono">{{ template?.itemCount ?? 0 }}개 항목</span>
        </div>

        <table class="table">
          <thead>
            <tr>
              <th>항목명</th>
              <th>정보 출처</th>
              <th>현재 값</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in items" :key="idx">
              <td class="mono">{{ item.name }}</td>
              <td>
                <select class="input small">
                  <option>대상 테이블</option>
                  <option>변경 작업</option>
                  <option>대상 조건</option>
                  <option>실행 SQL</option>
                  <option>승인자</option>
                </select>
              </td>
              <td class="mono">{{ item.value ?? '—' }}</td>
              <td>
                <button class="btn small">삭제</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div style="margin-top: 12px;">
          <button class="btn small">+ 항목</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const store = useAppStore()

const template = store.documentTemplates.find((t) => t.id === route.params.templateId) ?? store.documentTemplates[0]

const items = ref([
  { name: '대상 테이블', source: '대상 테이블', value: 'orders' },
  { name: '변경 작업', source: '변경 작업', value: 'UPDATE' },
  { name: '대상 조건', source: '대상 조건', value: 'tenant_id = 42, status = pending' },
  { name: '실행 SQL', source: '실행 SQL', value: 'UPDATE "public"."orders" SET "status" = \'cancelled\' WHERE ...' },
  { name: '승인자', source: '승인자', value: '' },
])
</script>

<style scoped>
.detail-page {
  max-width: 1180px;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
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

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  align-items: start;
}

.preview-card,
.edit-card {
  padding: 20px;
}

.preview-doc {
  background: #fafafa;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 12.5px;
}

.preview-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--text);
}

.preview-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 3px 0;
}

.preview-row span:first-child {
  color: var(--text-muted);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 12px;
  color: var(--text-muted);
}

.table .input.small {
  max-width: 120px;
  padding: 4px 6px;
  font-size: 12px;
}
</style>
