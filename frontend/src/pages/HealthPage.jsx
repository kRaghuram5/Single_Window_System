import { useState, useEffect } from 'react';
import { fetchHealth } from '../api';

export default function HealthPage() {
  const [health, setHealth] = useState({});
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const { data } = await fetchHealth();
      setHealth(data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); const i = setInterval(load, 3000); return () => clearInterval(i); }, []);

  if (loading) return <div className="loading"><div className="spinner" />Loading…</div>;

  const LABELS = {
    SWS: { icon: '🏛️', name: 'Single Window System' },
    FACTORY: { icon: '🏭', name: 'Factory Department' },
    SHOP: { icon: '🏪', name: 'Shop Establishment' },
  };

  return (
    <div>
      <div className="page-header">
        <h2>🩺 System Health</h2>
        <p>Real-time polling status and API availability</p>
      </div>
      <div className="health-grid">
        {Object.entries(health).map(([sys, data]) => {
          const l = LABELS[sys] || { icon: '📡', name: sys };
          return (
            <div key={sys} className="health-card">
              <div className={`health-indicator ${data.is_healthy ? 'healthy' : 'unhealthy'}`}>
                {data.is_healthy ? '✓' : '✗'}
              </div>
              <div style={{ fontSize: 28, marginBottom: 8 }}>{l.icon}</div>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>{l.name}</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, textAlign: 'left', padding: '0 12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                  <span style={{ color: 'var(--text-muted)' }}>Status</span>
                  <span className={`badge ${data.is_healthy ? 'badge-success' : 'badge-error'}`}>
                    {data.is_healthy ? 'HEALTHY' : 'DOWN'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                  <span style={{ color: 'var(--text-muted)' }}>Polls</span>
                  <span style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{data.poll_count || 0}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                  <span style={{ color: 'var(--text-muted)' }}>Last Poll</span>
                  <span style={{ fontSize: 11 }}>{data.last_poll_at ? new Date(data.last_poll_at).toLocaleTimeString() : 'Never'}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ marginTop: 24, padding: 16, background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border-color)', fontSize: 13, color: 'var(--text-secondary)' }}>
        <strong style={{ color: 'var(--accent-cyan)' }}>ℹ Polling:</strong> Each system polled every <strong>5 seconds</strong>. Only DIRECT changes are detected.
      </div>
    </div>
  );
}
