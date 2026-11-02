/** Shapes returned by the FastAPI backend. Keep in sync with app/api and app/services. */

export type Plan = "free" | "premium";

export interface User {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  plan: Plan;
  is_admin: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

export interface UsageFeature {
  used: number;
  limit: number;
  remaining: number;
}

export interface UsageSummary {
  date: string;
  plan: Plan;
  features: { generate: UsageFeature; enhance: UsageFeature };
}

export interface QualityScore {
  label: string;
  relevance: number;
  readability: number;
  hook_strength: number;
  structure: number;
  keyword_alignment: number;
  tone_alignment: number;
  cta_quality: number;
  originality_signals: number;
  overall: number;
}

export interface Suggestion {
  code: string;
  message: string;
}

export interface Analysis {
  post_type?: string;
  topic?: string;
  category?: string | null;
  tone?: string;
  emotion?: string;
  keywords?: string[];
  hook_type?: string;
  hook_strength?: number;
  structure?: string[];
  readability?: number;
  cta?: string;
  hashtags?: string[];
  length_words?: number;
}

export interface Blueprint {
  structure: string[];
  hook_suggestions: string[];
  cta: string;
  keywords: string[];
  hashtags: string[];
}

export interface GenerateResponse {
  post_id: string;
  post: string | null;
  variations: string[];
  keywords_used: string[];
  hashtags: string[];
  score: QualityScore | null;
  analysis: Analysis;
  suggestions: Suggestion[];
  blueprint: Blueprint;
  locked: boolean;
  plan: Plan;
  upgrade_hint: string | null;
  usage: UsageSummary;
}

export interface EnhanceResponse {
  post_id: string;
  analysis: Analysis;
  suggestions: Suggestion[];
  missing_keywords: string[];
  recommended_structure: string[];
  hook_suggestions: string[];
  score_before: QualityScore;
  enhanced_post: string | null;
  score_after: QualityScore | null;
  locked: boolean;
  plan: Plan;
  upgrade_hint: string | null;
  validation_issues?: string[];
  usage: UsageSummary;
}

export interface AnalyzeResponse {
  analysis: Analysis;
  suggestions: Suggestion[];
  score: QualityScore;
  advanced: Record<string, unknown> | null;
  plan: Plan;
}

export interface PostItem {
  id: string;
  type: "generate" | "enhance";
  input_text: string;
  output_text: string | null;
  category: string | null;
  topic: string | null;
  tone: string | null;
  keywords_used: string[];
  hashtags: string[];
  score: QualityScore | null;
  suggestions: Suggestion[];
  analysis: {
    emotion: string | null;
    hook_type: string | null;
    structure: string[];
    readability_score: number;
    hook_score: number;
    keyword_score: number;
    overall_score: number;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface PostList {
  items: PostItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface Taxonomy {
  knowledge_categories: string[];
  post_types: string[];
  tones: string[];
  emotions: string[];
  audiences: string[];
  lengths: string[];
  cta_types: string[];
}

export interface PlansInfo {
  free: {
    generations_per_day: number;
    enhancements_per_day: number;
    full_post_generation: boolean;
    enhanced_post: boolean;
    variations: number;
    advanced_analysis: boolean;
  };
  premium: {
    daily_cap: number;
    full_post_generation: boolean;
    enhanced_post: boolean;
    variations: number;
    advanced_analysis: boolean;
  };
}

export interface SubscriptionInfo {
  plan: Plan;
  status: string;
  provider: string;
  external_subscription_id: string | null;
  started_at: string | null;
  expires_at: string | null;
}

export interface IngestionReport {
  job_id: string;
  filename: string;
  status: string;
  records_uploaded: number;
  records_processed: number;
  records_rejected: number;
  duplicates: number;
  embeddings_generated: number;
  pii_redacted: number;
  errors: { row: number; reason: string }[];
  error_message: string | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface KnowledgeItem {
  id: string;
  category: string;
  topic: string;
  keywords: string[];
  hook_type: string;
  tone: string;
  structure: string[];
  cta_type: string;
  audience: string;
  source_type: string;
  is_active: boolean;
}
