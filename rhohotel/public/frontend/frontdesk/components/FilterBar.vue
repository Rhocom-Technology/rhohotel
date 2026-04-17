<template>
	<section class="filter-shell">
		<div class="filter-grid">
			<input
				class="fd-input"
				type="text"
				:value="modelValue.search"
				placeholder="Search room, guest, email"
				@input="update({ search: $event.target.value })"
			/>

			<select class="fd-input" :value="modelValue.floor" @change="update({ floor: $event.target.value })">
				<option value="">All Floors</option>
				<option v-for="floor in floors" :key="floor" :value="floor">{{ floor }}</option>
			</select>

			<select class="fd-input" :value="modelValue.roomType" @change="update({ roomType: $event.target.value })">
				<option value="">All Room Types</option>
				<option v-for="roomType in roomTypes" :key="roomType" :value="roomType">{{ roomType }}</option>
			</select>

			<select class="fd-input" :value="modelValue.status" @change="update({ status: $event.target.value })">
				<option value="">All Statuses</option>
				<option value="Occupied">Occupied</option>
				<option value="Vacant">Vacant</option>
				<option value="Reserved">Reserved</option>
				<option value="Maintenance">Maintenance</option>
			</select>

			<select
				class="fd-input"
				:value="modelValue.housekeeping"
				@change="update({ housekeeping: $event.target.value })"
			>
				<option value="">All Housekeeping</option>
				<option value="Clean">Clean</option>
				<option value="Dirty">Dirty</option>
				<option value="Inspected">Inspected</option>
				<option value="In Progress">In Progress</option>
			</select>
		</div>

		<div class="quick-row">
			<label><input type="checkbox" :checked="modelValue.onlyOverdue" @change="update({ onlyOverdue: $event.target.checked })" /> Only Overdue</label>
			<label><input type="checkbox" :checked="modelValue.vipOnly" @change="update({ vipOnly: $event.target.checked })" /> VIP</label>
			<label><input type="checkbox" :checked="modelValue.dirtyOnly" @change="update({ dirtyOnly: $event.target.checked })" /> Dirty Only</label>
			<button class="refresh-btn" @click="$emit('refresh')">Refresh Grid</button>
		</div>
	</section>
</template>

<script setup>
const props = defineProps({
	modelValue: {
		type: Object,
		required: true,
	},
	floors: {
		type: Array,
		default: () => [],
	},
	roomTypes: {
		type: Array,
		default: () => [],
	},
});

const emit = defineEmits(["update:modelValue", "refresh"]);

function update(patch) {
	emit("update:modelValue", { ...props.modelValue, ...patch });
}
</script>

<style scoped>
.filter-shell {
	padding: 0.95rem;
	border-radius: 14px;
	background: #ffffff;
	border: 1px solid #d8e5ee;
}

.filter-grid {
	display: grid;
	grid-template-columns: repeat(5, minmax(0, 1fr));
	gap: 0.55rem;
}

.fd-input {
	width: 100%;
	padding: 0.55rem 0.65rem;
	border: 1px solid #c9d7e2;
	border-radius: 10px;
	font-size: 0.9rem;
	background: #fefefe;
}

.fd-input:focus {
	outline: none;
	border-color: #2677a9;
	box-shadow: 0 0 0 2px rgba(38, 119, 169, 0.18);
}

.quick-row {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 0.85rem;
	margin-top: 0.75rem;
}

.quick-row label {
	display: inline-flex;
	align-items: center;
	gap: 0.32rem;
	font-size: 0.86rem;
	color: #334f62;
}

.refresh-btn {
	margin-left: auto;
	border: none;
	background: linear-gradient(135deg, #227fba, #1f9c85);
	color: #ffffff;
	font-weight: 600;
	padding: 0.55rem 0.9rem;
	border-radius: 10px;
	cursor: pointer;
	transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.refresh-btn:hover {
	transform: translateY(-1px);
	box-shadow: 0 8px 16px rgba(34, 127, 186, 0.22);
}

@media (max-width: 1100px) {
	.filter-grid {
		grid-template-columns: repeat(3, minmax(0, 1fr));
	}
}

@media (max-width: 760px) {
	.filter-grid {
		grid-template-columns: 1fr;
	}

	.refresh-btn {
		margin-left: 0;
	}
}
</style>
