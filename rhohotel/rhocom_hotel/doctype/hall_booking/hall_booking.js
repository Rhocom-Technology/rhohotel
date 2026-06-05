// Copyright (c) 2025, Rhocom Technology Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Hall Booking", {
	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			frm.set_df_property("hall", "read_only", 1);
			frm.set_df_property("start_datetime", "read_only", 1);
			frm.set_df_property("end_datetime", "read_only", 1);
			frm.set_df_property("rate", "read_only", 1);
			frm.set_df_property("total_days", "read_only", 1);
			frm.set_df_property("total_amount", "read_only", 1);
			frm.set_df_property("net_total", "read_only", 1);

			frm.add_custom_button(
				__("Booking Adjustment"),
				() => open_date_adjustment_dialog(frm)
			);

			if (frm.doc.sales_invoice) {
				frm.add_custom_button(__("Receive Payment"), () => {
					const d = new frappe.ui.Dialog({
						title: __("Receive Payment"),
						fields: [
							{
								fieldname: "payment_date",
								label: "Payment Date",
								fieldtype: "Date",
								default: frappe.datetime.nowdate(),
								reqd: 1
							},
							{
								fieldname: "payment_mode",
								label: "Mode of Payment",
								fieldtype: "Link",
								options: "Mode of Payment",
								reqd: 1
							},
							{
								fieldname: "paid_amount",
								label: "Amount Paid",
								fieldtype: "Currency",
								default: frm.doc.net_total,
								reqd: 1
							},
							{
								fieldname: "reference_no",
								label: "Reference No",
								fieldtype: "Data"
							},
							{
								fieldname: "reference_date",
								label: "Reference Date",
								fieldtype: "Date"
							},
							{
								fieldname: "remarks",
								label: "Remarks",
								fieldtype: "Small Text"
							}
						],
						primary_action_label: __("Submit Payment"),
						primary_action(values) {
							if (values.paid_amount <= 0) {
								frappe.msgprint(__("Paid amount must be greater than zero."));
								return;
							}

							frappe.call({
								method: "rhohotel.rhocom_hotel.doctype.hall_booking.hall_booking.create_payment_entry",
								args: {
									booking: frm.doc.name,
									data: JSON.stringify(values)
								},
								freeze: true,
								callback(r) {
									if (!r.exc) {
										frappe.msgprint({
											title: __("Payment Successful"),
											message: __("Payment Entry {0} created.", [r.message]),
											indicator: "green"
										});
										d.hide();
										frm.reload_doc();
									}
								}
							});
						}
					});

					d.show();
				});
			}

			frappe.call({
				method: "rhohotel.rhocom_hotel.doctype.hall_booking.hall_booking.get_payment_status",
				args: {
					booking_name: frm.doc.name
				},
				callback(r) {
					if (r.message) {
						const color = r.message.includes("Paid") ? "green" : "red";
						frm.fields_dict.payment_status.html(
							`<span style="color:${color}; font-weight:bold;">${r.message}</span>`
						);
					} else {
						frm.fields_dict.payment_status.html(
							"<span style='color:red; font-weight:bold;'>Unpaid</span>"
						);
					}
				}
			});
		}
	},

	start_datetime(frm) {
		calculate_total_days(frm);
		calculate_total_amount(frm);
	},

	end_datetime(frm) {
		calculate_total_days(frm);
		calculate_total_amount(frm);
	},

	discount_type(frm) {
		calculate_net_total_amount(frm);
	},

	discount_amount(frm) {
		calculate_net_total_amount(frm);
	},

	hall(frm) {
		if (!frm.doc.hall) {
			frm.set_value("rate", 0);
			calculate_total_amount(frm);
			return;
		}

		frappe.call({
			method: "rhohotel.rhocom_hotel.doctype.hall_booking.hall_booking.get_hall_rate",
			args: {
				hall_name: frm.doc.hall
			},
			callback(r) {
				frm.set_value("rate", r.message || 0);
				calculate_total_amount(frm);
			}
		});
	}
});


frappe.ui.form.on("Hall Booking Additional Billing", {
	service(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);

		if (!row.service) {
			frm.refresh_field("additional_billings");
			return;
		}

		frappe.call({
			method: "rhohotel.rhocom_hotel.doctype.hall_service.hall_service.get_service_rate",
			args: {
				hall_service: row.service
			},
			callback(r) {
				if (r.message) {
					let rate = r.message;
					frappe.model.set_value(cdt, cdn, "rate", rate);
					frappe.model.set_value(cdt, cdn, "amount", (rate * row.qty) - (row.discount_amount || 0));
				}

				frm.refresh_field("additional_billings");
				calculate_net_total_amount(frm);
			}
		});
	},

	rate(frm, cdt, cdn) {
		update_additional_billing_row(frm, cdt, cdn);
	},

	qty(frm, cdt, cdn) {
		update_additional_billing_row(frm, cdt, cdn);
	},

	discount_amount(frm, cdt, cdn) {
		update_additional_billing_row(frm, cdt, cdn);
	}
});


function update_additional_billing_row(frm, cdt, cdn) {
	let row = frappe.get_doc(cdt, cdn);
	frappe.model.set_value(
		cdt,
		cdn,
		"amount",
		((row.rate || 0) * (row.qty || 0)) - (row.discount_amount || 0)
	);

	frm.refresh_field("additional_billings");
	calculate_net_total_amount(frm);
}


function open_date_adjustment_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: "Adjust Booking Dates",
		fields: [
			{
				fieldname: "new_start_datetime",
				label: "New Start Date",
				fieldtype: "Datetime",
				reqd: 1,
				default: frm.doc.start_datetime,
				onchange() {
					update_dialog_total_days(d);
				}
			},
			{
				fieldname: "new_total_days",
				label: "Total Days",
				fieldtype: "Int",
				reqd: 1,
				default: frm.doc.total_days,
				read_only: 1
			},
			{
				fieldname: "column_break11",
				fieldtype: "Column Break"
			},
			{
				fieldname: "new_end_datetime",
				label: "New End Date",
				fieldtype: "Datetime",
				reqd: 1,
				default: frm.doc.end_datetime,
				onchange() {
					update_dialog_total_days(d);
				}
			},
			{
				fieldtype: "Section Break",
				fieldname: "section_break144"
			},
			{
				fieldname: "reason",
				label: "Adjustment Reason",
				fieldtype: "Small Text",
				reqd: 1
			}
		],
		primary_action_label: "Apply Adjustment",
		primary_action(values) {
			frappe.call({
				method: "rhohotel.rhocom_hotel.doctype.hall_booking.hall_booking.adjust_booking_datetime",
				args: {
					booking_name: frm.doc.name,
					start_datetime: values.new_start_datetime,
					end_datetime: values.new_end_datetime,
					reason: values.reason
				},
				freeze: true,
				callback() {
					d.hide();
					frm.reload_doc();
				}
			});
		}
	});

	d.show();
}


function update_dialog_total_days(d) {
	const start_value = d.get_value("new_start_datetime");
	const end_value = d.get_value("new_end_datetime");

	if (!start_value || !end_value) return;

	const start = new Date(start_value);
	const end = new Date(end_value);

	if (end <= start) {
		d.set_value("new_total_days", 0);
		return;
	}

	const diff_ms = end - start;
	const days = Math.ceil(diff_ms / (1000 * 60 * 60 * 24));

	d.set_value("new_total_days", Math.max(days, 1));
}


function calculate_total_days(frm) {
	if (frm.doc.start_datetime && frm.doc.end_datetime) {
		const start = new Date(frm.doc.start_datetime);
		const end = new Date(frm.doc.end_datetime);

		if (end <= start) {
			frm.set_value("total_days", 0);
			return;
		}

		const diff_ms = end - start;
		const days = Math.ceil(diff_ms / (1000 * 60 * 60 * 24));

		frm.set_value("total_days", Math.max(days, 1));
	}
}


function calculate_total_amount(frm) {
	const rate = Number(frm.doc.rate || 0);
	const total_days = Number(frm.doc.total_days || 0);

	if (rate && total_days) {
		frm.set_value("total_amount", rate * total_days);
	} else {
		frm.set_value("total_amount", 0);
	}

	calculate_net_total_amount(frm);
}


function calculate_net_total_amount(frm) {
	let additional_billings_total = 0;

	if (frm.doc.additional_billings && frm.doc.additional_billings.length > 0) {
		frm.doc.additional_billings.forEach(function (row) {
			additional_billings_total += row.amount || 0;
		});
	}

	let net_total = (frm.doc.total_amount || 0) + additional_billings_total;
	let discount = frm.doc.discount_amount || 0;

	if (discount > 0) {
		if (frm.doc.discount_type === "Percentage") {
			discount = (discount / 100) * net_total;
		}

		net_total -= discount;
	}

	frm.set_value("net_total", Math.max(net_total, 0));
}