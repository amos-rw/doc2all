// Screen 3: the second step, with a passkey or an emailed code.
import { useState } from 'react'
import { api } from '../api/calls.js'
import { usePasskeyOnDevice } from '../api/passkey.js'
import { Alert, AuthLayout, CodeInput, DemoHint, Icon, useAction } from '../components/ui.jsx'
import { useSession } from '../state/session.jsx'

export default function SecondStep() {
  const { session, setSession } = useSession()
  const [view, setView] = useState('choose')
  const [code, setCode] = useState('')
  const [busy, error, run, setError] = useAction()
  const { passkey, emailCode } = session.methods

  const withPasskey = () => {
    setView('passkey')
    run(async () => {
      const { challenge } = await api.passkeyOptions()
      const answer = await usePasskeyOnDevice(challenge)
      setSession(await api.signInPasskey(challenge, answer))
    })
  }
  const askCode = () =>
    run(async () => {
      await api.sendCode()
      setCode('')
      setView('code')
    })
  const withCode = (event) => {
    event.preventDefault()
    run(async () => setSession(await api.signInCode(code)))
  }
  const cancel = () => run(async () => setSession(await api.signOut()))
  const back = (
    <button className="link" onClick={cancel}>
      Cancel sign-in
    </button>
  )

  if (view === 'passkey') {
    return (
      <AuthLayout mood={error ? 'alert' : 'checking'} say={error ? 'That did not work.' : 'Waiting for you…'}>
        <h1 className="m-h">Confirm on your device</h1>
        <span className="m-sub">Your computer or phone will ask you to unlock it: fingerprint, face, PIN or security key.</span>
        <div className="fp">{Icon.key}</div>
        {error && <Alert>{error}</Alert>}
        <span className="note center">Passkeys only work on Doc2All. The key never leaves your device.</span>
        <div className="links">
          {error && (
            <button className="link" onClick={withPasskey}>
              Try again
            </button>
          )}
          {emailCode && (
            <button className="link" onClick={askCode} disabled={busy}>
              Use a code instead
            </button>
          )}
          {back}
        </div>
      </AuthLayout>
    )
  }
  if (view === 'code') {
    return (
      <AuthLayout mood={error ? 'alert' : 'checking'} say="Check your email.">
        <h1 className="m-h">Enter the code</h1>
        <span className="m-sub">Sent to {session.emailMasked}.</span>
        {error && <Alert>{error}</Alert>}
        <form className="stack" onSubmit={withCode}>
          <CodeInput value={code} onChange={setCode} />
          <span className="note">5 tries. Then the code stops working.</span>
          <DemoHint>the code is 123456.</DemoHint>
          <button className="mbtn" disabled={busy || code.length < 6}>
            Confirm
          </button>
        </form>
        <div className="links">
          {passkey && (
            <button
              className="link"
              onClick={() => {
                setError(null)
                withPasskey()
              }}
            >
              Use my passkey instead
            </button>
          )}
          {back}
        </div>
      </AuthLayout>
    )
  }
  return (
    <AuthLayout mood={error ? 'alert' : 'checking'} say="One more step.">
      <h1 className="m-h">Prove it is you</h1>
      <span className="m-sub">A password is never enough on its own.</span>
      {error && <Alert>{error}</Alert>}
      {passkey && (
        <button className="bigkey" onClick={withPasskey}>
          <span className="ic">{Icon.key}</span>
          <span>
            <b>Use my passkey</b>
            <span>Fingerprint, face, PIN or security key</span>
          </span>
        </button>
      )}
      {passkey && emailCode && <div className="or">or</div>}
      {emailCode && (
        <button className="mbtn ghost" onClick={askCode} disabled={busy}>
          Email me a code
        </button>
      )}
      <div className="links">{back}</div>
    </AuthLayout>
  )
}
