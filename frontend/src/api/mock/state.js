// Demo data. Everything here is made up. It lives in this browser tab only, so a reload keeps it.
export const DEMO = {
  userEmail: 'amos@example.com',
  adminEmail: 'admin@example.com',
  password: 'doc2all-demo-pass',
  code: '123456',
}

export const MINUTE = 60_000
export const HOUR = 60 * MINUTE
const KEY = 'doc2all-demo-v1'
const store = typeof window === 'undefined' ? null : window.sessionStorage

export const randomId = (prefix) => `${prefix}-${crypto.randomUUID().replace(/-/g, '')}`

function seed() {
  const now = Date.now()
  const ago = (ms) => now - ms
  const day = 24 * HOUR
  const user = (id, email, role, extra = {}) => ({
    id, email, role, password: DEMO.password, createdAt: ago(24 * day), passwordChangedAt: ago(14 * day),
    emailCode: true, settings: { fileNotices: true, finishSound: true }, passkeys: [],
    devices: [{ id: 'd-this', name: 'This laptop', lastSeenAt: now }], ...extra,
  })
  const files = []
  const jobs = []
  const past = (name, actions, outcome, hoursLeft, deleted = false) => {
    const fileId = randomId('f')
    const jobId = randomId('j')
    const created = ago((24 - hoursLeft) * HOUR)
    files.push({ id: fileId, ownerId: 'u-7f3a', name, kind: name.split('.').pop(), size: 214_000, createdAt: created, expiresAt: created + day, deleted })
    jobs.push({ id: jobId, ownerId: 'u-7f3a', fileId, actions, startedAt: created, removed: false, announced: true, outcome, findings: pastFindings(outcome, actions) })
  }
  past('contract.docx', ['clean', 'convert'], 'clear', 21)
  past('scan-id.jpg', ['scan'], 'clear', 19)
  past('invoice.docx', ['clean'], 'alert', 3)
  past('notes.pdf', ['blackout'], 'clear', 23)
  past('essay.docx', ['clean'], 'clear', 6, true)

  const line = (at, userId, action, targetId, result = 'OK') => ({ id: randomId('a'), at, userId, action, targetId, result })
  return {
    skew: 0,
    users: [
      user('u-7f3a', DEMO.userEmail, 'user', {
        passkeys: [{ id: 'k-laptop', name: 'Laptop', addedAt: ago(24 * day) }, { id: 'k-phone', name: 'Phone', addedAt: ago(17 * day) }],
        devices: [{ id: 'd-this', name: 'This laptop', lastSeenAt: now }, { id: 'd-phone', name: 'Phone', lastSeenAt: ago(2 * HOUR) }],
      }),
      user('u-1a90', DEMO.adminEmail, 'admin', { passkeys: [{ id: 'k-admin', name: 'Laptop', addedAt: ago(20 * day) }] }),
      user('u-5b2e', 'student@example.com', 'user'),
      user('u-c091', 'lecturer@example.com', 'user'),
    ],
    session: null,
    pending: {},
    codes: {},
    sent: [],
    failures: [],
    locked: {},
    challenge: null,
    newDevice: false,
    files,
    jobs,
    notices: [
      { id: 'n-3', userId: 'u-7f3a', kind: 'file', title: 'contract.docx is deleted in 21 hours', detail: 'Download it before then if you still need it.', security: false, pinned: false, read: false, at: ago(20 * MINUTE) },
      { id: 'n-2', userId: 'u-7f3a', kind: 'security', title: 'A passkey was added: Phone', detail: 'Was this you? This stays here until you answer.', security: true, pinned: true, read: false, at: ago(2 * HOUR) },
      { id: 'n-1', userId: 'u-7f3a', kind: 'security', title: 'Your password was changed', detail: 'We emailed you.', security: true, pinned: false, read: true, at: ago(day) },
    ],
    audit: [
      line(ago(46 * MINUTE), 'u-5b2e', 'Upload', 'f-8f2a41d0'),
      line(ago(44 * MINUTE), 'u-c091', 'Sign-in', 'u-c091', 'Refused'),
      line(ago(43 * MINUTE), 'u-c091', 'Sign-in', 'u-c091', 'Refused'),
      line(ago(41 * MINUTE), 'u-7f3a', 'Clean file', files[0].id),
      line(ago(40 * MINUTE), 'u-7f3a', 'Download', files[0].id),
      line(ago(39 * MINUTE), 'u-7f3a', 'Delete file', files[4].id),
    ],
  }
}

function pastFindings(outcome, actions) {
  const f = (ok, title, detail, tag) => ({ ok, title, detail, tag })
  if (outcome === 'alert') {
    return [
      f(false, 'A macro could not be removed', 'It may run a program when opened. Do not open this file.', 'Danger'),
      f(true, 'Author name removed', 'A name was stored inside the file.', 'Removed'),
      f(false, 'Scanned again: one problem left', 'The macro is still there.', 'Found'),
    ]
  }
  const first = actions.includes('scan')
    ? f(true, 'Text read on our server', 'The file never left Doc2All.', 'Done')
    : actions.includes('blackout')
      ? f(true, '4 details blacked out', 'They are removed from the file, not just covered.', 'Removed')
      : f(true, 'A macro was removed', 'The file had a hidden program in it. It is gone.', 'Removed')
  return [first, f(true, 'Scanned again', 'Nothing hidden is left.', 'Clean')]
}

function load() {
  try {
    const saved = store?.getItem(KEY)
    if (saved) return JSON.parse(saved)
  } catch {
    // damaged demo data: start again
  }
  return seed()
}

export let db = load()
export const now = () => Date.now() + db.skew
export const save = () => store?.setItem(KEY, JSON.stringify(db))

export function reset() {
  db = seed()
  save()
}

// Helpers for the demo panel.
export function passTime(ms) {
  db.skew += ms
  save()
}

export function addSecurityNotice() {
  const user = db.users.find((u) => u.id === db.session?.userId) || db.users[0]
  db.notices.unshift({ id: randomId('n'), userId: user.id, kind: 'security', title: 'Someone signed in on a new device', detail: 'Was this you? This stays here until you answer.', security: true, pinned: true, read: false, at: now() })
  save()
}
