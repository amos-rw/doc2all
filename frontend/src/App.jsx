import ServerStatus from './ServerStatus.jsx'

const TOOLS = [
  { name: 'Convert', does: 'Word or PowerPoint to PDF, PDF to images' },
  { name: 'Clean', does: 'Remove hidden data' },
  { name: 'Scan to text', does: 'Read a photo or scan' },
  { name: 'Black out', does: 'Hide personal data' },
]

export default function App() {
  return (
    <>
      <header className="top">
        <span className="logo">
          Doc<b>2</b>All
        </span>
      </header>
      <main>
        <h1>Your documents, safely</h1>
        <p className="lead">Scan, convert and clean your documents.</p>
        <ul className="tools">
          {TOOLS.map((tool) => (
            <li key={tool.name} className="tool">
              <b>{tool.name}</b>
              <span>{tool.does}</span>
              <em>Coming soon</em>
            </li>
          ))}
        </ul>
        {import.meta.env.DEV && <ServerStatus />}
      </main>
    </>
  )
}
