import { initSocket } from 'frappe-ui'

let socket = null

try {
  socket = initSocket()
} catch (e) {
  console.warn('Could not initialise socket.io — real-time events disabled.', e)
}

export { socket }
