import React from 'react';
import { Project, SystemHealth, Conversation, DocumentItem, WebsiteItem } from '../../types';
import { ActiveTab } from '../../components/Sidebar';
import {
  MessageSquare,
  FileText,
  Globe,
  Cpu,
  Plus,
  ArrowRight,
  HardDrive,
  Activity,
  CheckCircle2,
  AlertCircle,
  FileUp,
  Search,
  Sparkles
} from 'lucide-react';

interface DashboardProps {
  project: Project;
  health: SystemHealth | null;
  conversations: Conversation[];
  documents: DocumentItem[];
  websites: WebsiteItem[];
  onNavigate: (tab: ActiveTab) => void;
  onSelectConversation: (c: Conversation) => void;
}

export const DashboardModule: React.FC<DashboardProps> = ({
  project,
  health,
  conversations,
  documents,
  websites,
  onNavigate,
  onSelectConversation,
}) => {
  const isAiConnected = health?.ai?.connected ?? false;
  const sys = health?.system;

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-900/60 via-slate-900 to-slate-900 border border-brand-500/20 p-6 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-brand-500/20 text-brand-300 rounded-md border border-brand-500/30">
                Workspace Active
              </span>
              <span className="text-xs text-slate-400">• {project.name}</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Welcome to DOMCHAT
            </h1>
            <p className="text-sm text-slate-300 max-w-xl mt-1">
              Your local AI workstation powered by Ollama (<span className="text-brand-300 font-mono">qwen2.5:1.5b</span>) and high-precision hybrid RAG retrieval on CPU.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('assistant')}
              className="flex items-center gap-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-brand-600/30 transition-all transform hover:-translate-y-0.5"
            >
              <Plus className="w-4 h-4" />
              <span>Start New Chat</span>
            </button>
            <button
              onClick={() => onNavigate('documents')}
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition"
            >
              <FileUp className="w-4 h-4 text-brand-400" />
              <span>Upload Files</span>
            </button>
          </div>
        </div>
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => onNavigate('assistant')}
          className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-brand-500/50 hover:bg-slate-850 cursor-pointer transition-all group shadow-sm"
        >
          <div className="w-9 h-9 rounded-lg bg-brand-500/10 text-brand-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div className="font-semibold text-sm text-slate-100 group-hover:text-brand-300 transition-colors">
            AI Assistant
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Chat with local Qwen 2.5 or grounded RAG context.
          </div>
        </div>

        <div
          onClick={() => onNavigate('documents')}
          className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-blue-500/50 hover:bg-slate-850 cursor-pointer transition-all group shadow-sm"
        >
          <div className="w-9 h-9 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <FileText className="w-5 h-5" />
          </div>
          <div className="font-semibold text-sm text-slate-100 group-hover:text-blue-300 transition-colors">
            Document Intel
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Index PDF, DOCX, TXT, Markdown, CSV.
          </div>
        </div>

        <div
          onClick={() => onNavigate('domain')}
          className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-850 cursor-pointer transition-all group shadow-sm"
        >
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <Globe className="w-5 h-5" />
          </div>
          <div className="font-semibold text-sm text-slate-100 group-hover:text-emerald-300 transition-colors">
            Domain Intel
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Crawl and ground chat on live websites.
          </div>
        </div>

        <div
          onClick={() => onNavigate('settings')}
          className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-purple-500/50 hover:bg-slate-850 cursor-pointer transition-all group shadow-sm"
        >
          <div className="w-9 h-9 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <Cpu className="w-5 h-5" />
          </div>
          <div className="font-semibold text-sm text-slate-100 group-hover:text-purple-300 transition-colors">
            Model Studio
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Configure generation, tokens, and chunking.
          </div>
        </div>
      </div>

      {/* AI Model Status & System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Model Status Card */}
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-brand-400" />
                <span className="font-semibold text-sm text-slate-100">AI Model Status</span>
              </div>
              <span
                className={`flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${
                  isAiConnected ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${isAiConnected ? 'bg-emerald-400' : 'bg-red-400'}`} />
                {isAiConnected ? 'Ollama Online' : 'Ollama Offline'}
              </span>
            </div>

            <div className="mt-4 space-y-3">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Selected Model</span>
                <span className="font-mono font-semibold text-brand-300">
                  {health?.ai?.default_model || 'qwen2.5:1.5b'}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Execution Mode</span>
                <span className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-medium">
                  CPU Only (Optimized)
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Embedding Engine</span>
                <span className="font-mono text-slate-300">all-MiniLM-L6-v2 (384d)</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Vector Store</span>
                <span className="text-slate-300 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> ChromaDB Persistent
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onNavigate('settings')}
            className="mt-4 w-full py-2 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 rounded-lg text-xs font-medium flex items-center justify-center gap-1.5 transition"
          >
            <span>Model Settings</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* System Health Card */}
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span className="font-semibold text-sm text-slate-100">System Performance</span>
              </div>
              <span className="text-xs text-slate-400">Intel i3-1005G1 • 8GB</span>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">CPU Usage</span>
                  <span className="font-mono text-slate-200">{sys?.cpu_percent ?? 0}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-brand-500 h-full transition-all"
                    style={{ width: `${Math.min(100, Math.max(5, sys?.cpu_percent ?? 0))}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Memory (RAM)</span>
                  <span className="font-mono text-slate-200">
                    {sys ? `${Math.round(sys.memory_used_mb / 1024 * 10) / 10}GB / ${Math.round(sys.memory_total_mb / 1024 * 10) / 10}GB` : 'Loading...'}
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full transition-all"
                    style={{ width: `${Math.min(100, Math.max(5, sys?.memory_percent ?? 0))}%` }}
                  />
                </div>
              </div>

              <div className="flex justify-between items-center text-xs pt-1">
                <span className="text-slate-400">Storage Directories</span>
                <span className="text-emerald-400 text-[11px] flex items-center gap-1 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" /> All Initialized
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 text-[11px] text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
            Memory footprint is tuned for &lt;8GB RAM with batch-free CPU embeddings and zero GPU dependencies.
          </div>
        </div>

        {/* Knowledge Stats Card */}
        <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-blue-400" />
                <span className="font-semibold text-sm text-slate-100">Knowledge Stats</span>
              </div>
              <span className="text-xs text-brand-400 cursor-pointer hover:underline" onClick={() => onNavigate('knowledge')}>
                View All
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-4">
              <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
                <div className="text-xl font-bold text-white">{documents.length}</div>
                <div className="text-xs text-slate-400 mt-0.5">Documents</div>
              </div>
              <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
                <div className="text-xl font-bold text-white">{websites.length}</div>
                <div className="text-xs text-slate-400 mt-0.5">Websites</div>
              </div>
              <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
                <div className="text-xl font-bold text-emerald-400">
                  {documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0) +
                    websites.reduce((acc, w) => acc + (w.chunk_count || 0), 0)}
                </div>
                <div className="text-xs text-slate-400 mt-0.5">Total Chunks</div>
              </div>
              <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
                <div className="text-xl font-bold text-brand-400">{conversations.length}</div>
                <div className="text-xs text-slate-400 mt-0.5">Conversations</div>
              </div>
            </div>
          </div>

          <button
            onClick={() => onNavigate('knowledge')}
            className="mt-4 w-full py-2 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 rounded-lg text-xs font-medium flex items-center justify-center gap-1.5 transition"
          >
            <span>Search Knowledge Base</span>
            <Search className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Recent Activity Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Conversations */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="font-semibold text-sm text-slate-100 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-brand-400" />
              Recent Conversations
            </h3>
            <button
              onClick={() => onNavigate('assistant')}
              className="text-xs text-brand-400 hover:text-brand-300"
            >
              Open Assistant
            </button>
          </div>

          <div className="mt-3 space-y-2">
            {conversations.length === 0 ? (
              <div className="text-center py-6 text-xs text-slate-500">
                No conversations yet. Start a new chat!
              </div>
            ) : (
              conversations.slice(0, 5).map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => onSelectConversation(conv)}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/50 hover:bg-slate-800/80 cursor-pointer border border-slate-800/50 transition group"
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <MessageSquare className="w-3.5 h-3.5 text-slate-400 group-hover:text-brand-400" />
                    <span className="text-xs text-slate-200 font-medium truncate">
                      {conv.title}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 shrink-0 font-mono">
                    {new Date(conv.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Documents & Websites */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="font-semibold text-sm text-slate-100 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" />
              Indexed Sources
            </h3>
            <button
              onClick={() => onNavigate('documents')}
              className="text-xs text-brand-400 hover:text-brand-300"
            >
              Manage Sources
            </button>
          </div>

          <div className="mt-3 space-y-2">
            {documents.length === 0 && websites.length === 0 ? (
              <div className="text-center py-6 text-xs text-slate-500">
                No documents or websites indexed yet.
              </div>
            ) : (
              <>
                {documents.slice(0, 3).map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/50"
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <FileText className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                      <div className="truncate">
                        <div className="text-xs text-slate-200 font-medium truncate">
                          {doc.filename}
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {doc.file_type.toUpperCase()} • {Math.round(doc.file_size / 1024)} KB
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-mono">
                      {doc.chunk_count} chunks
                    </span>
                  </div>
                ))}

                {websites.slice(0, 2).map((site) => (
                  <div
                    key={site.id}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/50"
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <Globe className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <div className="truncate">
                        <div className="text-xs text-slate-200 font-medium truncate">
                          {site.title || site.url}
                        </div>
                        <div className="text-[10px] text-slate-500 truncate max-w-[200px]">
                          {site.url}
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-mono">
                      {site.chunk_count} chunks
                    </span>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
