export const sharedServerConfig = {
  port: 9098,
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true,
      rewrite: (path) => path
    },
    '/ai-query': {
      target: 'http://localhost:8001',
      changeOrigin: true
    },
    '/ai-chat': {
      target: 'http://localhost:8001',
      changeOrigin: true
    }
  }
}

export const sharedAliasConfig = (srcDir) => ({
  '@': srcDir
})
