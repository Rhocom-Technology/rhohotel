<template>
	<div class="fd-app-shell">
		<Sidebar />
		<div class="fd-main-panel">
			<TopHeader
				:page-title="pageTitle"
				:greeting="headerGreeting"
				:datetime="formattedDateTime"
			/>
			<main class="fd-content-area">
				<RouterView />
			</main>
		</div>
	</div>
</template>

<script setup>
const { computed, ref, onMounted, onUnmounted } = window.Vue;
const { useRoute } = window.VueRouter;

const props = defineProps({
	greeting: {
		type: String,
		default: "Good Morning",
	},
});

const route = useRoute();
const now = ref(new Date());
let clockTimer;

const currentUser = computed(() => {
	if (window.frappe?.session?.user_fullname) {
		return window.frappe.session.user_fullname;
	}
	return "Front Desk Agent";
});

const pageTitle = computed(() => route.meta?.pageTitle || "Front Desk");
const headerGreeting = computed(() => `${props.greeting}, ${currentUser.value}`);

const formattedDateTime = computed(() =>
	now.value.toLocaleString(undefined, {
		weekday: "short",
		month: "short",
		day: "numeric",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
		second: "2-digit",
	}),
);

onMounted(() => {
	clockTimer = window.setInterval(() => {
		now.value = new Date();
	}, 1000);
});

onUnmounted(() => {
	if (clockTimer) {
		window.clearInterval(clockTimer);
	}
});
</script>

<style scoped>
.fd-app-shell {
	display: grid;
	grid-template-columns: 280px 1fr;
	min-height: calc(100vh - 52px);
	background:
		radial-gradient(circle at 0 0, rgba(26, 102, 171, 0.08), transparent 42%),
		radial-gradient(circle at 100% 0, rgba(7, 135, 102, 0.1), transparent 40%),
		#f3f7fa;
}

.fd-main-panel {
	display: flex;
	flex-direction: column;
	min-width: 0;
}

.fd-content-area {
	padding: 1rem 1.25rem 1.5rem;
}

@media (max-width: 1100px) {
	.fd-app-shell {
		grid-template-columns: 86px 1fr;
	}
}

@media (max-width: 760px) {
	.fd-app-shell {
		grid-template-columns: 1fr;
	}

	.fd-content-area {
		padding: 0.85rem;
	}
}
</style>
