import { useState, useEffect } from 'react';
import { fetchConflicts } from '../api';

export default function ConflictsPage() {
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const { data } = await fetchConflicts();
      setConflicts(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading"><div className="spinner" />Loading…</div>;

  return (
    <div>
      <div className="page-header">
        <h2>⚡ Conflict Resolution</h2>
        <p>Detected concurrent updates and their automated resolutions</p>
      </div>

      {conflicts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <p>No conflicts detected. Trigger Demo Flow 3 to see conflict resolution in action.</p>
        </div>
      ) : (
        conflicts.map((c) => (
          <div key={c.id} className="conflict-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <span className="business-ubid">{c.ubid}</span>
              <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>Field: <strong style={{ color: 'var(--accent-orange)' }}>{c.field}</strong></span>
              <span className={`badge ${c.status === 'RESOLVED' ? 'badge-success' : 'badge-warning'}`}>{c.status}</span>
            </div>

            <div className="conflict-versus">
              <div className="conflict-side">
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                  <span className={`system-badge ${c.source_a?.toLowerCase()}`}>{c.source_a}</span>
                </div>
                <div style={{ fontSize: 15, fontWeight: 600, color: c.winning_source === c.source_a ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                  "{c.value_a}"
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                  {c.timestamp_a ? new Date(c.timestamp_a).toLocaleString() : '—'}
                </div>
              </div>

              <span className="vs-badge">VS</span>

              <div className="conflict-side">
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                  <span className={`system-badge ${c.source_b?.toLowerCase()}`}>{c.source_b}</span>
                </div>
                <div style={{ fontSize: 15, fontWeight: 600, color: c.winning_source === c.source_b ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                  "{c.value_b}"
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                  {c.timestamp_b ? new Date(c.timestamp_b).toLocaleString() : '—'}
                </div>
              </div>
            </div>

            <div className="conflict-resolution">
              <strong>🏆 Resolution:</strong> Policy <code style={{ color: 'var(--accent-cyan)' }}>{c.resolution_policy}</code> →
              Winner: <strong style={{ color: 'var(--accent-green)' }}>{c.winning_source}</strong> →
              Value: <strong>"{c.resolved_value}"</strong>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
