// frappe.ui.form.on('Maintenance Task', {

//     setup(frm) {
//         frm.set_query('supervisor', () => ({ filters: { status: 'Active' } }));
//     },

//     supervisor(frm) {
//         frm.trigger('validate_technician_supervisor');
//     },

//     validate_technician_supervisor(frm) {
//         if (
//             frm.doc.assigned_technician &&
//             frm.doc.supervisor &&
//             frm.doc.assigned_technician === frm.doc.supervisor
//         ) {
//             frappe.msgprint({
//                 title: __('Invalid Assignment'),
//                 message: __('The Assigned Technician and Supervisor cannot be the same person.'),
//                 indicator: 'red'
//             });
//             frm.set_value('supervisor', null);
//         }
//     },

//     end_time(frm) {
//         if (!frm.doc.start_time || !frm.doc.end_time) return;

//         const start = new Date(frm.doc.start_time.replace(' ', 'T'));
//         const end = new Date(frm.doc.end_time.replace(' ', 'T'));

//         if (end <= start) {
//             frappe.msgprint({
//                 title: __('Invalid Time'),
//                 message: __('End Time must be after Start Time.'),
//                 indicator: 'red'
//             });
//             frm.set_value('end_time', null);
//         }
//     },

//     refresh(frm) {
//         if (frm.doc.maintenance_request) {
//             frm.add_custom_button(__('Maintenance Request'), () => {
//                 frappe.set_route(
//                     'Form',
//                     'Maintenance Request',
//                     frm.doc.maintenance_request
//                 );
//             }, __('View'));
//         }
//     }
// });



// frappe.ui.form.on('Maintenance Task', {
//     end_time(frm) {
//         if (!frm.doc.start_time || !frm.doc.end_time) return

//         const start = new Date(frm.doc.start_time.replace(' ', 'T'))
//         const end = new Date(frm.doc.end_time.replace(' ', 'T'))

//         if (end <= start) {
//             frappe.msgprint({
//                 title: __('Invalid Time'),
//                 message: __('End Time must be after Start Time.'),
//                 indicator: 'red'
//             })

//             frm.set_value('end_time', null)
//         }
//     },

//     refresh(frm) {
//         if (frm.doc.maintenance_request) {
//             frm.add_custom_button(__('Maintenance Request'), () => {
//                 frappe.set_route(
//                     'Form',
//                     'Maintenance Request',
//                     frm.doc.maintenance_request
//                 )
//             }, __('View'))
//         }
//     }
// })


// frappe.ui.form.on('Maintenance Task', {
//     refresh(frm) {
//         if (frm.doc.maintenance_request) {
//             frm.add_custom_button(__('Maintenance Request'), () => {
//                 frappe.set_route(
//                     'Form',
//                     'Maintenance Request',
//                     frm.doc.maintenance_request
//                 )
//             }, __('View'))
//         }

//         refresh_all_available_qty(frm)
//     },

//     end_time(frm) {
//         if (!frm.doc.start_time || !frm.doc.end_time) return

//         const start = new Date(frm.doc.start_time.replace(' ', 'T'))
//         const end = new Date(frm.doc.end_time.replace(' ', 'T'))

//         if (end <= start) {
//             frappe.msgprint({
//                 title: __('Invalid Time'),
//                 message: __('End Time must be after Start Time.'),
//                 indicator: 'red'
//             })

//             frm.set_value('end_time', null)
//         }
//     }
// })


// frappe.ui.form.on('Maintenance Parts Used', {
//     item_code(frm, cdt, cdn) {
//         update_available_qty(frm, cdt, cdn)
//     },

//     warehouse(frm, cdt, cdn) {
//         update_available_qty(frm, cdt, cdn)
//     }
// })


// function refresh_all_available_qty(frm) {
//     ;(frm.doc.parts_used || []).forEach(row => {
//         update_available_qty(frm, row.doctype, row.name)
//     })

//     ;(frm.doc.parts_returned || []).forEach(row => {
//         update_available_qty(frm, row.doctype, row.name)
//     })
// }


// function update_available_qty(frm, cdt, cdn) {
//     const row = locals[cdt][cdn]

//     if (!row || !row.item_code || !row.warehouse) {
//         frappe.model.set_value(cdt, cdn, 'available_qty', 0)
//         return
//     }

//     frappe.db.get_value(
//         'Bin',
//         {
//             item_code: row.item_code,
//             warehouse: row.warehouse
//         },
//         'actual_qty'
//     ).then(r => {
//         const qty = r.message && r.message.actual_qty
//             ? r.message.actual_qty
//             : 0

//         frappe.model.set_value(cdt, cdn, 'available_qty', qty)
//     })
// }





// frappe.ui.form.on('Maintenance Task', {
//     refresh(frm) {
//         apply_witness_field_rules(frm)

//         if (frm.doc.maintenance_request) {
//             frm.add_custom_button(__('Maintenance Request'), () => {
//                 frappe.set_route(
//                     'Form',
//                     'Maintenance Request',
//                     frm.doc.maintenance_request
//                 )
//             }, __('View'))
//         }

//         refresh_all_available_qty(frm)
//     },

//     supervisor(frm) {
//         apply_witness_field_rules(frm)
//     },

//     end_time(frm) {
//         if (!frm.doc.start_time || !frm.doc.end_time) return

//         const start = new Date(frm.doc.start_time.replace(' ', 'T'))
//         const end = new Date(frm.doc.end_time.replace(' ', 'T'))

//         if (end <= start) {
//             frappe.msgprint({
//                 title: __('Invalid Time'),
//                 message: __('End Time must be after Start Time.'),
//                 indicator: 'red'
//             })

//             frm.set_value('end_time', null)
//         }
//     }
// })


// frappe.ui.form.on('Maintenance Parts Used', {
//     item_code(frm, cdt, cdn) {
//         update_available_qty(frm, cdt, cdn)
//     },

//     warehouse(frm, cdt, cdn) {
//         update_available_qty(frm, cdt, cdn)
//     }
// })


// // function apply_witness_field_rules(frm) {
// //     const witness_fields = [
// //         'supervisor_verified',
// //         'test_run_passed'
// //     ]

// //     witness_fields.forEach(fieldname => {
// //         frm.toggle_display(fieldname, false)
// //         frm.set_df_property(fieldname, 'read_only', 1)
// //     })

// //     if (!frm.doc.supervisor) {
// //         frm.refresh_fields(witness_fields)
// //         return
// //     }

// //     frappe.db.get_value(
// //         'Employee',
// //         frm.doc.supervisor,
// //         'user_id'
// //     ).then(r => {
// //         const witness_user = (
// //             r.message &&
// //             r.message.user_id
// //         ) || ''

// //         const is_witness = witness_user === frappe.session.user
// //         const is_system_manager = frappe.user.has_role('System Manager')

// //         const can_verify = is_witness || is_system_manager

// //         witness_fields.forEach(fieldname => {
// //             frm.toggle_display(fieldname, can_verify)
// //             frm.set_df_property(fieldname, 'read_only', !can_verify)
// //         })

// //         frm.refresh_fields(witness_fields)
// //     })
// // }

// function apply_witness_field_rules(frm) {
//     const witness_fields = ['supervisor_verified', 'test_run_passed']

//     const is_hotel_manager = frappe.user.has_role('Hotel Manager')
//     const is_system_manager = frappe.user.has_role('System Manager')

//     // Hotel Manager / System Manager: show read-only, never editable
//     if (is_hotel_manager || is_system_manager) {
//         witness_fields.forEach(fieldname => {
//             frm.toggle_display(fieldname, true)
//             frm.set_df_property(fieldname, 'read_only', 1)
//         })
//         frm.refresh_fields(witness_fields)
//         return
//     }

//     // Everyone else: hide by default until we confirm they are the witness
//     witness_fields.forEach(fieldname => {
//         frm.toggle_display(fieldname, false)
//         frm.set_df_property(fieldname, 'read_only', 1)
//     })

//     if (!frm.doc.supervisor) {
//         frm.refresh_fields(witness_fields)
//         return
//     }

//     frappe.db.get_value('Employee', frm.doc.supervisor, 'user_id').then(r => {
//         const witness_user = (r.message && r.message.user_id) || ''
//         const is_witness = witness_user === frappe.session.user

//         witness_fields.forEach(fieldname => {
//             frm.toggle_display(fieldname, is_witness)
//             frm.set_df_property(fieldname, 'read_only', !is_witness)
//         })

//         frm.refresh_fields(witness_fields)
//     })
// }

// function refresh_all_available_qty(frm) {
//     ;(frm.doc.parts_used || []).forEach(row => {
//         update_available_qty(frm, row.doctype, row.name)
//     })

//     ;(frm.doc.parts_returned || []).forEach(row => {
//         update_available_qty(frm, row.doctype, row.name)
//     })
// }


// function update_available_qty(frm, cdt, cdn) {
//     const row = locals[cdt][cdn]

//     if (!row || !row.item_code || !row.warehouse) {
//         frappe.model.set_value(cdt, cdn, 'available_qty', 0)
//         return
//     }

//     frappe.db.get_value(
//         'Bin',
//         {
//             item_code: row.item_code,
//             warehouse: row.warehouse
//         },
//         'actual_qty'
//     ).then(r => {
//         const qty = (
//             r.message &&
//             r.message.actual_qty
//         ) || 0

//         frappe.model.set_value(
//             cdt,
//             cdn,
//             'available_qty',
//             qty
//         )
//     })
// }


// frappe.ui.form.on('Maintenance Task', {
//     refresh(frm) {
//         apply_witness_field_rules(frm)

//         // Reload if doc is submitted but form thinks it's dirty (stale UI state)
//         if (frm.doc.docstatus === 1 && frm.is_dirty()) {
//             frm.reload_doc()
//             return
//         }

//         if (frm.doc.maintenance_request) {
//             frm.add_custom_button(__('Maintenance Request'), () => {
//                 frappe.set_route(
//                     'Form',
//                     'Maintenance Request',
//                     frm.doc.maintenance_request
//                 )
//             }, __('View'))
//         }

//         refresh_all_available_qty(frm)
//     },

//     supervisor(frm) {
//         apply_witness_field_rules(frm)
//     },

//     end_time(frm) {
//         if (!frm.doc.start_time || !frm.doc.end_time) return

//         const start = new Date(frm.doc.start_time.replace(' ', 'T'))
//         const end = new Date(frm.doc.end_time.replace(' ', 'T'))

//         if (end <= start) {
//             frappe.msgprint({
//                 title: __('Invalid Time'),
//                 message: __('End Time must be after Start Time.'),
//                 indicator: 'red'
//             })

//             frm.set_value('end_time', null)
//         }
//     }
// })


// frappe.ui.form.on('Maintenance Parts Used', {
//     item_code(frm, cdt, cdn) {
//         update_available_qty(frm, cdt, cdn)
//     },

//     warehouse(frm, cdt, cdn) {
//         update_available_qty(frm, cdt, cdn)
//     }
// })


// function apply_witness_field_rules(frm) {
//     // const witness_fields = ['supervisor_verified', 'test_run_passed']
//     const witness_fields = [ 'test_run_passed']

//     const is_hotel_manager = frappe.user.has_role('Hotel Manager')
//     const is_system_manager = frappe.user.has_role('System Manager')

//     // Hotel Manager / System Manager: show read-only, never editable
//     if (is_hotel_manager || is_system_manager) {
//         witness_fields.forEach(fieldname => {
//             frm.toggle_display(fieldname, true)
//             frm.set_df_property(fieldname, 'read_only', 1)
//         })
//         frm.refresh_fields(witness_fields)
//         return
//     }

//     // Everyone else: hide by default until we confirm they are the witness
//     witness_fields.forEach(fieldname => {
//         frm.toggle_display(fieldname, false)
//         frm.set_df_property(fieldname, 'read_only', 1)
//     })

//     if (!frm.doc.supervisor) {
//         frm.refresh_fields(witness_fields)
//         return
//     }

//     frappe.db.get_value('Employee', frm.doc.supervisor, 'user_id').then(r => {
//         const witness_user = (r.message && r.message.user_id) || ''
//         const is_witness = witness_user === frappe.session.user

//         witness_fields.forEach(fieldname => {
//             frm.toggle_display(fieldname, is_witness)
//             frm.set_df_property(fieldname, 'read_only', !is_witness)
//         })

//         frm.refresh_fields(witness_fields)
//     })
// }


// function refresh_all_available_qty(frm) {
//     ;(frm.doc.parts_used || []).forEach(row => {
//         update_available_qty(frm, row.doctype, row.name)
//     })

//     ;(frm.doc.parts_returned || []).forEach(row => {
//         update_available_qty(frm, row.doctype, row.name)
//     })
// }


// function update_available_qty(frm, cdt, cdn) {
//     const row = locals[cdt][cdn]

//     if (!row || !row.item_code || !row.warehouse) {
//         frappe.model.set_value(cdt, cdn, 'available_qty', 0)
//         return
//     }

//     frappe.db.get_value(
//         'Bin',
//         {
//             item_code: row.item_code,
//             warehouse: row.warehouse
//         },
//         'actual_qty'
//     ).then(r => {
//         const qty = (
//             r.message &&
//             r.message.actual_qty
//         ) || 0

//         frappe.model.set_value(
//             cdt,
//             cdn,
//             'available_qty',
//             qty
//         )
//     })
// }




frappe.ui.form.on('Maintenance Task', {
    refresh(frm) {
        // Reload if submitted but form is stale
        if (frm.doc.docstatus === 1 && frm.is_dirty()) {
            frm.reload_doc()
            return
        }

        apply_witness_field_rules(frm)

        if (frm.doc.maintenance_request) {
            frm.add_custom_button(__('Maintenance Request'), () => {
                frappe.set_route(
                    'Form',
                    'Maintenance Request',
                    frm.doc.maintenance_request
                )
            }, __('View'))
        }

        // Only refresh qty on saved docs to avoid marking form dirty
        if (!frm.is_new() && !frm.is_dirty()) {
            refresh_all_available_qty(frm)
        }
    },

    supervisor(frm) {
        apply_witness_field_rules(frm)
    },

    end_time(frm) {
        if (!frm.doc.start_time || !frm.doc.end_time) return

        const start = new Date(frm.doc.start_time.replace(' ', 'T'))
        const end = new Date(frm.doc.end_time.replace(' ', 'T'))

        if (end <= start) {
            frappe.msgprint({
                title: __('Invalid Time'),
                message: __('End Time must be after Start Time.'),
                indicator: 'red'
            })

            frm.set_value('end_time', null)
        }
    }
})


frappe.ui.form.on('Maintenance Parts Used', {
    item_code(frm, cdt, cdn) {
        update_available_qty(frm, cdt, cdn)
    },

    warehouse(frm, cdt, cdn) {
        update_available_qty(frm, cdt, cdn)
    }
})


function apply_witness_field_rules(frm) {
    const witness_fields = ['test_run_passed']

    const is_hotel_manager = frappe.user.has_role('Hotel Manager')
    const is_system_manager = frappe.user.has_role('System Manager')

    // Hotel Manager / System Manager: show read-only, never editable
    if (is_hotel_manager || is_system_manager) {
        witness_fields.forEach(fieldname => {
            frm.toggle_display(fieldname, true)
            frm.set_df_property(fieldname, 'read_only', 1)
        })
        frm.refresh_fields(witness_fields)
        return
    }

    // Everyone else: hide by default until we confirm they are the witness
    witness_fields.forEach(fieldname => {
        frm.toggle_display(fieldname, false)
        frm.set_df_property(fieldname, 'read_only', 1)
    })

    if (!frm.doc.supervisor) {
        frm.refresh_fields(witness_fields)
        return
    }

    frappe.db.get_value('Employee', frm.doc.supervisor, 'user_id').then(r => {
        const witness_user = (r.message && r.message.user_id) || ''
        const is_witness = witness_user === frappe.session.user

        witness_fields.forEach(fieldname => {
            frm.toggle_display(fieldname, is_witness)
            frm.set_df_property(fieldname, 'read_only', !is_witness)
        })

        frm.refresh_fields(witness_fields)
    })
}


function refresh_all_available_qty(frm) {
    ;(frm.doc.parts_used || []).forEach(row => {
        update_available_qty(frm, row.doctype, row.name)
    })

    ;(frm.doc.parts_returned || []).forEach(row => {
        update_available_qty(frm, row.doctype, row.name)
    })
}


function update_available_qty(frm, cdt, cdn) {
    const row = locals[cdt][cdn]

    if (!row || !row.item_code || !row.warehouse) {
        frappe.model.set_value(cdt, cdn, 'available_qty', 0)
        return
    }

    frappe.db.get_value(
        'Bin',
        {
            item_code: row.item_code,
            warehouse: row.warehouse
        },
        'actual_qty'
    ).then(r => {
        const qty = (
            r.message &&
            r.message.actual_qty
        ) || 0

        frappe.model.set_value(
            cdt,
            cdn,
            'available_qty',
            qty
        )
    })
}