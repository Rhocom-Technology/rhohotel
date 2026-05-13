<template>
  <div class="flex h-screen overflow-hidden" style="background-color: #f1f5f9;">
    <Sidebar v-if="showChrome" />
    <div class="flex flex-col flex-1 overflow-hidden">
      <TopHeader v-if="showChrome" />
      <main :class="['flex-1 overflow-y-auto', showChrome ? 'p-6' : 'p-0']">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'
import TopHeader from './TopHeader.vue'

const route = useRoute()

const showChrome = computed(() => {
  return !(route.name === 'PointOfSales' && route.query.fullscreen === '1')
})
</script>