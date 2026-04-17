frappe.pages["front-desk"].on_page_load = function (wrapper) {
	wrapper.innerHTML = '<div id="frontdesk-app"></div>';

	import("/assets/rhohotel/frontend/frontdesk/main.js")
		.then((module) => {
			module.mountVueApp("#frontdesk-app");
		})
		.catch((error) => {
			console.error("Failed to mount Front Desk Vue app", error);
			wrapper.innerHTML = `
				<div class="text-danger" style="padding: 1rem;">
					Unable to load Front Desk interface. Please refresh the page.
				</div>
			`;
		});
};
