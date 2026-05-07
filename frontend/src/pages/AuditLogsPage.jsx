import { useState, useEffect } from 'react';
import { fetchAuditLogs } from '../api';

const STATUS_BADGE = {
  SUCCESS: 'badge-success',
  FAILED: 'badge-error',
  RETRYING: 'badge-warning',
  EXHAUSTED: 'badge-error',
};

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const load = async () => {
    try {
      const { data } = await fetchAuditLogs(filter || undefined);
      setLogs(data);
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
  }, [filter]);

  return (
    <div>
      <div className="page-header">
        <h2>📋 Audit Trail</h2>
        <p>Complete propagation history — every write is traceable end-to-end</p>
      </div>

      <div style={{ marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Filter by UBID (e.g. UBID-1001)"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{
            padding: '8px 14px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: 13,
            fontFamily: 'Inter, sans-serif',
            width: 280,
          }}
        />
        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>{logs.length} records</span>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" />Loading logs…</div>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <p>No audit logs yet. Trigger a demo flow to generate entries.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Request ID</th>
                <th>UBID</th>
                <th>Source</th>
                <th>Target</th>
                <th>Field</th>
                <th>Old Value</th>
                <th>New Value</th>
                <th>Status</th>
                <th>Retries</th>
                <th>Conflict</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                  </td>
                  <td style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                    {log.request_id?.substring(0, 20)}…
                  </td>
                  <td><span className="business-ubid">{log.ubid}</span></td>
                  <td><span className={`system-badge ${log.source_system?.toLowerCase()}`}>{log.source_system}</span></td>
                  <td><span className={`system-badge ${log.target_system?.toLowerCase()}`}>{log.target_system}</span></td>
                  <td style={{ fontWeight: 500 }}>{log.field_changed}</td>
                  <td style={{ color: 'var(--accent-red)', fontSize: 12 }}>{log.old_value || '—'}</td>
                  <td style={{ color: 'var(--accent-green)', fontSize: 12 }}>{log.new_value || '—'}</td>
                  <td><span className={`badge ${STATUS_BADGE[log.status] || 'badge-info'}`}>{log.status}</span></td>
                  <td style={{ textAlign: 'center' }}>{log.retry_count || 0}</td>
                  <td>
                    {log.conflict_flag !== 'NONE' && (
                      <span className="badge badge-warning">{log.conflict_flag}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
