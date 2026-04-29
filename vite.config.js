import vue from './frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs'
import { fileURLToPath } from 'node:url'
import { sharedAliasConfig, sharedServerConfig } from './vite.shared.js'

const frontendRoot = fileURLToPath(new URL('./frontend', import.meta.url))
const frontendSrc = fileURLToPath(new URL('./frontend/src', import.meta.url))

export default {
  root: frontendRoot,
  plugins: [vue()],
  resolve: {
    alias: sharedAliasConfig(frontendSrc)
  },
  server: sharedServerConfig
}
