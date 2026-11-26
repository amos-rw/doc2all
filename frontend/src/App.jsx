// Which page is shown to whom. The server enforces access; the pages only follow it.
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router'
import { isDemo } from './api/client.js'
import DemoPanel from './components/DemoPanel.jsx'
import Layout from './components/Layout.jsx'
import { AuditLog, Records } from './pages/Admin.jsx'
import CreateAccount from './pages/CreateAccount.jsx'
import ForgotPassword from './pages/ForgotPassword.jsx'
import History from './pages/History.jsx'
import Info from './pages/Info.jsx'
import Report from './pages/Report.jsx'
import SecondStep from './pages/SecondStep.jsx'
import Settings from './pages/Settings.jsx'
import SignIn from './pages/SignIn.jsx'
import Tools from './pages/Tools.jsx'
import { ConfirmProvider } from './state/confirm.jsx'
import { SessionProvider, homeFor, useSession } from './state/session.jsx'

// Lets a page through only for the people it is meant for, and sends everyone else to their own start.
function Only({ who }) {
  const { session } = useSession()
  const { state, role } = session
  const allowed = {
    visitor: state === 'signed_out',
    halfway: state === 'password_done',
    member: state === 'signed_in',
    user: state === 'signed_in' && role === 'user',
    admin: state === 'signed_in' && role === 'admin',
  }[who]
  return allowed ? <Outlet /> : <Navigate to={homeFor(session)} replace />
}

function Home() {
  const { session } = useSession()
  return <Navigate to={homeFor(session)} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <ConfirmProvider>
          <Routes>
            <Route element={<Only who="visitor" />}>
              <Route path="/sign-in" element={<SignIn />} />
              <Route path="/create-account" element={<CreateAccount />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
            </Route>
            <Route element={<Only who="halfway" />}>
              <Route path="/second-step" element={<SecondStep />} />
            </Route>
            <Route element={<Only who="member" />}>
              <Route element={<Layout />}>
                <Route path="/settings/:tab?" element={<Settings />} />
                <Route element={<Only who="user" />}>
                  <Route path="/" element={<Tools />} />
                  <Route path="/history" element={<History />} />
                  <Route path="/report/:jobId" element={<Report />} />
                </Route>
                <Route element={<Only who="admin" />}>
                  <Route path="/admin/audit-log" element={<AuditLog />} />
                  <Route path="/admin/records" element={<Records />} />
                </Route>
              </Route>
            </Route>
            {['privacy', 'cookies', 'about', 'files', 'terms', 'contact'].map((page) => (
              <Route key={page} path={`/${page}`} element={<Info page={page} />} />
            ))}
            <Route path="*" element={<Home />} />
          </Routes>
          {isDemo && <DemoPanel />}
        </ConfirmProvider>
      </SessionProvider>
    </BrowserRouter>
  )
}
