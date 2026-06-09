import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'https://www.neurostore.in'   // only for local dev, not deployment
    }
  },
  build: {
    outDir: 'dist'
  }
})