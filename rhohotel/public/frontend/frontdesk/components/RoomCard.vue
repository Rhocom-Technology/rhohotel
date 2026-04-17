<template>
	<article class="room-card" :class="[statusClass, { overdue: overdue }]" @click="onSelect">
		<header>
			<div>
				<p class="room-number">{{ room.room_number }}</p>
				<p class="room-meta">{{ room.room_type }} · Floor {{ room.floor || "-" }}</p>
			</div>
			<span class="status-pill" :class="statusClass">{{ room.status }}</span>
		</header>

		<div class="room-body">
			<p class="label">Guest</p>
			<p class="value">{{ room.current_guest || "No guest assigned" }}</p>

			<p class="label">Check-out</p>
			<p class="value">
				{{ checkoutLabel }}
				<span v-if="overdue" class="overdue-text">Overdue by {{ overdueByText }}</span>
			</p>
		</div>

		<div class="badges-row">
			<span v-for="badge in badges" :key="badge" class="signal-badge" :class="badge.toLowerCase()">{{ badge }}</span>
		</div>
	</article>
</template>

<script setup>
const { computed } = window.Vue;

const props = defineProps({
	room: {
		type: Object,
		required: true,
	},
});

const emit = defineEmits(["select"]);

const statusClass = computed(() => {
	const map = {
		Occupied: "state-occupied",
		Vacant: "state-vacant",
		Reserved: "state-reserved",
		Maintenance: "state-maintenance",
	};
	return map[props.room.status] || "state-occupied";
});

const overdue = computed(() => {
	if (!props.room.expected_check_out_datetime || props.room.status !== "Occupied") {
		return false;
	}
	return new Date(props.room.expected_check_out_datetime).getTime() < Date.now();
});

const overdueByText = computed(() => {
	if (!overdue.value) return "";
	const diffMs = Date.now() - new Date(props.room.expected_check_out_datetime).getTime();
	const mins = Math.floor(diffMs / 60000);
	if (mins < 60) return `${mins} mins`;
	const hrs = Math.floor(mins / 60);
	const rem = mins % 60;
	return `${hrs}h ${rem}m`;
});

const checkoutLabel = computed(() => {
	if (!props.room.expected_check_out_datetime) return "Not set";
	return new Date(props.room.expected_check_out_datetime).toLocaleString();
});

const badges = computed(() => {
	const flags = props.room.flags || {};
	const list = [];
	if (flags.unpaid) list.push("UNPAID");
	if (flags.vip) list.push("VIP");
	if (flags.hold) list.push("HOLD");
	if (flags.hk) list.push("HK");
	if (flags.due || overdue.value) list.push("DUE");
	return list;
});

function onSelect() {
	emit("select", props.room);
}
</script>

<style scoped>
.room-card {
	background: #ffffff;
	border: 1px solid #d2e1eb;
	border-left: 5px solid #2576ba;
	border-radius: 14px;
	padding: 0.8rem;
	display: grid;
	gap: 0.75rem;
	cursor: pointer;
	box-shadow: 0 9px 24px rgba(16, 44, 62, 0.08);
	transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.room-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 16px 30px rgba(16, 44, 62, 0.14);
}

.room-card.overdue {
	border-left-color: #c43b32;
	background: linear-gradient(130deg, #fff9f8, #ffffff 45%);
}

header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 0.6rem;
}

.room-number {
	margin: 0;
	font-size: 1.15rem;
	font-weight: 700;
	color: #1c3040;
}

.room-meta {
	margin: 0.1rem 0 0;
	font-size: 0.82rem;
	color: #5f7a8d;
}

.status-pill {
	padding: 0.22rem 0.5rem;
	border-radius: 999px;
	font-size: 0.72rem;
	font-weight: 700;
	text-transform: uppercase;
}

.state-occupied { border-left-color: #2d73b0; }
.state-vacant { border-left-color: #1a8e59; }
.state-reserved { border-left-color: #dd9f1f; }
.state-maintenance { border-left-color: #677582; }

.status-pill.state-occupied { background: #d9ebff; color: #18528a; }
.status-pill.state-vacant { background: #d8f8e7; color: #0c6941; }
.status-pill.state-reserved { background: #ffefcc; color: #8c5b08; }
.status-pill.state-maintenance { background: #e6eaee; color: #495869; }

.room-body {
	display: grid;
	grid-template-columns: 1fr;
	gap: 0.2rem;
}

.label {
	margin: 0;
	font-size: 0.73rem;
	font-weight: 700;
	letter-spacing: 0.04em;
	text-transform: uppercase;
	color: #557082;
}

.value {
	margin: 0 0 0.35rem;
	font-size: 0.88rem;
	color: #253b4c;
}

.overdue-text {
	display: block;
	margin-top: 0.2rem;
	font-size: 0.8rem;
	font-weight: 600;
	color: #bb2f2f;
}

.badges-row {
	display: flex;
	flex-wrap: wrap;
	gap: 0.35rem;
}

.signal-badge {
	font-size: 0.67rem;
	font-weight: 700;
	border-radius: 8px;
	padding: 0.2rem 0.4rem;
	text-transform: uppercase;
}

.signal-badge.unpaid { background: #fde5e1; color: #9d1f14; }
.signal-badge.vip { background: #eee4ff; color: #5a2f9f; }
.signal-badge.hold { background: #e7edf3; color: #44596f; }
.signal-badge.hk { background: #fff2cf; color: #7c5905; }
.signal-badge.due { background: #ffe1d8; color: #a02d14; }
</style>
