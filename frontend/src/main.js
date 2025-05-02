import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Import styles - added explicit import
import './styles/main.scss'

import App from './App.vue'
import router from './router'

// Import UI components
import Button from './components/ui/Button.vue'
import Card from './components/ui/Card.vue'
import PageContainer from './components/ui/PageContainer.vue'

import PrimeVue from 'primevue/config'
import 'primevue/resources/primevue.min.css' // Core CSS
import 'primevue/resources/themes/arya-blue/theme.css' // Minimal dark theme (can be swapped for unstyled if needed)
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'

const app = createApp(App)

// Create and use Pinia store
app.use(createPinia())
app.use(router)

// Register global components
app.component('NrButton', Button)
app.component('NrCard', Card)
app.component('PageContainer', PageContainer)

app.use(PrimeVue, { ripple: true })

app.mount('#app')
