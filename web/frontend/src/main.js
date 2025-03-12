import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store'

const app = createApp(App)

// Use Pinia store and Vue Router
app.use(pinia)
app.use(router)

// Mount the app
app.mount('#app') 