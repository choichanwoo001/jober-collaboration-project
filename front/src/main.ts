import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'

import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/user'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

// Global styles
import './assets/styles/global.css'

const vuetify = createVuetify({
  components,
  directives,
})

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(vuetify)
app.use(VueQueryPlugin)

// 앱 초기화 시 토큰이 있으면 userStore 복원
const token = localStorage.getItem('accessToken')
if (token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const userStore = useUserStore()
    userStore.setUser({
      accountId: payload.account_id,
      role: payload.role
    })
  } catch (error) {
    console.error('토큰 파싱 실패:', error)
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
  }
}

app.mount('#app')

