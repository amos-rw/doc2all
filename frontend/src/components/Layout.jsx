// The signed-in frame: top bar, the phone's bottom bar, notices and the profile menu.
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router'
import { api } from '../api/calls.js'
import { ago, applyTheme, readTheme } from '../lib/helpers.js'
import { useConfirm } from '../state/confirm.jsx'
import { useSession } from '../state/session.jsx'
import { Alert, Icon, useAction } from './ui.jsx'

const NoticesContext = createContext(() => {})
export const useRefreshNotices = () => useContext(NoticesContext)

const MENUS = {
  user: [
    { to: '/', label: 'Tools', icon: Icon.tools },
    { to: '/history', label: 'History', icon: Icon.clock },
  ],
  admin: [
    { to: '/admin/audit-log', label: 'Audit log', icon: Icon.log },
    { to: '/admin/records', label: 'Records', icon: Icon.tools },
  ],
}

export default function Layout() {
  const { session, setSession } = useSession()
  const [notices, setNotices] = useState([])
  const [open, setOpen] = useState(null) // 'alerts' | 'profile' | null
  const location = useLocation()
  const navigate = useNavigate()
  const confirmed = useConfirm()
  const [busy, error, run] = useAction()
  const menu = MENUS[session.role] || MENUS.user

  const refresh = useCallback(() => api.notices().then((answer) => setNotices(answer.items), () => {}), [])

  useEffect(() => {
    setOpen(null)
    refresh()
  }, [location.pathname, refresh])

  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && setOpen(null)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const unread = notices.filter((n) => !n.read).length
  const toggle = (name) => setOpen(open === name ? null : name)
  const markRead = () => run(() => api.readNotices().then(refresh))
  const signOut = () => run(async () => setSession(await api.signOut()))
  const itWasMe = (id) =>
    run(async () => {
      await confirmed('Before I mark this notice as yours.', () => api.noticeMine(id))
      await refresh()
    })
  const notMe = (id) =>
    run(async () => {
      await api.noticeNotMine(id)
      await refresh()
      navigate('/settings/security', { state: { changePassword: true } })
    })

  const badge = unread > 0 && <em>{unread}</em>

  return (
    <div className="app">
      <a className="skip" href="#main">
        Skip to the page
      </a>
      <header className="m-top">
        <Link to={menu[0].to} className="m-brand">
          Doc<b>2</b>All
        </Link>
        <nav aria-label="Main">
          {menu.map((item) => (
            <NavLink key={item.to} to={item.to} end className={({ isActive }) => (isActive ? 'on' : '')}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="m-right">
          <button className="bell" aria-label={`Notifications, ${unread} unread`} aria-expanded={open === 'alerts'} onClick={() => toggle('alerts')}>
            {Icon.bell}
            {badge}
          </button>
          <button className="m-user" aria-label="Profile menu" aria-expanded={open === 'profile'} onClick={() => toggle('profile')}>
            {session.role === 'admin' && <span className="adm">Admin</span>}
            <i>{session.email[0].toUpperCase()}</i>
            <span>{session.email}</span>
            <u />
          </button>
        </div>
      </header>

      {open && <button className="backdrop" aria-label="Close the menu" onClick={() => setOpen(null)} />}
      {open === 'alerts' && (
        <div className="pop" role="dialog" aria-label="Notifications">
          <div className="ph">
            <span>Notifications</span>
            <button className="link small" onClick={markRead} disabled={busy}>
              Mark all as read
            </button>
          </div>
          {notices.length === 0 && <div className="mi note">Nothing new.</div>}
          {notices.slice(0, 6).map((n) => (
            <div key={n.id} className={n.read ? 'it read' : 'it'}>
              <div className="dotn" />
              <div>
                <b>{n.title}</b>
                <span>
                  {n.detail} · {ago(n.at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
      {open === 'profile' && (
        <div className="pop narrow" role="dialog" aria-label="Profile">
          <div className="ph email">{session.email}</div>
          <Link className="mi" to="/settings/security">
            Settings
          </Link>
          <Link className="mi" to="/settings/privacy">
            Privacy and about
          </Link>
          <ThemeChoice />
          <button className="mi out" onClick={signOut} disabled={busy}>
            Sign out
          </button>
        </div>
      )}

      <main id="main" className="m-main pad-b">
        {error && <Alert>{error}</Alert>}
        {notices
          .filter((n) => n.pinned)
          .map((n) => (
            <section key={n.id} className="pinned" aria-label="Security notice">
              <div>
                <b>{n.title}</b>
                <span>{n.detail}</span>
              </div>
              <div className="actr">
                <button className="mbtn sm" onClick={() => itWasMe(n.id)} disabled={busy}>
                  Yes, it was me
                </button>
                <button className="mbtn sm ghost danger" onClick={() => notMe(n.id)} disabled={busy}>
                  No, secure my account
                </button>
              </div>
            </section>
          ))}
        <NoticesContext.Provider value={refresh}>
          <Outlet />
        </NoticesContext.Provider>
      </main>

      <nav className="m-bottom" aria-label="Main, phone">
        {menu.map((item) => (
          <NavLink key={item.to} to={item.to} end className={({ isActive }) => (isActive ? 'mb on' : 'mb')}>
            {item.icon}
            {item.label}
          </NavLink>
        ))}
        <button className="mb" onClick={() => toggle('alerts')}>
          {Icon.bell}Alerts
          {badge}
        </button>
        <button className={location.pathname.startsWith('/settings') ? 'mb on' : 'mb'} onClick={() => toggle('profile')}>
          {Icon.user}Profile
        </button>
      </nav>
    </div>
  )
}

function ThemeChoice() {
  const [theme, setTheme] = useState(readTheme)
  const choose = (value) => {
    applyTheme(value)
    setTheme(value)
  }
  return (
    <div className="mi theme" role="group" aria-label="Light or dark">
      {['auto', 'light', 'dark'].map((value) => (
        <button key={value} aria-pressed={theme === value} onClick={() => choose(value)}>
          {value[0].toUpperCase() + value.slice(1)}
        </button>
      ))}
    </div>
  )
}
