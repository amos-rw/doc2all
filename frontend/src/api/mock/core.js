// The rules every demo call shares: who may ask, codes, notices and the audit log.
import { ApiError } from '../errors.js'
import { db, now, randomId, DEMO, MINUTE, HOUR } from './state.js'

export const routes = []

// who: open, half (password done), full (signed in), owner, fresh (confirmed), admin
export function route(method, pattern, who, handler) {
  const names = []
  const source = pattern.replace(/\{(\w+)\}/g, (_, name) => {
    names.push(name)
    return '([^/]+)'
  })
  routes.push({ method, pattern, who, handler, names, test: new RegExp(`^${source}$`) })
}

export const fail = (status, code, message, extra) => {
  throw new ApiError(status, code, message, extra)
}

export const currentUser = () => db.users.find((u) => u.id === db.session?.userId)
export const userByEmail = (email) => db.users.find((u) => u.email === String(email || '').trim().toLowerCase())

export function mine(list, id, user, field = 'ownerId') {
  const item = list.find((entry) => entry.id === id && entry[field] === user.id)
  return item || fail(404, 'not_found', 'Not found.')
}

export function cleanEmail(email) {
  const value = String(email || '').trim().toLowerCase()
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) fail(400, 'bad_email', 'Enter an email address.')
  return value
}

export function goodPassword(password) {
  if (String(password || '').length < 12) fail(400, 'weak_password', 'Use 12 or more characters.')
  return password
}

export function maskEmail(email) {
  const [name, domain] = email.split('@')
  return `${name[0]}***@${domain}`
}

// At most 3 codes an hour for one address, whether or not it has an account.
export function sendCode(address, purpose) {
  db.sent = db.sent.filter((s) => now() - s.at < HOUR)
  if (db.sent.filter((s) => s.address === address).length >= 3) fail(429, 'too_many_codes', 'Too many codes. Try again in an hour.')
  db.sent.push({ address, at: now() })
  db.codes[purpose] = { expiresAt: now() + 10 * MINUTE, tries: 0, used: false }
}

export function useCode(purpose, code) {
  const entry = db.codes[purpose]
  const dead = () => fail(400, 'code_dead', 'That code no longer works. Ask for a new one.')
  if (!entry) fail(400, 'bad_code', 'That code is not right.')
  if (entry.used || entry.tries >= 5 || now() > entry.expiresAt) dead()
  if (code !== DEMO.code) {
    entry.tries += 1
    if (entry.tries >= 5) dead()
    fail(400, 'bad_code', 'That code is not right.')
  }
  entry.used = true
}

export function newChallenge() {
  db.challenge = randomId('c')
  return db.challenge
}

export function useChallenge(challenge, answer) {
  const right = challenge && challenge === db.challenge && answer === 'demo-passkey'
  db.challenge = null // works once
  if (!right) fail(400, 'passkey_failed', 'The passkey did not work. Try again.')
}

export function audit(userId, action, targetId, result = 'OK') {
  db.audit.unshift({ id: randomId('a'), at: now(), userId, action, targetId, result })
}

export function notify(userId, title, { security = true, detail } = {}) {
  db.notices.unshift({
    id: randomId('n'), userId, kind: security ? 'security' : 'file', title, security, pinned: security, read: false, at: now(),
    detail: detail || (security ? 'Was this you? This stays here until you answer.' : 'Shown here in the app only.'),
  })
}
