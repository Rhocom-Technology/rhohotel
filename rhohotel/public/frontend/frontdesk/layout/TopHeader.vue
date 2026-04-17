<template>
	<header class="fd-top-header">
		<div>
			<p class="fd-overline">Front Desk Command Center</p>
			<h2>{{ pageTitle }}</h2>
		</div>
		<div class="fd-top-meta">
			<p>{{ greeting }}</p>
			<p>{{ datetime }}</p>
		</div>
	</header>
</template>

<script setup>
defineProps({
	pageTitle: {
		type: String,
		default: "Front Desk",
	},
	greeting: {
		type: String,
		default: "Good Morning",
	},
	datetime: {
		type: String,
		default: "",
	},
});
</script>

<style scoped>
.fd-top-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 1rem;
	padding: 1rem 1.25rem;
	border-bottom: 1px solid #dce8f0;
	background: linear-gradient(95deg, #f8fcff 0%, #eef9f5 70%, #f8f4eb 100%);
}

.fd-overline {
	margin: 0;
	font-size: 0.76rem;
	font-weight: 700;
	letter-spacing: 0.11em;
	text-transform: uppercase;
	color: #2d7a7a;
}

h2 {
	margin: 0.1rem 0 0;
	font-size: 1.42rem;
	font-weight: 700;
	color: #22344a;
}

.fd-top-meta {
	text-align: right;
}

.fd-top-meta p {
	margin: 0;
	font-size: 0.88rem;
	color: #486277;
}

.fd-top-meta p:first-child {
	font-weight: 600;
	color: #1f4359;
}

@media (max-width: 760px) {
	.fd-top-header {
		padding: 0.8rem;
		flex-direction: column;
		align-items: flex-start;
	}

	.fd-top-meta {
		text-align: left;
	}
}
</style>
