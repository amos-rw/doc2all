// Screen 11 and the records page. An administrator sees ids, times and results, never names or content.
import { useEffect, useState } from 'react'
import { api } from '../api/calls.js'
import { Alert, Corner, Pill, useAction } from '../components/ui.jsx'
import { clock, day, dayAndTime } from '../lib/helpers.js'

const brief = (id) => (id.length > 14 ? `${id.slice(0, 6)}…${id.slice(-4)}` : id)
const result = (value) => <Pill tone={value === 'OK' || value === 'clear' ? 'ok' : value === 'kept' ? 'info' : 'warn'}>{value}</Pill>

function useLoaded(call) {
  const [data, setData] = useState(null)
  const [, error, run] = useAction()
  useEffect(() => {
    run(async () => setData(await call()))
  }, [call]) // eslint-disable-line react-hooks/exhaustive-deps
  return [data, error]
}

export function AuditLog() {
  const [data, error] = useLoaded(api.auditLog)
  const [today, setToday] = useState(false)
  const [user, setUser] = useState('')
  const [action, setAction] = useState('')
  const [chosen, setChosen] = useState(null)
  const lines = data?.lines || []
  const midnight = new Date().setHours(0, 0, 0, 0)
  const shown = lines.filter((l) => (!today || l.at >= midnight) && (!user || l.userId === user) && (!action || l.action === action))
  const options = (key) => [...new Set(lines.map((l) => l[key]))].sort()

  return (
    <>
      <div>
        <h1 className="m-h">Audit log</h1>
        <span className="m-sub">Records only. Nobody can edit or delete a line.</span>
      </div>
      {error && <Alert>{error}</Alert>}
      <div className="filters">
        <select aria-label="Day" value={today ? 'today' : ''} onChange={(e) => setToday(e.target.value === 'today')}>
          <option value="">All days</option>
          <option value="today">Today</option>
        </select>
        <select aria-label="User" value={user} onChange={(e) => setUser(e.target.value)}>
          <option value="">All users</option>
          {options('userId').map((id) => (
            <option key={id} value={id}>
              {brief(id)}
            </option>
          ))}
        </select>
        <select aria-label="Action" value={action} onChange={(e) => setAction(e.target.value)}>
          <option value="">All actions</option>
          {options('action').map((name) => (
            <option key={name}>{name}</option>
          ))}
        </select>
      </div>
      <div className={chosen ? 'split' : ''}>
        <div className="scroll-x">
          <table className="tbl">
            <thead>
              <tr>
                <th>Time</th>
                <th>User</th>
                <th>Action</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((line) => (
                <tr key={line.id} className={chosen?.id === line.id ? 'picked' : ''}>
                  <td className="mono-s">
                    <button onClick={() => setChosen(line)} aria-label={`Open the record of ${clock(line.at)}`}>
                      {clock(line.at)}
                    </button>
                  </td>
                  <td className="mono-s">{brief(line.userId)}</td>
                  <td>{line.action}</td>
                  <td>{result(line.result)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && shown.length === 0 && <p className="note">No line matches.</p>}
        </div>
        {chosen && (
          <aside className="side">
            <b>Record {clock(chosen.at)}</b>
            <KeyValue name="Date" value={dayAndTime(chosen.at)} />
            <KeyValue name="User" value={brief(chosen.userId)} />
            <KeyValue name="Action" value={chosen.action} />
            <KeyValue name="Target id" value={brief(chosen.targetId)} />
            <KeyValue name="Result" value={chosen.result} />
            <div className="alertbox bad">✕ Document content is not available to administrators.</div>
            <button className="link" onClick={() => setChosen(null)}>
              Close
            </button>
          </aside>
        )}
      </div>
      <Corner mood={chosen ? 'alert' : 'hello'}>{chosen ? 'That part is private. Only its owner can open it.' : 'I write down what happened, never what was in the file.'}</Corner>
    </>
  )
}

const KeyValue = ({ name, value }) => (
  <div className="kv">
    <span>{name}</span>
    <span className="mono-s">{value}</span>
  </div>
)

export function Records() {
  const [data, error] = useLoaded(api.records)
  return (
    <>
      <div>
        <h1 className="m-h">Records</h1>
        <span className="m-sub">Users and jobs by id. No file names and no content.</span>
      </div>
      {error && <Alert>{error}</Alert>}
      {data && (
        <>
          <Table title="Users" heads={['User', 'Role', 'Since', 'Files', 'Jobs']} rows={data.users.map((u) => [u.id, [brief(u.id), u.role, day(u.createdAt), u.files, u.jobs]])} />
          <Table title="Jobs" heads={['Job', 'User', 'Action', 'Result', 'When']} rows={data.jobs.map((j) => [j.id, [brief(j.id), brief(j.userId), j.action, result(j.result), dayAndTime(j.at)]])} />
        </>
      )}
      <Corner>Ids only. Names stay private.</Corner>
    </>
  )
}

const Table = ({ title, heads, rows }) => (
  <section className="card">
    <b>{title}</b>
    <div className="scroll-x">
      <table className="tbl">
        <thead>
          <tr>
            {heads.map((h) => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(([key, cells]) => (
            <tr key={key}>
              {cells.map((cell, i) => (
                <td key={heads[i]}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </section>
)
