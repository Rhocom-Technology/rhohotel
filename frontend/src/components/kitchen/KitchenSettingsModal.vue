<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
      style="background:rgba(15,23,42,0.6);backdrop-filter:blur(4px);"
      @click.self="$emit('close')">
      <div class="bg-white rounded-2xl w-full shadow-2xl overflow-hidden flex flex-col" style="max-width:1000px;max-height:92vh;">

        <!-- Header -->
        <div class="px-8 pt-8 pb-6 border-b border-gray-100">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">Kitchen Settings</h2>
              <p class="text-xs text-gray-400 mt-1">Configure kitchen stations, ticket flow, preparation timers, alert rules, and display behavior for the kitchen terminal.</p>
            </div>
            <div class="flex items-center gap-2 ml-4 flex-shrink-0">
              <button class="px-4 py-2 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                @click="$emit('close')">Close</button>
              <button class="px-4 py-2 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                @click="saveSettings">Save</button>
            </div>
          </div>
          <p v-if="savedMessage" class="mt-4 text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">{{ savedMessage }}</p>
        </div>

        <div class="overflow-y-auto flex-1 px-8 py-6">
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:32px;">

            <!-- Left: Kitchen Configuration -->
            <div class="space-y-6">
              <h3 class="text-sm font-bold text-gray-900">Kitchen Configuration</h3>

              <!-- Primary Station + Mode -->
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Primary Kitchen Station</p>
                  <select v-model="station" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                    <option>Hot Kitchen</option>
                    <option>Cold Kitchen</option>
                    <option>Bar Snacks</option>
                  </select>
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-700 mb-1.5">Kitchen Mode</p>
                  <div class="px-4 py-2.5 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-200 rounded-lg text-center">
                    Live Display Board
                  </div>
                </div>
              </div>

              <!-- Ticket Routing -->
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-2">Ticket Routing</p>
                <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
                  <label v-for="r in routing" :key="r" class="flex items-center gap-2.5 cursor-pointer">
                    <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
                    <span class="text-xs text-gray-700">{{ r }}</span>
                  </label>
                </div>
              </div>

              <!-- Preparation SLA Timers -->
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-2">Preparation SLA Timers</p>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;">
                  <label class="bg-white rounded-xl border border-gray-200 px-4 py-3 text-xs text-gray-700 font-medium">
                    <span class="block text-gray-500 mb-1">New Ticket</span>
                    <input v-model.number="newTicketMinutes" type="number" min="1" class="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs" />
                  </label>
                  <label class="bg-white rounded-xl border border-gray-200 px-4 py-3 text-xs text-gray-700 font-medium">
                    <span class="block text-gray-500 mb-1">Preparation</span>
                    <input v-model.number="preparationMinutes" type="number" min="1" class="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs" />
                  </label>
                  <label class="bg-white rounded-xl border border-gray-200 px-4 py-3 text-xs text-gray-700 font-medium">
                    <span class="block text-gray-500 mb-1">Warning</span>
                    <input v-model.number="warningMinutes" type="number" min="1" class="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs" />
                  </label>
                  <label class="bg-white rounded-xl border border-gray-200 px-4 py-3 text-xs text-gray-700 font-medium">
                    <span class="block text-gray-500 mb-1">Critical</span>
                    <input v-model.number="criticalMinutes" type="number" min="1" class="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs" />
                  </label>
                  <label class="bg-white rounded-xl border border-gray-200 px-4 py-3 text-xs text-gray-700 font-medium">
                    <span class="block text-gray-500 mb-1">Ready Pickup</span>
                    <input v-model.number="readyPickupMinutes" type="number" min="1" class="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs" />
                  </label>
                </div>
                <p class="text-[11px] text-gray-400 mt-2">New, prep, and pickup countdowns use these timers. Tickets are marked delayed after the critical timer.</p>
              </div>

              <!-- Ticket Actions -->
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-2">Ticket Actions</p>
                <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
                  <label v-for="a in ticketActions" :key="a" class="flex items-center gap-2.5 cursor-pointer">
                    <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
                    <span class="text-xs text-gray-700">{{ a }}</span>
                  </label>
                </div>
              </div>

              <!-- Kitchen Note -->
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-1.5">Kitchen Note / Footer Message</p>
                <textarea v-model="kitchenNote"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows="4"
                  placeholder="Enter kitchen-wide operational note, service reminder, or chef instruction..."></textarea>
              </div>
            </div>

            <!-- Right: Display Options -->
            <div class="space-y-6">
              <h3 class="text-sm font-bold text-gray-900">Display Options</h3>

              <!-- Auto Refresh -->
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-1.5">Auto Refresh</p>
                <input v-model.number="autoRefreshSeconds" type="number" min="5"
                  class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600" />
              </div>

              <!-- Default Ticket View -->
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-1.5">Default Ticket View</p>
                <select v-model="ticketView" class="w-full px-3 py-2.5 text-xs border border-gray-200 rounded-lg focus:outline-none text-gray-600">
                  <option>All Tickets</option>
                  <option>New Only</option>
                  <option>Preparing Only</option>
                  <option>Delayed Only</option>
                </select>
              </div>

              <!-- Color Alerts -->
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-2">Color Alerts</p>
                <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
                  <label v-for="a in colorAlerts" :key="a" class="flex items-center gap-2.5 cursor-pointer">
                    <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
                    <span class="text-xs text-gray-700">{{ a }}</span>
                  </label>
                </div>
              </div>

              <!-- Sound / Notification -->
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-2">Sound / Notification</p>
                <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2.5">
                  <div v-for="s in sounds" :key="s.label" class="flex items-center gap-2.5">
                    <input type="checkbox" checked class="accent-blue-600 w-3.5 h-3.5" />
                    <span class="text-xs text-gray-700 flex-1">{{ s.label }}</span>
                    <span class="text-xs font-semibold text-gray-900">{{ s.status }}</span>
                  </div>
                </div>
              </div>

              <!-- Station Assignment -->
              <div>
                <p class="text-xs font-semibold text-gray-700 mb-2">Station Assignment</p>
                <div class="bg-white rounded-xl border border-gray-200 px-4 py-3 space-y-2">
                  <div v-for="s in stationAssignment" :key="s.name" class="flex items-center justify-between text-xs">
                    <span class="text-gray-600">{{ s.name }}</span>
                    <span class="font-bold text-gray-900">{{ s.pct }}</span>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  settings: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close', 'save'])

const station = ref(props.settings.station || 'Hot Kitchen')
const ticketView = ref(props.settings.ticketView || 'All Tickets')
const kitchenNote = ref(props.settings.kitchenNote || '')
const newTicketMinutes = ref(Number(props.settings.newTicketMinutes || 5))
const preparationMinutes = ref(Number(props.settings.preparationMinutes || props.settings.criticalMinutes || 25))
const warningMinutes = ref(Number(props.settings.warningMinutes || 15))
const criticalMinutes = ref(Number(props.settings.criticalMinutes || 25))
const readyPickupMinutes = ref(Number(props.settings.readyPickupMinutes || 10))
const autoRefreshSeconds = ref(Number(props.settings.autoRefreshSeconds || 15))
const savedMessage = ref('')

const routing = ['Restaurant dining orders', 'Room service orders', 'Takeaway / pickup orders']
const ticketActions = ['Allow mark ready from kitchen board', 'Allow dispatch confirmation', 'Require delay reason before escalation']
const colorAlerts = ['Highlight new tickets', 'Show warning timer color', 'Show delayed ticket alert']
const sounds = [
  { label: 'New order tone', status: 'Enabled' },
  { label: 'Delay alert tone', status: 'Enabled' },
]
const stationAssignment = [
  { name: 'Hot kitchen queue', pct: '82%' },
  { name: 'Cold kitchen queue', pct: '18%' },
]

function saveSettings() {
  const nextSettings = {
    station: station.value,
    ticketView: ticketView.value,
    kitchenNote: kitchenNote.value,
    newTicketMinutes: Math.max(1, Number(newTicketMinutes.value || 5)),
    preparationMinutes: Math.max(1, Number(preparationMinutes.value || 25)),
    warningMinutes: Math.max(1, Number(warningMinutes.value || 15)),
    criticalMinutes: Math.max(1, Number(criticalMinutes.value || 25)),
    readyPickupMinutes: Math.max(1, Number(readyPickupMinutes.value || 10)),
    autoRefreshSeconds: Math.max(5, Number(autoRefreshSeconds.value || 15)),
  }
  emit('save', nextSettings)
  savedMessage.value = 'Kitchen settings saved.'
  setTimeout(() => {
    savedMessage.value = ''
    emit('close')
  }, 700)
}
</script>