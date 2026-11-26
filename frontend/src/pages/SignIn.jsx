// Screen 1: sign-in.
import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router'
import { api } from '../api/calls.js'
import { isDemo } from '../api/client.js'
import { Alert, AuthLayout, Field, useAction } from '../components/ui.jsx'
import { readCookie, writeCookie } from '../lib/helpers.js'
import { useSession } from '../state/session.jsx'

export default function SignIn() {
  const { session, setSession } = useSession()
  const fromState = useLocation().state?.message
  const message = session.message || fromState
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [lockedFor, setLockedFor] = useState(0)
  const [notice, setNotice] = useState(() => !readCookie('cookie_ok'))
  const [busy, error, run, setError] = useAction()

  useEffect(() => {
    if (!lockedFor) return undefined
    const timer = setTimeout(() => {
      setLockedFor(lockedFor - 1)
      if (lockedFor === 1) setError(null)
    }, 1000)
    return () => clearTimeout(timer)
  }, [lockedFor, setError])

  const submit = (event) => {
    event.preventDefault()
    run(async () => {
      try {
        setSession(await api.signIn(email, password))
      } catch (problem) {
        if (problem.code === 'locked') setLockedFor(problem.retryAfterSeconds)
        throw problem
      }
    })
  }
  // The lock belongs to one account. Another address may try; the server decides in any case.
  const changeEmail = (value) => {
    setEmail(value)
    if (lockedFor) {
      setLockedFor(0)
      setError(null)
    }
  }
  const fill = (address) => {
    changeEmail(address)
    setPassword('doc2all-demo-pass')
    setError(null)
  }
  const accept = () => {
    writeCookie('cookie_ok', '1')
    setNotice(false)
  }

  const mood = error ? 'alert' : 'hello'
  const say = lockedFor ? 'Too many tries. I locked the door.' : error ? 'That did not match. Try again.' : notice ? 'Welcome to Doc2All!' : 'Welcome back!'

  return (
    <AuthLayout mood={mood} say={say}>
      <h1 className="m-h">Sign in</h1>
      <span className="m-sub">Your files stay yours.</span>
      {message && !error && <Alert tone="good">{message}</Alert>}
      {error && <Alert>{error}</Alert>}
      <form className="stack" onSubmit={submit}>
        <Field label="Email" type="email" autoComplete="username" required value={email} onChange={changeEmail} />
        <Field label="Password" type="password" autoComplete="current-password" required value={password} onChange={setPassword} />
        <button className="mbtn" disabled={busy || lockedFor > 0}>
          {lockedFor ? `Try again in ${Math.ceil(lockedFor / 60)} min` : 'Sign in'}
        </button>
      </form>
      <div className="links">
        <Link to="/forgot-password">Forgot password?</Link>
        <Link to="/create-account">Create account</Link>
      </div>
      <span className="note">Five wrong tries lock the account for 15 minutes.</span>
      {isDemo && (
        <div className="demohint">
          Demo:{' '}
          <button className="link small" onClick={() => fill('amos@example.com')}>
            fill in the user
          </button>
          {' · '}
          <button className="link small" onClick={() => fill('admin@example.com')}>
            fill in the administrator
          </button>
        </div>
      )}
      {notice && (
        <div className="cookie" role="region" aria-label="Cookie notice">
          <span>We only use cookies Doc2All needs: to sign you in, to know your device and to remember light or dark. No tracking, no ads.</span>
          <div className="actr">
            <Link className="mbtn sm ghost" to="/cookies">
              Details
            </Link>
            <button className="mbtn sm" onClick={accept}>
              OK
            </button>
          </div>
        </div>
      )}
    </AuthLayout>
  )
}
