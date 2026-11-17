import React, { useState, useEffect } from 'react';
import { Project, KnowledgeSummary } from '../../types';
import { api } from '../../services/api';
import {
  Database,
  Search,
  FileText,
  Globe,
  Sliders,
  Layers,
  Sparkles,
  ArrowRight,
  Eye,
  CheckCircle2,
  Trash2
} from 'lucide-react';

interface KnowledgeModuleProps {
  project: Project;
  onRefresh: () => void;
}

export const KnowledgeModule: React.FC<KnowledgeModuleProps> = ({ project, onRefresh }) => {
  const [summary, setSummary] = useState<KnowledgeSummary | null>(null);
  const [loading, setLoading] = useState(false);

  // Hybrid Query Tester State
  const [testQuery, setTestQuery] = useState('');
  const [alpha, setAlpha] = useState(0.6);
  const [topK, setTopK] = useState(4);
  const [testResults, setTestResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  // Raw Chunks Inspector State
  const [chunks, setChunks] = useState<any[]>([]);
  const [viewingChunks, setViewingChunks] = useState(false);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const res = await api.getKnowledgeSummary(project.id);
      setSummary(res);
    } catch (err) {
      console.error('Failed to load knowledge summary', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [project.id]);

  const handleTestSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testQuery.trim()) return;
    try {
      setSearching(true);
      const res = await api.searchKnowledge(project.id, testQuery.trim(), topK, alpha);
      setTestResults(res.results);
    } catch (err: any) {
      alert(`Search failed: ${err.message}`);
    } finally {
      setSearching(false);
    }
  };

  const handleInspectChunks = async () => {
    try {
      setViewingChunks(true);
      const res = await api.inspectChunks(project.id, 50);
      setChunks(res.chunks);
    } catch (err: any) {
      alert(`Failed to load chunks: ${err.message}`);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Database className="w-5 h-5 text-purple-400" />
          Knowledge Management & Vector Store
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Inspect indexed vectors, test hybrid BM25 + dense semantic retrieval, and examine chunk distributions.
        </p>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-xs text-slate-400">Total Sources</div>
          <div className="text-2xl font-bold text-white mt-1">{summary?.total_sources || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-xs text-slate-400">Documents</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{summary?.total_documents || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-xs text-slate-400">Websites</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{summary?.total_websites || 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-xs text-slate-400">Indexed Chunks</div>
          <div className="text-2xl font-bold text-purple-400 mt-1">{summary?.total_chunks || 0}</div>
        </div>
      </div>

      {/* Hybrid Retrieval Tester */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-brand-400" />
            <span className="font-semibold text-sm text-slate-100">Hybrid Retrieval Tester</span>
          </div>
          <span className="text-xs text-slate-400">
            Compare semantic dense embeddings vs BM25 keyword matching
          </span>
        </div>

        <form onSubmit={handleTestSearch} className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                required
                value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                placeholder="Enter query to test retrieval relevance (e.g. 'What are the main findings?')"
                className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 outline-none transition"
              />
            </div>
            <button
              type="submit"
              disabled={searching || !testQuery.trim()}
              className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-brand-600/20 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Search className="w-4 h-4" />
              <span>{searching ? 'Querying...' : 'Test Retrieval'}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            {/* Hybrid Alpha Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-slate-400">
                <span>Retrieval Fusion (Alpha): <span className="font-mono text-brand-300">{alpha}</span></span>
                <span>{Math.round((1 - alpha) * 100)}% BM25 / {Math.round(alpha * 100)}% Semantic</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={alpha}
                onChange={(e) => setAlpha(parseFloat(e.target.value))}
                className="w-full accent-brand-500 cursor-pointer"
              />
            </div>

            {/* Top-K */}
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400">Top-K Chunks:</span>
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-brand-500"
              >
                <option value={2}>2 Chunks</option>
                <option value={4}>4 Chunks</option>
                <option value={6}>6 Chunks</option>
                <option value={10}>10 Chunks</option>
              </select>
            </div>
          </div>
        </form>

        {/* Test Results Display */}
        {testResults.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-800 space-y-3">
            <div className="text-xs font-semibold text-slate-300">
              Retrieved {testResults.length} Chunks (Ranked by Fused Score):
            </div>
            {testResults.map((r, i) => (
              <div key={i} className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-xs space-y-1.5">
                <div className="flex items-center justify-between text-[11px] text-slate-400 pb-1 border-b border-slate-800">
                  <div className="flex items-center gap-2 font-medium text-slate-200">
                    <span className="text-brand-400 font-mono">#{i + 1}</span>
                    <span>{r.metadata?.filename || r.metadata?.title || 'Source'}</span>
                    {r.metadata?.page_number && r.metadata.page_number !== '0' && (
                      <span className="text-[10px] px-1 py-0.2 bg-slate-800 rounded">
                        Page {r.metadata.page_number}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="text-emerald-400">Fused: {r.score}</span>
                    {r.semantic_score !== undefined && (
                      <span className="text-slate-500">(Dense: {r.semantic_score} | BM25: {r.keyword_score})</span>
                    )}
                  </div>
                </div>
                <div className="text-slate-300 leading-relaxed font-sans italic">
                  "{r.text}"
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Raw Chunks Explorer */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold text-sm text-slate-100">ChromaDB Chunk Inspector</span>
          </div>
          <button
            onClick={handleInspectChunks}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition"
          >
            {chunks.length > 0 ? 'Refresh Chunks' : 'Inspect Raw Chunks'}
          </button>
        </div>

        {chunks.length > 0 && (
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {chunks.map((c, i) => (
              <div key={i} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/60 text-xs">
                <div className="flex justify-between text-[10px] text-slate-500 mb-1 font-mono">
                  <span>ID: {c.id}</span>
                  <span>{c.metadata?.filename || c.metadata?.url}</span>
                </div>
                <div className="text-slate-300 text-[11px] line-clamp-3">
                  {c.text}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
