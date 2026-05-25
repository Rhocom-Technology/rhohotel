<template>
	<div class="space-y-4">
		<!-- AI Briefing Banner -->
		<AIInsightPanel
			title="AI Front Desk Briefing"
			context-type="room_view_briefing"
			:context-data="aiContext"
			:auto-load="true"
			panel-id="room-view"
		/>

		<!-- Stats Row -->
		<div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px">
			<div
				v-for="stat in statCards"
				:key="stat.label"
				class="bg-white rounded-xl border border-gray-200 px-4 py-4"
				:class="stat.to ? 'cursor-pointer hover:border-red-200 transition-colors' : ''"
				@click="stat.to ? $router.push(stat.to) : null"
			>
				<p class="text-xs text-gray-400 mb-1">{{ stat.label }}</p>
				<p class="text-3xl font-bold text-gray-900">{{ stat.value }}</p>
				<p class="text-xs mt-1 font-medium" :style="{ color: stat.hexColor }">
					{{ stat.subtitle }}
				</p>
			</div>
		</div>

		<!-- Page Tabs -->

		<!-- Filters -->
		<div
			class="bg-white rounded-xl border border-gray-200 px-5 py-3 flex items-center gap-3 flex-wrap"
		>
			<div class="relative" style="flex: 1; min-width: 160px">
				<Search
					class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400"
				/>
				<input
					v-model="search"
					type="text"
					placeholder="Search room or guest"
					class="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
				/>
			</div>
			<select
				v-model="filterFloor"
				class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none"
			>
				<option value="">Floor</option>
				<option v-for="f in floors" :key="f" :value="f">Floor {{ f }}</option>
			</select>
			<select
				v-model="filterType"
				class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none"
			>
				<option value="">Room Type</option>
				<option v-for="t in roomTypes" :key="t" :value="t">{{ t }}</option>
			</select>
			<select
				v-model="filterStatus"
				class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none"
			>
				<option value="">Status</option>
				<option value="Vacant">Vacant</option>
				<option value="Occupied">Occupied</option>
				<option value="Reserved">Reserved</option>
				<option value="Maintenance">Maintenance</option>
			</select>
			<select
				v-model="filterHK"
				class="text-xs border border-gray-200 rounded-lg px-3 py-2 text-gray-600 focus:outline-none"
			>
				<option value="">Housekeeping</option>
				<option value="Clean">Clean</option>
				<option value="Dirty">Dirty</option>
				<option value="In Progress">In Progress</option>
				<option value="Inspected">Inspected</option>
			</select>
			<button
				@click="filterOverdue = !filterOverdue"
				class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
				:style="
					filterOverdue
						? 'background:#fef2f2;color:#ef4444;border-color:#fecaca'
						: 'color:#6b7280;border-color:#e5e7eb'
				"
			>
				Only Overdue
			</button>
			<button
				@click="filterVIP = !filterVIP"
				class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
				:style="
					filterVIP
						? 'background:#f5f3ff;color:#7c3aed;border-color:#ddd6fe'
						: 'color:#6b7280;border-color:#e5e7eb'
				"
			>
				VIP
			</button>
			<button
				@click="filterDirty = !filterDirty"
				class="px-3 py-2 text-xs font-medium rounded-lg border transition-colors"
				:style="
					filterDirty
						? 'background:#fffbeb;color:#d97706;border-color:#fde68a'
						: 'color:#6b7280;border-color:#e5e7eb'
				"
			>
				Dirty Only
			</button>
			<button
				@click="refreshRooms"
				style="background: #2563eb; color: white"
				class="px-4 py-2 text-xs font-semibold rounded-lg hover:opacity-90 transition-opacity"
			>
				Refresh Grid
			</button>
		</div>

		<!-- Live Room Grid -->
		<div>
			<div class="mb-3">
				<h3 class="text-sm font-bold text-gray-900">Live Room Grid</h3>
				<p class="text-xs text-gray-400">
					Compact operational tiles for rapid front desk scanning and action
				</p>
			</div>

			<div
				v-if="filteredRooms.length === 0"
				class="bg-white rounded-xl border border-gray-200 flex flex-col items-center justify-center py-16"
			>
				<p class="text-sm font-medium text-gray-400">No rooms match your filters</p>
			</div>

			<div v-else style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px">
				<div
					v-for="room in filteredRooms"
					:key="room.name"
					class="rounded-xl p-4 border cursor-pointer hover:shadow-md transition-shadow"
					:style="roomCardStyle(room)"
					@click="selectedRoom = room"
				>
					<!-- Header -->
					<div class="flex items-start justify-between mb-2">
						<div>
							<p class="text-sm font-bold" :style="{ color: roomTextColor(room) }">
								{{ room.room_number }}
							</p>
							<p class="text-xs mt-0.5" style="color: #6b7280">
								{{ room.room_type }} • Floor {{ room.floor }}
							</p>
						</div>
						<div class="flex flex-wrap gap-1 justify-end">
							<span
								v-if="room.unpaid"
								style="
									background: #fee2e2;
									color: #dc2626;
									font-size: 10px;
									font-weight: 700;
									padding: 1px 6px;
									border-radius: 4px;
								"
								>UNPAID</span
							>
							<span
								v-if="room.overdue"
								style="
									background: #fff7ed;
									color: #ea580c;
									font-size: 10px;
									font-weight: 700;
									padding: 1px 6px;
									border-radius: 4px;
								"
								>DUE</span
							>
							<span
								v-if="room.status === 'Reserved'"
								style="
									background: #ede9fe;
									color: #7c3aed;
									font-size: 10px;
									font-weight: 700;
									padding: 1px 6px;
									border-radius: 4px;
								"
								>RESERVED</span
							>
							<span
								v-if="room.housekeeping_status === 'In Progress'"
								style="
									background: #fef9c3;
									color: #ca8a04;
									font-size: 10px;
									font-weight: 700;
									padding: 1px 6px;
									border-radius: 4px;
								"
								>HK</span
							>
							<span
								v-if="room.status === 'Reserved'"
								style="
									background: #dbeafe;
									color: #2563eb;
									font-size: 10px;
									font-weight: 700;
									padding: 1px 6px;
									border-radius: 4px;
								"
								>HOLD</span
							>
							<span
								v-if="
									room.status === 'Vacant' &&
									(room.housekeeping_status === 'Clean' ||
										room.housekeeping_status === 'Inspected')
								"
								style="
									background: #dcfce7;
									color: #16a34a;
									font-size: 10px;
									font-weight: 700;
									padding: 1px 6px;
									border-radius: 4px;
								"
								>READY</span
							>
						</div>
					</div>

					<!-- Guest -->
					<p class="text-xs font-semibold truncate" style="color: #374151">
						{{ room.current_guest || "\u00a0" }}
					</p>

					<!-- Status line -->
					<p
						class="text-xs font-semibold mt-1"
						:style="{ color: statusLineColor(room) }"
					>
						{{ statusLine(room) }}
					</p>

					<!-- Subtitle -->
					<p class="text-xs mt-0.5 truncate" style="color: #9ca3af">
						{{ room.subtitle }}
					</p>
				</div>
			</div>
			<RoomControlModal
				v-if="selectedRoom"
				:room="selectedRoom"
				@close="selectedRoom = null"
			/>
		</div>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";
import { Search } from "lucide-vue-next";
import { createResource } from "frappe-ui";
import RoomControlModal from "@/components/roomview/RoomControlModal.vue";
import AIInsightPanel from "@/components/ai/AIInsightPanel.vue";
const selectedRoom = ref(null);

const search = ref("");
const filterFloor = ref("");
const filterType = ref("");
const filterStatus = ref("");
const filterHK = ref("");
const filterOverdue = ref(false);
const filterVIP = ref(false);
const filterDirty = ref(false);

const roomViewResource = createResource({
	url: "rhohotel.rhocom_hotel.api.front_desk.get_room_view_data",
	params: { filters: {} },
	auto: true,
});

const roomViewPayload = computed(() => {
	const data = roomViewResource.data || {};
	return data.message || data;
});

const roomRows = computed(() => roomViewPayload.value.rooms || []);

const floors = computed(() => [...new Set(roomRows.value.map((r) => r.floor).filter(Boolean))].sort());
const roomTypes = computed(() => [...new Set(roomRows.value.map((r) => r.room_type).filter(Boolean))].sort());

const stats = computed(() => {
	const fallback = {
		vacant: 0,
		occupied: 0,
		reserved: 0,
		dirty: 0,
		maintenance: 0,
		overdue: 0,
		unpaid: 0,
		vip: 0,
	};
	return { ...fallback, ...(roomViewPayload.value.stats || {}) };
});

const aiContext = computed(() => ({
	vacant: stats.value.vacant,
	occupied: stats.value.occupied,
	reserved: stats.value.reserved,
	dirty_rooms: stats.value.dirty,
	maintenance: stats.value.maintenance,
	overdue_checkouts: stats.value.overdue,
	unpaid_folios: stats.value.unpaid,
	vip_arrivals: stats.value.vip,
	total_rooms: stats.value.vacant + stats.value.occupied + stats.value.reserved + stats.value.maintenance,
}));

// const statCards = computed(() => [
//   { label: 'Vacant Rooms', value: stats.value.vacant, subtitle: 'Ready for sale', hexColor: '#22c55e' },
//   { label: 'Occupied', value: stats.value.occupied, subtitle: 'Live stays', hexColor: '#3b82f6' },
//   { label: 'Reserved Today', value: stats.value.reserved, subtitle: 'Incoming arrivals', hexColor: '#8b5cf6' },
//   { label: 'Dirty Rooms', value: stats.value.dirty, subtitle: 'Housekeeping queue', hexColor: '#f97316' },
//   { label: 'Maintenance', value: stats.value.maintenance, subtitle: 'Out of order', hexColor: '#6b7280' },
//   { label: 'Overdue Check-outs', value: stats.value.overdue, subtitle: 'Immediate desk action', hexColor: '#ef4444' },
// ])

const statCards = computed(() => [
	{
		label: "Vacant Rooms",
		value: stats.value.vacant,
		subtitle: "Ready for sale",
		hexColor: "#22c55e",
	},
	{
		label: "Occupied",
		value: stats.value.occupied,
		subtitle: "Live stays",
		hexColor: "#3b82f6",
	},
	{
		label: "Reserved Today",
		value: stats.value.reserved,
		subtitle: "Incoming arrivals",
		hexColor: "#8b5cf6",
		to: { name: "Reservations", query: { arrival: "today", status: "Confirmed" } },
	},
	{
		label: "Dirty Rooms",
		value: stats.value.dirty,
		subtitle: "Housekeeping queue",
		hexColor: "#f97316",
	},
	{
		label: "Maintenance",
		value: stats.value.maintenance,
		subtitle: "Out of order",
		hexColor: "#6b7280",
	},
	{
		label: "Overdue Check-outs",
		value: stats.value.overdue,
		subtitle: "Immediate desk action",
		hexColor: "#ef4444",
		to: "/check-outs/overdue",
	},
]);

const filteredRooms = computed(() => {
	let list = roomRows.value;
	if (search.value) {
		const q = search.value.toLowerCase();
		list = list.filter(
			(r) =>
				String(r.room_number || "")
					.toLowerCase()
					.includes(q) ||
				String(r.current_guest || "")
					.toLowerCase()
					.includes(q) ||
				String(r.room_type || "")
					.toLowerCase()
					.includes(q),
		);
	}
	if (filterFloor.value)
		list = list.filter((r) => String(r.floor || "") === String(filterFloor.value));
	if (filterType.value) list = list.filter((r) => r.room_type === filterType.value);
	if (filterStatus.value) list = list.filter((r) => r.status === filterStatus.value);
	if (filterHK.value) list = list.filter((r) => r.housekeeping_status === filterHK.value);
	if (filterOverdue.value) list = list.filter((r) => r.overdue);
	if (filterVIP.value) list = list.filter((r) => r.status === "Reserved");
	if (filterDirty.value) list = list.filter((r) => r.housekeeping_status === "Dirty");
	return list;
});

function roomCardStyle(room) {
	if (room.overdue)
		return "background:#fff1f2;border-color:#fecdd3;border-left:4px solid #ef4444;";
	if (
		room.status === "Vacant" &&
		(room.housekeeping_status === "Clean" || room.housekeeping_status === "Inspected")
	)
		return "background:#f0fdf4;border-color:#bbf7d0;border-left:4px solid #22c55e;";
	if (room.status === "Vacant" && room.housekeeping_status === "Dirty")
		return "background:#fffbeb;border-color:#fde68a;border-left:4px solid #f59e0b;";
	if (room.status === "Occupied")
		return "background:#eff6ff;border-color:#bfdbfe;border-left:4px solid #3b82f6;";
	if (room.status === "Reserved")
		return "background:#f5f3ff;border-color:#ddd6fe;border-left:4px solid #8b5cf6;";
	if (room.status === "Maintenance")
		return "background:#f9fafb;border-color:#e5e7eb;border-left:4px solid #9ca3af;";
	if (room.housekeeping_status === "In Progress")
		return "background:#fffbeb;border-color:#fde68a;border-left:4px solid #f59e0b;";
	return "background:white;border-color:#e5e7eb;border-left:4px solid #e5e7eb;";
}

function roomTextColor(room) {
	if (room.overdue) return "#991b1b";
	if (room.status === "Vacant") return "#166534";
	if (room.status === "Occupied") return "#1e40af";
	if (room.status === "Reserved") return "#5b21b6";
	return "#111827";
}

function statusLineColor(room) {
	if (room.overdue) return "#ef4444";
	if (
		room.status === "Vacant" &&
		(room.housekeeping_status === "Clean" || room.housekeeping_status === "Inspected")
	)
		return "#22c55e";
	if (room.status === "Vacant" && room.housekeeping_status === "Dirty") return "#f59e0b";
	if (room.status === "Reserved") return "#8b5cf6";
	if (room.housekeeping_status === "In Progress") return "#f59e0b";
	if (room.status === "Maintenance") return "#6b7280";
	return "#374151";
}

function statusLine(room) {
	if (room.overdue) return overdueByText(room.expected_check_out_datetime);
	if (
		room.status === "Vacant" &&
		(room.housekeeping_status === "Clean" || room.housekeeping_status === "Inspected")
	)
		return "Vacant and clean";
	if (room.status === "Vacant" && room.housekeeping_status === "Dirty")
		return "Vacant but dirty";
	if (room.status === "Maintenance") return "In maintenance";
	if (room.housekeeping_status === "In Progress") return "Cleaning in progress";
	if (room.status === "Reserved") return "Reserved for today";
	if (room.status === "Occupied") return "Occupied";
	return room.status || "—";
}

function overdueByText(expectedCheckoutDatetime) {
	const overdueMs = getOverdueMs(expectedCheckoutDatetime);
	if (!overdueMs) return "Overdue check-out";

	const totalMinutes = Math.floor(overdueMs / (1000 * 60));
	if (totalMinutes < 1) return "Overdue by less than a minute";

	const minutesInHour = 60;
	const minutesInDay = 60 * 24;

	if (totalMinutes < minutesInHour)
		return `Overdue by ${totalMinutes} minute${totalMinutes === 1 ? "" : "s"}`;

	if (totalMinutes < minutesInDay) {
		const hours = Math.floor(totalMinutes / minutesInHour);
		return `Overdue by ${hours} hour${hours === 1 ? "" : "s"}`;
	}

	const days = Math.floor(totalMinutes / minutesInDay);
	const remainingHours = Math.floor((totalMinutes % minutesInDay) / minutesInHour);
	if (!remainingHours) return `Overdue by ${days} day${days === 1 ? "" : "s"}`;

	return `Overdue by ${days} day${days === 1 ? "" : "s"} ${remainingHours} hour${remainingHours === 1 ? "" : "s"}`;
}

function getOverdueMs(expectedCheckoutDatetime) {
	if (!expectedCheckoutDatetime) return 0;

	const checkout = new Date(expectedCheckoutDatetime);
	if (Number.isNaN(checkout.getTime())) return 0;

	const now = new Date();
	const diff = now.getTime() - checkout.getTime();
	return diff > 0 ? diff : 0;
}

function refreshRooms() {
	roomViewResource.reload();
}
</script>
