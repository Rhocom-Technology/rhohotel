import { buildRoutes } from "./router.js";

const VUE_CDN = "https://unpkg.com/vue@3/dist/vue.global.prod.js";
const VUE_ROUTER_CDN = "https://unpkg.com/vue-router@4/dist/vue-router.global.prod.js";
const SFC_LOADER_CDN = "https://unpkg.com/vue3-sfc-loader/dist/vue3-sfc-loader.js";
const BASE_PATH = "/assets/rhohotel/frontend/frontdesk";

const mountedApps = new Map();
let bootPromise = null;

function loadScript(src) {
	return new Promise((resolve, reject) => {
		const existing = Array.from(document.scripts).find((s) => s.src === src);
		if (existing) {
			if (existing.dataset.loaded === "true") {
				resolve();
				return;
			}
			existing.addEventListener("load", () => resolve(), { once: true });
			existing.addEventListener("error", (err) => reject(err), { once: true });
			return;
		}

		const script = document.createElement("script");
		script.src = src;
		script.async = true;
		script.addEventListener("load", () => {
			script.dataset.loaded = "true";
			resolve();
		});
		script.addEventListener("error", (err) => reject(err));
		document.head.appendChild(script);
	});
}

async function ensureVueRuntime() {
	if (!bootPromise) {
		bootPromise = Promise.all([
			loadScript(VUE_CDN),
			loadScript(VUE_ROUTER_CDN),
			loadScript(SFC_LOADER_CDN),
		]);
	}
	await bootPromise;
}

function createLoaderOptions() {
	const { Vue, VueRouter } = window;

	return {
		moduleCache: {
			vue: Vue,
			"vue-router": VueRouter,
		},
		async getFile(url) {
			const res = await fetch(url);
			if (!res.ok) {
				throw new Error(`${res.status} ${res.statusText} while loading ${url}`);
			}
			return {
				getContentData: (asBinary) => (asBinary ? res.arrayBuffer() : res.text()),
			};
		},
		addStyle(textContent) {
			const style = Object.assign(document.createElement("style"), {
				textContent,
			});
			document.head.appendChild(style);
		},
	};
}

function createVueLoader(options) {
	const { loadModule } = window["vue3-sfc-loader"];
	return (path) =>
		window.Vue.defineAsyncComponent(() => loadModule(path, options));
}

function buildGreeting() {
	const hour = new Date().getHours();
	if (hour < 12) return "Good Morning";
	if (hour < 17) return "Good Afternoon";
	return "Good Evening";
}

export async function mountVueApp(selector) {
	await ensureVueRuntime();

	const mountEl = typeof selector === "string" ? document.querySelector(selector) : selector;
	if (!mountEl) {
		throw new Error("Front Desk mount element not found");
	}

	if (mountedApps.has(mountEl)) {
		return mountedApps.get(mountEl);
	}

	const { Vue, VueRouter } = window;
	const options = createLoaderOptions();
	const loadVueComponent = createVueLoader(options);

	const router = VueRouter.createRouter({
		history: VueRouter.createWebHashHistory(),
		routes: buildRoutes(loadVueComponent, BASE_PATH),
	});

	const AppLayout = loadVueComponent(`${BASE_PATH}/layout/AppLayout.vue`);
	const Sidebar = loadVueComponent(`${BASE_PATH}/layout/Sidebar.vue`);
	const TopHeader = loadVueComponent(`${BASE_PATH}/layout/TopHeader.vue`);
	const StatCard = loadVueComponent(`${BASE_PATH}/components/StatCard.vue`);
	const RoomCard = loadVueComponent(`${BASE_PATH}/components/RoomCard.vue`);
	const FilterBar = loadVueComponent(`${BASE_PATH}/components/FilterBar.vue`);
	const AIInsightBanner = loadVueComponent(`${BASE_PATH}/components/AIInsightBanner.vue`);

	const app = Vue.createApp({
		components: { AppLayout },
		setup() {
			return {
				initialGreeting: buildGreeting(),
			};
		},
		template: "<AppLayout :greeting='initialGreeting' />",
	});

	app.component("Sidebar", Sidebar);
	app.component("TopHeader", TopHeader);
	app.component("StatCard", StatCard);
	app.component("RoomCard", RoomCard);
	app.component("FilterBar", FilterBar);
	app.component("AIInsightBanner", AIInsightBanner);

	app.use(router);
	app.mount(mountEl);
	mountedApps.set(mountEl, app);
	return app;
}
