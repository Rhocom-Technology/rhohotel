<template>
  <div class="flex h-screen overflow-hidden" style="background-color: #f1f5f9;">
    <Sidebar v-if="showChrome" />
    <div class="flex flex-col flex-1 overflow-hidden">
      <TopHeader v-if="showChrome" />
      <main :class="['flex-1 overflow-y-auto', showChrome ? 'p-6' : 'p-0']">
        <router-view />
      </main>
    </div>
    <AIChatbot v-if="showChrome" />

    <!-- Room Upgrade Toast Notification -->
    <Transition name="toast-slide">
      <div v-if="upgradeToast.show"
        class="fixed bottom-6 right-6 z-50 max-w-sm w-full bg-white rounded-2xl shadow-2xl border border-emerald-200 overflow-hidden"
        style="min-width:320px;">
        <div class="bg-emerald-600 px-4 py-2 flex items-center justify-between">
          <p class="text-xs font-bold text-white tracking-wide">ROOM UPGRADE — ACTION REQUIRED</p>
          <button @click="dismissToast" class="text-emerald-100 hover:text-white text-sm leading-none">✕</button>
        </div>
        <div class="px-4 py-4">
          <p class="text-sm font-semibold text-gray-900 mb-1">{{ upgradeToast.guest }}</p>
          <p class="text-xs text-gray-600">
            Move from <span class="font-bold text-gray-800">Room {{ upgradeToast.old_room }}</span>
            → <span class="font-bold text-emerald-700">Room {{ upgradeToast.new_room }}</span>
          </p>
          <p v-if="upgradeToast.waiver > 0" class="text-xs text-gray-500 mt-1">
            Rate waiver: ₦{{ Number(upgradeToast.waiver).toLocaleString() }}
          </p>
          <div class="flex gap-2 mt-3">
            <button @click="goToRoomView" class="flex-1 px-3 py-1.5 text-xs font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700">
              Go to Room View
            </button>
            <button @click="dismissToast" class="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Sidebar from './Sidebar.vue'
import TopHeader from './TopHeader.vue'
import AIChatbot from '@/components/ai/AIChatbot.vue'
import { socket } from '@/lib/socket'

const route = useRoute()
const router = useRouter()

const showChrome = computed(() => {
  return !(route.name === 'PointOfSales' && route.query.fullscreen === '1')
})

// ── Room Upgrade Toast ───────────────────────────────────────────────────────
const upgradeToast = ref({ show: false, guest: '', old_room: '', new_room: '', waiver: 0 })
let toastTimer = null

function showUpgradeToast(data) {
  if (toastTimer) clearTimeout(toastTimer)
  upgradeToast.value = {
    show: true,
    guest: data.guest || 'Guest',
    old_room: data.old_room || '?',
    new_room: data.new_room || '?',
    waiver: data.waiver || 0,
  }
  toastTimer = setTimeout(dismissToast, 30000)
}

function dismissToast() {
  upgradeToast.value.show = false
  if (toastTimer) { clearTimeout(toastTimer); toastTimer = null }
}

function goToRoomView() {
  dismissToast()
  router.push('/room-view')
}

onMounted(() => {
  if (socket) socket.on('rhohotel_room_upgrade', showUpgradeToast)
})

onUnmounted(() => {
  if (socket) socket.off('rhohotel_room_upgrade', showUpgradeToast)
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<style scoped>
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.3s ease;
}
.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translateY(16px);
}
</style>