import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { sharedAliasConfig, sharedServerConfig } from '../vite.shared.js'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: sharedAliasConfig(fileURLToPath(new URL('./src', import.meta.url)))
  },
  server: sharedServerConfig
})
