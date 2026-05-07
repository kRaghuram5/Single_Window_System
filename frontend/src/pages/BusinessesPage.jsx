import { useState, useEffect } from 'react';
import { fetchBusinesses } from '../api';

const SYSTEM_COLORS = {
  SWS: 'sws',
  FACTORY: 'factory',
  SHOP: 'shop',
};

const SYSTEM_LABELS = {
  SWS: '🏛️ Single Window System',
  FACTORY: '🏭 Factory Department',
  SHOP: '🏪 Shop Establishment',
};

const FIELD_LABELS = {
  // SWS
  business_name: 'Business Name',
  registered_address: 'Address',
  authorized_signatory: 'Signatory',
  contact_email: 'Email',
  status: 'Status',
  // Factory
  establishment_name: 'Establishment',
  factory_addr: 'Address',
  signatory_name: 'Signatory',
  license_status: 'License Status',
  // Shop
  shop_name: 'Shop Name',
  shop_location: 'Location',
  owner_name: 'Owner',
};

export default function BusinessesPage() {
  const [businesses, setBusinesses] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const { data } = await fetchBusinesses();
      setBusinesses(data);
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

  if (loading) return <div className="loading"><div className="spinner" />Loading businesses…</div>;

  return (
    <div>
      <div className="page-header">
        <h2>📊 Synchronized Businesses</h2>
        <p>Each business shows its current state across all three systems, synchronized via UBID</p>
      </div>

      <div className="business-cards">
        {businesses.map((biz) => (
          <div key={biz.ubid} className="business-card">
            <div className="business-card-header">
              <div>
                <span className="business-ubid">{biz.ubid}</span>
                <span className="business-name" style={{ marginLeft: 16 }}>
                  {biz.systems?.SWS?.business_name || biz.systems?.FACTORY?.establishment_name || '—'}
                </span>
              </div>
              <span className="badge badge-success">SYNCED</span>
            </div>
            <div className="business-systems">
              {Object.entries(biz.systems).map(([sys, data]) => (
                <div key={sys} className="system-column">
                  <div className={`system-column-header`}>
                    <span className={`system-badge ${SYSTEM_COLORS[sys]}`}>{SYSTEM_LABELS[sys]}</span>
                  </div>
                  {Object.entries(data)
                    .filter(([k]) => k !== 'updated_at')
                    .map(([field, value]) => (
                      <div key={field} className="system-field">
                        <div className="system-field-label">{FIELD_LABELS[field] || field}</div>
                        <div className="system-field-value">{value || '—'}</div>
                      </div>
                    ))}
                  <div className="system-field">
                    <div className="system-field-label">Last Updated</div>
                    <div className="system-field-value" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {data.updated_at ? new Date(data.updated_at).toLocaleString() : '—'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {businesses.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">🏢</div>
          <p>No businesses found. Run the seed data.</p>
        </div>
      )}
    </div>
  );
}
