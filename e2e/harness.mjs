// Starts a private copy of the app for browser checks.
// Safety by construction: ports come from the OS, so they cannot collide with
// a running app; the database is always a new temp file, never backend/skills.db;
// only child processes started here are ever stopped; live mode needs ALLOW_LIVE=1.
import { spawn, spawnSync } from 'node:child_process'
import { mkdtempSync } from 'node:fs'
import net from 'node:net'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const PYTHON = join(ROOT, 'backend', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const children = new Set()
process.on('exit', () => children.forEach((c) => c.kill()))

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function freePort() {
  return new Promise((ok, fail) => {
    const s = net.createServer()
    s.on('error', fail)
    s.listen(0, '127.0.0.1', () => {
      const { port } = s.address()
      s.close(() => ok(port))
    })
  })
}

function start(cmd, args, options) {
  const child = spawn(cmd, args, { ...options, stdio: ['ignore', 'pipe', 'pipe'] })
  child.log = ''
  child.stdout.on('data', (d) => (child.log += d))
  child.stderr.on('data', (d) => (child.log += d))
  children.add(child)
  child.on('exit', () => children.delete(child))
  return child
}

async function waitFor(url, child) {
  for (let i = 0; i < 100; i++) {
    if (child.exitCode !== null || child.signalCode !== null) throw new Error(`process exited early:\n${child.log}`)
    try {
      if ((await fetch(url)).ok) return
    } catch {}
    await sleep(100)
  }
  throw new Error(`timed out waiting for ${url}`)
}

async function stopChild(child) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return
  const gone = new Promise((r) => child.on('exit', r))
  child.kill()
  await gone
}

// mode: mock | mock_error | mock_timeout | mock_malformed | live
// down: true starts the frontend with no backend behind it.
export async function startStack({ mode = 'mock', mockChat = 'auto', seed = false, down = false, maxCalls = 0 } = {}) {
  if (mode === 'live' && process.env.ALLOW_LIVE !== '1') throw new Error('Live mode needs ALLOW_LIVE=1')
  const dir = mkdtempSync(join(tmpdir(), 'skills-e2e-'))
  const db = join(dir, 'e2e.db')
  const [apiPort, webPort] = [await freePort(), await freePort()]
  const env = { ...process.env, SKILLS_DB_PATH: db, LLM_MODE: mode, LLM_MOCK_CHAT: mockChat, LLM_MAX_CALLS: String(maxCalls) }
  const backendDir = join(ROOT, 'backend')

  if (seed) {
    const r = spawnSync(PYTHON, ['scripts/seed_demo.py'], { cwd: backendDir, env, encoding: 'utf8' })
    if (r.status !== 0) throw new Error(r.stderr)
  }
  const startBackend = async () => {
    const child = start(PYTHON, ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(apiPort)], { cwd: backendDir, env })
    await waitFor(`http://127.0.0.1:${apiPort}/api/health`, child)
    return child
  }
  let backend = down ? null : await startBackend()
  const vite = start(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', String(webPort), '--strictPort'], {
    cwd: join(ROOT, 'frontend'),
    env: { ...env, API_PORT: String(apiPort) },
  })
  const url = `http://127.0.0.1:${webPort}`
  await waitFor(url, vite)

  return {
    url,
    api: `http://127.0.0.1:${apiPort}/api`,
    db,
    backendLog: () => backend?.log ?? '',
    stopBackend: async () => {
      await stopChild(backend)
    },
    startBackend: async () => {
      backend = await startBackend()
    },
    // Read-only query of this stack's temp database.
    rows(sql) {
      const code = 'import json,sqlite3,sys\nc=sqlite3.connect(f"file:{sys.argv[1]}?mode=ro",uri=True)\nc.row_factory=sqlite3.Row\nprint(json.dumps([dict(r) for r in c.execute(sys.argv[2])]))'
      const r = spawnSync(PYTHON, ['-c', code, db, sql], { encoding: 'utf8' })
      if (r.status !== 0) throw new Error(r.stderr)
      return JSON.parse(r.stdout)
    },
    stop: async () => {
      await stopChild(vite)
      await stopChild(backend)
    },
  }
}

