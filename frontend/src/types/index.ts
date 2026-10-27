export type ThemeMode = 'light' | 'dark';

export interface HealthStatus {
  status: string;
  llm_key_set: boolean;
  model: string;
}

export interface PatientContext {
  age?: number | null;
  reason?: string | null;
  allergies?: string | null;
  pregnancy?: 'yes' | 'no' | 'not_applicable' | null;
  kidney_liver?: string | null;
}

export interface Medicine {
  id: string;
  name_text: string;
  strength?: string | null;
  dose?: string | null;
  frequency?: string | null;
  duration?: string | null;
  page?: number | null;
  read_quality: 'clear' | 'unclear';
  match_status: 'matched' | 'several_possible' | 'not_found';
  matched_id?: string | null;
  candidates?: string[];
  ingredients?: string[];
  confirmed: boolean;
}

export interface AnalysisSummary {
  id: string;
  created_at: string;
  original_name: string;
  status: 'uploaded' | 'confirmed' | 'running' | 'done' | 'failed';
  file_kind?: string;
  text_source?: string;
  page_count?: number;
}

export interface InteractionRuleResult {
  rule_id: string;
  medicines: string[];
  medicine_names?: string[];
  ingredients?: string[];
  severity: 'high' | 'moderate' | 'low';
  note: string;
  source_label: string;
}

export interface DuplicateIngredientResult {
  ingredient: string;
  medicines: string[];
  medicine_names?: string[];
  note?: string;
}

export interface NotCheckedMedicine {
  id: string;
  name_text: string;
  status: string;
  reason?: string;
}

export interface CoverageResult {
  total: number;
  found_in_list: number;
  not_found: string[];
  not_checked?: NotCheckedMedicine[];
}

export interface GraphNodeData {
  id: string;
  label: string;
  type: 'medicine' | 'ingredient';
  is_known?: boolean;
  strength?: string | null;
  dose?: string | null;
  match_status?: string;
  position?: { x: number; y: number };
}

export interface GraphEdgeData {
  id?: string;
  from: string;
  to: string;
  source?: string;
  target?: string;
  type: 'contains' | 'interacts';
  severity?: 'high' | 'moderate' | 'low';
  rule_id?: string;
  note?: string;
  source_label?: string;
}

export interface KnowledgeGraphData {
  nodes: GraphNodeData[];
  edges: GraphEdgeData[];
}

export interface SafetyCheckResults {
  interactions: InteractionRuleResult[];
  duplicates: DuplicateIngredientResult[];
  coverage: CoverageResult;
  graph: KnowledgeGraphData;
  notice: string;
}

export interface AnalysisEvent {
  id: number;
  analysis_id: string;
  run_id: string;
  time: string;
  component: string;
  status: 'waiting' | 'running' | 'done' | 'failed' | 'skipped';
  task: string;
  detail: string;
}

export interface WebSource {
  title: string;
  url: string;
  publication_date?: string | null;
  source_type?: string;
  evidence_excerpt?: string;
}

export interface EvidenceItem {
  medicine_id: string;
  medicine_name?: string;
  findings: string[];
  sources: WebSource[];
  status: 'ok' | 'no_source' | 'no_results' | 'unavailable';
  evidence_tier?: 'local_catalog' | 'live_evidence' | 'cached_evidence' | 'ai_generated' | 'research_unavailable' | 'not_confidently_identified';
}

export interface AlternativeItem {
  for_medicine_id: string;
  medicine_name?: string;
  options: string[];
  sources: WebSource[];
  status?: string;
}

export interface AlternativesResult {
  status: 'ok' | 'needs_more_info' | 'unavailable';
  missing: string[];
  items: AlternativeItem[];
}

export interface ReviewIssue {
  where: string;
  issue: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AnalysisResponse {
  id: string;
  created_at: string;
  original_name: string;
  stored_name: string;
  file_kind: 'image' | 'pdf';
  text_source: 'pdf_text' | 'ocr';
  page_count: number;
  medicines: Medicine[];
  context?: PatientContext | null;
  results?: SafetyCheckResults | Record<string, any> | null;
  status: 'uploaded' | 'confirmed' | 'running' | 'done' | 'failed';
}

export interface ChatResponse {
  reply: string;
  flags: string[];
  language?: string;
}

export interface PharmacyListing {
  pharmacy_id: string;
  pharmacy_name: string;
  matching_medicine_name: string;
  brand?: string;
  active_ingredient?: string;
  strength?: string;
  dosage_form?: string;
  pack_size?: string;
  is_rx_required?: boolean;
  price_status: 'unverified_link_only' | 'verified_live' | 'cached';
  verified_price?: number | null;
  discounted_price?: number | null;
  price_display: string;
  availability: string;
  delivery_note?: string;
  direct_url: string;
  action_label: string;
}

export interface CategoryBBrand {
  category: 'B';
  category_label: string;
  brand_name: string;
  manufacturer: string;
  active_ingredients: string;
  strength: string;
  dosage_form: string;
  pack_size: string;
  verified_mrp_inr: number;
  savings_percentage?: number;
  equivalence_rationale: string;
  safety_note: string;
}

export interface CategoryCGeneric {
  category: 'C';
  category_label: string;
  product_name: string;
  manufacturer: string;
  active_ingredients: string;
  strength: string;
  dosage_form: string;
  pack_size: string;
  verified_mrp_inr: number;
  savings_percentage?: number;
  equivalence_rationale: string;
  safety_note: string;
}

export interface CategoryDNonInterchangeable {
  category: 'D';
  category_label: string;
  drug_name: string;
  warning: string;
  safety_rule: string;
}

export interface AlternativesData {
  status: string;
  original_medicine?: {
    id: string;
    brand_name: string;
    active_ingredients: string;
    strength: string;
    dosage_form: string;
    release_type?: string;
    pack_size: string;
    reference_mrp_inr: number;
    is_rx_required: boolean;
  };
  category_b_brands: CategoryBBrand[];
  category_c_generics: CategoryCGeneric[];
  category_d_non_interchangeable: CategoryDNonInterchangeable[];
  substitution_notice: string;
}

export interface PriceComparisonData {
  medicine_name: string;
  active_ingredient?: string;
  strength?: string;
  dosage_form?: string;
  pack_size?: string;
  is_rx_required?: boolean;
  reference_benchmark_mrp?: number | null;
  benchmark_note?: string | null;
  retrieval_timestamp: string;
  providers_compared: PharmacyListing[];
  alternatives?: AlternativesData | null;
  price_honesty_note: string;
  safety_disclaimer: string;
}

export interface AssistantChatResponse {
  reply: string;
  language: 'en' | 'hi_devanagari' | 'hinglish';
  medicine_detected?: string | null;
  price_comparison?: PriceComparisonData | null;
  alternatives?: AlternativesData | null;
  sources: WebSource[];
  flags: string[];
}

export interface AssistantMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  language?: string;
  price_comparison?: PriceComparisonData | null;
  alternatives?: AlternativesData | null;
  sources?: WebSource[];
  flags?: string[];
}



