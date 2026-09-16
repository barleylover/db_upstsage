<template>
  <div class="app-layout">
    <Sidebar @new-review="handleNewReview" />
    <div class="main-wrap">
      <Topbar />
      <main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'
import Topbar from '@/components/layout/Stepper.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

function handleNewReview() {
  router.push('/home')
}
</script>

<style>
.app-layout {
  display: grid;
  grid-template-columns: 264px 1fr;
  min-height: 100vh;
}

.main-wrap {
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg);
}

.main {
  flex: 1;
  padding: 24px 32px 40px;
  overflow: auto;
}
</style>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
