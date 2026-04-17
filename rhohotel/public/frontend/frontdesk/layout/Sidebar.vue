<template>
	<aside class="fd-sidebar">
		<div class="fd-logo-wrap">
			<div class="fd-logo-mark">rho</div>
			<div>
				<h1>rhoHMS</h1>
				<p>Hotel Control</p>
			</div>
		</div>

		<div class="fd-section">
			<h2>Front Desk</h2>
			<RouterLink
				v-for="item in frontDeskItems"
				:key="item.path"
				:to="item.path"
				class="fd-nav-link"
				:class="{ active: route.path === item.path }"
			>
				<span>{{ item.label }}</span>
			</RouterLink>
		</div>

		<div class="fd-section">
			<RouterLink class="fd-nav-link" to="/housekeeping" :class="{ active: route.path === '/housekeeping' }">
				<span>Housekeeping</span>
			</RouterLink>
			<div class="fd-nav-link disabled"><span>Maintenance</span></div>
			<div class="fd-nav-link disabled"><span>Billing</span></div>
			<div class="fd-nav-link disabled"><span>Reports</span></div>
			<div class="fd-nav-link disabled"><span>POS</span></div>
			<div class="fd-nav-link disabled"><span>Kitchen</span></div>
			<div class="fd-nav-link disabled"><span>Assets</span></div>
		</div>
	</aside>
</template>

<script setup>
const { useRoute } = window.VueRouter;

const route = useRoute();

const frontDeskItems = [
	{ label: "Room View", path: "/room-view" },
	{ label: "Check-ins", path: "/check-ins" },
	{ label: "Check-outs", path: "/check-outs" },
	{ label: "Reservations", path: "/reservations" },
	{ label: "Corporate", path: "/corporate" },
	{ label: "Hall Bookings", path: "/hall-bookings" },
	{ label: "Guests", path: "/guests" },
	{ label: "Payments", path: "/payments" },
	{ label: "Stay Report", path: "/stay-report" },
	{ label: "Night Audit", path: "/night-audit" },
];
</script>

<style scoped>
.fd-sidebar {
	position: sticky;
	top: 0;
	height: calc(100vh - 52px);
	padding: 1.1rem 0.9rem;
	background: linear-gradient(180deg, #0f2d43 0%, #11293a 50%, #0f3a36 100%);
	border-right: 1px solid rgba(255, 255, 255, 0.08);
	overflow-y: auto;
}

.fd-logo-wrap {
	display: flex;
	align-items: center;
	gap: 0.75rem;
	margin-bottom: 1.25rem;
	padding-bottom: 1rem;
	border-bottom: 1px solid rgba(255, 255, 255, 0.16);
}

.fd-logo-mark {
	width: 40px;
	height: 40px;
	border-radius: 12px;
	background: linear-gradient(135deg, #1c8e7c, #35b6c6);
	color: #f4fcff;
	font-size: 0.8rem;
	font-weight: 700;
	display: grid;
	place-items: center;
	text-transform: uppercase;
}

.fd-logo-wrap h1 {
	margin: 0;
	font-size: 1.1rem;
	font-weight: 700;
	color: #f6fbff;
	letter-spacing: 0.03em;
}

.fd-logo-wrap p {
	margin: 0;
	font-size: 0.78rem;
	color: rgba(236, 246, 255, 0.72);
}

.fd-section h2 {
	font-size: 0.74rem;
	font-weight: 700;
	margin: 0.65rem 0 0.55rem;
	color: #92b8ca;
	text-transform: uppercase;
	letter-spacing: 0.08em;
}

.fd-nav-link {
	display: block;
	padding: 0.58rem 0.7rem;
	margin-bottom: 0.25rem;
	border-radius: 9px;
	color: #dceaf4;
	text-decoration: none;
	font-size: 0.92rem;
	transition: background 0.2s ease, transform 0.2s ease, color 0.2s ease;
}

.fd-nav-link:hover {
	background: rgba(53, 174, 181, 0.22);
	transform: translateX(2px);
	color: #ffffff;
}

.fd-nav-link.active {
	background: linear-gradient(135deg, #1e9ca7, #276f9c);
	color: #ffffff;
	font-weight: 600;
	box-shadow: 0 8px 18px rgba(13, 64, 89, 0.35);
}

.fd-nav-link.disabled {
	opacity: 0.55;
	cursor: not-allowed;
}

@media (max-width: 1100px) {
	.fd-sidebar {
		padding: 1rem 0.45rem;
	}

	.fd-logo-wrap h1,
	.fd-logo-wrap p,
	.fd-section h2,
	.fd-nav-link span {
		display: none;
	}

	.fd-logo-wrap {
		justify-content: center;
	}

	.fd-nav-link {
		text-align: center;
		padding: 0.65rem 0.45rem;
	}
}

@media (max-width: 760px) {
	.fd-sidebar {
		position: static;
		height: auto;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.65rem;
	}

	.fd-logo-wrap {
		margin-bottom: 0;
		padding-bottom: 0;
		border: none;
	}

	.fd-section {
		display: none;
	}
}
</style>
