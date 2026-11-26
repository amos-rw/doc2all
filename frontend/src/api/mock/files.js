// Files and the work done on them. Nothing is really converted or cleaned: the results are made up.
import { db, now, randomId, HOUR } from './state.js'
import { route, fail, mine, audit, notify } from './core.js'

export const JOB_TIME = 3500 // how long a demo job takes
const FIRST_BYTES = { pdf: [0x25, 0x50, 0x44, 0x46], docx: [0x50, 0x4b], pptx: [0x50, 0x4b], png: [0x89, 0x50, 0x4e, 0x47], jpg: [0xff, 0xd8, 0xff] }
const ALLOWED = {
  docx: ['convert', 'clean', 'blackout'], pptx: ['convert', 'clean', 'blackout'], pdf: ['convert', 'clean', 'scan', 'blackout'],
  png: ['clean', 'scan'], jpg: ['clean', 'scan'],
}

route('POST', '/api/files', 'full', async ({ body: file, user }) => {
  if (!file?.name) fail(400, 'no_file', 'Choose a file.')
  const extension = file.name.split('.').pop().toLowerCase()
  const kind = extension === 'jpeg' ? 'jpg' : extension
  const refuse = (message) => {
    audit(user.id, 'Upload', user.id, 'Refused')
    fail(400, 'refused', message)
  }
  if (db.files.filter((f) => f.ownerId === user.id && now() - f.createdAt < HOUR).length >= 20) fail(429, 'too_many_uploads', 'That is 20 uploads in an hour. Try again later.')
  if (!FIRST_BYTES[kind]) refuse('Only PDF, Word, PowerPoint, PNG and JPG files are accepted.')
  if (file.size > 20 * 1024 * 1024) refuse('The file is larger than 20 MB.')
  const start = new Uint8Array(await file.slice(0, 4).arrayBuffer())
  if (start[0] === 0x4d && start[1] === 0x5a) refuse(`Its name says ${file.name}, but it is a program.`)
  if (!FIRST_BYTES[kind].every((byte, i) => start[i] === byte)) refuse(`Its name says ${file.name}, but the content is something else.`)
  const record = { id: randomId('f'), ownerId: user.id, name: file.name.slice(0, 120), kind, size: file.size, createdAt: now(), expiresAt: now() + 24 * HOUR, deleted: false }
  db.files.push(record)
  audit(user.id, 'Upload', record.id)
  return { id: record.id, name: record.name, kind, size: record.size, expiresAt: record.expiresAt, allowed: ALLOWED[kind] }
})

const liveFile = (id, user) => {
  const file = mine(db.files, id, user)
  if (file.deleted || now() > file.expiresAt) fail(404, 'not_found', 'This file was deleted.')
  return file
}

// rule: always = removed whatever you say, keepable = removed unless kept, choice = your choice
function hiddenThings(kind) {
  const group = (key, rule, title, detail, remove = true) => ({ key, rule, title, detail, remove })
  if (kind === 'png' || kind === 'jpg') {
    return [group('author', 'choice', 'Camera, date and place', 'The photo holds a location'), group('previews', 'choice', 'Previews', '1 small preview')]
  }
  return [
    group('active', 'always', 'Runs by itself or reaches outside', kind === 'pdf' ? '1 script that starts on opening' : '1 macro, 1 remote template'),
    group('attached', 'keepable', 'Attached files and objects', '1 spreadsheet. If you keep it, I cannot say All clear.'),
    group('author', 'choice', 'Who made the file', 'A name and a company'),
    group('history', 'choice', 'Edit history', '14 tracked changes'),
    group('comments', 'choice', 'Comments', '2 comments you may want to keep', false),
    group('hidden', 'choice', 'Hidden text and sheets', '1 hidden sheet'),
    group('previews', 'choice', 'Previews and old versions', '1 small preview'),
  ]
}

route('GET', '/api/files/{id}/check', 'owner', ({ params, user }) => ({ groups: hiddenThings(liveFile(params.id, user).kind) }))

const MATCHES = [
  { id: 'm1', kind: 'ids', label: 'ID', value: '1 0000 0 0000000 0 00' },
  { id: 'm2', kind: 'phones', label: 'Phone', value: '+250 700 000 000' },
  { id: 'm3', kind: 'emails', label: 'Email', value: 'name@example.com' },
  { id: 'm4', kind: 'phones', label: 'Office', value: '+250 700 000 111' },
]

route('GET', '/api/files/{id}/matches', 'owner', ({ params, user }) => {
  liveFile(params.id, user)
  return { title: 'Employment letter', person: 'Name: A. Person', matches: MATCHES }
})

const DID = { clean: 'Clean', convert: 'Convert', scan: 'Scan to text', blackout: 'Black out' }
const DOING = { clean: 'Cleaning hidden data', convert: 'Converting', scan: 'Reading the text', blackout: 'Blacking out' }

function work(file, actions, keep, blackout, outsideOcr) {
  const findings = []
  const add = (ok, title, detail, tag) => findings.push({ ok, title, detail, tag })
  const groups = hiddenThings(file.kind)
  const stuck = file.name.toLowerCase() === 'invoice.docx' // the demo file that cannot be cleaned
  if (groups.some((g) => g.key === 'active')) {
    if (stuck) add(false, 'A macro could not be removed', 'It may run a program when opened. Do not open this file.', 'Danger')
    else add(true, 'A macro was removed', 'The file had a hidden program in it. It is gone.', 'Removed')
  }
  let keptRisk = false
  if (actions.includes('clean')) {
    for (const g of groups.filter((x) => x.rule !== 'always')) {
      if (!keep.includes(g.key)) add(true, `${g.title}: removed`, g.detail.split('.')[0], 'Removed')
      else if (g.rule === 'keepable') {
        keptRisk = true
        add(false, `${g.title}: kept`, 'You chose to keep them. I cannot promise they are safe.', 'Kept')
      } else add(true, `${g.title}: kept`, 'You chose to keep this.', 'Kept')
    }
  }
  if (actions.includes('blackout')) {
    const left = MATCHES.length - blackout.length
    if (blackout.length) add(true, `${blackout.length} details blacked out`, 'They are removed from the file, not just covered.', 'Removed')
    if (left) add(true, `${left} left visible`, 'You chose to keep them.', 'Kept')
  }
  if (actions.includes('convert')) add(true, file.kind === 'pdf' ? 'Pages saved as images' : 'Converted to PDF', 'Made from the checked copy.', 'Done')
  if (actions.includes('scan')) {
    if (outsideOcr) add(true, 'Text read by an outside service', 'You allowed this, for this file only.', 'Done')
    else add(true, 'Text read on our server', 'The file never left Doc2All.', 'Done')
  }
  if (stuck) add(false, 'Scanned again: one problem left', 'The macro is still there.', 'Found')
  else if (keptRisk) add(true, 'Scanned again', 'Nothing else that can run was found.', 'Checked')
  else add(true, 'Scanned again', 'Nothing hidden that can run is left.', 'Clean')
  return { findings, outcome: stuck ? 'alert' : keptRisk ? 'kept' : 'clear' }
}

route('POST', '/api/jobs', 'owner', ({ body, user }) => {
  const file = liveFile(body.fileId, user)
  const actions = (body.actions || []).filter((a) => ALLOWED[file.kind].includes(a))
  if (!actions.length) fail(400, 'no_action', 'Choose what to do with the file.')
  const keep = Array.isArray(body.keep) ? body.keep : []
  const blackout = (body.blackout || []).filter((id) => MATCHES.some((m) => m.id === id))
  const job = { id: randomId('j'), ownerId: user.id, fileId: file.id, actions, startedAt: now(), removed: false, announced: false, ...work(file, actions, keep, blackout, body.outsideOcr === true) }
  db.jobs.push(job)
  audit(user.id, `${DID[actions[0]]} file`, file.id)
  return { id: job.id }
})

route('GET', '/api/jobs/{id}', 'owner', ({ params, user }) => {
  const job = mine(db.jobs, params.id, user)
  const progress = Math.min(1, (now() - job.startedAt) / JOB_TIME)
  const labels = ['I checked what the file really is', 'I opened a copy in the sandbox', job.actions.map((a) => DOING[a]).join(', '), 'Scanning the result again']
  const steps = labels.map((label, i) => ({ label, state: progress >= (i + 1) / 4 ? 'done' : progress >= i / 4 ? 'now' : 'waiting' }))
  if (progress === 1 && !job.announced) {
    job.announced = true
    notify(user.id, `${db.files.find((f) => f.id === job.fileId).name} is ready`, { security: false })
  }
  return { id: job.id, status: progress === 1 ? 'done' : 'working', progress, steps }
})

route('GET', '/api/jobs/{id}/report', 'owner', ({ params, user }) => {
  const job = mine(db.jobs, params.id, user)
  const file = db.files.find((f) => f.id === job.fileId)
  return {
    jobId: job.id, fileId: file.id, fileName: file.name, actions: job.actions, outcome: job.outcome, findings: job.findings,
    expiresAt: file.expiresAt, fileDeleted: file.deleted || now() > file.expiresAt,
  }
})

route('GET', '/api/files/{id}/download', 'owner', ({ params, user }) => {
  const file = liveFile(params.id, user)
  audit(user.id, 'Download', file.id)
  const text = `Doc2All demo\n\nThe real server will send the finished ${file.name} here.\nThis text file only stands in for it.\n`
  return { blob: new Blob([text], { type: 'text/plain' }), name: `${file.name}.demo.txt` }
})

route('DELETE', '/api/files/{id}', 'owner', ({ params, user }) => {
  const file = liveFile(params.id, user)
  file.deleted = true
  audit(user.id, 'Delete file', file.id)
  return { deletedAt: now() }
})

route('GET', '/api/history', 'full', ({ user }) => {
  const latest = new Map()
  for (const job of db.jobs.filter((j) => j.ownerId === user.id && !j.removed).sort((a, b) => a.startedAt - b.startedAt)) latest.set(job.fileId, job)
  const items = [...latest.values()].reverse().map((job) => {
    const file = db.files.find((f) => f.id === job.fileId)
    return {
      id: job.id, jobId: job.id, fileId: file.id, name: file.name, did: job.actions.map((a, i) => (i ? DID[a].toLowerCase() : DID[a])).join(', '),
      outcome: job.outcome, expiresAt: file.expiresAt, deleted: file.deleted || now() > file.expiresAt,
    }
  })
  return { items }
})

route('DELETE', '/api/history/{id}', 'owner', ({ params, user }) => {
  const { fileId } = mine(db.jobs, params.id, user)
  db.jobs.filter((j) => j.fileId === fileId).forEach((j) => (j.removed = true))
  db.files.find((f) => f.id === fileId).deleted = true
  audit(user.id, 'Remove from history', fileId)
  return { ok: true }
})
