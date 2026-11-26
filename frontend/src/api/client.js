// Every call to the server goes through here.
// Demo mode (the default for now) answers from src/api/mock. Start with VITE_API=server to use the real server.
import { ApiError } from './errors.js'

export const isDemo = import.meta.env.VITE_API !== 'server'

let formToken = ''
let signedOutListener = () => {}

export function onSignedOut(listener) {
  signedOutListener = listener
}

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function send(method, path, body) {
  const headers = {}
  let payload
  if (body instanceof Blob) {
    payload = new FormData()
    payload.append('file', body, body.name)
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  if (method !== 'GET') headers['X-CSRFToken'] = formToken
  const response = await fetch(path, { method, headers, body: payload, credentials: 'same-origin' })
  const isJson = response.headers.get('Content-Type')?.includes('json')
  if (!response.ok) {
    const data = isJson ? await response.json() : {}
    throw new ApiError(response.status, data.error, data.message || 'Something went wrong.', data)
  }
  if (isJson) return response.json()
  const name = /filename="([^"]+)"/.exec(response.headers.get('Content-Disposition') || '')?.[1]
  return { blob: await response.blob(), name: name || 'download' }
}

export async function request(method, path, body) {
  try {
    let data
    if (import.meta.env.VITE_API !== 'server') {
      const server = await import('./mock/server.js')
      await pause(220) // a real server takes a moment
      data = await server.handle(method, path, body)
    } else {
      data = await send(method, path, body)
    }
    if (data?.formToken) formToken = data.formToken
    return data
  } catch (error) {
    if (error.status === 401) signedOutListener()
    throw error
  }
}
