// Getting in, and a forgotten password.
import { db, now, randomId, MINUTE } from './state.js'
import { route, fail, currentUser, userByEmail, cleanEmail, goodPassword, maskEmail, sendCode, useCode, newChallenge, useChallenge, audit, notify } from './core.js'

export function sessionInfo() {
  const user = currentUser()
  const formToken = 'demo-form-token'
  if (!db.session || !user) return { state: 'signed_out', formToken }
  return {
    state: db.session.step,
    formToken,
    email: user.email,
    emailMasked: maskEmail(user.email),
    role: db.session.step === 'signed_in' ? user.role : null,
    methods: { passkey: user.passkeys.length > 0, emailCode: user.emailCode },
  }
}

function completeSignIn(user) {
  db.session.step = 'signed_in'
  if (db.newDevice) notify(user.id, 'Someone signed in on a new device')
  db.newDevice = false
  audit(user.id, 'Sign-in', user.id)
  return sessionInfo()
}

route('GET', '/api/session', 'open', () => sessionInfo())

route('POST', '/api/register', 'open', ({ body }) => {
  const email = cleanEmail(body.email)
  goodPassword(body.password)
  // A known address gets the same answer. The real server emails its owner instead of sending a code.
  sendCode(email, `register:${email}`)
  db.pending.register = userByEmail(email) ? null : { email, password: body.password }
  return { next: 'code' }
})

route('POST', '/api/register/confirm', 'open', ({ body }) => {
  const email = cleanEmail(body.email)
  const waiting = db.pending.register
  if (!waiting || waiting.email !== email) fail(400, 'bad_code', 'That code is not right.')
  useCode(`register:${email}`, body.code)
  const user = {
    id: randomId('u'), email, password: waiting.password, role: 'user', createdAt: now(), passwordChangedAt: now(), emailCode: true,
    settings: { fileNotices: true, finishSound: true }, passkeys: [], devices: [{ id: 'd-this', name: 'This laptop', lastSeenAt: now() }],
  }
  db.users.push(user)
  db.pending.register = null
  audit(user.id, 'Create account', user.id)
  return { ok: true }
})

route('POST', '/api/sign-in', 'open', ({ body }) => {
  const email = String(body.email || '').trim().toLowerCase()
  const locked = () => fail(429, 'locked', 'Too many tries. Try again in 15 minutes.', { retryAfterSeconds: Math.ceil((db.locked[email] - now()) / 1000) })
  if (db.locked[email] > now()) locked()
  const user = userByEmail(email)
  if (!user || user.password !== body.password) {
    db.failures = db.failures.filter((f) => now() - f.at < 10 * MINUTE)
    db.failures.push({ email, at: now() })
    if (user) audit(user.id, 'Sign-in', user.id, 'Refused')
    if (db.failures.filter((f) => f.email === email).length >= 5) {
      db.locked[email] = now() + 15 * MINUTE
      db.failures = db.failures.filter((f) => f.email !== email)
      locked()
    }
    fail(400, 'wrong', 'Email or password is not right.')
  }
  db.session = { userId: user.id, step: 'password_done', lastSeenAt: now(), confirmedAt: null }
  return sessionInfo()
})

route('POST', '/api/sign-in/passkey/options', 'half', () => ({ challenge: newChallenge() }))

route('POST', '/api/sign-in/passkey', 'half', ({ body, user }) => {
  if (!user.passkeys.length) fail(400, 'no_passkey', 'This account has no passkey yet.')
  useChallenge(body.challenge, body.answer)
  return completeSignIn(user)
})

route('POST', '/api/sign-in/code/send', 'half', ({ user }) => {
  if (!user.emailCode) fail(400, 'codes_off', 'Email codes are switched off. Use your passkey.')
  sendCode(user.email, `second:${user.id}`)
  return { sentTo: maskEmail(user.email) }
})

route('POST', '/api/sign-in/code', 'half', ({ body, user }) => {
  if (!user.emailCode) fail(400, 'codes_off', 'Email codes are switched off. Use your passkey.')
  useCode(`second:${user.id}`, body.code)
  return completeSignIn(user)
})

route('POST', '/api/sign-out', 'half', ({ user }) => {
  audit(user.id, 'Sign-out', user.id)
  db.session = null
  return sessionInfo()
})

route('POST', '/api/password/forgot', 'open', ({ body }) => {
  const email = cleanEmail(body.email)
  sendCode(email, `reset:${email}`) // the same answer for any address
  db.pending.reset = { email, codeDone: false, passkeyDone: false }
  return { next: 'code' }
})

route('POST', '/api/password/reset/code', 'open', ({ body }) => {
  const email = cleanEmail(body.email)
  const reset = db.pending.reset
  const user = userByEmail(email)
  if (!reset || reset.email !== email) fail(400, 'bad_code', 'That code is not right.')
  // An address without an account never received a code, so no code is right for it.
  useCode(`reset:${email}`, user ? body.code : '')
  reset.codeDone = true
  const passkeyNeeded = user.passkeys.length > 0
  return { passkeyNeeded, challenge: passkeyNeeded ? newChallenge() : null }
})

route('POST', '/api/password/reset/passkey', 'open', ({ body }) => {
  if (!db.pending.reset?.codeDone) fail(403, 'code_first', 'Enter the emailed code first.')
  useChallenge(body.challenge, body.answer)
  db.pending.reset.passkeyDone = true
  return { ok: true }
})

route('POST', '/api/password/reset', 'open', ({ body }) => {
  const reset = db.pending.reset
  const user = reset && userByEmail(reset.email)
  if (!user || !reset.codeDone || (user.passkeys.length && !reset.passkeyDone)) fail(403, 'not_proven', 'Start the reset again.')
  user.password = goodPassword(body.password)
  user.passwordChangedAt = now()
  user.devices = user.devices.filter((d) => d.id === 'd-this')
  if (db.session?.userId === user.id) db.session = null
  delete db.locked[user.email]
  db.pending.reset = null
  notify(user.id, 'Your password was changed')
  audit(user.id, 'Password reset', user.id)
  return { ok: true }
})
