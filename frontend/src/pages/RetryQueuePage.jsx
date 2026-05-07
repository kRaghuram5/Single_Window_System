import { useState, useEffect } from 'react';
import { fetchRetryQueue } from '../api';

const STATUS_BADGE = {
  PENDING: 'badge-warning',
  SUCCESS: 'badge-success',
  EXHAUSTED: 'badge-error',
};

export default function RetryQueuePage() {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const { data } = await fetchRetryQueue();
      setQueue(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading"><div className="spinner" />Loading…</div>;

  return (
    <div>
      <div className="page-header">
        <h2>🔄 Retry Queue</h2>
        <p>Failed propagations with exponential backoff retry — guarantees at-least-once delivery</p>
      </div>

      {queue.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔄</div>
          <p>Retry queue is empty. Trigger Demo Flow 4 to simulate failures.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Request ID</th>
                <th>UBID</th>
                <th>Source</th>
                <th>Target</th>
                <th>Retry Count</th>
                <th>Max Retries</th>
                <th>Status</th>
                <th>Error</th>
                <th>Next Retry</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((item) => (
                <tr key={item.id}>
                  <td style={{ fontSize: 11, fontFamily: 'monospace' }}>{item.request_id?.substring(0, 25)}…</td>
                  <td><span className="business-ubid">{item.ubid}</span></td>
                  <td><span className={`system-badge ${item.source_system?.toLowerCase()}`}>{item.source_system}</span></td>
                  <td><span className={`system-badge ${item.target_system?.toLowerCase()}`}>{item.target_system}</span></td>
                  <td style={{ textAlign: 'center', fontWeight: 600 }}>{item.retry_count}</td>
                  <td style={{ textAlign: 'center' }}>{item.max_retries}</td>
                  <td><span className={`badge ${STATUS_BADGE[item.status]}`}>{item.status}</span></td>
                  <td style={{ fontSize: 11, color: 'var(--accent-red)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.error_message || '—'}
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {item.next_retry_at ? new Date(item.next_retry_at).toLocaleTimeString() : '—'}
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {item.created_at ? new Date(item.created_at).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ marginTop: 20, padding: 16, background: 'var(--bg-card)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          <strong style={{ color: 'var(--accent-cyan)' }}>ℹ Retry Policy:</strong> Exponential backoff (5s × 2^n, max 60s). After 5 failures, the item is marked as EXHAUSTED.
          Each retry checks idempotency to prevent duplicate writes.
        </div>
      </div>
    </div>
  );
}
