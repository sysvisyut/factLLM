export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNCERTAIN';

export type RelationshipType = 
  | 'CORROBORATES'
  | 'CONTRADICTS'
  | 'RECONCILES'
  | 'TEMPORALLY_EVOLVES'
  | 'SCOPE_DIFFERENCE'
  | 'UNIT_EQUIVALENT'
  | 'POSSIBLE_DUPLICATE'
  | 'UNCERTAIN';

export interface HealthData {
  status: string;
  version: string;
  timestamp: string;
  database: {
    status: string;
    dialect: string;
  };
  llm_provider: string;
  storage: {
    path: string;
    available: boolean;
  };
}

export interface DocumentItem {
  id: string;
  filename: string;
  content_hash: string;
  file_size_bytes: number;
  page_count: number;
  created_at: string;
  fact_count?: number;
  issue_count?: number;
}

export interface EvidenceAtom {
  id: string;
  document_id: string;
  page_number: number;
  section_heading?: string;
  exact_text: string;
  char_start?: number;
  char_end?: number;
  bbox?: number[];
  table_cell_info?: Record<string, any>;
  extraction_method: string;
  source_hash: string;
  created_at: string;
}

export interface FactItem {
  id: string;
  document_id: string;
  evidence_id: string;
  subject_raw: string;
  subject_canonical: string;
  predicate_raw: string;
  predicate_canonical: string;
  predicate_type: string;
  value_raw: string;
  value_normalized?: number;
  value_type: string;
  unit_raw?: string;
  unit_canonical?: string;
  polarity: string;
  fingerprint: string;
  confidence_extraction: number;
  confidence_normalization: number;
  confidence_overall: number;
  confidence_level: ConfidenceLevel;
  created_at: string;
  context?: {
    time?: {
      type?: string;
      start?: string;
      end?: string;
      raw?: string;
    };
    geography?: string;
    scope?: string;
    population?: string;
    measurement_basis?: string;
    qualifiers?: string[];
  };
  evidence?: EvidenceAtom;
}

export interface RelationshipItem {
  id: string;
  fact_a_id: string;
  fact_b_id: string;
  relationship_type: RelationshipType;
  confidence: number;
  explanation: string;
  dimensions: Record<string, any>;
  important_differences: string[];
  reasoning_basis: string;
  created_at: string;
  fact_a?: FactItem;
  fact_b?: FactItem;
}

export interface ExtractionIssueItem {
  id: string;
  document_id?: string;
  page_number?: number;
  issue_type: string;
  description: string;
  affected_text?: string;
  attempted_resolution?: string;
  confidence?: number;
  status: string;
  created_at: string;
}

export interface AnalyticsOverview {
  documents: {
    total_documents: number;
    total_pages: number;
    total_evidence_atoms: number;
  };
  facts: {
    total_facts: number;
    confidence_breakdown: Record<string, number>;
  };
  relationships: {
    total_relationships: number;
    breakdown: Record<string, number>;
  };
  retrieval_efficiency: {
    total_facts: number;
    naive_comparisons: number;
    cross_document_pairs: number;
    candidate_pairs_count: number;
    reduction_percent: number;
    efficiency_multiplier: number;
  };
  issues: {
    total_issues: number;
    breakdown: Record<string, number>;
  };
}
