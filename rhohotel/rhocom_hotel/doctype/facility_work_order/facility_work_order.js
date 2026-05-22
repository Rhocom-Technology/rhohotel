frappe.ui.form.on('Facility Work Order', {
    refresh(frm) {
        frm.set_query('asset', () => ({
            filters: { docstatus: ['!=', 2] }
        }))

        frm.set_query('assigned_technician', () => ({
            filters: { visible_for_assignment: 1 }
        }))
    },

    location_type(frm) {
        frm.set_value('room', null)
        frm.set_value('asset_location', null)
        frm.set_value('location_description', null)
    }
})