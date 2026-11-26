// Screen 4: forgot password: email, code, passkey when there is one, new password.
import { useState } from 'react'
import { Link } from 'react-router'
import { api } from '../api/calls.js'
import { usePasskeyOnDevice } from '../api/passkey.js'
import { Alert, AuthLayout, CodeInput, DemoHint, Field, Icon, Steps, Strength, useAction } from '../components/ui.jsx'

const STEPS = ['Email', 'Code', 'New password']

export default function ForgotPassword() {
  const [view, setView] = useState('email')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
  const [challenge, setChallenge] = useState(null)
  const [busy, error, run] = useAction()
  const mood = (usual) => (error ? 'alert' : usual)

  const submit = (action) => (event) => {
    event.preventDefault()
    run(action)
  }
  const sendEmail = async () => {
    await api.forgotPassword(email)
    setView('code')
  }
  const checkCode = async () => {
    const answer = await api.resetCode(email, code)
    setChallenge(answer.challenge)
    setView(answer.passkeyNeeded ? 'passkey' : 'new')
  }
  const proveDevice = () =>
    run(async () => {
      const answer = await usePasskeyOnDevice(challenge)
      await api.resetPasskey(challenge, answer)
      setView('new')
    })
  const savePassword = async () => {
    await api.resetPassword(password)
    setView('done')
  }

  if (view === 'email') {
    return (
      <AuthLayout mood={mood('hello')} say="It happens to all of us.">
        <h1 className="m-h">Forgot your password?</h1>
        <Steps labels={STEPS} active={1} />
        {error && <Alert>{error}</Alert>}
        <form className="stack" onSubmit={submit(sendEmail)}>
          <Field label="Email" type="email" autoComplete="username" required value={email} onChange={setEmail} />
          <button className="mbtn" disabled={busy}>
            Send me a code
          </button>
        </form>
        <span className="note">If this email has an account, a code is on its way.</span>
        <div className="links">
          <Link to="/sign-in">Back to sign-in</Link>
        </div>
      </AuthLayout>
    )
  }
  if (view === 'code') {
    return (
      <AuthLayout mood={mood('checking')} say="Check your email.">
        <h1 className="m-h">Enter the code</h1>
        <Steps labels={STEPS} active={2} />
        {error && <Alert>{error}</Alert>}
        <form className="stack" onSubmit={submit(checkCode)}>
          <CodeInput value={code} onChange={setCode} />
          <DemoHint>the code is 123456.</DemoHint>
          <button className="mbtn" disabled={busy || code.length < 6}>
            Continue
          </button>
        </form>
        <span className="note">If your account has a passkey, I ask for it next.</span>
        <div className="links">
          <button className="link" onClick={() => setView('email')}>
            Start again
          </button>
        </div>
      </AuthLayout>
    )
  }
  if (view === 'passkey') {
    return (
      <AuthLayout mood={mood('checking')} say="One more step.">
        <h1 className="m-h">Use your passkey</h1>
        <Steps labels={STEPS} active={2} />
        <div className="fp">{Icon.key}</div>
        {error && <Alert>{error}</Alert>}
        <span className="m-sub center">Confirm on your device. The code alone cannot change your password.</span>
        <button className="mbtn" onClick={proveDevice} disabled={busy}>
          {busy ? 'Waiting for your device…' : 'Use my passkey'}
        </button>
      </AuthLayout>
    )
  }
  if (view === 'new') {
    return (
      <AuthLayout mood={mood('hello')} say="Make it a good one.">
        <h1 className="m-h">Choose a new password</h1>
        <Steps labels={STEPS} active={3} />
        {error && <Alert>{error}</Alert>}
        <form className="stack" onSubmit={submit(savePassword)}>
          <Field label="New password" type="password" autoComplete="new-password" required value={password} onChange={setPassword} />
          <Strength password={password} />
          <button className="mbtn" disabled={busy || password.length < 12}>
            Save password
          </button>
        </form>
      </AuthLayout>
    )
  }
  return (
    <AuthLayout mood="safe" say="All done!">
      <h1 className="m-h">Password changed</h1>
      <Alert tone="good">We sent you an email.</Alert>
      <span className="m-sub">Now sign in with your new password.</span>
      <Link className="mbtn" to="/sign-in">
        Sign in
      </Link>
    </AuthLayout>
  )
}
