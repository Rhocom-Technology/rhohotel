export function buildRoutes(loadVueComponent, basePath) {
	return [
		{ path: "/", redirect: "/room-view" },
		{
			path: "/room-view",
			name: "room-view",
			component: loadVueComponent(`${basePath}/pages/RoomView.vue`),
			meta: { pageTitle: "Room View" },
		},
		{
			path: "/check-ins",
			name: "check-ins",
			component: loadVueComponent(`${basePath}/pages/CheckIns.vue`),
			meta: { pageTitle: "Check-ins" },
		},
		{
			path: "/check-outs",
			name: "check-outs",
			component: loadVueComponent(`${basePath}/pages/CheckOuts.vue`),
			meta: { pageTitle: "Check-outs" },
		},
		{
			path: "/reservations",
			name: "reservations",
			component: loadVueComponent(`${basePath}/pages/Reservations.vue`),
			meta: { pageTitle: "Reservations" },
		},
		{
			path: "/corporate",
			name: "corporate",
			component: loadVueComponent(`${basePath}/pages/Corporate.vue`),
			meta: { pageTitle: "Corporate Reservations" },
		},
		{
			path: "/hall-bookings",
			name: "hall-bookings",
			component: loadVueComponent(`${basePath}/pages/HallBookings.vue`),
			meta: { pageTitle: "Hall Bookings" },
		},
		{
			path: "/guests",
			name: "guests",
			component: loadVueComponent(`${basePath}/pages/Guests.vue`),
			meta: { pageTitle: "Guests" },
		},
		{
			path: "/housekeeping",
			name: "housekeeping",
			component: loadVueComponent(`${basePath}/pages/Housekeeping.vue`),
			meta: { pageTitle: "Housekeeping" },
		},
		{
			path: "/payments",
			name: "payments",
			component: loadVueComponent(`${basePath}/pages/Payments.vue`),
			meta: { pageTitle: "Payments" },
		},
		{
			path: "/stay-report",
			name: "stay-report",
			component: loadVueComponent(`${basePath}/pages/StayReport.vue`),
			meta: { pageTitle: "Room Stay Report" },
		},
		{
			path: "/night-audit",
			name: "night-audit",
			component: loadVueComponent(`${basePath}/pages/NightAudit.vue`),
			meta: { pageTitle: "Night Audit" },
		},
	];
}
