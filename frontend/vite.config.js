import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The browser talks to one address. Calls under /api are passed on to the Django server.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    strictPort: true,
    // changeOrigin stays off: the server compares the page's address with the one it was called by (form token).
    proxy: { '/api': { target: 'http://127.0.0.1:8010', changeOrigin: false } },
  },
})
