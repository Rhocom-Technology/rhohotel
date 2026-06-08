import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/index.css'
import {
    setConfig,
    frappeRequest,
    resourcesPlugin,
    Button,
    FeatherIcon
} from 'frappe-ui'
import { getCsrfToken } from './lib/api'
import { useSessionStore } from './stores/session'

const csrfToken = getCsrfToken()
if (csrfToken && !window.csrf_token) {
    window.csrf_token = csrfToken
}

setConfig('resourceFetcher', (options = {}) => {
    options.headers = { ...(options.headers || {}) }

    const token = getCsrfToken()
    if (token && token !== 'Guest') {
        options.headers['X-Frappe-CSRF-Token'] = token
    }

    return frappeRequest(options)
})

setConfig('cache', false)

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(resourcesPlugin)
app.component('Button', Button)
app.component('FeatherIcon', FeatherIcon)

const session = useSessionStore(pinia)

session.initialize().finally(() => {
    app.mount('#app')
})