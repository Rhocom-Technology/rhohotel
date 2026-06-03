function getReservationNumber() {
	const params = new URLSearchParams(window.location.search);

	return params.get("reservation") || params.get("reference") || params.get("trxref");
}

document.addEventListener("DOMContentLoaded", verifyBookingPayment);

async function verifyBookingPayment() {
	const reservation = getReservationNumber();
	const container = document.getElementById("bookingSuccessContainer");

	if (!container) return;

	if (!reservation) {
		showError(container, "Reservation not found.");
		return;
	}

	try {
		const response = await fetch(
			`/api/method/rhohotel.hotel_api.verify_reservation_payment?reference=${reservation}`,
		);

		const result = await response.json();
		const data = result.message;

		if (!data.success) {
			showError(container, data.message);
			return;
		}

		showSuccess(container, data);
	} catch (error) {
		showError(container, "Unable to verify payment. Please try again.");
	}
}

function printReceipt() {
	const receiptEl = document.getElementById("receiptArea");

	if (!receiptEl) return;

	const receipt = receiptEl.innerHTML;

	const win = window.open("", "_blank");

	win.document.write(`
        <html>
        <head><title>Receipt</title></head>
        <body>${receipt}</body>
        </html>
    `);

	win.document.close();
	win.print();
}

function showSuccess(container, data) {
	container.innerHTML = `
    <div class="web-confirmation-page">

        <!-- SUCCESS (still kept but minimal) -->
        <div class="web-success-banner">
            <i class="fa-solid fa-circle-check"></i>
            <h2>Booking Confirmed</h2>
            <p>Your reservation has been successfully processed</p>
        </div>

        <!-- SINGLE RECEIPT ONLY -->
        <div id="receiptArea" class="web-receipt">

            <!-- HOTEL HEADER -->
            <div class="web-receipt-header">

                <div class="web-hotel-branding">

                <img src="${window.HOTEL.logo || "/assets/rhohotel/logo.png"}"
     alt="Hotel Logo"
     onerror="this.src='/assets/rhohotel/logo.png'" />

                    <div>
                        <h2>${window.HOTEL.name}</h2>
                        <p>${window.HOTEL.email}</p>
                        <p>${window.HOTEL.phone}</p>
                        <small>${window.HOTEL.address || ""}</small>
                    </div>

                </div>
            </div>

            <!-- RECEIPT BODY (ALL IN ONE) -->
            <div class="web-receipt-body">

                <h3>Reservation Receipt</h3>

                <div class="web-receipt-row">
                    <strong>Guest Name</strong>
                    <span>${data.guest_name || ""}</span>
                </div>

                <div class="web-receipt-row">
                    <strong>Email</strong>
                    <span>${data.guest_email || ""}</span>
                </div>

                <div class="web-receipt-row">
                    <strong>Phone</strong>
                    <span>${data.guest_phone || ""}</span>
                </div>

                <div class="web-receipt-row">
                    <strong>Reservation</strong>
                    <span>${data.reservation}</span>
                </div>

                <div class="web-receipt-row">
                    <strong>Check-in</strong>
                    <span>${data.check_in || ""}</span>
                </div>

                <div class="web-receipt-row">
                    <strong>Check-out</strong>
                    <span>${data.check_out || ""}</span>
                </div>

                <div class="web-receipt-row">
                    <strong>Status</strong>
                    <span>${data.reservation_status}</span>
                </div>

                <div class="web-receipt-row">
                    <strong>Payment</strong>
                    <span>${data.payment_status}</span>
                </div>

            </div>

        </div>

        <!-- ACTIONS -->
        <div class="web-actions">

            <button class="web-btn-outline" onclick="window.print()">
                Print Receipt
            </button>

            <button class="web-btn-solid" onclick="window.location.href='/'">
                Back Home
            </button>

        </div>

    </div>
    `;
}

function showError(container, message) {
	container.innerHTML = `
        <div class="card shadow-sm border-danger">
            <div class="card-body text-center">

                <i class="fa-solid fa-triangle-exclamation text-danger display-3"></i>

                <h2 class="mt-3">Payment Failed</h2>

                <p>${message}</p>

                <hr>

                <p>
                    Please contact the hotel for assistance:
                </p>

                <p>
                    📞 <strong>+234 XXX XXX XXXX</strong><br>
                    📧 <strong>support@yourhotel.com</strong>
                </p>

            </div>
        </div>
    `;
}

function printReceipt() {
	window.print();
}
