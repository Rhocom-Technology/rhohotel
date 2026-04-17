<template>
	<section class="room-view-page">
		<AIInsightBanner :message="insightMessage" :urgent="overdueRooms.length > 0" />

		<div class="stats-grid">
			<StatCard title="Vacant Rooms" :value="stats.vacant" subtitle="Ready for check-in" color="green" />
			<StatCard title="Occupied" :value="stats.occupied" subtitle="Guests currently in-house" color="blue" />
			<StatCard title="Reserved Today" :value="stats.reserved" subtitle="Expected arrivals" color="yellow" />
			<StatCard title="Dirty Rooms" :value="stats.dirty" subtitle="Housekeeping queue" color="purple" />
			<StatCard title="Maintenance" :value="stats.maintenance" subtitle="Out of service" color="grey" />
			<StatCard title="Overdue Checkouts" :value="stats.overdue" subtitle="Needs intervention" color="red" />
		</div>

		<FilterBar
			v-model="filters"
			:floors="floorOptions"
			:room-types="roomTypeOptions"
			@refresh="refreshGrid"
		/>

		<div class="room-grid">
			<RoomCard v-for="room in filteredRooms" :key="room.name" :room="room" @select="handleRoomSelect" />
		</div>

		<div v-if="filteredRooms.length === 0" class="empty-state">
			<p>No rooms match your current filters.</p>
		</div>
	</section>
</template>

<script setup>
const { ref, computed } = window.Vue;

const filters = ref({
	search: "",
	floor: "",
	roomType: "",
	status: "",
	housekeeping: "",
	onlyOverdue: false,
	vipOnly: false,
	dirtyOnly: false,
});

const rooms = ref(buildMockRooms());
const refreshSeed = ref(0);

const floorOptions = computed(() =>
	Array.from(new Set(rooms.value.map((room) => room.floor))).filter(Boolean),
);

const roomTypeOptions = computed(() =>
	Array.from(new Set(rooms.value.map((room) => room.room_type))).filter(Boolean),
);

const overdueRooms = computed(() =>
	rooms.value.filter((room) => isOverdue(room.expected_check_out_datetime, room.status)),
);

const filteredRooms = computed(() => {
	const query = filters.value.search.trim().toLowerCase();

	return rooms.value.filter((room) => {
		if (query) {
			const haystack = [
				room.room_number,
				room.current_guest,
				room.room_type,
				room.floor,
			]
				.filter(Boolean)
				.join(" ")
				.toLowerCase();
			if (!haystack.includes(query)) return false;
		}

		if (filters.value.floor && room.floor !== filters.value.floor) return false;
		if (filters.value.roomType && room.room_type !== filters.value.roomType) return false;
		if (filters.value.status && room.status !== filters.value.status) return false;
		if (filters.value.housekeeping && room.housekeeping_status !== filters.value.housekeeping) {
			return false;
		}
		if (filters.value.onlyOverdue && !isOverdue(room.expected_check_out_datetime, room.status)) {
			return false;
		}
		if (filters.value.vipOnly && !room.flags?.vip) return false;
		if (filters.value.dirtyOnly && room.housekeeping_status !== "Dirty") return false;
		return true;
	});
});

const stats = computed(() => ({
	vacant: rooms.value.filter((room) => room.status === "Vacant").length,
	occupied: rooms.value.filter((room) => room.status === "Occupied").length,
	reserved: rooms.value.filter((room) => room.status === "Reserved").length,
	dirty: rooms.value.filter((room) => room.housekeeping_status === "Dirty").length,
	maintenance: rooms.value.filter((room) => room.status === "Maintenance").length,
	overdue: overdueRooms.value.length,
}));

const insightMessage = computed(() => {
	const overdue = overdueRooms.value.length;
	const dirty = stats.value.dirty;
	const vip = rooms.value.filter((room) => room.flags?.vip).length;
	return `${overdue + dirty} rooms need immediate attention: ${overdue} overdue check-outs, ${dirty} dirty rooms, ${vip} VIP rooms in-house.`;
});

function refreshGrid() {
	refreshSeed.value += 1;
	rooms.value = buildMockRooms(refreshSeed.value);
}

function handleRoomSelect(room) {
	console.log("Selected room:", room);
}

function isOverdue(datetime, status) {
	if (!datetime || status !== "Occupied") return false;
	return new Date(datetime).getTime() < Date.now();
}

function buildMockRooms(seed = 0) {
	const now = Date.now();
	const hour = 60 * 60 * 1000;
	const rotate = seed % 3;

	return [
		{
			name: "ROOM-101",
			room_number: "101",
			room_type: "Deluxe Queen",
			floor: "1",
			status: "Occupied",
			housekeeping_status: "Clean",
			current_guest: "Aisha Bello",
			expected_check_out_datetime: new Date(now - (40 + rotate * 8) * 60000).toISOString(),
			flags: { unpaid: true, vip: true, hold: false, hk: false, due: true },
		},
		{
			name: "ROOM-102",
			room_number: "102",
			room_type: "Executive Twin",
			floor: "1",
			status: "Vacant",
			housekeeping_status: "Clean",
			current_guest: "",
			expected_check_out_datetime: null,
			flags: { unpaid: false, vip: false, hold: false, hk: false, due: false },
		},
		{
			name: "ROOM-203",
			room_number: "203",
			room_type: "Suite",
			floor: "2",
			status: "Reserved",
			housekeeping_status: "Inspected",
			current_guest: "Incoming: Chinedu Okafor",
			expected_check_out_datetime: new Date(now + 24 * hour).toISOString(),
			flags: { unpaid: false, vip: true, hold: true, hk: false, due: false },
		},
		{
			name: "ROOM-204",
			room_number: "204",
			room_type: "Standard",
			floor: "2",
			status: "Occupied",
			housekeeping_status: "Dirty",
			current_guest: "Mariam Yusuf",
			expected_check_out_datetime: new Date(now + (1 + rotate) * hour).toISOString(),
			flags: { unpaid: true, vip: false, hold: false, hk: true, due: false },
		},
		{
			name: "ROOM-305",
			room_number: "305",
			room_type: "Presidential",
			floor: "3",
			status: "Occupied",
			housekeeping_status: "In Progress",
			current_guest: "Mr. D. K. Thompson",
			expected_check_out_datetime: new Date(now - (95 - rotate * 10) * 60000).toISOString(),
			flags: { unpaid: false, vip: true, hold: false, hk: true, due: true },
		},
		{
			name: "ROOM-306",
			room_number: "306",
			room_type: "Executive Twin",
			floor: "3",
			status: "Maintenance",
			housekeeping_status: "Dirty",
			current_guest: "",
			expected_check_out_datetime: null,
			flags: { unpaid: false, vip: false, hold: false, hk: true, due: false },
		},
		{
			name: "ROOM-401",
			room_number: "401",
			room_type: "Deluxe Queen",
			floor: "4",
			status: "Vacant",
			housekeeping_status: "Dirty",
			current_guest: "",
			expected_check_out_datetime: null,
			flags: { unpaid: false, vip: false, hold: false, hk: true, due: false },
		},
		{
			name: "ROOM-402",
			room_number: "402",
			room_type: "Suite",
			floor: "4",
			status: "Occupied",
			housekeeping_status: "Clean",
			current_guest: "Lara Chukwu",
			expected_check_out_datetime: new Date(now + 3 * hour).toISOString(),
			flags: { unpaid: false, vip: false, hold: false, hk: false, due: false },
		},
	];
}
</script>

<style scoped>
.room-view-page {
	display: grid;
	gap: 0.9rem;
}

.stats-grid {
	display: grid;
	grid-template-columns: repeat(6, minmax(0, 1fr));
	gap: 0.65rem;
}

.room-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
	gap: 0.75rem;
}

.empty-state {
	padding: 1rem;
	border-radius: 12px;
	border: 1px dashed #b8ccd9;
	background: rgba(255, 255, 255, 0.66);
	text-align: center;
	color: #3f5f72;
}

@media (max-width: 1300px) {
	.stats-grid {
		grid-template-columns: repeat(3, minmax(0, 1fr));
	}
}

@media (max-width: 760px) {
	.stats-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.room-grid {
		grid-template-columns: 1fr;
	}
}
</style>
