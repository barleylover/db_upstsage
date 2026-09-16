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
  router.push('/spec/new')
}
</script>

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
