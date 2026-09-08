import React from 'react';
import { Layers, Activity, FileText, Search, GitMerge, AlertTriangle, Database } from 'lucide-react';
import { HealthData } from '../types';

interface NavbarProps {
  activeTab: 'dashboard' | 'documents' | 'facts' | 'conflicts' | 'issues';
  setActiveTab: (tab: 'dashboard' | 'documents' | 'facts' | 'conflicts' | 'issues') => void;
  health: HealthData | null;
  loadingHealth: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  health,
  loadingHealth
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'facts', label: 'Fact Ledger', icon: Search },
    { id: 'conflicts', label: 'Conflict & Reconciliation', icon: GitMerge },
    { id: 'issues', label: 'Issue Center', icon: AlertTriangle }
  ] as const;

  return (
    <header style={{
      background: 'var(--bg-glass)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-color)',
      padding: '0.75rem 2rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 50
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: 'var(--shadow-glow)'
        }}>
          <Layers size={22} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff', margin: 0 }}>
            FACT<span style={{ color: 'var(--accent-cyan)' }}>MESH</span>
          </h1>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: 0 }}>
            Context-Aware Fact Knowledge Layer
          </p>
        </div>
      </div>

      {/* Tab Navigation */}
      <nav style={{
        display: 'flex',
        gap: '0.4rem',
        background: 'var(--bg-secondary)',
        padding: '0.3rem',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-color)'
      }}>
        {navItems.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.45rem 0.95rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.85rem',
                fontWeight: 600,
                transition: 'all 0.2s ease',
                background: isActive ? 'var(--accent-primary)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                cursor: 'pointer'
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* System Health Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.45rem',
          padding: '0.35rem 0.8rem',
          borderRadius: 'var(--radius-full)',
          background: health?.status === 'ok' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          border: `1px solid ${health?.status === 'ok' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          fontSize: '0.75rem',
          fontWeight: 600,
          color: health?.status === 'ok' ? '#10b981' : '#ef4444'
        }}>
          <Database size={13} />
          <span>DB: {health?.database?.dialect || (loadingHealth ? 'Connecting...' : 'Offline')}</span>
          <span style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            backgroundColor: health?.status === 'ok' ? '#10b981' : '#ef4444'
          }}></span>
        </div>
      </div>
    </header>
  );
};
