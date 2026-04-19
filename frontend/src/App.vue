<template>
  <div>
    <AppLayout v-if="session.isLoggedIn" />
    <router-view v-else />
  </div>
</template>

<script setup>
import AppLayout from '@/components/layout/AppLayout.vue'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
</script>