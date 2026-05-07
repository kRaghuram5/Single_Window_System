import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import './index.css';
import DemoPage from './pages/DemoPage';
import BusinessesPage from './pages/BusinessesPage';
import AuditLogsPage from './pages/AuditLogsPage';
import ConflictsPage from './pages/ConflictsPage';
import RetryQueuePage from './pages/RetryQueuePage';
import HealthPage from './pages/HealthPage';

const NAV = [
  { path: '/', icon: '🎮', label: 'Demo Controls' },
  { path: '/businesses', icon: '📊', label: 'Businesses' },
  { path: '/audit', icon: '📋', label: 'Audit Trail' },
  { path: '/conflicts', icon: '⚡', label: 'Conflicts' },
  { path: '/retries', icon: '🔄', label: 'Retry Queue' },
  { path: '/health', icon: '🩺', label: 'System Health' },
];

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <aside className="sidebar">
          <div className="sidebar-header">
            <div className="sidebar-logo">
              <div className="sidebar-logo-icon">U</div>
              <div className="sidebar-logo-text">
                <h1>UBID-Sync</h1>
                <p>Interoperability Middleware</p>
              </div>
            </div>
          </div>
          <nav className="sidebar-nav">
            {NAV.map(({ path, icon, label }) => (
              <NavLink
                key={path}
                to={path}
                end={path === '/'}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">{icon}</span>
                {label}
              </NavLink>
            ))}
          </nav>
          <div style={{ padding: '14px 16px', borderTop: '1px solid var(--border-color)', fontSize: 10, color: 'var(--text-muted)' }}>
            Karnataka SWS Prototype v1.0
          </div>
        </aside>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<DemoPage />} />
            <Route path="/businesses" element={<BusinessesPage />} />
            <Route path="/audit" element={<AuditLogsPage />} />
            <Route path="/conflicts" element={<ConflictsPage />} />
            <Route path="/retries" element={<RetryQueuePage />} />
            <Route path="/health" element={<HealthPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
