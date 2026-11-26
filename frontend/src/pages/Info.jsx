// Privacy, Cookies, About and the other open pages. They can be read without signing in.
import { Link } from 'react-router'
import { LegalLinks } from '../components/ui.jsx'
import { homeFor, useSession } from '../state/session.jsx'
import { Cookies, Row } from './Settings.jsx'

const PAGES = {
  privacy: {
    title: 'Privacy notice',
    rows: [
      ['Your account', 'Your email and your settings. Passwords are stored only in a scrambled form.'],
      ['Your files and results', 'Deleted after 24 hours, or when you delete them.'],
      ['Your history', 'The list of your files, until you remove it.'],
      ['The audit log', 'Time, action and result. Never file content.'],
      ['Email', 'Used for codes and notices only, never for file content or file names.'],
    ],
  },
  cookies: { title: 'Cookie notice', rows: [] },
  about: {
    title: 'About Doc2All',
    rows: [
      ['Scan, convert and clean your documents safely', 'Doc2All checks a file before opening it, removes what is dangerous and shows you a report.'],
      ['A school project', 'Made for the module Application Security Technologies.'],
    ],
  },
  files: {
    title: 'How we handle your files',
    rows: [
      ['Checked first', 'The type is decided from the content, not only the name.'],
      ['Opened in a closed box', 'Each job has its own folder, a time limit and a memory limit.'],
      ['Read on our server', 'An outside service is used only if you agree, for that one file.'],
      ['Removed', 'After 24 hours, or at once when you ask.'],
    ],
  },
  terms: {
    title: 'Terms of use',
    rows: [
      ['Your files', 'Upload only files you are allowed to use.'],
      ['No promise of perfection', 'Doc2All lowers the risk. It cannot promise that every file is harmless.'],
    ],
  },
  contact: { title: 'Contact', rows: [['Questions', 'Open an issue on the project page: github.com/amos-rw/doc2all']] },
}

export default function Info({ page }) {
  const { session } = useSession()
  const { title, rows } = PAGES[page]
  return (
    <div className="app">
      <header className="m-top">
        <Link to={homeFor(session)} className="m-brand">
          Doc<b>2</b>All
        </Link>
        <div className="m-right keep">
          <Link className="mbtn sm ghost" to={homeFor(session)}>
            Back
          </Link>
        </div>
      </header>
      <main className="m-main">
        <h1 className="m-h">{title}</h1>
        {page === 'cookies' ? (
          <Cookies />
        ) : (
          <section className="card">
            {rows.map(([name, detail]) => (
              <Row key={name} title={name} detail={detail} />
            ))}
          </section>
        )}
        <LegalLinks />
      </main>
    </div>
  )
}
