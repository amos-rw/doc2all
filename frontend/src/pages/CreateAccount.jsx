// Screen 2: create an account, then confirm the address with a code.
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { api } from '../api/calls.js'
import { Alert, AuthLayout, CodeInput, DemoHint, Field, Strength, useAction } from '../components/ui.jsx'

export default function CreateAccount() {
  const navigate = useNavigate()
  const [view, setView] = useState('form')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [busy, error, run] = useAction()

  const send = (event) => {
    event?.preventDefault()
    run(async () => {
      await api.register(email, password)
      setCode('')
      setView('code')
    })
  }
  const finish = (event) => {
    event.preventDefault()
    run(async () => {
      await api.confirmRegistration(email, code)
      navigate('/sign-in', { state: { message: 'Your account is ready. Sign in.' } })
    })
  }

  if (view === 'form') {
    return (
      <AuthLayout mood={error ? 'alert' : 'hello'} say="Let us set you up.">
        <h1 className="m-h">Create your account</h1>
        {error && <Alert>{error}</Alert>}
        <form className="stack" onSubmit={send}>
          <Field label="Email" type="email" autoComplete="username" required value={email} onChange={setEmail} />
          <Field label="Password" type="password" autoComplete="new-password" required value={password} onChange={setPassword} />
          <Strength password={password} />
          <button className="mbtn" disabled={busy || password.length < 12}>
            Send me a code
          </button>
        </form>
        <div className="links">
          <Link to="/sign-in">I already have an account</Link>
        </div>
      </AuthLayout>
    )
  }
  return (
    <AuthLayout mood={error ? 'alert' : 'checking'} say="Check your email.">
      <h1 className="m-h">Enter the code</h1>
      <span className="m-sub">We sent an email to {email}.</span>
      {error && <Alert>{error}</Alert>}
      <form className="stack" onSubmit={finish}>
        <CodeInput value={code} onChange={setCode} />
        <span className="note">The code lasts 10 minutes and works once.</span>
        <DemoHint>the code is 123456.</DemoHint>
        <button className="mbtn" disabled={busy || code.length < 6}>
          Confirm
        </button>
      </form>
      <div className="links">
        <button className="link" onClick={() => send()} disabled={busy}>
          Send a new code
        </button>
        <button className="link" onClick={() => setView('form')}>
          Back
        </button>
      </div>
    </AuthLayout>
  )
}
