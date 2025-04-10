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

const app = createApp(App)

// Create and use Pinia store
app.use(createPinia())
app.use(router)

// Register global components
app.component('NrButton', Button)
app.component('NrCard', Card)
app.component('PageContainer', PageContainer)

app.mount('#app')
