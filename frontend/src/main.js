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

setConfig('resourceFetcher', (url, options) => {
    if (!options) options = {}
    if (!options.headers) options.headers = {}
    options.credentials = 'include'

    const token = getCsrfToken()
    if (token && token !== 'Guest') {
        options.headers['X-Frappe-CSRF-Token'] = token
    }

    return frappeRequest(url, options)
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