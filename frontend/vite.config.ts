import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    // Allow Codespaces / tunnel hosts in addition to localhost.
    allowedHosts: [
      'localhost',
      '.app.github.dev',
      '.preview.app.github.dev',
      '.loca.lt',
      '.ngrok-free.app',
      '.trycloudflare.com',
    ],
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
