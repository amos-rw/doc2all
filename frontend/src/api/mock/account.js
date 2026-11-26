// My account, notices and the administrator pages.
import { db, now, randomId, MINUTE } from './state.js'
import { route, fail, mine, userByEmail, cleanEmail, goodPassword, sendCode, useCode, newChallenge, useChallenge, audit, notify } from './core.js'

route('GET', '/api/me', 'full', ({ user }) => ({
  email: user.email,
  settings: user.settings,
  emailCode: user.emailCode,
  passwordChangedAt: user.passwordChangedAt,
  passkeys: user.passkeys,
  sessions: user.devices.map((d) => ({ id: d.id, device: d.name, lastSeenAt: d.lastSeenAt, current: d.id === 'd-this' })),
}))

route('PATCH', '/api/me/settings', 'full', ({ body, user }) => {
  for (const key of ['fileNotices', 'finishSound']) {
    if (typeof body[key] === 'boolean') user.settings[key] = body[key]
  }
  return user.settings
})

route('DELETE', '/api/me/sessions/{id}', 'owner', ({ params, user }) => {
  if (!user.devices.some((d) => d.id === params.id)) fail(404, 'not_found', 'Not found.')
  if (params.id === 'd-this') fail(400, 'current', 'Use Sign out for this device.')
  user.devices = user.devices.filter((d) => d.id !== params.id)
  return { ok: true }
})

route('POST', '/api/me/confirm', 'full', ({ body, user }) => {
  if (body.method === 'passkey') useChallenge(body.challenge, body.answer)
  else {
    if (!user.emailCode) fail(400, 'codes_off', 'Email codes are switched off. Use your passkey.')
    useCode(`second:${user.id}`, body.code)
  }
  db.session.confirmedAt = now()
  return { confirmedUntil: now() + 5 * MINUTE }
})

route('PUT', '/api/me/password', 'fresh', ({ body, user }) => {
  user.password = goodPassword(body.password)
  user.passwordChangedAt = now()
  user.devices = user.devices.filter((d) => d.id === 'd-this')
  notify(user.id, 'Your password was changed')
  audit(user.id, 'Password changed', user.id)
  return { ok: true }
})

route('POST', '/api/me/email', 'fresh', ({ body, user }) => {
  const email = cleanEmail(body.email)
  sendCode(email, `email:${user.id}`)
  // An address that someone else uses gets the same answer, and can never be confirmed.
  db.pending.email = { userId: user.id, email: userByEmail(email) ? null : email }
  return { next: 'code' }
})

route('POST', '/api/me/email/confirm', 'fresh', ({ body, user }) => {
  const waiting = db.pending.email
  if (waiting?.userId !== user.id) fail(400, 'bad_code', 'That code is not right.')
  useCode(`email:${user.id}`, waiting.email ? body.code : '')
  const old = user.email
  user.email = waiting.email
  db.pending.email = null
  notify(user.id, 'Your email was changed', { detail: `We told your old address, ${old}.` })
  audit(user.id, 'Email changed', user.id)
  return { email: user.email }
})

route('POST', '/api/me/passkeys/options', 'fresh', () => ({ challenge: newChallenge() }))

route('POST', '/api/me/passkeys', 'fresh', ({ body, user }) => {
  const name = String(body.name || '').trim().slice(0, 40)
  if (!name) fail(400, 'no_name', 'Give the passkey a name.')
  useChallenge(body.challenge, body.answer)
  const passkey = { id: randomId('k'), name, addedAt: now() }
  user.passkeys.push(passkey)
  notify(user.id, `A passkey was added: ${name}`)
  audit(user.id, 'Passkey added', passkey.id)
  return passkey
})

route('DELETE', '/api/me/passkeys/{id}', 'fresh', ({ params, user }) => {
  const passkey = user.passkeys.find((k) => k.id === params.id) || fail(404, 'not_found', 'Not found.')
  if (!user.emailCode && user.passkeys.length <= 2) fail(400, 'keep_two', 'Email codes are off, so two passkeys must stay. Switch email codes on first.')
  user.passkeys = user.passkeys.filter((k) => k !== passkey)
  notify(user.id, `A passkey was removed: ${passkey.name}`)
  audit(user.id, 'Passkey removed', passkey.id)
  return { ok: true }
})

route('PUT', '/api/me/email-code', 'fresh', ({ body, user }) => {
  const allowed = body.allowed === true
  if (!allowed && user.passkeys.length < 2) fail(400, 'need_two_passkeys', 'Add a second passkey before you switch email codes off.')
  user.emailCode = allowed
  notify(user.id, allowed ? 'Email codes were switched on' : 'Email codes were switched off')
  audit(user.id, 'Email codes changed', user.id)
  return { emailCode: allowed }
})

route('DELETE', '/api/me', 'fresh', ({ user }) => {
  audit(user.id, 'Delete account', user.id)
  db.files = db.files.filter((f) => f.ownerId !== user.id)
  db.jobs = db.jobs.filter((j) => j.ownerId !== user.id)
  db.notices = db.notices.filter((n) => n.userId !== user.id)
  db.users = db.users.filter((u) => u.id !== user.id)
  db.session = null
  return { ok: true }
})

route('GET', '/api/notices', 'full', ({ user }) => ({
  items: db.notices.filter((n) => n.userId === user.id && (n.security || user.settings.fileNotices)).sort((a, b) => b.at - a.at),
}))

route('POST', '/api/notices/read', 'full', ({ user }) => {
  db.notices.filter((n) => n.userId === user.id).forEach((n) => (n.read = true))
  return { ok: true }
})

route('POST', '/api/notices/{id}/mine', 'fresh', ({ params, user }) => {
  const notice = mine(db.notices, params.id, user, 'userId')
  Object.assign(notice, { pinned: false, read: true, detail: 'You said this was you.' })
  return { ok: true }
})

route('POST', '/api/notices/{id}/not-mine', 'owner', ({ params, user }) => {
  const notice = mine(db.notices, params.id, user, 'userId')
  Object.assign(notice, { pinned: false, read: true, detail: 'You said this was not you. Other devices were signed out.' })
  user.devices = user.devices.filter((d) => d.id === 'd-this')
  audit(user.id, 'Secure account', user.id)
  return { next: 'change_password' }
})

// Ids, times and results only: never a file name or content.
route('GET', '/api/admin/audit', 'admin', () => ({ lines: [...db.audit].sort((a, b) => b.at - a.at) }))

route('GET', '/api/admin/records', 'admin', () => ({
  users: db.users.map((u) => ({
    id: u.id, role: u.role, createdAt: u.createdAt,
    files: db.files.filter((f) => f.ownerId === u.id && !f.deleted).length,
    jobs: db.jobs.filter((j) => j.ownerId === u.id).length,
  })),
  jobs: [...db.jobs].sort((a, b) => b.startedAt - a.startedAt).map((j) => ({ id: j.id, userId: j.ownerId, action: j.actions.join(', '), result: j.outcome, at: j.startedAt })),
}))
