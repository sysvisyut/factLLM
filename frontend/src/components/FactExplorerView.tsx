import React, { useState, useMemo } from 'react';
import { Search, Filter, Eye, RefreshCw, Calendar, Tag } from 'lucide-react';
import { FactItem } from '../types';
import { EvidenceModal } from './EvidenceModal';

interface FactExplorerViewProps {
  facts: FactItem[];
  loading: boolean;
  onRefresh: () => void;
}

export const FactExplorerView: React.FC<FactExplorerViewProps> = ({
  facts,
  loading,
  onRefresh
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedEntity, setSelectedEntity] = useState<string>('ALL');
  const [selectedPredicateType, setSelectedPredicateType] = useState<string>('ALL');
  const [selectedConfidence, setSelectedConfidence] = useState<string>('ALL');
  const [inspectingFact, setInspectingFact] = useState<FactItem | null>(null);

  // Derive unique entities
  const entities = useMemo(() => {
    const set = new Set<string>();
    facts.forEach(f => {
      if (f.subject_canonical) set.add(f.subject_canonical);
    });
    return Array.from(set).sort();
  }, [facts]);

  // Derive unique predicate types
  const predicateTypes = useMemo(() => {
    const set = new Set<string>();
    facts.forEach(f => {
      if (f.predicate_type) set.add(f.predicate_type);
    });
    return Array.from(set).sort();
  }, [facts]);

  // Filtered facts
  const filteredFacts = useMemo(() => {
    return facts.filter(f => {
      // Entity match
      if (selectedEntity !== 'ALL' && f.subject_canonical !== selectedEntity) {
        return false;
      }
      // Predicate type match
      if (selectedPredicateType !== 'ALL' && f.predicate_type !== selectedPredicateType) {
        return false;
      }
      // Confidence level match
      if (selectedConfidence !== 'ALL' && f.confidence_level !== selectedConfidence) {
        return false;
      }
      // Search term match
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchesSubject = f.subject_canonical.toLowerCase().includes(query) || f.subject_raw.toLowerCase().includes(query);
        const matchesPredicate = f.predicate_canonical.toLowerCase().includes(query) || f.predicate_raw.toLowerCase().includes(query);
        const matchesValue = f.value_raw.toLowerCase().includes(query) || (f.value_normalized?.toString().includes(query) ?? false);
        const matchesEvidence = f.evidence?.exact_text.toLowerCase().includes(query) ?? false;
        if (!matchesSubject && !matchesPredicate && !matchesValue && !matchesEvidence) {
          return false;
        }
      }
      return true;
    });
  }, [facts, selectedEntity, selectedPredicateType, selectedConfidence, searchTerm]);

  const getConfidenceBadgeColor = (level: string) => {
    switch (level) {
      case 'HIGH':
        return { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', border: 'rgba(16, 185, 129, 0.3)' };
      case 'MEDIUM':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', border: 'rgba(245, 158, 11, 0.3)' };
      case 'LOW':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444', border: 'rgba(239, 68, 68, 0.3)' };
      default:
        return { bg: 'rgba(100, 116, 139, 0.15)', text: '#64748b', border: 'rgba(100, 116, 139, 0.3)' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Evidence Inspector Modal */}
      {inspectingFact && (
        <EvidenceModal
          fact={inspectingFact}
          onClose={() => setInspectingFact(null)}
        />
      )}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', color: '#ffffff', margin: 0 }}>
            Grounded Fact Ledger Explorer
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.3rem' }}>
            Fully normalized, fingerprinted, and evidence-grounded facts extracted across all ingested documents.
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
          Refresh Facts
        </button>
      </div>

      {/* Search & Filter Bar */}
      <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        <div style={{ flex: '1 1 280px', position: 'relative' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search facts by entity, metric name, value, or source text..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '0.65rem 1rem 0.65rem 2.6rem',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              color: '#ffffff',
              fontSize: '0.85rem',
              outline: 'none'
            }}
          />
        </div>

        {/* Entity Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Tag size={15} color="var(--accent-cyan)" />
          <select
            value={selectedEntity}
            onChange={e => setSelectedEntity(e.target.value)}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              padding: '0.6rem 0.85rem',
              fontSize: '0.82rem',
              outline: 'none'
            }}
          >
            <option value="ALL">All Entities ({entities.length})</option>
            {entities.map(e => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
        </div>

        {/* Predicate Type Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={15} color="var(--accent-primary)" />
          <select
            value={selectedPredicateType}
            onChange={e => setSelectedPredicateType(e.target.value)}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              padding: '0.6rem 0.85rem',
              fontSize: '0.82rem',
              outline: 'none'
            }}
          >
            <option value="ALL">All Metric Types</option>
            {predicateTypes.map(pt => (
              <option key={pt} value={pt}>{pt}</option>
            ))}
          </select>
        </div>

        {/* Confidence Filter */}
        <select
          value={selectedConfidence}
          onChange={e => setSelectedConfidence(e.target.value)}
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)',
            padding: '0.6rem 0.85rem',
            fontSize: '0.82rem',
            outline: 'none'
          }}
        >
          <option value="ALL">All Confidence Levels</option>
          <option value="HIGH">HIGH (&ge; 85%)</option>
          <option value="MEDIUM">MEDIUM (70% - 84%)</option>
          <option value="LOW">LOW (&lt; 70%)</option>
        </select>
      </div>

      {/* Fact Ledger Table */}
      <div className="glass-panel" style={{ padding: '1.25rem', overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Showing <strong style={{ color: '#ffffff' }}>{filteredFacts.length}</strong> of {facts.length} extracted facts
          </span>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading extracted fact ledger...
          </div>
        ) : filteredFacts.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No facts match the selected filters or search query.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.76rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Subject / Entity</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Predicate / Metric</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Stated Value</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Normalized</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Canonical Unit</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Temporal Window</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Confidence</th>
                  <th style={{ padding: '0.75rem 0.85rem', textAlign: 'right' }}>Provenance</th>
                </tr>
              </thead>
              <tbody>
                {filteredFacts.map(fact => {
                  const confBadge = getConfidenceBadgeColor(fact.confidence_level);
                  return (
                    <tr 
                      key={fact.id} 
                      style={{ 
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        transition: 'background 0.15s ease'
                      }}
                    >
                      {/* Subject */}
                      <td style={{ padding: '0.85rem', fontWeight: 600, color: '#ffffff' }}>
                        <div>{fact.subject_canonical}</div>
                        {fact.subject_raw !== fact.subject_canonical && (
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            as "{fact.subject_raw}"
                          </div>
                        )}
                      </td>

                      {/* Predicate */}
                      <td style={{ padding: '0.85rem' }}>
                        <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                          {fact.predicate_canonical}
                        </div>
                        <span style={{
                          display: 'inline-block',
                          fontSize: '0.68rem',
                          color: 'var(--text-muted)',
                          padding: '0.1rem 0.4rem',
                          borderRadius: 'var(--radius-sm)',
                          background: 'rgba(255, 255, 255, 0.04)',
                          marginTop: '0.2rem'
                        }}>
                          {fact.predicate_type}
                        </span>
                      </td>

                      {/* Stated Value */}
                      <td style={{ padding: '0.85rem', fontWeight: 700, color: '#ffffff' }}>
                        {fact.value_raw}
                      </td>

                      {/* Normalized Value */}
                      <td style={{ padding: '0.85rem' }}>
                        {fact.value_normalized !== undefined && fact.value_normalized !== null ? (
                          <code style={{ fontSize: '0.8rem', color: '#10b981', fontFamily: 'var(--font-mono)' }}>
                            {fact.value_normalized.toLocaleString(undefined, { maximumFractionDigits: 4 })}
                          </code>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>-</span>
                        )}
                      </td>

                      {/* Canonical Unit */}
                      <td style={{ padding: '0.85rem', color: 'var(--accent-cyan)', fontSize: '0.82rem' }}>
                        {fact.unit_canonical || (fact.unit_raw ? `(${fact.unit_raw})` : '-')}
                      </td>

                      {/* Temporal Window */}
                      <td style={{ padding: '0.85rem' }}>
                        {fact.context?.time?.raw ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                            <Calendar size={13} color="var(--accent-primary)" />
                            <span>{fact.context.time.raw}</span>
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Unspecified</span>
                        )}
                      </td>

                      {/* Confidence */}
                      <td style={{ padding: '0.85rem' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.6rem',
                          borderRadius: 'var(--radius-full)',
                          fontSize: '0.74rem',
                          fontWeight: 700,
                          background: confBadge.bg,
                          color: confBadge.text,
                          border: `1px solid ${confBadge.border}`
                        }}>
                          {fact.confidence_level} ({(fact.confidence_overall * 100).toFixed(0)}%)
                        </span>
                      </td>

                      {/* Provenance Action */}
                      <td style={{ padding: '0.85rem', textAlign: 'right' }}>
                        <button
                          onClick={() => setInspectingFact(fact)}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            padding: '0.35rem 0.75rem',
                            borderRadius: 'var(--radius-sm)',
                            background: 'rgba(6, 182, 212, 0.1)',
                            border: '1px solid rgba(6, 182, 212, 0.3)',
                            color: 'var(--accent-cyan)',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer'
                          }}
                        >
                          <Eye size={13} />
                          Page {fact.evidence?.page_number ?? 'Ev'}
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
    </div>
  );
};
