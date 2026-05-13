frappe.pages["front-desk"].on_page_load = function (wrapper) {
    // Hide Frappe chrome
    document.querySelector('.navbar')?.style.setProperty('display', 'none', 'important');
    document.querySelector('.page-head')?.style.setProperty('display', 'none', 'important');
    document.body.style.overflow = 'hidden';

    // Mount container fullscreen
    wrapper.innerHTML = '<div id="app" style="height:100vh;width:100vw;position:fixed;top:0;left:0;z-index:99999;background:#f1f5f9;overflow:auto;"></div>';

    // Load CSS
    if (!document.querySelector('link[href*="rhohotel/frontend/index.css"]')) {
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/assets/rhohotel/frontend/index.css';
        document.head.appendChild(link);
    }

    // Load Vue app
    import("/assets/rhohotel/frontend/index.js")
        .then(() => {
            console.log("rhoHMS loaded successfully");
        })
        .catch((error) => {
            console.error("rhoHMS load error:", error);
            document.getElementById('app').innerHTML = `
                <div style="padding:2rem;font-family:sans-serif;">
                    <h3 style="color:#ef4444;">Failed to load rhoHMS</h3>
                    <p style="color:#6b7280;font-size:14px;">Error: ${error.message}</p>
                    <p style="color:#6b7280;font-size:14px;">Check browser console for details.</p>
                    <button onclick="location.reload()" style="margin-top:1rem;padding:8px 16px;background:#2563eb;color:white;border:none;border-radius:6px;cursor:pointer;">
                        Reload Page
                    </button>
                </div>
            `;
        });
};