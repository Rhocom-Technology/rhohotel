<template>
  <div class="flex h-screen overflow-hidden" style="background-color: #f1f5f9;">
    <Sidebar />
    <div class="flex flex-col flex-1 overflow-hidden">
      <TopHeader />
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import TopHeader from './TopHeader.vue'
</script>