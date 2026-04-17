<template>
	<section class="ai-banner" :class="{ urgent }">
		<div class="ai-badges">
			<span class="badge ai-on">AI On</span>
			<span class="badge urgent-tag" v-if="urgent">Urgent</span>
		</div>
		<p>{{ message }}</p>
	</section>
</template>

<script setup>
defineProps({
	message: {
		type: String,
		required: true,
	},
	urgent: {
		type: Boolean,
		default: false,
	},
});
</script>

<style scoped>
.ai-banner {
	padding: 0.95rem 1rem;
	border-radius: 14px;
	background:
		linear-gradient(135deg, rgba(255, 242, 198, 0.58), rgba(231, 245, 255, 0.8)),
		repeating-linear-gradient(
			45deg,
			rgba(26, 82, 118, 0.03),
			rgba(26, 82, 118, 0.03) 12px,
			transparent 12px,
			transparent 24px
		);
	border: 1px solid #d8e7f2;
	display: grid;
	gap: 0.55rem;
}

.ai-banner.urgent {
	border-color: #e5a83d;
	box-shadow: 0 8px 24px rgba(190, 130, 33, 0.2);
}

.ai-badges {
	display: flex;
	gap: 0.55rem;
}

.badge {
	display: inline-flex;
	align-items: center;
	padding: 0.22rem 0.55rem;
	border-radius: 999px;
	font-size: 0.72rem;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.03em;
}

.ai-on {
	background: #d5f6ea;
	color: #0d6f4a;
}

.urgent-tag {
	background: #ffe4cc;
	color: #8a4b06;
}

p {
	margin: 0;
	font-size: 0.95rem;
	color: #233648;
	font-weight: 500;
}
</style>
