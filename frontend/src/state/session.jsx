// Who is here: signed out, password done, or signed in. The server decides, the pages follow.
import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { api } from '../api/calls.js'
import { onSignedOut } from '../api/client.js'
import { Dialog } from '../components/ui.jsx'

const SessionContext = createContext(null)
export const useSession = () => useContext(SessionContext)

export const homeFor = (session) => {
  if (session.state === 'signed_out') return '/sign-in'
  if (session.state === 'password_done') return '/second-step'
  return session.role === 'admin' ? '/admin/audit-log' : '/'
}

export function SessionProvider({ children }) {
  const [session, setSession] = useState(null)
  const [ended, setEnded] = useState(false)
  const latest = useRef(session)
  latest.current = session

  const refresh = useCallback(() => api.session().then(setSession), [])

  useEffect(() => {
    onSignedOut(() => {
      if (latest.current?.state === 'signed_in') setEnded(true)
    })
    refresh()
  }, [refresh])

  const signInAgain = () => {
    setEnded(false)
    refresh()
  }

  if (!session) return <p className="loading">Loading…</p>
  return (
    <SessionContext.Provider value={{ session, setSession, refresh }}>
      {children}
      {ended && (
        <Dialog mood="alert" title="You were signed out" sub="After 30 minutes without activity, I sign you out to keep your files safe.">
          <button className="mbtn" onClick={signInAgain}>
            Sign in again
          </button>
        </Dialog>
      )}
    </SessionContext.Provider>
  )
}
