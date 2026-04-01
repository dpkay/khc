import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'fs'
import { homedir } from 'os'
import { join } from 'path'

// Read secrets from ~/khc-private/.env
const envFile = readFileSync(join(homedir(), 'khc-private', '.env'), 'utf-8')
const envVars = Object.fromEntries(
  envFile.split('\n')
    .filter(l => l.includes('=') && !l.startsWith('#'))
    .map(l => l.split('=', 2).map(s => s.trim()))
)

export default defineConfig({
  plugins: [react()],
  base: '/local/',
  define: {
    __HA_TOKEN__: JSON.stringify(envVars.HA_TOKEN || ''),
  },
})
