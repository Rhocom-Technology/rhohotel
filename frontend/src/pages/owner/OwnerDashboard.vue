<template>
  <div class="space-y-5">
    <div class="bg-white border border-gray-200 rounded-lg px-4 py-4 sm:px-5">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold text-gray-500">Finance period</p>
          <p class="mt-1 text-sm font-bold text-gray-900">{{ fmtDate(fromDate) }} to {{ fmtDate(toDate) }}</p>
        </div>
        <div class="flex flex-col gap-2 sm:flex-row sm:items-end">
          <label class="text-xs font-medium text-gray-500">
            Period
            <select v-model="selectedPeriod" class="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:w-40" @change="applyPeriodPreset(selectedPeriod)">
              <option v-for="option in periodPresets" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
          </label>
          <label class="text-xs font-medium text-gray-500">
            From
            <input v-model="fromDate" type="date" class="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:w-auto" />
          </label>
          <label class="text-xs font-medium text-gray-500">
            To
            <input v-model="toDate" type="date" class="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:w-auto" />
          </label>
          <button
            type="button"
            class="inline-flex items-center justify-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
            @click="resetDates"
          >
            <RotateCcw class="h-3.5 w-3.5" />
            Reset
          </button>
          <button
            type="button"
            class="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-700"
            @click="load"
          >
            <RefreshCcw class="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center rounded-lg border border-gray-200 bg-white py-14 text-xs text-gray-400">
      Loading owner dashboard...
    </div>

    <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 px-5 py-4 text-xs text-red-600">
      {{ error }}
      <button type="button" class="ml-3 font-semibold underline" @click="load">Retry</button>
    </div>

    <template v-else>
      <div v-if="sectionErrors.length" class="rounded-lg border border-amber-200 bg-amber-50 px-5 py-3 text-xs text-amber-700">
        Some dashboard sections could not be loaded. Available sections are shown below.
      </div>

      <AIInsightPanel
        v-if="aiContext"
        title="AI Owner Finance Summary"
        context-type="owner_finance_dashboard_summary"
        :context-data="aiContext"
        :auto-load="false"
        panel-id="owner-dashboard"
      />

      <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
        <div class="rounded-lg bg-slate-900 px-5 py-4 text-white xl:col-span-2">
          <div class="flex items-center justify-between gap-3">
            <p class="text-xs text-slate-300">Period Revenue</p>
            <span class="rounded-md bg-white/10 px-2 py-1 text-xs font-semibold text-slate-200">Finance</span>
          </div>
          <p class="mt-3 text-3xl font-bold">{{ money(finance.period_invoiced) }}</p>
          <div class="mt-4 grid grid-cols-2 gap-3 border-t border-white/10 pt-3">
            <div>
              <p class="text-xs text-slate-400">Collected</p>
              <p class="text-sm font-bold text-emerald-300">{{ money(finance.period_collected) }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400">Outstanding</p>
              <p class="text-sm font-bold text-amber-300">{{ money(finance.period_outstanding) }}</p>
            </div>
          </div>
        </div>

        <StatCard label="Total Outstanding" :value="money(finance.total_outstanding)" tone="red" />
        <StatCard label="Overdue AR" :value="money(finance.total_overdue)" tone="orange" />
        <StatCard label="Collection Rate" :value="`${finance.collection_rate || 0}%`" tone="green" />
      </div>

      <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Accounting Revenue" :value="money(profitability.accounting_revenue)" tone="green" />
        <StatCard label="Operating Expenses" :value="money(profitability.operating_expenses)" tone="orange" />
        <StatCard label="Net Profit" :value="money(profitability.net_profit)" :tone="Number(profitability.net_profit || 0) < 0 ? 'red' : 'green'" />
        <StatCard label="Profit Margin" :value="`${profitability.profit_margin || 0}%`" :tone="Number(profitability.profit_margin || 0) < 15 ? 'orange' : 'green'" />
      </div>

      <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4 md:col-span-2">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 class="text-sm font-bold text-gray-900">Profitability Breakdown</h3>
              <p class="text-xs text-gray-400">{{ profitability.basis }}</p>
            </div>
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              @click="$router.push('/reports')"
            >
              <FileText class="h-3.5 w-3.5" />
              Reports
            </button>
          </div>
          <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div>
              <p class="mb-2 text-xs font-semibold text-gray-500">Top income accounts</p>
              <div v-if="profitability.income_accounts?.length === 0" class="rounded-lg bg-gray-50 px-4 py-8 text-center text-xs text-gray-400">No income account postings found.</div>
              <div v-else class="space-y-2">
                <div v-for="row in profitability.income_accounts" :key="row.account" class="flex items-center justify-between rounded-lg bg-emerald-50 px-3 py-2">
                  <span class="truncate pr-3 text-xs font-semibold text-gray-700">{{ row.account }}</span>
                  <span class="text-xs font-bold text-emerald-700">{{ money(row.amount) }}</span>
                </div>
              </div>
            </div>
            <div>
              <p class="mb-2 text-xs font-semibold text-gray-500">Top expense accounts</p>
              <div v-if="profitability.expense_accounts?.length === 0" class="rounded-lg bg-gray-50 px-4 py-8 text-center text-xs text-gray-400">No expense account postings found.</div>
              <div v-else class="space-y-2">
                <div v-for="row in profitability.expense_accounts" :key="row.account" class="flex items-center justify-between rounded-lg bg-amber-50 px-3 py-2">
                  <span class="truncate pr-3 text-xs font-semibold text-gray-700">{{ row.account }}</span>
                  <span class="text-xs font-bold text-amber-700">{{ money(row.amount) }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900">Cost Signals</h3>
          <div class="mt-4 space-y-3">
            <MiniStat label="Payroll" :value="money(costSignals.payroll)" />
            <MiniStat label="Utilities" :value="money(costSignals.utilities)" />
            <MiniStat label="Maintenance" :value="money(costSignals.maintenance)" />
            <MiniStat label="Housekeeping" :value="money(costSignals.housekeeping)" />
            <MiniStat label="F&B Cost" :value="money(costSignals.fnb_cost)" />
          </div>
        </section>
      </div>

      <div class="grid grid-cols-1 gap-3 xl:grid-cols-3">
        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4 xl:col-span-2">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 class="text-sm font-bold text-gray-900">Revenue Mix</h3>
              <p class="text-xs text-gray-400">Rooms, POS, halls, and other invoiced revenue</p>
            </div>
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-lg border border-blue-200 px-3 py-2 text-xs font-semibold text-blue-600 hover:bg-blue-50"
              @click="$router.push('/billing')"
            >
              <ExternalLink class="h-3.5 w-3.5" />
              Billing
            </button>
          </div>
          <div v-if="revenueMix.length === 0" class="py-10 text-center text-xs text-gray-400">No revenue found in this period.</div>
          <div v-else class="space-y-3">
            <div v-for="row in revenueMix" :key="row.category">
              <div class="mb-1 flex items-center justify-between gap-3">
                <span class="text-xs font-semibold text-gray-700">{{ row.category }}</span>
                <span class="text-xs font-bold text-gray-900">{{ money(row.amount) }} · {{ row.share }}%</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-gray-100">
                <div class="h-full rounded-full bg-blue-500" :style="{ width: `${Math.min(100, row.share || 0)}%` }"></div>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900">Occupancy Economics</h3>
          <div class="mt-4 grid grid-cols-2 gap-3">
            <MiniStat label="Occupancy" :value="`${occupancy.occupancy_rate || 0}%`" />
            <MiniStat label="Room Nights" :value="number(occupancy.room_nights)" />
            <MiniStat label="ADR" :value="money(occupancy.adr)" />
            <MiniStat label="RevPAR" :value="money(occupancy.revpar)" />
          </div>
          <div class="mt-4 grid grid-cols-3 gap-2 border-t border-gray-100 pt-4">
            <MiniStat label="Occupied" :value="number(occupancy.occupied)" compact />
            <MiniStat label="Vacant" :value="number(occupancy.vacant)" compact />
            <MiniStat label="Blocked" :value="number(occupancy.maintenance)" compact />
          </div>
        </section>
      </div>

      <div class="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-4">
        <StatCard label="POS Sales" :value="money(cashControl.pos_sales)" tone="blue" />
        <StatCard label="Open POS Drafts" :value="number(cashControl.open_drafts)" tone="orange" />
        <StatCard label="Active Terminals" :value="number(cashControl.active_terminals)" tone="green" />
        <StatCard label="Shift Differences" :value="money(cashControl.shift_differences)" tone="red" />
      </div>

      <div class="grid grid-cols-1 gap-3 xl:grid-cols-3">
        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900">Cashflow</h3>
          <div class="mt-4 grid grid-cols-3 gap-2">
            <MiniStat label="Cash In" :value="money(cashflow.cash_in)" compact />
            <MiniStat label="Cash Out" :value="money(cashflow.cash_out)" compact />
            <MiniStat label="Net" :value="money(cashflow.net_cashflow)" compact />
          </div>
          <div class="mt-4 overflow-hidden rounded-lg border border-gray-100">
            <table class="w-full">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500">Mode</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Net</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-if="cashflow.payment_modes?.length === 0">
                  <td colspan="2" class="px-3 py-6 text-center text-xs text-gray-400">No payment entries found.</td>
                </tr>
                <tr v-for="row in cashflow.payment_modes" :key="row.mode">
                  <td class="px-3 py-2 text-xs font-semibold text-gray-700">{{ row.mode }}</td>
                  <td class="px-3 py-2 text-right text-xs font-bold text-gray-900">{{ money(row.net) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4 xl:col-span-2">
          <h3 class="text-sm font-bold text-gray-900">Channel Performance</h3>
          <div class="mt-4 overflow-hidden rounded-lg border border-gray-100">
            <table class="w-full">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500">Channel</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Bookings</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Nights</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Net Revenue</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Commission</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-if="channelPerformance.length === 0">
                  <td colspan="5" class="px-3 py-8 text-center text-xs text-gray-400">No channel data found.</td>
                </tr>
                <tr v-for="row in channelPerformance" :key="row.channel">
                  <td class="px-3 py-2 text-xs font-semibold text-gray-700">{{ row.channel }}</td>
                  <td class="px-3 py-2 text-right text-xs text-gray-600">{{ number(row.bookings) }}</td>
                  <td class="px-3 py-2 text-right text-xs text-gray-600">{{ number(row.room_nights) }}</td>
                  <td class="px-3 py-2 text-right text-xs font-bold text-gray-900">{{ money(row.net_revenue) }}</td>
                  <td class="px-3 py-2 text-right text-xs text-amber-600">{{ money(row.commission) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section class="rounded-lg border border-gray-200 bg-white px-5 py-4">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 class="text-sm font-bold text-gray-900">Hall Bookings</h3>
            <p class="text-xs text-gray-400">Events, hall revenue, and unpaid hall booking exposure</p>
          </div>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
            @click="$router.push('/hall/booking')"
          >
            <ExternalLink class="h-3.5 w-3.5" />
            Halls
          </button>
        </div>
        <div class="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">
          <MiniStat label="Bookings" :value="number(hallBookings.total_bookings)" />
          <MiniStat label="Scheduled" :value="number(hallBookings.scheduled)" />
          <MiniStat label="Completed" :value="number(hallBookings.completed)" />
          <MiniStat label="Cancelled" :value="number(hallBookings.cancelled)" />
          <MiniStat label="Revenue" :value="money(hallBookings.revenue)" />
          <MiniStat label="Unpaid" :value="money(hallBookings.unpaid_amount)" />
        </div>
        <div class="mt-4 overflow-hidden rounded-lg border border-gray-100">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500">Event</th>
                <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500">Hall</th>
                <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500">Date</th>
                <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Amount</th>
                <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-if="hallBookings.events?.length === 0">
                <td colspan="5" class="px-3 py-8 text-center text-xs text-gray-400">No hall bookings found in this period.</td>
              </tr>
              <tr v-for="event in hallBookings.events" :key="event.name">
                <td class="px-3 py-2">
                  <p class="text-xs font-semibold text-gray-700">{{ event.event_type || 'Event' }}</p>
                  <p class="text-xs text-gray-400">{{ event.customer_name || 'No customer' }}</p>
                </td>
                <td class="px-3 py-2 text-xs text-gray-600">{{ event.hall || '-' }}</td>
                <td class="px-3 py-2 text-xs text-gray-600">{{ shortDate(event.start_datetime) }}</td>
                <td class="px-3 py-2 text-right text-xs font-bold text-gray-900">{{ money(event.amount) }}</td>
                <td class="px-3 py-2 text-xs text-gray-600">{{ event.event_status || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div class="grid grid-cols-1 gap-3 xl:grid-cols-2">
        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900">Room Type Performance</h3>
          <div class="mt-4 overflow-hidden rounded-lg border border-gray-100">
            <table class="w-full">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500">Room Type</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Stays</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Nights</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">ADR</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-if="roomTypePerformance.length === 0">
                  <td colspan="4" class="px-3 py-8 text-center text-xs text-gray-400">No room type data found.</td>
                </tr>
                <tr v-for="row in roomTypePerformance" :key="row.room_type">
                  <td class="px-3 py-2 text-xs font-semibold text-gray-700">{{ row.room_type }}</td>
                  <td class="px-3 py-2 text-right text-xs text-gray-600">{{ number(row.stays) }}</td>
                  <td class="px-3 py-2 text-right text-xs text-gray-600">{{ number(row.room_nights) }}</td>
                  <td class="px-3 py-2 text-right text-xs font-bold text-gray-900">{{ money(row.adr) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900">Corporate Account Risk</h3>
          <div class="mt-4 overflow-hidden rounded-lg border border-gray-100">
            <table class="w-full">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500">Customer</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Invoices</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Outstanding</th>
                  <th class="px-3 py-2 text-right text-xs font-semibold text-gray-500">Overdue</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-if="corporateRisk.length === 0">
                  <td colspan="4" class="px-3 py-8 text-center text-xs text-gray-400">No corporate debtor exposure found.</td>
                </tr>
                <tr v-for="row in corporateRisk" :key="row.customer">
                  <td class="px-3 py-2 text-xs font-semibold text-gray-700">{{ row.customer }}</td>
                  <td class="px-3 py-2 text-right text-xs text-gray-600">{{ number(row.invoice_count) }}</td>
                  <td class="px-3 py-2 text-right text-xs font-bold text-gray-900">{{ money(row.outstanding) }}</td>
                  <td class="px-3 py-2 text-right text-xs font-bold text-red-600">{{ money(row.overdue) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <div class="grid grid-cols-1 gap-3 xl:grid-cols-3">
        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4">
          <h3 class="text-sm font-bold text-gray-900">Operational Pulse</h3>
          <div class="mt-4 space-y-3">
            <PulseRow label="Arrivals" :value="operations.arrivals" route="/reservations" />
            <PulseRow label="Departures" :value="operations.departures" route="/check-outs" />
            <PulseRow label="Overdue checkouts" :value="operations.overdue_checkouts" route="/check-outs/overdue" warning />
            <PulseRow label="Unpaid folios" :value="operations.unpaid_folios" route="/room-view" warning />
            <PulseRow label="Housekeeping attention" :value="operations.housekeeping_attention" route="/housekeeping/dashboard" />
            <PulseRow label="Maintenance attention" :value="operations.maintenance_attention" route="/maintenance/dashboard" />
          </div>
        </section>

        <section class="rounded-lg border border-gray-200 bg-white px-5 py-4 xl:col-span-2">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 class="text-sm font-bold text-gray-900">Executive Watchlist</h3>
              <p class="text-xs text-gray-400">Finance and sellable-inventory exceptions</p>
            </div>
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              @click="$router.push('/reports')"
            >
              <FileText class="h-3.5 w-3.5" />
              Reports
            </button>
          </div>
          <div class="overflow-hidden rounded-lg border border-gray-100">
            <table class="w-full">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500">Item</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500">Severity</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold text-gray-500">Value</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="item in watchlist" :key="item.title" class="hover:bg-gray-50">
                  <td class="px-4 py-3">
                    <button class="text-left" type="button" @click="$router.push(item.route)">
                      <p class="text-xs font-bold text-gray-900">{{ item.title }}</p>
                      <p class="mt-0.5 text-xs text-gray-400">{{ item.detail }}</p>
                    </button>
                  </td>
                  <td class="px-4 py-3">
                    <span class="rounded-md px-2 py-1 text-xs font-semibold" :class="severityClass(item.severity)">
                      {{ item.severity }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right text-xs font-bold text-gray-900">{{ displayWatchValue(item) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section class="rounded-lg border border-gray-200 bg-white px-5 py-4">
        <h3 class="text-sm font-bold text-gray-900">Revenue Trend</h3>
        <div v-if="trends.length === 0" class="py-10 text-center text-xs text-gray-400">No trend data found in this period.</div>
        <div v-else class="mt-4 flex h-40 items-end gap-2">
          <div v-for="row in trends" :key="row.date" class="flex min-w-0 flex-1 flex-col items-center gap-2">
            <div class="w-full rounded-t-md bg-emerald-500" :style="{ height: `${trendHeight(row.revenue)}%` }"></div>
            <p class="w-full truncate text-center text-xs text-gray-400">{{ shortDate(row.date) }}</p>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ExternalLink, FileText, RefreshCcw, RotateCcw } from 'lucide-vue-next'
import { callMethod } from '@/lib/api'
import AIInsightPanel from '@/components/ai/AIInsightPanel.vue'

const router = useRouter()

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

const periodPresets = [
  { label: 'Today', value: 'today' },
  { label: 'Yesterday', value: 'yesterday' },
  { label: 'This Week', value: 'this_week' },
  { label: 'Last Week', value: 'last_week' },
  { label: 'This Month', value: 'this_month' },
  { label: 'Last Month', value: 'last_month' },
  { label: 'This Quarter', value: 'this_quarter' },
  { label: 'Last Quarter', value: 'last_quarter' },
  { label: 'This Year', value: 'this_year' },
  { label: 'Last Year', value: 'last_year' },
  { label: 'Custom', value: 'custom' },
]

const fromDate = ref(todayISO())
const toDate = ref(todayISO())
const selectedPeriod = ref('today')
const loading = ref(false)
const error = ref('')
const data = ref({})

const finance = computed(() => data.value.finance || {})
const profitability = computed(() => data.value.profitability || {})
const costSignals = computed(() => profitability.value.cost_signals || {})
const cashflow = computed(() => data.value.cashflow || {})
const revenueMix = computed(() => data.value.revenue_mix || [])
const channelPerformance = computed(() => data.value.channel_performance || [])
const roomTypePerformance = computed(() => data.value.room_type_performance || [])
const hallBookings = computed(() => data.value.hall_bookings || {})
const corporateRisk = computed(() => data.value.corporate_risk || [])
const occupancy = computed(() => data.value.occupancy || {})
const cashControl = computed(() => data.value.cash_control || {})
const operations = computed(() => data.value.operations || {})
const trends = computed(() => data.value.trends || [])
const watchlist = computed(() => data.value.watchlist || [])
const sectionErrors = computed(() => data.value.section_errors || [])

const maxTrendRevenue = computed(() => Math.max(...trends.value.map((row) => Number(row.revenue || 0)), 1))

const aiContext = computed(() => {
  if (!data.value.finance) return null
  return {
    date_range: `${fromDate.value} to ${toDate.value}`,
    finance: finance.value,
    profitability: profitability.value,
    cashflow: cashflow.value,
    revenue_mix: revenueMix.value,
    channel_performance: channelPerformance.value,
    room_type_performance: roomTypePerformance.value,
    hall_bookings: hallBookings.value,
    corporate_risk: corporateRisk.value,
    occupancy: occupancy.value,
    cash_control: cashControl.value,
    operations: operations.value,
    watchlist: watchlist.value.slice(0, 6),
  }
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await callMethod('rhohotel.rhocom_hotel.api.owner_dashboard.get_owner_dashboard_data', {
      from_date: fromDate.value,
      to_date: toDate.value,
    })
  } catch (err) {
    error.value = err?.message || 'Failed to load owner dashboard.'
  } finally {
    loading.value = false
  }
}

function toISO(date) {
  const copy = new Date(date)
  copy.setHours(12, 0, 0, 0)
  return copy.toISOString().slice(0, 10)
}

function startOfWeek(date) {
  const copy = new Date(date)
  const day = copy.getDay() || 7
  copy.setDate(copy.getDate() - day + 1)
  return copy
}

function startOfQuarter(date) {
  return new Date(date.getFullYear(), Math.floor(date.getMonth() / 3) * 3, 1)
}

function endOfMonth(year, month) {
  return new Date(year, month + 1, 0)
}

function getPeriodRange(period) {
  const today = new Date()
  today.setHours(12, 0, 0, 0)

  if (period === 'today') return { from: today, to: today }
  if (period === 'yesterday') {
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    return { from: yesterday, to: yesterday }
  }
  if (period === 'this_week') {
    return { from: startOfWeek(today), to: today }
  }
  if (period === 'last_week') {
    const from = startOfWeek(today)
    from.setDate(from.getDate() - 7)
    const to = new Date(from)
    to.setDate(to.getDate() + 6)
    return { from, to }
  }
  if (period === 'this_month') {
    return { from: new Date(today.getFullYear(), today.getMonth(), 1), to: today }
  }
  if (period === 'last_month') {
    const month = today.getMonth() - 1
    const from = new Date(today.getFullYear(), month, 1)
    return { from, to: endOfMonth(from.getFullYear(), from.getMonth()) }
  }
  if (period === 'this_quarter') {
    return { from: startOfQuarter(today), to: today }
  }
  if (period === 'last_quarter') {
    const currentQuarterStart = startOfQuarter(today)
    const from = new Date(currentQuarterStart.getFullYear(), currentQuarterStart.getMonth() - 3, 1)
    const to = new Date(currentQuarterStart)
    to.setDate(to.getDate() - 1)
    return { from, to }
  }
  if (period === 'this_year') {
    return { from: new Date(today.getFullYear(), 0, 1), to: today }
  }
  if (period === 'last_year') {
    return { from: new Date(today.getFullYear() - 1, 0, 1), to: new Date(today.getFullYear() - 1, 11, 31) }
  }
  return null
}

function applyPeriodPreset(period) {
  const range = getPeriodRange(period)
  if (!range) return
  fromDate.value = toISO(range.from)
  toDate.value = toISO(range.to)
}

function resetDates() {
  selectedPeriod.value = 'today'
  applyPeriodPreset(selectedPeriod.value)
}

let debounceTimer = null
watch([fromDate, toDate], () => {
  selectedPeriod.value = matchingPreset() || 'custom'
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 300)
})

function matchingPreset() {
  return periodPresets
    .filter((option) => option.value !== 'custom')
    .find((option) => {
      const range = getPeriodRange(option.value)
      return range && fromDate.value === toISO(range.from) && toDate.value === toISO(range.to)
    })?.value
}

onMounted(() => {
  applyPeriodPreset(selectedPeriod.value)
  load()
})

function money(value) {
  const n = Number(value) || 0
  if (Math.abs(n) >= 1_000_000) return `NGN ${+(n / 1_000_000).toFixed(2)}M`
  if (Math.abs(n) >= 1_000) return `NGN ${+(n / 1_000).toFixed(1)}K`
  return `NGN ${n.toLocaleString()}`
}

function number(value) {
  return Number(value || 0).toLocaleString()
}

function fmtDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function shortDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

function trendHeight(value) {
  return Math.max(10, Math.round((Number(value || 0) / maxTrendRevenue.value) * 100))
}

function severityClass(severity) {
  return {
    High: 'bg-red-50 text-red-600',
    Medium: 'bg-amber-50 text-amber-600',
    Good: 'bg-emerald-50 text-emerald-600',
  }[severity] || 'bg-gray-100 text-gray-600'
}

function displayWatchValue(item) {
  if (item?.value_type === 'money') return money(item.value)
  if (item?.value_type === 'percent') return `${Number(item.value || 0).toLocaleString()}%`
  return number(item?.value)
}

const StatCard = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], required: true },
    tone: { type: String, default: 'blue' },
  },
  setup(props) {
    const tones = {
      blue: 'border-blue-100 bg-blue-50 text-blue-700',
      green: 'border-emerald-100 bg-emerald-50 text-emerald-700',
      orange: 'border-amber-100 bg-amber-50 text-amber-700',
      red: 'border-red-100 bg-red-50 text-red-600',
    }
    return () => h('div', { class: 'rounded-lg border bg-white px-5 py-4' }, [
      h('p', { class: 'text-xs text-gray-400' }, props.label),
      h('p', { class: 'mt-2 text-2xl font-bold text-gray-900' }, props.value),
      h('div', { class: `mt-3 h-1.5 rounded-full ${tones[props.tone] || tones.blue}` }),
    ])
  },
})

const MiniStat = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], required: true },
    compact: { type: Boolean, default: false },
  },
  setup(props) {
    return () => h('div', { class: props.compact ? '' : 'rounded-lg bg-gray-50 px-3 py-3' }, [
      h('p', { class: 'text-xs text-gray-400' }, props.label),
      h('p', { class: props.compact ? 'mt-1 text-base font-bold text-gray-900' : 'mt-1 text-lg font-bold text-gray-900' }, props.value),
    ])
  },
})

const PulseRow = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: Number, default: 0 },
    route: { type: String, required: true },
    warning: { type: Boolean, default: false },
  },
  setup(props) {
    return () => h('button', {
      type: 'button',
      class: 'flex w-full items-center justify-between rounded-lg border border-gray-100 px-3 py-2 text-left hover:bg-gray-50',
      onClick: () => router.push(props.route),
    }, [
      h('span', { class: 'text-xs font-semibold text-gray-700' }, props.label),
      h('span', { class: props.warning && props.value > 0 ? 'text-sm font-bold text-red-600' : 'text-sm font-bold text-gray-900' }, number(props.value)),
    ])
  },
})
</script>
