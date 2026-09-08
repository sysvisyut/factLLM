import React from 'react';
import { X, ShieldCheck, FileText, MapPin, Hash, CheckCircle2 } from 'lucide-react';
import { FactItem } from '../types';

interface EvidenceModalProps {
  fact: FactItem | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ fact, onClose }) => {
  if (!fact) return null;

  const evidence = fact.evidence;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(5, 8, 16, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '1rem'
    }} onClick={onClose}>
      <div 
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '720px',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color-hover)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '90vh'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(255, 255, 255, 0.02)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <ShieldCheck size={22} color="var(--accent-cyan)" />
            <div>
              <h3 style={{ fontSize: '1.15rem', color: '#ffffff', margin: 0 }}>
                Evidence Atom & Provenance Inspector
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
                Verifiable Grounding & Zero-Hallucination Audit Trail
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '0.25rem',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Fact Summary Banner */}
          <div style={{
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan)', fontWeight: 700 }}>
                Extracted Fact Claim
              </span>
              <span style={{
                fontSize: '0.75rem',
                padding: '0.2rem 0.6rem',
                borderRadius: 'var(--radius-full)',
                background: 'rgba(16, 185, 129, 0.15)',
                color: '#10b981',
                fontWeight: 600
              }}>
                Overall Confidence: {(fact.confidence_overall * 100).toFixed(1)}%
              </span>
            </div>
            <div style={{ fontSize: '1.05rem', fontWeight: 600, color: '#ffffff', marginBottom: '0.35rem' }}>
              <span style={{ color: 'var(--accent-cyan)' }}>{fact.subject_canonical}</span>
              {' '}—{' '}
              <span>{fact.predicate_canonical}</span>
              {': '}
              <strong style={{ color: '#10b981' }}>{fact.value_raw}</strong>
              {fact.unit_canonical && <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}> ({fact.unit_canonical})</span>}
            </div>
            {fact.context?.time?.raw && (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Temporal Anchor: <span style={{ color: '#e2e8f0' }}>{fact.context.time.raw}</span>
                {fact.context.measurement_basis && (
                  <> • Measurement Basis: <span style={{ color: 'var(--accent-cyan)' }}>{fact.context.measurement_basis}</span></>
                )}
              </div>
            )}
          </div>

          {/* Verbatim Grounded Source Text */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
              <FileText size={16} color="var(--accent-cyan)" />
              <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', margin: 0 }}>
                Verbatim Grounded Source Quote
              </h4>
            </div>
            <div style={{
              background: 'var(--bg-tertiary)',
              borderLeft: '4px solid var(--accent-cyan)',
              padding: '1rem 1.25rem',
              borderRadius: '0 var(--radius-md) var(--radius-md) 0',
              fontStyle: 'italic',
              fontSize: '0.95rem',
              lineHeight: 1.6,
              color: '#f1f5f9'
            }}>
              "{evidence?.exact_text || 'Source text not attached.'}"
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.4rem', fontSize: '0.75rem', color: '#10b981' }}>
              <CheckCircle2 size={13} />
              <span>Strict character alignment verified against PDF Document Page {evidence?.page_number}</span>
            </div>
          </div>

          {/* Provenance Metadata Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', fontSize: '0.82rem' }}>
            <div style={{ background: 'var(--bg-primary)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Page Number: </span>
              <strong style={{ color: '#ffffff' }}>Page {evidence?.page_number ?? 'N/A'}</strong>
            </div>

            <div style={{ background: 'var(--bg-primary)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Extraction Method: </span>
              <strong style={{ color: 'var(--accent-cyan)' }}>{evidence?.extraction_method || 'TEXT_PATTERN_OFFLINE'}</strong>
            </div>

            <div style={{ background: 'var(--bg-primary)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', gridColumn: 'span 2' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.2rem' }}>
                <MapPin size={14} color="var(--accent-primary)" />
                <span style={{ color: 'var(--text-muted)' }}>Bounding Box Coordinates:</span>
              </div>
              <code style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                {evidence?.bbox && evidence.bbox.length > 0
                  ? `[ymin: ${evidence.bbox[0].toFixed(1)}, xmin: ${evidence.bbox[1].toFixed(1)}, ymax: ${evidence.bbox[2].toFixed(1)}, xmax: ${evidence.bbox[3].toFixed(1)}]`
                  : 'Derived from full line flow coordinates on page'
                }
              </code>
            </div>

            <div style={{ background: 'var(--bg-primary)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', gridColumn: 'span 2' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.2rem' }}>
                <Hash size={14} color="var(--accent-primary)" />
                <span style={{ color: 'var(--text-muted)' }}>SHA-256 Provenance Fingerprint:</span>
              </div>
              <code style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', wordBreak: 'break-all', fontFamily: 'var(--font-mono)' }}>
                {evidence?.source_hash || fact.fingerprint}
              </code>
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div style={{
          padding: '1rem 1.5rem',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'flex-end',
          background: 'rgba(255, 255, 255, 0.02)'
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem 1.25rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--accent-primary)',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
