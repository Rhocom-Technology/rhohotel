frappe.ui.form.on('Staff Shift Preference', {
  refresh(frm) {
    if (frm.doc.status === 'Submitted') {
      frm.disable_save();

      frm.dashboard.add_comment(
        __('This preference has been submitted and cannot be changed.'),
        'yellow',
        true
      );
    }
  },

  week_start(frm) {
    if (frm.doc.week_start) {
      frappe.call({
        method: 'frappe.client.get_value',
        args: {
          doctype: 'Staff Shift Preference',
          filters: {
            employee: frm.doc.employee,
            week_start: frm.doc.week_start
          },
          fieldname: ['name']
        },
        callback(r) {
          if (r.message && r.message.name && r.message.name !== frm.doc.name) {
            frappe.msgprint(__('A preference already exists for this employee and week.'));
          }
        }
      });
    }
  }
});