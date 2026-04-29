import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import router from './router'

// 引入企业级样式
import './styles/global.css'

const app = createApp(App)

app.use(ElementPlus, {
  locale: zhCn,
  size: 'default',
  zIndex: 3000
})
app.use(router)
app.mount('#app')
