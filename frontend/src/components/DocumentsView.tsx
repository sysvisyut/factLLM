import React, { useState } from 'react';
import { Upload, FileText, RefreshCw, CheckCircle2, AlertCircle, HardDrive, Layers } from 'lucide-react';
import { DocumentItem } from '../types';
import { api } from '../services/api';

interface DocumentsViewProps {
  documents: DocumentItem[];
  loading: boolean;
  onRefresh: () => void;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({
  documents,
  loading,
  onRefresh
}) => {
  const [uploading, setUploading] = useState<boolean>(false);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadMessage(null);

    try {
      const uploadRes = await api.uploadDocument(file);
      setUploadMessage({
        type: 'success',
        text: `Uploaded "${file.name}" (${(file.size / 1024 / 1024).toFixed(2)} MB). Processing pages...`
      });
      // Trigger processing
      await api.reprocessDocument(uploadRes.document_id);
      setUploadMessage({
        type: 'success',
        text: `Successfully ingested and parsed "${file.name}" into Evidence Atoms!`
      });
      onRefresh();
    } catch (err: any) {
      console.error("Upload error:", err);
      setUploadMessage({
        type: 'error',
        text: err.response?.data?.detail || err.message || 'Failed to upload document.'
      });
    } finally {
      setUploading(false);
    }
  };

  const handleReprocess = async (docId: string, filename: string) => {
    setProcessingId(docId);
    try {
      await api.reprocessDocument(docId);
      setUploadMessage({
        type: 'success',
        text: `Reprocessed "${filename}" successfully!`
      });
      onRefresh();
    } catch (err: any) {
      setUploadMessage({
        type: 'error',
        text: `Failed to reprocess ${filename}: ${err.message}`
      });
    } finally {
      setProcessingId(null);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', color: '#ffffff', margin: 0 }}>
            Document Ingestion & Parsing Engine
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.3rem' }}>
            Upload arbitrary PDFs. The ingestion pipeline extracts page text, bounding boxes, tables, and fragments into immutable Evidence Atoms.
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
          Refresh List
        </button>
      </div>

      {/* Upload Dropzone */}
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', border: '2px dashed var(--border-color-hover)' }}>
        <input
          type="file"
          id="pdf-upload"
          accept=".pdf"
          style={{ display: 'none' }}
          onChange={handleFileUpload}
          disabled={uploading}
        />
        <label
          htmlFor="pdf-upload"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            cursor: uploading ? 'not-allowed' : 'pointer'
          }}
        >
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'rgba(99, 102, 241, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '1rem'
          }}>
            <Upload size={28} color="var(--accent-primary)" />
          </div>
          <h3 style={{ fontSize: '1.15rem', color: '#ffffff', marginBottom: '0.3rem' }}>
            {uploading ? 'Processing and extracting Evidence Atoms...' : 'Upload an Arbitrary PDF Document'}
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: '500px' }}>
            Drag and drop or browse files. Generates verifiable evidence atoms with coordinates, paragraph boundaries, and source hashes.
          </p>
          <div style={{
            marginTop: '1.25rem',
            padding: '0.5rem 1.25rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--accent-primary)',
            color: '#ffffff',
            fontWeight: 600,
            fontSize: '0.85rem'
          }}>
            {uploading ? 'Parsing...' : 'Select PDF File'}
          </div>
        </label>

        {uploadMessage && (
          <div style={{
            marginTop: '1.25rem',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
            background: uploadMessage.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${uploadMessage.type === 'success' ? '#10b981' : '#ef4444'}`,
            color: uploadMessage.type === 'success' ? '#10b981' : '#ef4444',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85rem'
          }}>
            {uploadMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{uploadMessage.text}</span>
          </div>
        )}
      </div>

      {/* Ingested Documents List */}
      <div className="glass-panel" style={{ padding: '1.5rem', overflow: 'hidden' }}>
        <h3 style={{ fontSize: '1.15rem', color: '#ffffff', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <HardDrive size={18} color="var(--accent-cyan)" /> Ingested PDF Repositories ({documents.length})
        </h3>

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading ingested documents...
          </div>
        ) : documents.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No documents ingested yet. Upload a PDF above to begin.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Document Name</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Pages</th>
                  <th style={{ padding: '0.75rem 1rem' }}>File Size</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Content Hash</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Ingested Date</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map(doc => (
                  <tr key={doc.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', transition: 'background 0.15s' }}>
                    <td style={{ padding: '1rem', fontWeight: 600, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <FileText size={17} color="var(--accent-cyan)" />
                      <span>{doc.filename}</span>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
                      <span style={{
                        padding: '0.2rem 0.6rem',
                        borderRadius: 'var(--radius-full)',
                        background: 'rgba(99, 102, 241, 0.12)',
                        color: 'var(--accent-primary)',
                        fontSize: '0.78rem',
                        fontWeight: 600
                      }}>
                        {doc.page_count} Pages
                      </span>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
                      {formatBytes(doc.file_size_bytes)}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <code style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {doc.content_hash.slice(0, 16)}...
                      </code>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                      {new Date(doc.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <button
                        onClick={() => handleReprocess(doc.id, doc.filename)}
                        disabled={processingId === doc.id}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          padding: '0.35rem 0.75rem',
                          borderRadius: 'var(--radius-sm)',
                          background: 'transparent',
                          border: '1px solid var(--border-color)',
                          color: 'var(--text-secondary)',
                          fontSize: '0.78rem',
                          cursor: 'pointer'
                        }}
                      >
                        <RefreshCw size={13} className={processingId === doc.id ? 'spin' : ''} />
                        {processingId === doc.id ? 'Processing...' : 'Reprocess'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Two-Layer Extraction Info Banner */}
      <div style={{
        background: 'rgba(6, 182, 212, 0.06)',
        border: '1px solid rgba(6, 182, 212, 0.2)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem 1.5rem',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem'
      }}>
        <Layers size={28} color="var(--accent-cyan)" />
        <div>
          <h4 style={{ color: '#ffffff', fontSize: '0.95rem', margin: 0 }}>
            Architecture Principle: Immutable Evidence Atoms Grounding
          </h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', margin: '0.25rem 0 0 0', lineHeight: 1.5 }}>
            Every raw PDF page is decomposed into immutable <code>EvidenceAtom</code> records capturing exact text, 
            character indices, table cells, and spatial bounding boxes. Facts are only created if they hold a cryptographic 
            foreign-key link back to an Evidence Atom, guaranteeing zero hallucinated claims.
          </p>
        </div>
      </div>
    </div>
  );
};
