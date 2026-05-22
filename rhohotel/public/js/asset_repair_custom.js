frappe.ui.form.on('Asset Repair', {

    refresh(frm) {
        frm.set_query('rh_facility_work_order', () => ({
            filters: {
                workflow_state: 'Pending Facility Supervisor Approval'
            }
        }))

        frm.set_query('rh_material_request', () => ({
            filters: {
                rh_facility_work_order: frm.doc.rh_facility_work_order || ['!=', ''],
                docstatus: 1
            },
            order_by: 'modified desc'
        }))
    },

    rh_facility_work_order(frm) {
        if (!frm.doc.rh_facility_work_order) return

        frm.set_value('rh_material_request', null)

        frappe.db.get_doc('Facility Work Order', frm.doc.rh_facility_work_order)
            .then(wo => {
                if (!frm.doc.asset && wo.asset) {
                    frm.set_value('asset', wo.asset)
                }
                if (!frm.doc.rh_vendor_technician && wo.assigned_technician) {
                    frm.set_value('rh_vendor_technician', wo.assigned_technician)
                }
                frm.set_query('rh_material_request', () => ({
                    filters: {
                        rh_facility_work_order: frm.doc.rh_facility_work_order,
                        docstatus: 1
                    },
                    order_by: 'modified desc'
                }))
            })
    },

    rh_material_request(frm) {
        if (!frm.doc.rh_material_request) return

        frappe.db.get_doc('Material Request', frm.doc.rh_material_request)
            .then(mr => {
                frm.clear_table('stock_items')
                mr.items.forEach(item => {
                    let row = frm.add_child('stock_items')
                    row.item_code = item.item_code
                    row.item_name = item.item_name
                    row.qty = item.qty
                    row.warehouse = item.warehouse || item.set_warehouse
                })
                frm.refresh_field('stock_items')
            })
    }
})