export interface Project {
  id: string;
  name: string;
  description?: string;
  conversation_count?: number;
  document_count?: number;
  website_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  source_index: number;
  source_id: string;
  source_type: 'document' | 'website';
  filename?: string;
  url?: string;
  page?: number | string;
  title?: string;
  snippet: string;
  score: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: Citation[];
  model?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentItem {
  id: string;
  project_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  file_path: string;
  chunk_count: number;
  status: 'uploaded' | 'indexing' | 'indexed' | 'error';
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface WebsiteItem {
  id: string;
  project_id: string;
  url: string;
  title?: string;
  page_count: number;
  chunk_count: number;
  status: 'pending' | 'crawling' | 'indexed' | 'error';
  error_message?: string;
  last_crawled?: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeSource {
  id: string;
  type: 'document' | 'website';
  title: string;
  meta: string;
  chunk_count: number;
  status: string;
  error_message?: string;
  created_at: string;
}

export interface KnowledgeSummary {
  project_id: string;
  total_sources: number;
  total_documents: number;
  total_websites: number;
  total_chunks: number;
  sources: KnowledgeSource[];
}

export interface SystemHealth {
  status: string;
  system: {
    cpu_percent: number;
    memory_total_mb: number;
    memory_used_mb: number;
    memory_available_mb: number;
    memory_percent: number;
  };
  ai: {
    connected: boolean;
    models: string[];
    default_model: string;
    has_default_model: boolean;
    error?: string;
  };
  storage: {
    chroma_exists: boolean;
    uploads_exists: boolean;
    db_exists: boolean;
  };
}

export interface AppSettingsConfig {
  default_model: string;
  temperature: number;
  top_p: number;
  max_tokens: number;
  system_prompt: string;
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  hybrid_alpha: number;
  local_only: boolean;
  embedding_model: string;
  has_openai_key: boolean;
  has_gemini_key: boolean;
  has_anthropic_key: boolean;
}
