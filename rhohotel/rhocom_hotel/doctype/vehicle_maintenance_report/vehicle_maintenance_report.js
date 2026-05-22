frappe.ui.form.on('Vehicle Maintenance Report', {
    refresh(frm) {
        frm.set_query('facility_work_order', () => ({
            filters: {
                docstatus: ['!=', 2],
                workflow_state: ['in', [
                    'Pending Facility Supervisor Approval',
                    'In Progress',
                    'Completed'
                ]]
            },
            order_by: 'modified desc'
        }))

        frm.set_query('driver', () => ({
            filters: {
                status: 'Active'
            }
        }))

        frm.set_query('workshop_vendor', () => ({
            filters: {
                disabled: 0
            }
        }))

        frm.set_df_property('vehicle_asset', 'read_only', 1)
    },

    facility_work_order(frm) {
        if (!frm.doc.facility_work_order) {
            frm.set_value('vehicle_asset', null)
            return
        }

        frappe.db.get_doc('Facility Work Order', frm.doc.facility_work_order).then(doc => {
            frm.set_value('vehicle_asset', doc.asset || null)

            if (doc.contact_person && !frm.doc.driver) {
                frm.set_value('driver', doc.contact_person)
            }

            if (doc.description_of_problem && !frm.doc.issue_description) {
                frm.set_value('issue_description', doc.description_of_problem)
            }
        })
    },

    vehicle_asset(frm) {
        if (!frm.doc.vehicle_asset) return

        frappe.db.get_doc('Asset', frm.doc.vehicle_asset).then(asset => {
            if (!frm.doc.plate_registration_number) {
                if (asset.vehicle_registration_number) {
                    frm.set_value('plate_registration_number', asset.vehicle_registration_number)
                } else if (asset.registration_number) {
                    frm.set_value('plate_registration_number', asset.registration_number)
                } else if (asset.license_plate) {
                    frm.set_value('plate_registration_number', asset.license_plate)
                }
            }
        })
    }
})