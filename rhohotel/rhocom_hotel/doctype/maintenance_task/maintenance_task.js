frappe.ui.form.on('Maintenance Task', {

    setup(frm) {
        frm.set_query('supervisor', () => ({ filters: { status: 'Active' } }));
    },

    supervisor(frm) {
        frm.trigger('validate_technician_supervisor');
    },

    validate_technician_supervisor(frm) {
        if (
            frm.doc.assigned_technician &&
            frm.doc.supervisor &&
            frm.doc.assigned_technician === frm.doc.supervisor
        ) {
            frappe.msgprint({
                title: __('Invalid Assignment'),
                message: __('The Assigned Technician and Supervisor cannot be the same person.'),
                indicator: 'red'
            });
            frm.set_value('supervisor', null);
        }
    },

    end_time(frm) {
        if (!frm.doc.start_time || !frm.doc.end_time) return;

        const start = new Date(frm.doc.start_time.replace(' ', 'T'));
        const end = new Date(frm.doc.end_time.replace(' ', 'T'));

        if (end <= start) {
            frappe.msgprint({
                title: __('Invalid Time'),
                message: __('End Time must be after Start Time.'),
                indicator: 'red'
            });
            frm.set_value('end_time', null);
        }
    },

    refresh(frm) {
        if (frm.doc.maintenance_request) {
            frm.add_custom_button(__('Maintenance Request'), () => {
                frappe.set_route(
                    'Form',
                    'Maintenance Request',
                    frm.doc.maintenance_request
                );
            }, __('View'));
        }
    }
});