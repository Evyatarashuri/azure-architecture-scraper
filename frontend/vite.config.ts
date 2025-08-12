import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
    define: {
      __APP_BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    },
  }
})
