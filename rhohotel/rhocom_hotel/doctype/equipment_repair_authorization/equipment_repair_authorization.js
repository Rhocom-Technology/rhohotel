frappe.ui.form.on('Equipment Repair Authorization', {
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

        frm.set_query('asset', () => ({
            filters: {
                docstatus: ['!=', 2]
            }
        }))

        frm.set_df_property('asset_id', 'read_only', 1)
    },

    facility_work_order(frm) {
        if (!frm.doc.facility_work_order) return

        frappe.db.get_doc('Facility Work Order', frm.doc.facility_work_order).then(doc => {
            if (doc.asset) {
                frm.set_value('asset', doc.asset)
                frm.set_value('asset_id', doc.asset)
            }

            if (doc.description_of_problem && !frm.doc.repair_description) {
                frm.set_value('repair_description', doc.description_of_problem)
            }

            if (doc.inspection_findings && !frm.doc.reason_for_repair) {
                frm.set_value('reason_for_repair', doc.inspection_findings)
            }
        })
    },

    asset(frm) {
        if (frm.doc.asset) {
            frm.set_value('asset_id', frm.doc.asset)
        } else {
            frm.set_value('asset_id', null)
        }
    }
})