// Every call to the server goes through here. Three ways to run:
//   mixed (the usual way while building): the calls the server already has go to it, the rest to src/api/mock
//   demo  (npm run demo): everything is answered in the browser, no server needed
//   server (VITE_API=server): everything goes to the server
import { ApiError } from './errors.js'

const mode = import.meta.env.MODE === 'demo' ? 'demo' : import.meta.env.VITE_API || 'mixed'
export const isDemo = mode !== 'server' // some data is still made up
export const realFiles = mode !== 'demo' // upload and convert use the server

// Built on the server so far: upload, convert, report, download, delete and history.
const BUILT = /^\/api\/(files|jobs|history)(\/[^/]+)?(\/(download|report))?$/
const useServer = (path) => mode === 'server' || (mode === 'mixed' && BUILT.test(path))

const NO_SERVER = 'The server is not answering. Is it running on port 8010?'

let formToken = '' // the server's, fetched when first needed
let signedOutListener = () => {}

export function onSignedOut(listener) {
  signedOutListener = listener
}

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function fetchFormToken() {
  const response = await fetch('/api/session', { credentials: 'same-origin' }).catch(() => null)
  if (response?.ok) formToken = (await response.json()).formToken
}

async function send(method, path, body, again = false) {
  const headers = {}
  let payload
  if (body instanceof Blob) {
    payload = new FormData()
    payload.append('file', body, body.name)
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  if (method !== 'GET') {
    if (!formToken || again) await fetchFormToken()
    headers['X-CSRFToken'] = formToken
  }
  let response
  try {
    response = await fetch(path, { method, headers, body: payload, credentials: 'same-origin' })
  } catch {
    throw new ApiError(503, 'no_server', NO_SERVER)
  }
  const isJson = response.headers.get('Content-Type')?.includes('json')
  if (!response.ok) {
    const data = isJson ? await response.json() : {}
    if (data.error === 'token' && !again) return send(method, path, body, true) // the token was out of date
    const fallback = response.status >= 500 && !isJson ? NO_SERVER : 'Something went wrong.'
    throw new ApiError(response.status, data.error, data.message || fallback, data)
  }
  if (isJson) return response.json()
  return { blob: await response.blob(), name: fileName(response.headers.get('Content-Disposition') || '') }
}

// Names with letters outside plain English arrive as filename*=utf-8''...
function fileName(header) {
  const encoded = /filename\*=utf-8''([^;]+)/i.exec(header)?.[1]
  if (encoded) return decodeURIComponent(encoded)
  return /filename="((?:[^"\\]|\\.)*)"/.exec(header)?.[1].replace(/\\(.)/g, '$1') || 'download'
}

export async function request(method, path, body) {
  try {
    let data
    if (import.meta.env.VITE_API !== 'server' && !useServer(path)) {
      const server = await import('./mock/server.js')
      await pause(220) // a real server takes a moment
      data = await server.handle(method, path, body)
    } else {
      data = await send(method, path, body)
    }
    return data
  } catch (error) {
    if (error.status === 401) signedOutListener()
    throw error
  }
}
