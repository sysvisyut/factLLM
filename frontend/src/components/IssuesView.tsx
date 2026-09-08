import React, { useState, useMemo } from 'react';
import { AlertTriangle, CheckCircle2, ShieldAlert, RefreshCw } from 'lucide-react';
import { ExtractionIssueItem } from '../types';
import { api } from '../services/api';

interface IssuesViewProps {
  issues: ExtractionIssueItem[];
  loading: boolean;
  onRefresh: () => void;
}

export const IssuesView: React.FC<IssuesViewProps> = ({
  issues,
  loading,
  onRefresh
}) => {
  const [activeFilter, setActiveFilter] = useState<string>('ALL');
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const filteredIssues = useMemo(() => {
    if (activeFilter === 'ALL') return issues;
    return issues.filter(i => i.status.toUpperCase() === activeFilter);
  }, [issues, activeFilter]);

  const handleStatusToggle = async (issueId: string, currentStatus: string) => {
    setUpdatingId(issueId);
    try {
      if (currentStatus === 'OPEN') {
        await api.resolveIssue(issueId, 'Resolved via Audit Console');
      }
      onRefresh();
    } catch (err) {
      console.error("Failed to update issue status:", err);
    } finally {
      setUpdatingId(null);
    }
  };

  const getSeverityBadge = (type: string) => {
    if (type.includes('FALLBACK') || type.includes('ERROR') || type.includes('UNGROUNDED')) {
      return { label: type, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.3)' };
    }
    if (type.includes('AMBIGUITY') || type.includes('LOW_CONFIDENCE')) {
      return { label: type, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.3)' };
    }
    return { label: type, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', border: 'rgba(59, 130, 246, 0.3)' };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', color: '#ffffff', margin: 0 }}>
            Honest Failure & Extraction Issue Center
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.3rem' }}>
            Auditable tracking of ungrounded claims, scanned OCR warnings, and ambiguity detections without silent hallucination.
          </p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.55rem 1.1rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
            fontSize: '0.85rem',
            cursor: 'pointer'
          }}
        >
          <RefreshCw size={15} className={loading ? 'spin' : ''} />
          Refresh Issues
        </button>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        {['ALL', 'OPEN', 'RESOLVED', 'IGNORED'].map(status => {
          const isActive = activeFilter === status;
          const count = status === 'ALL'
            ? issues.length
            : issues.filter(i => i.status.toUpperCase() === status).length;
          return (
            <button
              key={status}
              onClick={() => setActiveFilter(status)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.45rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
                background: isActive ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                border: `1px solid ${isActive ? 'transparent' : 'var(--border-color)'}`,
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <span>{status}</span>
              <span style={{
                fontSize: '0.72rem',
                padding: '0.1rem 0.4rem',
                borderRadius: 'var(--radius-full)',
                background: isActive ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.06)',
                color: '#ffffff'
              }}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Issues Table */}
      <div className="glass-panel" style={{ padding: '1.25rem', overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Showing <strong style={{ color: '#ffffff' }}>{filteredIssues.length}</strong> recorded extraction issues
          </span>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading extraction issues...
          </div>
        ) : filteredIssues.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No extraction issues matching "{activeFilter}". The pipeline operates with zero unresolved flags.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.76rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Issue Type</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Location</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Description & Failure Context</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Attempted Resolution</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Status</th>
                  <th style={{ padding: '0.75rem 0.85rem', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredIssues.map(issue => {
                  const badge = getSeverityBadge(issue.issue_type);
                  const isResolved = issue.status.toUpperCase() === 'RESOLVED';
                  return (
                    <tr key={issue.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      {/* Type Badge */}
                      <td style={{ padding: '0.85rem' }}>
                        <span style={{
                          display: 'inline-block',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.55rem',
                          borderRadius: 'var(--radius-full)',
                          background: badge.bg,
                          color: badge.color,
                          border: `1px solid ${badge.border}`
                        }}>
                          {issue.issue_type}
                        </span>
                      </td>

                      {/* Location */}
                      <td style={{ padding: '0.85rem', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                        {issue.page_number ? `Page ${issue.page_number}` : 'Global'}
                      </td>

                      {/* Description & Affected text */}
                      <td style={{ padding: '0.85rem', maxWidth: '380px' }}>
                        <div style={{ color: '#ffffff', fontWeight: 500, lineHeight: 1.4 }}>
                          {issue.description}
                        </div>
                        {issue.affected_text && (
                          <code style={{
                            display: 'block',
                            marginTop: '0.35rem',
                            fontSize: '0.72rem',
                            color: 'var(--accent-cyan)',
                            background: 'var(--bg-primary)',
                            padding: '0.25rem 0.5rem',
                            borderRadius: 'var(--radius-sm)',
                            wordBreak: 'break-word',
                            fontFamily: 'var(--font-mono)'
                          }}>
                            {issue.affected_text}
                          </code>
                        )}
                      </td>

                      {/* Attempted Resolution */}
                      <td style={{ padding: '0.85rem', color: 'var(--text-secondary)', fontSize: '0.82rem', maxWidth: '240px' }}>
                        {issue.attempted_resolution || 'Logged for human verification'}
                      </td>

                      {/* Status */}
                      <td style={{ padding: '0.85rem' }}>
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '0.15rem 0.5rem',
                          borderRadius: 'var(--radius-full)',
                          background: isResolved ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                          color: isResolved ? '#10b981' : '#ef4444'
                        }}>
                          {isResolved ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
                          {issue.status}
                        </span>
                      </td>

                      {/* Action */}
                      <td style={{ padding: '0.85rem', textAlign: 'right' }}>
                        <button
                          onClick={() => handleStatusToggle(issue.id, issue.status)}
                          disabled={updatingId === issue.id}
                          style={{
                            padding: '0.35rem 0.75rem',
                            borderRadius: 'var(--radius-sm)',
                            background: isResolved ? 'transparent' : 'rgba(16, 185, 129, 0.15)',
                            border: `1px solid ${isResolved ? 'var(--border-color)' : '#10b981'}`,
                            color: isResolved ? 'var(--text-secondary)' : '#10b981',
                            fontSize: '0.76rem',
                            fontWeight: 600,
                            cursor: 'pointer'
                          }}
                        >
                          {updatingId === issue.id ? 'Updating...' : isResolved ? 'Reopen' : 'Mark Resolved'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Honest Failure Philosophy Card */}
      <div style={{
        background: 'rgba(239, 68, 68, 0.06)',
        border: '1px solid rgba(239, 68, 68, 0.2)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem 1.5rem',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem'
      }}>
        <ShieldAlert size={28} color="#ef4444" />
        <div>
          <h4 style={{ color: '#ffffff', fontSize: '0.95rem', margin: 0 }}>
            Architecture Principle: Fail Fast & Honest Reporting Over Hallucination
          </h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', margin: '0.25rem 0 0 0', lineHeight: 1.5 }}>
            Traditional RAG chatbots silently hallucinate plausible answers when confronted with blurry text, scanned cover art, 
            or conflicting table schemas. FACTMESH explicitly detects, isolates, and logs extraction ambiguities into this ledger, 
            enabling automated audits and human-in-the-loop review.
          </p>
        </div>
      </div>
    </div>
  );
};
