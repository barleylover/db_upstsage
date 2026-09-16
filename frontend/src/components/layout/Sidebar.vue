<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="brand-mark"></span>
      <span class="brand-text">ChangeSpec</span>
    </div>
    <nav class="sidebar-nav">
      <button class="sidebar-btn" @click="$emit('newReview')">
        <span class="plus">+</span> 새 검토
      </button>
      <button class="sidebar-btn" @click="$router.push('/setup/schemas')">스키마</button>
      <button class="sidebar-btn" @click="$router.push('/setup/templates')">양식</button>
    </nav>
    <div class="sidebar-tools">
      <div class="tool-group-label mono">검색 필터 정렬</div>
      <div class="tool-row"><span>북마크</span></div>
      <div class="tool-row"><span>폴더</span> +</div>
      <div class="tool-row"><span>최근 대화 내역</span></div>
      <div class="tool-row"><span>오늘</span></div>
      <div class="tool-row"><span>어제</span></div>
    </div>
    <div class="sidebar-footer">
      <span class="mono">설정   ·   SQL 편집기 · 토크나이저</span>
    </div>
  </aside>
</template>

<script setup lang="ts">
defineEmits<{ newReview: [] }>()
</script>
