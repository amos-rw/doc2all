// A pretend server inside the browser. It answers the same calls, with the same "who may ask" rules,
// as the real server must (docs/design/server-interfaces.md).
import { db, now, save, MINUTE } from './state.js'
import { routes, fail, currentUser } from './core.js'
import './auth.js'
import './account.js'
import './files.js'

export { routes }

export async function handle(method, path, body) {
  let match
  const found = routes.find((r) => r.method === method && (match = r.test.exec(path)))
  if (!found) fail(404, 'not_found', 'Not found.')

  if (db.session && now() - db.session.lastSeenAt > 30 * MINUTE) db.session = null
  const user = currentUser()
  const signedIn = user && db.session.step === 'signed_in'
  try {
    if (found.who === 'half' && !user) fail(401, 'sign_in', 'Sign in first.')
    if (!['open', 'half'].includes(found.who) && !signedIn) fail(401, 'sign_in', 'Sign in first.')
    if (found.who === 'fresh' && !(now() - db.session.confirmedAt < 5 * MINUTE)) fail(403, 'confirm', 'Do your second step again.')
    if (found.who === 'admin' && user.role !== 'admin') fail(404, 'not_found', 'Not found.')
    if (db.session) db.session.lastSeenAt = now()

    const params = Object.fromEntries(found.names.map((name, i) => [name, match[i + 1]]))
    const input = body instanceof Blob ? body : structuredClone(body ?? {})
    const result = await found.handler({ body: input, params, user })
    return result.blob ? result : JSON.parse(JSON.stringify(result))
  } finally {
    save() // wrong tries and refused uploads must be remembered too
  }
}
