frappe.ui.form.on('Shift Swap Request', {
  refresh(frm) {
    frm.set_query('requesting_employee', () => {
      return {
        filters: {
          status: 'Active',
          department: frm.doc.department || ''
        }
      }
    })

    frm.set_query('target_employee', () => {
      return {
        filters: {
          status: 'Active',
          department: frm.doc.department || '',
          name: ['!=', frm.doc.requesting_employee || '']
        }
      }
    })

    if (!frm.is_new() && frm.doc.status === 'Pending') {
      frm.add_custom_button(__('Approve Swap'), () => {
        approve_swap(frm)
      }, __('Actions'))

      frm.add_custom_button(__('Reject'), () => {
        reject_swap(frm)
      }, __('Actions'))
    }

    if (frm.doc.status === 'Approved' || frm.doc.status === 'Rejected') {
      frm.disable_form()
    }
  },

  department(frm) {
    frm.set_value('requesting_employee', '')
    frm.set_value('target_employee', '')
    clear_shift_fields(frm)
  },

  swap_date(frm) {
    fetch_shift_details(frm)
  },

  requesting_employee(frm) {
    if (
      frm.doc.requesting_employee &&
      frm.doc.target_employee &&
      frm.doc.requesting_employee === frm.doc.target_employee
    ) {
      frappe.msgprint(__('Requesting Employee and Target Employee cannot be the same.'))
      frm.set_value('requesting_employee', '')
      return
    }

    fetch_shift_details(frm)
  },

  target_employee(frm) {
    if (
      frm.doc.requesting_employee &&
      frm.doc.target_employee &&
      frm.doc.requesting_employee === frm.doc.target_employee
    ) {
      frappe.msgprint(__('Requesting Employee and Target Employee cannot be the same.'))
      frm.set_value('target_employee', '')
      return
    }

    fetch_shift_details(frm)
  }
})

function clear_shift_fields(frm) {
  frm.set_value('requesting_employee_name', '')
  frm.set_value('requesting_shift', '')
  frm.set_value('requesting_shift_time', '')
  frm.set_value('target_employee_name', '')
  frm.set_value('target_shift', '')
  frm.set_value('target_shift_time', '')
  frm.set_value('check_status', 'Review')
}

function fetch_shift_details(frm) {
  if (!frm.doc.department || !frm.doc.swap_date) {
    return
  }

  if (frm.doc.requesting_employee) {
    frappe.call({
      method: 'rhohotel.rhocom_hotel.api.swap_request.get_employee_shift',
      args: {
        employee: frm.doc.requesting_employee,
        date: frm.doc.swap_date
      },
      callback(r) {
        const data = r.message
        if (!data) return

        frm.set_value('requesting_employee_name', data.employee_name)
        frm.set_value('requesting_shift', data.value)
        frm.set_value('requesting_shift_time', data.time)
      }
    })
  }

  if (frm.doc.target_employee) {
    frappe.call({
      method: 'rhohotel.rhocom_hotel.api.swap_request.get_employee_shift',
      args: {
        employee: frm.doc.target_employee,
        date: frm.doc.swap_date
      },
      callback(r) {
        const data = r.message
        if (!data) return

        frm.set_value('target_employee_name', data.employee_name)
        frm.set_value('target_shift', data.value)
        frm.set_value('target_shift_time', data.time)
      }
    })
  }

  if (
    frm.doc.department &&
    frm.doc.swap_date &&
    frm.doc.requesting_employee &&
    frm.doc.target_employee
  ) {
    frappe.call({
      method: 'rhohotel.rhocom_hotel.api.swap_request.check_swap_availability',
      args: {
        department: frm.doc.department,
        date: frm.doc.swap_date,
        requesting_employee: frm.doc.requesting_employee,
        target_employee: frm.doc.target_employee
      },
      callback(r) {
        const data = r.message
        if (!data) return

        frm.set_value('check_status', data.ok ? 'Clear' : 'Conflict')

        if (!data.ok && data.errors && data.errors.length) {
          frappe.msgprint({
            title: __('Availability & Conflict Check'),
            message: data.errors.join('<br>'),
            indicator: 'red'
          })
        }
      }
    })
  }
}

function approve_swap(frm) {
  frappe.prompt(
    [
      {
        fieldname: 'manager_note',
        fieldtype: 'Small Text',
        label: __('Manager Note')
      }
    ],
    (values) => {
      frappe.call({
        method: 'rhohotel.rhocom_hotel.api.swap_request.approve_swap_request',
        args: {
          name: frm.doc.name,
          manager_note: values.manager_note || ''
        },
        freeze: true,
        freeze_message: __('Approving shift swap...'),
        callback(r) {
          if (r.message && r.message.ok) {
            frappe.msgprint(__('Shift swap approved and applied.'))
            frm.reload_doc()
          }
        }
      })
    },
    __('Approve Swap'),
    __('Approve')
  )
}

function reject_swap(frm) {
  frappe.prompt(
    [
      {
        fieldname: 'manager_note',
        fieldtype: 'Small Text',
        label: __('Manager Note'),
        reqd: 1
      }
    ],
    (values) => {
      frappe.call({
        method: 'rhohotel.rhocom_hotel.api.swap_request.reject_swap_request',
        args: {
          name: frm.doc.name,
          manager_note: values.manager_note
        },
        freeze: true,
        freeze_message: __('Rejecting shift swap request...'),
        callback(r) {
          if (r.message && r.message.ok) {
            frappe.msgprint(__('Shift swap request rejected.'))
            frm.reload_doc()
          }
        }
      })
    },
    __('Reject Swap Request'),
    __('Reject')
  )
}