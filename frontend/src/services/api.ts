import { Project, Conversation, Message, DocumentItem, WebsiteItem, KnowledgeSummary, SystemHealth, AppSettingsConfig } from '../types';

const API_BASE = 'http://127.0.0.1:5000/api';

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {})
    },
    ...options
  });
  if (!res.ok) {
    let errMessage = `HTTP ${res.status}`;
    try {
      const errData = await res.json();
      if (errData && errData.error) errMessage = errData.error;
    } catch {
      // ignore
    }
    throw new Error(errMessage);
  }
  return res.json();
}

export const api = {
  // System Health
  getHealth: () => fetchJson<SystemHealth>('/health'),

  // Projects
  listProjects: () => fetchJson<{ projects: Project[] }>('/projects'),
  createProject: (name: string, description?: string) =>
    fetchJson<{ project: Project }>('/projects', {
      method: 'POST',
      body: JSON.stringify({ name, description })
    }),
  updateProject: (id: string, name: string, description?: string) =>
    fetchJson<{ message: string }>(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ name, description })
    }),
  deleteProject: (id: string) =>
    fetchJson<{ message: string }>(`/projects/${id}`, { method: 'DELETE' }),

  // Conversations
  listConversations: (projectId: string) =>
    fetchJson<{ conversations: Conversation[] }>(`/projects/${projectId}/conversations`),
  createConversation: (projectId: string, title?: string) =>
    fetchJson<{ conversation: Conversation }>(`/projects/${projectId}/conversations`, {
      method: 'POST',
      body: JSON.stringify({ title: title || 'New Conversation' })
    }),
  getConversation: (id: string) =>
    fetchJson<{ conversation: Conversation; messages: Message[] }>(`/conversations/${id}`),
  updateConversation: (id: string, title: string) =>
    fetchJson<{ message: string }>(`/conversations/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ title })
    }),
  deleteConversation: (id: string) =>
    fetchJson<{ message: string }>(`/conversations/${id}`, { method: 'DELETE' }),

  // Chat
  sendMessage: (data: {
    conversation_id?: string;
    project_id: string;
    message: string;
    use_rag?: boolean;
    source_ids?: string[];
    source_type?: string;
    model?: string;
  }) =>
    fetchJson<{
      conversation_id: string;
      user_message: Message;
      message: Message;
      citations: any[];
      model: string;
    }>('/chat', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  regenerateMessage: (conversationId: string, model?: string) =>
    fetchJson<{ message: Message; citations: any[] }>('/chat/regenerate', {
      method: 'POST',
      body: JSON.stringify({ conversation_id: conversationId, model })
    }),

  // Documents
  listDocuments: (projectId: string) =>
    fetchJson<{ documents: DocumentItem[] }>(`/projects/${projectId}/documents`),
  uploadDocument: async (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/projects/${projectId}/documents/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Upload failed with status ${res.status}`);
    }
    return res.json() as Promise<{ document: DocumentItem; chunk_count: number; message: string }>;
  },
  deleteDocument: (docId: string) =>
    fetchJson<{ message: string }>(`/documents/${docId}`, { method: 'DELETE' }),
  reindexDocument: (docId: string) =>
    fetchJson<{ document: DocumentItem; chunk_count: number; message: string }>(`/documents/${docId}/reindex`, {
      method: 'POST'
    }),

  // Domain / Websites
  listWebsites: (projectId: string) =>
    fetchJson<{ websites: WebsiteItem[] }>(`/projects/${projectId}/websites`),
  crawlWebsite: (projectId: string, url: string, maxPages: number = 5) =>
    fetchJson<{ website: WebsiteItem; message: string; chunk_count: number; page_count: number }>(
      `/projects/${projectId}/websites/crawl`,
      {
        method: 'POST',
        body: JSON.stringify({ url, max_pages: maxPages })
      }
    ),
  deleteWebsite: (siteId: string) =>
    fetchJson<{ message: string }>(`/websites/${siteId}`, { method: 'DELETE' }),
  recrawlWebsite: (siteId: string, maxPages: number = 5) =>
    fetchJson<{ website: WebsiteItem; chunk_count: number; page_count: number; message: string }>(
      `/websites/${siteId}/recrawl`,
      {
        method: 'POST',
        body: JSON.stringify({ max_pages: maxPages })
      }
    ),

  // Knowledge
  getKnowledgeSummary: (projectId: string) =>
    fetchJson<KnowledgeSummary>(`/projects/${projectId}/knowledge`),
  searchKnowledge: (projectId: string, query: string, topK: number = 5, alpha: number = 0.6, sourceIds?: string[]) =>
    fetchJson<{ query: string; alpha: number; count: number; results: any[] }>(
      `/projects/${projectId}/knowledge/search`,
      {
        method: 'POST',
        body: JSON.stringify({ query, top_k: topK, alpha, source_ids: sourceIds })
      }
    ),
  inspectChunks: (projectId: string, limit: number = 50) =>
    fetchJson<{ project_id: string; count: number; chunks: any[] }>(
      `/projects/${projectId}/knowledge/chunks?limit=${limit}`
    ),

  // Models & Settings
  getModels: () =>
    fetchJson<{
      status: string;
      default_model: string;
      models: any[];
      config: AppSettingsConfig;
    }>('/models'),
  updateSettings: (data: Partial<AppSettingsConfig>) =>
    fetchJson<{ message: string }>('/models/settings', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  testInference: (prompt: string, model?: string) =>
    fetchJson<{ status: string; model: string; response: string; duration_ms: number }>('/models/test', {
      method: 'POST',
      body: JSON.stringify({ prompt, model })
    }),

  // Export URLs
  getExportConversationUrl: (conversationId: string, format: 'markdown' | 'json' = 'markdown') =>
    `${API_BASE}/export/conversation/${conversationId}?format=${format}`,
  getExportMessageUrl: (messageId: string) =>
    `${API_BASE}/export/message/${messageId}`
};
