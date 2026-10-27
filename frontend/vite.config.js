import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Backend port for the /api proxy. Override if 8000 is taken: API_PORT=8010 npm run dev
const apiPort = process.env.API_PORT || '8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // Same-origin /api keeps navigator.sendBeacon free of CORS preflights.
    proxy: { '/api': `http://127.0.0.1:${apiPort}` },
    // Allow importing ../shared/crisis_phrases.json (the one phrase list).
    fs: { allow: ['..'] },
  },
})
