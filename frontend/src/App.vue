<template>
  <div>
    <div v-if="!session.initialized" class="min-h-screen flex items-center justify-center text-sm text-gray-500">
      Loading session...
    </div>
    <AppLayout v-else-if="session.isLoggedIn" />
    <router-view v-else />
  </div>
</template>

<script setup>
import AppLayout from '@/components/layout/AppLayout.vue'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
</script>