import { createApp } from 'vue'
import App from './App.vue'

// 关键：必须导入 VueFlow 的样式
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

createApp(App).mount('#app')
