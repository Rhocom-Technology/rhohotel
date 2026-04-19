frappe.pages["front-desk"].on_page_load = function (wrapper) {
    // Hide Frappe page header
    $(wrapper).closest('.page-head').hide();
    $(wrapper).closest('.layout-main-section').css('padding', '0');

    // Mount container
    wrapper.innerHTML = '<div id="app" style="height:100vh;width:100%;"></div>';

    // Load CSS
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/assets/rhohotel/frontend/index.css';
    document.head.appendChild(link);

    // Load Vue app
    import("/assets/rhohotel/frontend/index.js")
        .then((module) => {
            console.log("Front Desk Vue app loaded");
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
