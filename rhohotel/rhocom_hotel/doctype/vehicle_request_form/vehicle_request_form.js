frappe.ui.form.on('Vehicle Request Form', {
    refresh(frm) {
        frm.set_query('hotel_vehicle', () => ({
            filters: {
                status: 'Active'
            }
        }))

        frm.set_query('staff_name', () => ({
            filters: {
                status: 'Active'
            }
        }))

        frm.set_df_property('registration_number', 'read_only', 1)
        frm.set_df_property('make_model', 'read_only', 1)
        frm.set_df_property('vehicle_asset', 'read_only', 1)
    },

    hotel_vehicle(frm) {
        if (!frm.doc.hotel_vehicle) {
            frm.set_value('registration_number', null)
            frm.set_value('make_model', null)
            frm.set_value('vehicle_asset', null)
            return
        }

        frappe.db.get_doc('Hotel Vehicle', frm.doc.hotel_vehicle).then(vehicle => {
            frm.set_value('registration_number', vehicle.plate_number || null)

            const makeModel = [vehicle.make, vehicle.model].filter(Boolean).join(' ')
            frm.set_value('make_model', makeModel || null)

            frm.set_value('vehicle_asset', vehicle.asset || null)
        })
    },

    staff_name(frm) {
        if (!frm.doc.staff_name) return

        frappe.db.get_doc('Employee', frm.doc.staff_name).then(employee => {
            if (employee.department && !frm.doc.department) {
                frm.set_value('department', employee.department)
            }
        })
    }
})