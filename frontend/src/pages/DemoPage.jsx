import { useState, useEffect } from 'react';
import { triggerSwsToDept, triggerDeptToSws, triggerConflict, triggerRetry, triggerReset, fetchStats } from '../api';

const FLOWS = [
  {
    id: 1, color: 'primary', icon: '🔵',
    title: 'SWS → Departments',
    desc: 'Updates registered address in SWS for UBID-1001. The middleware detects the change via polling, translates the schema, and propagates to both Factory & Shop systems automatically.',
    fn: triggerSwsToDept,
  },
  {
    id: 2, color: 'success', icon: '🟠',
    title: 'Department → SWS',
    desc: 'Updates signatory name directly in the Factory system. Polling adapter detects the change, translates from Factory schema to canonical, and writes to SWS & Shop.',
    fn: triggerDeptToSws,
  },
  {
    id: 3, color: 'warning', icon: '⚡',
    title: 'Conflict Detection',
    desc: 'Simultaneous address updates in SWS ("Hubli") and Factory ("Dharwad") for UBID-1002. Conflict detected and resolved using LATEST_TIMESTAMP_WINS policy.',
    fn: triggerConflict,
  },
  {
    id: 4, color: 'primary', icon: '🔄',
    title: 'Retry & Idempotency',
    desc: 'Enables transient Factory API failures for UBID-1003. Middleware queues retries with exponential backoff. Idempotency engine prevents duplicate writes on success.',
    fn: triggerRetry,
  },
];

export default function DemoPage() {
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  const [stats, setStats] = useState({});

  useEffect(() => {
    fetchStats().then(r => setStats(r.data)).catch(() => {});
    const i = setInterval(() => fetchStats().then(r => setStats(r.data)).catch(() => {}), 4000);
    return () => clearInterval(i);
  }, []);

  const run = async (fn, label) => {
    setBusy(true);
    setStatus(`⏳ Running: ${label}...`);
    try {
      const { data } = await fn();
      setStatus(`✅ ${label} — ${data.note || data.status || 'Done'}`);
      fetchStats().then(r => setStats(r.data)).catch(() => {});
    } catch (e) {
      setStatus(`❌ ${label} failed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>🎮 Demo Controls</h2>
        <p>Trigger demonstration flows to showcase all interoperability mechanics end-to-end</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card blue"><div className="stat-label">Businesses</div><div className="stat-value blue">{stats.total_businesses || 0}</div></div>
        <div className="stat-card green"><div className="stat-label">Audit Entries</div><div className="stat-value green">{stats.total_audit_logs || 0}</div></div>
        <div className="stat-card orange"><div className="stat-label">Conflicts</div><div className="stat-value orange">{stats.total_conflicts || 0}</div></div>
        <div className="stat-card purple"><div className="stat-label">Pending Retries</div><div className="stat-value purple">{stats.pending_retries || 0}</div></div>
      </div>

      {status && <div className="status-banner">{status}</div>}

      <div className="demo-grid">
        {FLOWS.map(f => (
          <div key={f.id} className="demo-card">
            <h3>{f.icon} Flow {f.id}: {f.title}</h3>
            <p>{f.desc}</p>
            <button className={`btn btn-${f.color}`} disabled={busy} onClick={() => run(f.fn, f.title)}>
              ▶ Run Flow {f.id}
            </button>
          </div>
        ))}
      </div>

      <button className="btn btn-outline" disabled={busy} onClick={() => run(triggerReset, 'Reset All Data')}>
        🔄 Reset All Data to Seed State
      </button>
    </div>
  );
}
