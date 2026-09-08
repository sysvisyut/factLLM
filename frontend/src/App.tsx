import { useState, useEffect, useCallback } from 'react';
import { api } from './services/api';
import { 
  HealthData, 
  AnalyticsOverview, 
  DocumentItem, 
  FactItem, 
  RelationshipItem, 
  ExtractionIssueItem 
} from './types';
import { Navbar } from './components/Navbar';
import { DashboardView } from './components/DashboardView';
import { DocumentsView } from './components/DocumentsView';
import { FactExplorerView } from './components/FactExplorerView';
import { ConflictAuditView } from './components/ConflictAuditView';
import { IssuesView } from './components/IssuesView';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'documents' | 'facts' | 'conflicts' | 'issues'>('dashboard');
  const [conflictFilter, setConflictFilter] = useState<string>('ALL');

  // Shared Data States
  const [health, setHealth] = useState<HealthData | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [facts, setFacts] = useState<FactItem[]>([]);
  const [relationships, setRelationships] = useState<RelationshipItem[]>([]);
  const [issues, setIssues] = useState<ExtractionIssueItem[]>([]);

  // Loading States
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [loadingAnalytics, setLoadingAnalytics] = useState<boolean>(false);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(false);
  const [loadingFacts, setLoadingFacts] = useState<boolean>(false);
  const [loadingRels, setLoadingRels] = useState<boolean>(false);
  const [loadingIssues, setLoadingIssues] = useState<boolean>(false);

  // Fetch Health
  const loadHealth = useCallback(async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (err) {
      console.error("Health check error:", err);
    } finally {
      setLoadingHealth(false);
    }
  }, []);

  // Fetch Analytics
  const loadAnalytics = useCallback(async () => {
    setLoadingAnalytics(true);
    try {
      const data = await api.getAnalyticsOverview();
      setAnalytics(data);
    } catch (err) {
      console.error("Analytics fetch error:", err);
    } finally {
      setLoadingAnalytics(false);
    }
  }, []);

  // Fetch Documents
  const loadDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const data = await api.getDocuments();
      setDocuments(data);
    } catch (err) {
      console.error("Documents fetch error:", err);
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  // Fetch Facts
  const loadFacts = useCallback(async () => {
    setLoadingFacts(true);
    try {
      const data = await api.getFacts({ limit: 200 });
      setFacts(data);
    } catch (err) {
      console.error("Facts fetch error:", err);
    } finally {
      setLoadingFacts(false);
    }
  }, []);

  // Fetch Relationships
  const loadRelationships = useCallback(async () => {
    setLoadingRels(true);
    try {
      const data = await api.getRelationships({ limit: 200 });
      setRelationships(data);
    } catch (err) {
      console.error("Relationships fetch error:", err);
    } finally {
      setLoadingRels(false);
    }
  }, []);

  // Fetch Issues
  const loadIssues = useCallback(async () => {
    setLoadingIssues(true);
    try {
      const data = await api.getIssues();
      setIssues(data);
    } catch (err) {
      console.error("Issues fetch error:", err);
    } finally {
      setLoadingIssues(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadHealth();
    loadAnalytics();
    loadDocuments();
    loadFacts();
    loadRelationships();
    loadIssues();
  }, [loadHealth, loadAnalytics, loadDocuments, loadFacts, loadRelationships, loadIssues]);

  const handleNavigate = (tab: 'dashboard' | 'documents' | 'facts' | 'conflicts' | 'issues', filter?: string) => {
    if (filter && tab === 'conflicts') {
      setConflictFilter(filter);
    }
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        loadingHealth={loadingHealth}
      />

      {/* Main View Area */}
      <main style={{ flex: 1, padding: '2rem', maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
        {activeTab === 'dashboard' && (
          <DashboardView
            analytics={analytics}
            health={health}
            loading={loadingAnalytics}
            onNavigate={handleNavigate}
          />
        )}

        {activeTab === 'documents' && (
          <DocumentsView
            documents={documents}
            loading={loadingDocs}
            onRefresh={() => {
              loadDocuments();
              loadAnalytics();
            }}
          />
        )}

        {activeTab === 'facts' && (
          <FactExplorerView
            facts={facts}
            loading={loadingFacts}
            onRefresh={() => {
              loadFacts();
              loadAnalytics();
            }}
          />
        )}

        {activeTab === 'conflicts' && (
          <ConflictAuditView
            relationships={relationships}
            loading={loadingRels}
            onRefresh={() => {
              loadRelationships();
              loadAnalytics();
            }}
            initialFilter={conflictFilter}
          />
        )}

        {activeTab === 'issues' && (
          <IssuesView
            issues={issues}
            loading={loadingIssues}
            onRefresh={() => {
              loadIssues();
              loadAnalytics();
            }}
          />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-color)',
        padding: '1.25rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '0.78rem',
        color: 'var(--text-muted)',
        background: 'var(--bg-primary)',
        marginTop: 'auto'
      }}>
        <div>
          FACTMESH Knowledge Layer &copy; 2026 — Context-Aware Cross-Document Disambiguation & Provenance Grounding
        </div>
        <div style={{ display: 'flex', gap: '1.25rem' }}>
          <span>97.4% Search Pruning</span>
          <span>•</span>
          <span>Zero Silent Hallucination</span>
          <span>•</span>
          <span>Multi-Tier Deterministic Matrix</span>
        </div>
      </footer>
    </div>
  );
}
export default App;
