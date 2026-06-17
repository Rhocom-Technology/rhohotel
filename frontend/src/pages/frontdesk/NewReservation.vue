<template>
  <div v-if="loadingDraft" class="flex items-center justify-center py-20 text-sm text-gray-400">Loading draft…</div>
  <NewReservationForm
    v-else
    :type="type"
    :edit-doc="draftDoc"
    @close="router.push({ name: 'Reservations' })"
    @saved="onSaved"
  />
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NewReservationForm from '@/components/reservations/NewReservationForm.vue'
import { callMethod } from '@/lib/api'

const route = useRoute()
const router = useRouter()
const type = computed(() => route.query.type || 'Individual')

const draftDoc = ref(null)
const loadingDraft = ref(false)

onMounted(async () => {
  const draftName = String(route.query.draft || '').trim()
  if (!draftName) return
  loadingDraft.value = true
  try {
    draftDoc.value = await callMethod('frappe.client.get', {
      doctype: 'Hotel Reservation',
      name: draftName,
    })
  } catch {
    // silently fall through to empty form
  } finally {
    loadingDraft.value = false
  }
})

function onSaved(doc) {
  const name = doc?.name
  if (!name) {
    router.push({ name: 'Reservations' })
    return
  }
  router.push({ name: 'SavedReservation', params: { id: name } })
}
</script>