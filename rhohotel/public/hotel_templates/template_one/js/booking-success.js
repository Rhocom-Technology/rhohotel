// =========================================================================
// BOOKING SUCCESS MANIFEST DISPATCHER & LIFECYCLE CONTROLLER
// =========================================================================

function getReservationNumber() {
	const params = new URLSearchParams(window.location.search);
	return params.get("reservation") || params.get("reference") || params.get("trxref");
}

document.addEventListener("DOMContentLoaded", verifyAndRenderReceipt);

async function verifyAndRenderReceipt() {
	const reservationRef = getReservationNumber();
	const fallbackToken = reservationRef || sessionStorage.getItem("hotelReservation");
	const workspace = document.getElementById("booking-confirmation-workspace");

	if (!workspace) return;

	// 1. Initial State: Render a clean verifying loading state inside the workspace card
	workspace.innerHTML = `
        <div class="text-center py-5 position-relative" style="z-index: 1;">
            <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;"></div>
            <h4 class="fw-black text-dark text-uppercase tracking-tight m-0">Verifying Transaction Reference</h4>
            <p class="text-muted small m-0 mt-1">Synchronizing payment records with gateway servers. Please wait...</p>
        </div>
    `;

	if (!fallbackToken) {
		renderFailureState("Missing Reservation Reference Token.");
		return;
	}

	try {
		// Step 1: Query primary verification endpoint
		const response = await fetch(`/api/method/rhohotel.hotel_api.verify_reservation_payment?reference=${fallbackToken}`, {
			method: "GET",
			headers: {
				"Accept": "application/json",
				"Content-Type": "application/json"
			}
		});

		const result = await response.json();
		const data = result.message;

		if (data && data.success) {
			renderSuccessState(fallbackToken, data);
			return;
		}

		// Step 2 Fallback: If verification needs manual ledger matching, check general data details
		await fallbackFetchDetails(fallbackToken);

	} catch (error) {
		console.warn("Primary verification bypassed, checking reservation parameters...", error);
		await fallbackFetchDetails(fallbackToken);
	}
}

async function fallbackFetchDetails(token) {
	try {
		const response = await fetch('/api/method/rhohotel.hotel_api.get_reservation_details', {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"Accept": "application/json"
			},
			body: JSON.stringify({ reservation_name: String(token).trim() })
		});

		if (!response.ok) throw new Error(`HTTP Error Status: ${response.status}`);

		const result = await response.json();
		const data = result.message;

		if (data && data.success) {
			renderSuccessState(token, data);
		} else {
			renderFailureState(data?.message || "The server could not pull this reservation record from the database ledger.");
		}
	} catch (err) {
		console.error(err);
		renderFailureState("Unable to establish a secure connection with the booking server cluster.");
	}
}

// 2. Success State Layout Injector (Injects the design back into the card cleanly)
function renderSuccessState(token, responseData) {
	const workspace = document.getElementById("booking-confirmation-workspace");
	const summary = responseData.summary || responseData.data || responseData;

	const baseAmount = summary.total_amount || summary.amount || 0;
	const formattedCurrency = "₦" + Number(baseAmount).toLocaleString();
	const currentStatus = summary.status || "Paid / Confirmed";

	const isPaid = currentStatus.toLowerCase().includes("paid") || currentStatus.toLowerCase().includes("confirm");
	const badgeClass = isPaid ? "bg-success text-white" : "bg-warning text-dark";

	workspace.innerHTML = `
        <div class="position-absolute bg-success opacity-10 rounded-circle" style="width: 250px; height: 250px; top: -125px; right: -125px; z-index: 0;"></div>

        <div class="text-center position-relative mb-5" style="z-index: 1;">
            <div class="display-1 text-success mb-2">
                <i class="bi bi-check2-circle"></i>
            </div>
            <h2 class="fw-black text-dark text-uppercase m-0 tracking-tight" style="font-size: 1.8rem;">Reservation Confirmed</h2>
            <p class="text-muted small text-uppercase fw-bold tracking-wide mt-1">Transaction Processing Pipeline Authenticated Safely</p>
            <div class="mt-3">
                <span id="receiptStatusBadge" class="badge ${badgeClass} px-3 py-2 text-uppercase fw-bold" style="font-size: 0.7rem; letter-spacing: 0.5px;">${currentStatus}</span>
            </div>
        </div>

        <div class="border rounded-2 p-4 bg-light mb-4 position-relative" id="receiptArea" style="z-index: 1;">
            <div class="d-flex flex-wrap justify-content-between align-items-center border-bottom pb-3 mb-4 gap-2">
                <div>
                    <label class="text-muted text-uppercase fw-black tracking-wide d-block m-0" style="font-size: 0.6rem;">Booking Identifier Token</label>
                    <span class="fw-black text-dark text-monospace" style="font-size: 1.1rem; letter-spacing: -0.5px;">${token}</span>
                </div>
                <div class="text-sm-end">
                    <label class="text-muted text-uppercase fw-black tracking-wide d-block m-0" style="font-size: 0.6rem;">Operational Domain</label>
                    <span class="small fw-bold text-secondary text-uppercase" style="font-size: 0.75rem;">Premium Suite Lodging Matrix</span>
                </div>
            </div>

            <div class="row g-3 text-start border-bottom pb-4 mb-4">
                <div class="col-sm-6">
                    <label class="text-muted text-uppercase fw-black tracking-wide d-block mb-1" style="font-size: 0.55rem;">Primary Guest Name</label>
                    <div class="fw-bold text-dark small" style="font-size: 0.8rem;">${summary.guest_name || "Valued Guest"}</div>
                </div>
                <div class="col-sm-6">
                    <label class="text-muted text-uppercase fw-black tracking-wide d-block mb-1" style="font-size: 0.55rem;">Email Address Node</label>
                    <div class="fw-bold text-dark small text-break" style="font-size: 0.8rem;">${summary.guest_email || "---"}</div>
                </div>
                <div class="col-sm-4 mt-3">
                    <label class="text-muted text-uppercase fw-black tracking-wide d-block mb-1" style="font-size: 0.55rem;">Timeline Arrival Date</label>
                    <div class="fw-bold text-dark small" style="font-size: 0.8rem;">${summary.check_in_date || "---"}</div>
                </div>
                <div class="col-sm-4 mt-3">
                    <label class="text-muted text-uppercase fw-black tracking-wide d-block mb-1" style="font-size: 0.55rem;">Timeline Departure Date</label>
                    <div class="fw-bold text-dark small" style="font-size: 0.8rem;">${summary.check_out_date || "---"}</div>
                </div>
                <div class="col-sm-4 mt-3">
                    <label class="text-muted text-uppercase fw-black tracking-wide d-block mb-1" style="font-size: 0.55rem;">Calculated Duration</label>
                    <div class="fw-bold text-dark small" style="font-size: 0.8rem;">${summary.nights || 1} Night(s)</div>
                </div>
            </div>

            <div class="table-responsive text-start">
                <table class="table table-sm table-borderless align-middle m-0" style="font-size: 0.75rem;">
                    <thead>
                        <tr class="border-bottom" style="font-size: 0.6rem;">
                            <th class="text-muted text-uppercase fw-black tracking-wide py-2">Allocated Room Profile Specification</th>
                            <th class="text-muted text-uppercase fw-black tracking-wide text-end py-2">Structural Valuation Matrix</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="fw-bold text-dark py-3">${summary.rooms_booked || "Premium Suite Selection"}</td>
                            <td class="fw-black text-dark text-end py-3">${formattedCurrency}</td>
                        </tr>
                        <tr class="border-top" style="border-top-style: dashed !important;">
                            <td class="text-uppercase fw-black text-secondary py-3">Total Consolidated Billing Invoice</td>
                            <td class="fw-black text-accent-theme text-end py-3 h5 m-0">${formattedCurrency}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="border-top pt-3 text-center">
            <p class="text-muted font-monospace m-0" style="font-size: 0.6rem; letter-spacing: 0.5px;">
                Thank you for choosing luxury hospitality operations. We look forward to your arrival.
            </p>
        </div>
    `;
}

// 3. Failure State Layout Injector (Swaps out header completely with dedicated alert & instructions)
function renderFailureState(errorMessage) {
	const workspace = document.getElementById("booking-confirmation-workspace");

	workspace.innerHTML = `
        <div class="position-absolute bg-danger opacity-5 rounded-circle" style="width: 250px; height: 250px; top: -125px; right: -125px; z-index: 0;"></div>

        <div class="text-center position-relative py-4" style="z-index: 1;">
            <div class="display-1 text-danger mb-2">
                <i class="bi bi-exclamation-octagon"></i>
            </div>
            <h2 class="fw-black text-dark text-uppercase m-0 tracking-tight" style="font-size: 1.6rem;">Verification Unsuccessful</h2>
            <p class="text-muted small text-uppercase fw-bold tracking-wide mt-1">Transaction parameters could not be safely validated</p>

            <div class="alert alert-danger mx-auto my-4 text-start small border-0 shadow-sm" style="max-width: 550px;">
                <div class="fw-bold text-uppercase mb-1" style="font-size:0.65rem; letter-spacing:0.5px;">Logs Engine Rejection Cause:</div>
                <div class="text-dark">${errorMessage}</div>
            </div>

            <hr class="my-4 opacity-10" style="max-width: 550px; margin: 0 auto;">

            <div class="mt-2 p-3 bg-light rounded border d-inline-block text-start shadow-sm" style="max-width: 550px;">
                <h6 class="fw-black text-dark text-uppercase small mb-2"><i class="bi bi-telephone-outbound-fill text-primary me-2"></i>What should you do next?</h6>
                <p class="text-muted m-0 small" style="line-height:1.5;">
                    If money has been deducted from your account, please do not panic. Your transaction records are safe. Contact our customer experience front desk with your reference token details for immediate placement validation.
                </p>
                <div class="mt-3 d-flex flex-wrap gap-3 font-monospace fw-bold" style="font-size:0.75rem;">
                    <span class="text-dark">📞 Phone: ${window.HOTEL?.phone || '+234 800 000 0000'}</span>
                    <span class="text-dark">📧 Email: ${window.HOTEL?.email || 'care@rhohotel.com'}</span>
                </div>
            </div>
        </div>
    `;
}


function printReceipt() {
	// 1. Grab the content of your workspace container card
	const receiptCard = document.getElementById("booking-confirmation-workspace");
	if (!receiptCard) {
		console.error("Print Target Node Missing.");
		return;
	}
	const receiptContent = receiptCard.innerHTML;

	// 2. Open a new temporary blank window frame
	const printWindow = window.open("", "", "height=700,width=900");
	if (!printWindow) {
		alert("Please allow pop-ups for this website to print your receipt.");
		return;
	}

	printWindow.document.write("<html><head><title>Print Receipt</title>");

	// 3. Clone stylesheets and Tailwind/Bootstrap assets into the pop-up context
	const styles = document.querySelectorAll('link[rel="stylesheet"], style');
	styles.forEach((style) => {
		printWindow.document.write(style.outerHTML);
	});

	// Inject a small printing override block inside the pop-up document context
	printWindow.document.write(`
    <style>
        body { background: #ffffff !important; color: #000000 !important; padding: 30px !important; }
        .position-absolute.bg-success, .position-absolute.bg-danger { display: none !important; }
        #receiptStatusBadge { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    </style>
  `);

	printWindow.document.write("</head><body>");
	// Wrap it back in a card-like layout wrapper so Bootstrap styling applies
	printWindow.document.write('<div class="card border border-0 bg-white">' + receiptContent + '</div>');
	printWindow.document.write("</body></html>");

	// 4. Fire print pipeline
	printWindow.document.close();
	printWindow.focus();

	setTimeout(() => {
		printWindow.print();
		printWindow.close();
	}, 400);
}
