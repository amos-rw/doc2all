// The 41 calls of docs/design/server-interfaces.md. The pages use only these.
import { request } from './client.js'

const get = (path) => request('GET', path)
const post = (path, body) => request('POST', path, body)
const put = (path, body) => request('PUT', path, body)
const del = (path) => request('DELETE', path)

export const api = {
  // getting in
  session: () => get('/api/session'),
  register: (email, password) => post('/api/register', { email, password }),
  confirmRegistration: (email, code) => post('/api/register/confirm', { email, code }),
  signIn: (email, password) => post('/api/sign-in', { email, password }),
  passkeyOptions: () => post('/api/sign-in/passkey/options'),
  signInPasskey: (challenge, answer) => post('/api/sign-in/passkey', { challenge, answer }),
  sendCode: () => post('/api/sign-in/code/send'),
  signInCode: (code) => post('/api/sign-in/code', { code }),
  signOut: () => post('/api/sign-out'),

  // forgot password
  forgotPassword: (email) => post('/api/password/forgot', { email }),
  resetCode: (email, code) => post('/api/password/reset/code', { email, code }),
  resetPasskey: (challenge, answer) => post('/api/password/reset/passkey', { challenge, answer }),
  resetPassword: (password) => post('/api/password/reset', { password }),

  // my account
  me: () => get('/api/me'),
  changeSettings: (settings) => request('PATCH', '/api/me/settings', settings),
  signOutDevice: (id) => del(`/api/me/sessions/${id}`),
  confirm: (proof) => post('/api/me/confirm', proof),
  changePassword: (password) => put('/api/me/password', { password }),
  changeEmail: (email) => post('/api/me/email', { email }),
  confirmEmail: (code) => post('/api/me/email/confirm', { code }),
  newPasskeyOptions: () => post('/api/me/passkeys/options'),
  addPasskey: (challenge, answer, name) => post('/api/me/passkeys', { challenge, answer, name }),
  removePasskey: (id) => del(`/api/me/passkeys/${id}`),
  setEmailCode: (allowed) => put('/api/me/email-code', { allowed }),
  deleteAccount: () => del('/api/me'),

  // files and work
  upload: (file) => post('/api/files', file),
  check: (fileId) => get(`/api/files/${fileId}/check`),
  matches: (fileId) => get(`/api/files/${fileId}/matches`),
  startJob: (job) => post('/api/jobs', job),
  job: (id) => get(`/api/jobs/${id}`),
  report: (jobId) => get(`/api/jobs/${jobId}/report`),
  download: (fileId) => get(`/api/files/${fileId}/download`),
  deleteFile: (fileId) => del(`/api/files/${fileId}`),
  history: () => get('/api/history'),
  removeHistory: (id) => del(`/api/history/${id}`),

  // notices
  notices: () => get('/api/notices'),
  readNotices: () => post('/api/notices/read'),
  noticeMine: (id) => post(`/api/notices/${id}/mine`),
  noticeNotMine: (id) => post(`/api/notices/${id}/not-mine`),

  // administrator
  auditLog: () => get('/api/admin/audit'),
  records: () => get('/api/admin/records'),
}
