<template>
	<div class="stat-card" :class="`stat-${color}`">
		<p class="stat-title">{{ title }}</p>
		<p class="stat-value">{{ value }}</p>
		<p class="stat-subtitle">{{ subtitle }}</p>
	</div>
</template>

<script setup>
defineProps({
	title: {
		type: String,
		required: true,
	},
	value: {
		type: [String, Number],
		required: true,
	},
	subtitle: {
		type: String,
		default: "",
	},
	color: {
		type: String,
		default: "blue",
	},
});
</script>

<style scoped>
.stat-card {
	padding: 0.9rem;
	border-radius: 14px;
	background: #ffffff;
	border: 1px solid #dae6ef;
	box-shadow: 0 9px 28px rgba(16, 42, 56, 0.08);
	transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.stat-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 16px 34px rgba(16, 42, 56, 0.12);
}

.stat-title {
	margin: 0;
	font-size: 0.8rem;
	font-weight: 700;
	letter-spacing: 0.03em;
	text-transform: uppercase;
	color: #4c6777;
}

.stat-value {
	margin: 0.22rem 0 0;
	font-size: 1.85rem;
	font-weight: 700;
	line-height: 1;
}

.stat-subtitle {
	margin: 0.48rem 0 0;
	font-size: 0.82rem;
	color: #5a7588;
}

.stat-red .stat-value { color: #c33632; }
.stat-green .stat-value { color: #13824f; }
.stat-yellow .stat-value { color: #9c6e10; }
.stat-blue .stat-value { color: #206cb8; }
.stat-purple .stat-value { color: #6756b5; }
.stat-grey .stat-value { color: #495768; }
</style>
