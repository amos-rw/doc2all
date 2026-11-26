import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The browser talks to one address. Calls under /api are passed on to the Django server.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    strictPort: true,
    proxy: { '/api': 'http://127.0.0.1:8010' },
  },
})
