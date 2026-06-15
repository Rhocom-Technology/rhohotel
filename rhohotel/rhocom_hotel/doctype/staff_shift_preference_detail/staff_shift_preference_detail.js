frappe.ui.form.on('Staff Shift Preference Detail', {
  date(frm, cdt, cdn) {
    const row = locals[cdt][cdn];

    if (!row.date) return;

    const date = frappe.datetime.str_to_obj(row.date);
    const day = date.toLocaleDateString('en-US', { weekday: 'long' });

    frappe.model.set_value(cdt, cdn, 'day', day);
  }
});