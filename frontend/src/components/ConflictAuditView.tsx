import React, { useState, useMemo } from 'react';
import { Scale, RefreshCw, Eye, FileText } from 'lucide-react';
import { RelationshipItem, RelationshipType, FactItem } from '../types';
import { EvidenceModal } from './EvidenceModal';

interface ConflictAuditViewProps {
  relationships: RelationshipItem[];
  loading: boolean;
  onRefresh: () => void;
  initialFilter?: string;
}

export const ConflictAuditView: React.FC<ConflictAuditViewProps> = ({
  relationships,
  loading,
  onRefresh,
  initialFilter
}) => {
  const [activeTypeFilter, setActiveTypeFilter] = useState<string>(initialFilter || 'ALL');
  const [selectedRelId, setSelectedRelId] = useState<string | null>(null);
  const [inspectingFact, setInspectingFact] = useState<FactItem | null>(null);

  // Filtered list
  const filteredRelationships = useMemo(() => {
    if (activeTypeFilter === 'ALL') return relationships;
    return relationships.filter(r => r.relationship_type === activeTypeFilter);
  }, [relationships, activeTypeFilter]);

  // Selected item
  const selectedRel = useMemo(() => {
    if (selectedRelId) {
      const found = relationships.find(r => r.id === selectedRelId);
      if (found) return found;
    }
    return filteredRelationships[0] || null;
  }, [selectedRelId, filteredRelationships, relationships]);

  const getRelationshipBadge = (type: RelationshipType) => {
    switch (type) {
      case 'CORROBORATES':
        return { label: 'Corroborates', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.3)' };
      case 'CONTRADICTS':
        return { label: 'Contradicts', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.3)' };
      case 'RECONCILES':
        return { label: 'Reconciled', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.3)' };
      case 'TEMPORALLY_EVOLVES':
        return { label: 'Temporal Evolution', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', border: 'rgba(59, 130, 246, 0.3)' };
      case 'SCOPE_DIFFERENCE':
        return { label: 'Scope Difference', color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.15)', border: 'rgba(139, 92, 246, 0.3)' };
      case 'UNIT_EQUIVALENT':
        return { label: 'Unit Equivalent', color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.15)', border: 'rgba(6, 182, 212, 0.3)' };
      default:
        return { label: type, color: '#64748b', bg: 'rgba(100, 116, 139, 0.15)', border: 'rgba(100, 116, 139, 0.3)' };
    }
  };

  const typeTabs: { id: string; label: string }[] = [
    { id: 'ALL', label: 'All Relationships' },
    { id: 'RECONCILES', label: 'Reconciled' },
    { id: 'CORROBORATES', label: 'Corroborations' },
    { id: 'CONTRADICTS', label: 'Contradictions' },
    { id: 'TEMPORALLY_EVOLVES', label: 'Temporal Evolutions' },
    { id: 'SCOPE_DIFFERENCE', label: 'Scope Differences' },
    { id: 'UNIT_EQUIVALENT', label: 'Unit Equivalent' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Evidence Modal */}
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
            Cross-Document Conflict & Reconciliation Audit
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.3rem' }}>
            Multidimensional context resolution: disambiguating measurement basis, time evolution, scope, and unit scaling.
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
          Refresh Audit
        </button>
      </div>

      {/* Type Tabs */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        overflowX: 'auto',
        paddingBottom: '0.25rem'
      }}>
        {typeTabs.map(tab => {
          const isActive = activeTypeFilter === tab.id;
          const count = tab.id === 'ALL'
            ? relationships.length
            : relationships.filter(r => r.relationship_type === tab.id).length;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTypeFilter(tab.id);
                setSelectedRelId(null);
              }}
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
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              <span>{tab.label}</span>
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

      {/* Master-Detail Split Screen */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 380px) 1fr', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* Left: Relationship List */}
        <div className="glass-panel" style={{ padding: '1rem', maxHeight: 'calc(100vh - 250px)', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0.25rem 0.5rem' }}>
            Resolved Candidate Pairs ({filteredRelationships.length})
          </div>

          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading candidate relationships...
            </div>
          ) : filteredRelationships.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No relationships found for selected filter.
            </div>
          ) : (
            filteredRelationships.map(rel => {
              const badge = getRelationshipBadge(rel.relationship_type);
              const isSelected = selectedRel?.id === rel.id;
              return (
                <div
                  key={rel.id}
                  onClick={() => setSelectedRelId(rel.id)}
                  style={{
                    padding: '0.9rem',
                    borderRadius: 'var(--radius-sm)',
                    background: isSelected ? 'rgba(99, 102, 241, 0.16)' : 'var(--bg-secondary)',
                    border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--border-color)'}`,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '0.15rem 0.5rem',
                      borderRadius: 'var(--radius-full)',
                      background: badge.bg,
                      color: badge.color,
                      border: `1px solid ${badge.border}`
                    }}>
                      {badge.label}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {(rel.confidence * 100).toFixed(0)}% conf
                    </span>
                  </div>

                  <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#ffffff', marginBottom: '0.3rem' }}>
                    {rel.fact_a?.predicate_canonical || 'Metric'}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    <span>Fact A: <strong style={{ color: 'var(--accent-cyan)' }}>{rel.fact_a?.value_raw}</strong></span>
                    <span>vs</span>
                    <span>Fact B: <strong style={{ color: '#10b981' }}>{rel.fact_b?.value_raw}</strong></span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right: Deep Dive Inspector */}
        {selectedRel ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            
            {/* Top Banner */}
            {(() => {
              const badge = getRelationshipBadge(selectedRel.relationship_type);
              return (
                <div className="glass-panel" style={{
                  padding: '1.25rem 1.5rem',
                  borderLeft: `5px solid ${badge.color}`,
                  background: badge.bg
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span style={{
                        fontSize: '0.85rem',
                        fontWeight: 800,
                        padding: '0.3rem 0.8rem',
                        borderRadius: 'var(--radius-full)',
                        background: 'rgba(0, 0, 0, 0.4)',
                        color: badge.color,
                        border: `1px solid ${badge.border}`,
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em'
                      }}>
                        {badge.label}
                      </span>
                      <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>
                        {selectedRel.fact_a?.predicate_canonical}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#ffffff', background: 'rgba(0, 0, 0, 0.3)', padding: '0.25rem 0.75rem', borderRadius: 'var(--radius-sm)' }}>
                      Resolution Confidence: <strong>{(selectedRel.confidence * 100).toFixed(1)}%</strong>
                    </div>
                  </div>

                  {selectedRel.important_differences && selectedRel.important_differences.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.75rem' }}>
                      {selectedRel.important_differences.map((diff, i) => (
                        <span key={i} style={{
                          fontSize: '0.72rem',
                          background: 'rgba(0, 0, 0, 0.35)',
                          color: '#e2e8f0',
                          padding: '0.15rem 0.5rem',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid rgba(255, 255, 255, 0.1)'
                        }}>
                          • {diff}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Side-by-Side Comparison Columns */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.25rem' }}>
              
              {/* Fact A */}
              <div className="glass-panel" style={{ padding: '1.25rem', borderTop: '3px solid var(--accent-cyan)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Fact A Claim
                  </span>
                  {selectedRel.fact_a && (
                    <button
                      onClick={() => setInspectingFact(selectedRel.fact_a!)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--accent-cyan)',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        fontWeight: 600
                      }}
                    >
                      <Eye size={13} />
                      Inspect Provenance
                    </button>
                  )}
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#ffffff' }}>
                    {selectedRel.fact_a?.value_raw}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Normalized: <code style={{ color: 'var(--accent-cyan)' }}>{selectedRel.fact_a?.value_normalized?.toLocaleString() ?? 'N/A'} {selectedRel.fact_a?.unit_canonical}</code>
                  </div>
                </div>

                {/* Dimensions list */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.8rem', background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Subject: </span>
                    <strong style={{ color: '#ffffff' }}>{selectedRel.fact_a?.subject_canonical}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Time Period: </span>
                    <strong style={{ color: '#ffffff' }}>{selectedRel.fact_a?.context?.time?.raw || 'Unspecified'}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Scope: </span>
                    <strong style={{ color: '#ffffff' }}>{selectedRel.fact_a?.context?.scope || 'CONSOLIDATED'}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Measurement Basis: </span>
                    <strong style={{ color: '#ffffff' }}>{selectedRel.fact_a?.context?.measurement_basis || 'ACTUAL'}</strong>
                  </div>
                </div>

                {/* Grounded Source Quote */}
                <div style={{ marginTop: '0.85rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.3rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Grounded Source (Page {selectedRel.fact_a?.evidence?.page_number ?? '?'})
                  </div>
                  <div style={{
                    fontSize: '0.82rem',
                    fontStyle: 'italic',
                    color: '#cbd5e1',
                    background: 'var(--bg-primary)',
                    padding: '0.65rem 0.85rem',
                    borderRadius: 'var(--radius-sm)',
                    borderLeft: '3px solid var(--accent-cyan)',
                    lineHeight: 1.5
                  }}>
                    "{selectedRel.fact_a?.evidence?.exact_text || 'No text evidence available'}"
                  </div>
                </div>
              </div>

              {/* Fact B */}
              <div className="glass-panel" style={{ padding: '1.25rem', borderTop: '3px solid #10b981' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Fact B Claim
                  </span>
                  {selectedRel.fact_b && (
                    <button
                      onClick={() => setInspectingFact(selectedRel.fact_b!)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        background: 'transparent',
                        border: 'none',
                        color: '#10b981',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        fontWeight: 600
                      }}
                    >
                      <Eye size={13} />
                      Inspect Provenance
                    </button>
                  )}
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#ffffff' }}>
                    {selectedRel.fact_b?.value_raw}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Normalized: <code style={{ color: '#10b981' }}>{selectedRel.fact_b?.value_normalized?.toLocaleString() ?? 'N/A'} {selectedRel.fact_b?.unit_canonical}</code>
                  </div>
                </div>

                {/* Dimensions list */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.8rem', background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Subject: </span>
                    <strong style={{ color: '#ffffff' }}>{selectedRel.fact_b?.subject_canonical}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Time Period: </span>
                    <strong style={{ color: '#ffffff' }}>{selectedRel.fact_b?.context?.time?.raw || 'Unspecified'}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Scope: </span>
                    <strong style={{ color: '#ffffff' }}>{selectedRel.fact_b?.context?.scope || 'CONSOLIDATED'}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Measurement Basis: </span>
                    <strong style={{ color: '#ffffff' }}>{selectedRel.fact_b?.context?.measurement_basis || 'ACTUAL'}</strong>
                  </div>
                </div>

                {/* Grounded Source Quote */}
                <div style={{ marginTop: '0.85rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.3rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Grounded Source (Page {selectedRel.fact_b?.evidence?.page_number ?? '?'})
                  </div>
                  <div style={{
                    fontSize: '0.82rem',
                    fontStyle: 'italic',
                    color: '#cbd5e1',
                    background: 'var(--bg-primary)',
                    padding: '0.65rem 0.85rem',
                    borderRadius: 'var(--radius-sm)',
                    borderLeft: '3px solid #10b981',
                    lineHeight: 1.5
                  }}>
                    "{selectedRel.fact_b?.evidence?.exact_text || 'No text evidence available'}"
                  </div>
                </div>
              </div>

            </div>

            {/* Multidimensional Comparison Matrix */}
            <div className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Scale size={18} color="var(--accent-primary)" />
                <h4 style={{ fontSize: '1rem', color: '#ffffff', margin: 0 }}>
                  Multidimensional Decision Matrix Evaluation
                </h4>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem', fontSize: '0.82rem' }}>
                <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase' }}>Value Delta</div>
                  <div style={{ fontWeight: 700, color: '#ffffff', marginTop: '0.2rem' }}>
                    {selectedRel.dimensions?.value_diff_percent !== undefined 
                      ? `${(selectedRel.dimensions.value_diff_percent * 100).toFixed(2)}%`
                      : '0.00%'
                    }
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    Tolerance: &plusmn;0.5%
                  </div>
                </div>

                <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase' }}>Unit Alignment</div>
                  <div style={{ fontWeight: 700, color: selectedRel.dimensions?.same_canonical_unit ? '#10b981' : '#f59e0b', marginTop: '0.2rem' }}>
                    {selectedRel.dimensions?.same_canonical_unit ? 'Canonical Match' : 'Unit Converted'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    Base: {selectedRel.fact_a?.unit_canonical || 'N/A'}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase' }}>Temporal Alignment</div>
                  <div style={{ fontWeight: 700, color: '#ffffff', marginTop: '0.2rem' }}>
                    {selectedRel.dimensions?.temporal_relation || 'SAME_PERIOD'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    Time Dimension
                  </div>
                </div>

                <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase' }}>Scope Alignment</div>
                  <div style={{ fontWeight: 700, color: '#ffffff', marginTop: '0.2rem' }}>
                    {selectedRel.dimensions?.scope_relation || 'SAME_SCOPE'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    Entity Boundary
                  </div>
                </div>

                <div style={{ background: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase' }}>Measurement Basis</div>
                  <div style={{ fontWeight: 700, color: '#ffffff', marginTop: '0.2rem' }}>
                    {selectedRel.dimensions?.basis_relation || 'SAME_BASIS'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    Accounting / Estimate
                  </div>
                </div>
              </div>
            </div>

            {/* Grounded Natural Language Explanation */}
            <div className="glass-panel" style={{ padding: '1.25rem 1.5rem', background: 'var(--bg-tertiary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.6rem' }}>
                <FileText size={17} color="var(--accent-cyan)" />
                <h4 style={{ fontSize: '0.92rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--accent-cyan)', margin: 0 }}>
                  Grounded Resolution Narrative & Provenance Audit
                </h4>
              </div>
              <p style={{ fontSize: '0.92rem', lineHeight: 1.6, color: '#f8fafc', margin: 0 }}>
                {selectedRel.explanation}
              </p>
            </div>

          </div>
        ) : (
          <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Select a candidate pair on the left to audit cross-document reconciliation.
          </div>
        )}

      </div>
    </div>
  );
};
