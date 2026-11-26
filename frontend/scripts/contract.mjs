// Walks through every call on the demo server, checks the access rules, and writes example requests and
// answers to docs/design/api-examples.md, for building the real server.  Run: npm test
import assert from 'node:assert/strict'
import { readFileSync, writeFileSync } from 'node:fs'
import { handle, routes } from '../src/api/mock/server.js'
import { db, passTime, reset, DEMO, MINUTE } from '../src/api/mock/state.js'

const design = new URL('../../docs/design/', import.meta.url)
const examples = new Map()

const short = (value) => JSON.parse(JSON.stringify(value, (key, v) => {
  if (Array.isArray(v)) return v.slice(0, 2)
  if (typeof v === 'string') return v.replace(/\b([a-z])-[0-9a-f]{32}\b/g, '$1-4f1c…')
  if (typeof v === 'number' && v > 1e12) return 1795689000000
  return v
}))

async function call(method, path, body) {
  const route = routes.find((r) => r.method === method && r.test.test(path))
  const result = await handle(method, path, body)
  const key = `${method} ${route.pattern}`
  if (!examples.has(key)) {
    const sent = body instanceof Blob ? '(the file, as form field "file")' : body && short(body)
    examples.set(key, { who: route.who, sent, answer: result.blob ? '(the file itself, with its name in Content-Disposition)' : short(result) })
  }
  return result
}

const refused = async (status, method, path, body) => {
  await assert.rejects(handle(method, path, body), (error) => error.status === status, `${method} ${path} should answer ${status}`)
}

const docx = (name = 'contract.docx') => new File([new Uint8Array([0x50, 0x4b, 3, 4, 0])], name)
const code = DEMO.code
const proof = async (path) => ({ ...(await call('POST', path)), answer: 'demo-passkey' })
const confirm = async () => call('POST', '/api/me/confirm', { method: 'passkey', ...(await proof('/api/sign-in/passkey/options')) })

reset()
await call('GET', '/api/session')
await refused(401, 'GET', '/api/history')
await refused(404, 'GET', '/api/nothing')

// create an account
await call('POST', '/api/register', { email: 'new@example.com', password: DEMO.password })
await call('POST', '/api/register/confirm', { email: 'new@example.com', code })

// five wrong tries lock the account
for (let i = 0; i < 4; i++) await refused(400, 'POST', '/api/sign-in', { email: 'new@example.com', password: 'wrong' })
await refused(429, 'POST', '/api/sign-in', { email: 'new@example.com', password: 'wrong' })
await refused(429, 'POST', '/api/sign-in', { email: 'new@example.com', password: DEMO.password })

// forgot password, with a passkey
reset()
await call('POST', '/api/password/forgot', { email: DEMO.userEmail })
const reset1 = await call('POST', '/api/password/reset/code', { email: DEMO.userEmail, code })
await refused(403, 'POST', '/api/password/reset', { password: 'another-long-password' })
await call('POST', '/api/password/reset/passkey', { challenge: reset1.challenge, answer: 'demo-passkey' })
await call('POST', '/api/password/reset', { password: DEMO.password })

// sign in: password only gives no access
reset() // a password reset signs other devices out; start again for the account pages
await call('POST', '/api/sign-in', { email: DEMO.userEmail, password: DEMO.password })
await refused(401, 'GET', '/api/me')
await call('POST', '/api/sign-in/code/send')
await call('POST', '/api/sign-in/code', { code })
await call('POST', '/api/sign-out')
await call('POST', '/api/sign-in', { email: DEMO.userEmail, password: DEMO.password })
await call('POST', '/api/sign-in/passkey', await proof('/api/sign-in/passkey/options'))

// account: changes need a confirmation, which lasts 5 minutes
const me = await call('GET', '/api/me')
await call('PATCH', '/api/me/settings', { finishSound: false })
await call('DELETE', '/api/me/sessions/d-phone')
await refused(403, 'PUT', '/api/me/password', { password: DEMO.password })
await confirm()
await call('PUT', '/api/me/password', { password: DEMO.password })
await call('POST', '/api/me/email', { email: 'moved@example.com' })
await call('POST', '/api/me/email/confirm', { code })
await call('POST', '/api/me/passkeys', { ...(await proof('/api/me/passkeys/options')), name: 'Tablet' })
await call('PUT', '/api/me/email-code', { allowed: false })
await call('DELETE', `/api/me/passkeys/${me.passkeys[0].id}`)
await refused(400, 'DELETE', `/api/me/passkeys/${me.passkeys[1].id}`) // two must stay
passTime(6 * MINUTE)
await refused(403, 'PUT', '/api/me/email-code', { allowed: true })

// files
await refused(400, 'POST', '/api/files', new File([new Uint8Array([0x4d, 0x5a])], 'report.pdf'))
const file = await call('POST', '/api/files', docx())
await call('GET', `/api/files/${file.id}/check`)
await call('GET', `/api/files/${file.id}/matches`)
const job = await call('POST', '/api/jobs', { fileId: file.id, actions: ['clean', 'convert'], keep: ['attached', 'active'] })
passTime(5000)
await call('GET', `/api/jobs/${job.id}`)
const report = await call('GET', `/api/jobs/${job.id}/report`)
assert.equal(report.outcome, 'kept', 'a kept attachment is never All clear')
assert.ok(report.findings.some((f) => f.title === 'A macro was removed'), 'what runs by itself is removed even if asked to keep')
await call('GET', `/api/files/${file.id}/download`)
await call('DELETE', `/api/files/${file.id}`)
await refused(404, 'GET', `/api/files/${file.id}/download`)
await call('GET', '/api/history')
await call('DELETE', `/api/history/${job.id}`)

// notices
const { items } = await call('GET', '/api/notices')
await call('POST', '/api/notices/read')
await refused(403, 'POST', `/api/notices/${items[0].id}/mine`)
await confirm().catch(async () => confirm())
await call('POST', `/api/notices/${items[0].id}/mine`)
await call('POST', `/api/notices/${items[1].id}/not-mine`)

// another person's things are "not found", and so are the admin pages
await refused(404, 'GET', '/api/admin/audit')
await call('POST', '/api/sign-out')
await call('POST', '/api/sign-in', { email: 'student@example.com', password: DEMO.password })
await call('POST', '/api/sign-in/code/send')
await call('POST', '/api/sign-in/code', { code })
await refused(404, 'GET', `/api/jobs/${job.id}/report`)
await confirm().catch(() => call('POST', '/api/sign-in/code/send').then(() => call('POST', '/api/me/confirm', { method: 'code', code })))
await call('DELETE', '/api/me')

// administrator: ids only
await call('POST', '/api/sign-in', { email: DEMO.adminEmail, password: DEMO.password })
await call('POST', '/api/sign-in/passkey', await proof('/api/sign-in/passkey/options'))
const audit = await call('GET', '/api/admin/audit')
const records = await call('GET', '/api/admin/records')
const names = db.files.map((f) => f.name)
assert.ok(names.every((name) => !JSON.stringify([audit, records]).includes(name)), 'administrators never see file names')

// the demo server and the design list the same calls
const normal = (text) => text.replace(/\{\w+\}/g, '{id}')
const designed = [...readFileSync(new URL('server-interfaces.md', design), 'utf8').matchAll(/^\| `([A-Z]+ [^`]+)` \|/gm)].map((m) => normal(m[1]))
const demo = routes.map((r) => normal(`${r.method} ${r.pattern}`))
assert.deepEqual([...demo].sort(), [...designed].sort(), 'the demo server and the design differ')
const unused = demo.filter((key) => !examples.has(key))
assert.deepEqual(unused, [], 'calls never walked through')

const LEVEL = { open: 'Anyone', half: 'Password done', full: 'Signed in', owner: 'Owner only', fresh: 'Confirmed', admin: 'Administrator' }
const out = ['# API examples', '', '<!-- Written by frontend/scripts/contract.mjs (npm test). Do not edit by hand. -->', '',
  'What the pages send and what they expect back. The demo server in `frontend/src/api/mock/` answers like this today.',
  'The real server must answer the same way. Long lists are cut to two entries; ids and times are shortened.',
  '', 'A refused call answers with the status from the [server interfaces](server-interfaces.md) and `{"error": "code", "message": "plain words"}`.']
for (const key of designed) {
  const [method, path] = key.split(' ')
  const found = [...examples.entries()].find(([k]) => normal(k) === `${method} ${path}`)
  const [name, example] = found
  out.push('', `## \`${name}\``, '', `Who: ${LEVEL[example.who]}`)
  if (example.sent && Object.keys(example.sent).length) out.push('', 'Sends:', '', '```json', typeof example.sent === 'string' ? example.sent : JSON.stringify(example.sent, null, 2), '```')
  out.push('', 'Answers:', '', '```json', typeof example.answer === 'string' ? example.answer : JSON.stringify(example.answer, null, 2), '```')
}
writeFileSync(new URL('api-examples.md', design), `${out.join('\n')}\n`)
console.log(`OK: ${demo.length} calls walked through, access rules checked, api-examples.md written`)
