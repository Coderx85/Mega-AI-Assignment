import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/ws/video': {
        target: 'ws://localhost:8080',
        ws: true,
      },
      '/feed': {
        target: 'http://localhost:8080',
      },
      '/roi': {
        target: 'http://localhost:8080',
      },
      '/stats': {
        target: 'http://localhost:8080',
      },
    },
  },
})
