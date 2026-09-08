import {
  HealthData,
  DocumentItem,
  FactItem,
  RelationshipItem,
  ExtractionIssueItem,
  AnalyticsOverview
} from '../types';

export const API_BASE = '/api/v1';

export const api = {
  // Health
  async getHealth(): Promise<HealthData> {
    const res = await fetch('/health');
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  // Documents
  async getDocuments(limit: number = 50, offset: number = 0): Promise<DocumentItem[]> {
    const res = await fetch(`${API_BASE}/documents?limit=${limit}&offset=${offset}`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async getDocument(id: string): Promise<DocumentItem> {
    const res = await fetch(`${API_BASE}/documents/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch document ${id}`);
    return res.json();
  },

  async uploadDocument(file: File): Promise<{ document_id: string; filename: string; status: string; message: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async reprocessDocument(id: string): Promise<{ document_id: string; facts_extracted: number }> {
    const res = await fetch(`${API_BASE}/documents/${id}/reprocess`, { method: 'POST' });
    if (!res.ok) throw new Error('Reprocess failed');
    return res.json();
  },

  // Facts
  async getFacts(params?: {
    document_id?: string;
    subject?: string;
    predicate?: string;
    predicate_type?: string;
    confidence_level?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<FactItem[]> {
    const sp = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          sp.append(k, String(v));
        }
      });
    }
    const res = await fetch(`${API_BASE}/facts?${sp.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch facts');
    return res.json();
  },

  async getFact(id: string): Promise<FactItem> {
    const res = await fetch(`${API_BASE}/facts/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch fact ${id}`);
    return res.json();
  },

  async getSubjects(): Promise<string[]> {
    const res = await fetch(`${API_BASE}/facts/subjects/all`);
    if (!res.ok) return [];
    return res.json();
  },

  async getPredicates(): Promise<string[]> {
    const res = await fetch(`${API_BASE}/facts/predicates/all`);
    if (!res.ok) return [];
    return res.json();
  },

  // Relationships
  async getRelationships(params?: {
    relationship_type?: string;
    subject?: string;
    document_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<RelationshipItem[]> {
    const sp = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          sp.append(k, String(v));
        }
      });
    }
    const res = await fetch(`${API_BASE}/relationships?${sp.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch relationships');
    return res.json();
  },

  async getRelationship(id: string): Promise<RelationshipItem> {
    const res = await fetch(`${API_BASE}/relationships/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch relationship ${id}`);
    return res.json();
  },

  async resolveRelationships(documentIds?: string[]): Promise<{ status: string; relationships_resolved: number; summary: any }> {
    const res = await fetch(`${API_BASE}/relationships/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(documentIds || null)
    });
    if (!res.ok) throw new Error('Relationship resolution failed');
    return res.json();
  },

  // Extraction Issues
  async getIssues(params?: {
    document_id?: string;
    issue_type?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<ExtractionIssueItem[]> {
    const sp = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          sp.append(k, String(v));
        }
      });
    }
    const res = await fetch(`${API_BASE}/issues?${sp.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch issues');
    return res.json();
  },

  async resolveIssue(id: string, note?: string): Promise<ExtractionIssueItem> {
    const url = `${API_BASE}/issues/${id}/resolve${note ? `?resolution_note=${encodeURIComponent(note)}` : ''}`;
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to resolve issue');
    return res.json();
  },

  // Analytics Overview
  async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    const res = await fetch(`${API_BASE}/analytics/overview`);
    if (!res.ok) throw new Error('Failed to fetch analytics overview');
    return res.json();
  }
};
