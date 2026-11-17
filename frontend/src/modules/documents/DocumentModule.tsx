import React, { useState, useRef } from 'react';
import { Project, DocumentItem } from '../../types';
import { api } from '../../services/api';
import { ActiveTab } from '../../components/Sidebar';
import {
  FileText,
  Upload,
  Trash2,
  RefreshCw,
  MessageSquare,
  FileCheck,
  AlertCircle,
  FileUp,
  Search,
  ExternalLink,
  Layers
} from 'lucide-react';

interface DocumentModuleProps {
  project: Project;
  documents: DocumentItem[];
  onRefresh: () => void;
  onNavigate: (tab: ActiveTab) => void;
  onSelectDocForChat?: (docId: string) => void;
}

export const DocumentModule: React.FC<DocumentModuleProps> = ({
  project,
  documents,
  onRefresh,
  onNavigate,
  onSelectDocForChat,
}) => {
  const [uploading, setUploading] = useState(false);
  const [reindexingId, setReindexingId] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    
    // Check extension
    const allowed = ['.pdf', '.docx', '.doc', '.txt', '.md', '.markdown', '.csv'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowed.includes(ext)) {
      setErrorMsg(`Unsupported file type: ${ext}. Supported: PDF, DOCX, TXT, MD, CSV.`);
      return;
    }

    try {
      setUploading(true);
      setErrorMsg('');
      await api.uploadDocument(project.id, file);
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'File upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"? All associated chunks and embeddings will be removed.`)) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      onRefresh();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleReindex = async (docId: string) => {
    try {
      setReindexingId(docId);
      await api.reindexDocument(docId);
      onRefresh();
    } catch (err: any) {
      alert(`Reindexing failed: ${err.message}`);
    } finally {
      setReindexingId(null);
    }
  };

  const filteredDocs = documents.filter((d) =>
    d.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Document Intelligence
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Upload documents to extract, chunk, and index them into ChromaDB for grounded local RAG.
          </p>
        </div>

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-brand-600/20 transition disabled:opacity-50"
        >
          <Upload className="w-4 h-4" />
          <span>{uploading ? 'Processing File...' : 'Upload Document'}</span>
        </button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleFileUpload(e.target.files)}
          accept=".pdf,.docx,.doc,.txt,.md,.markdown,.csv"
          className="hidden"
        />
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-950/60 border border-red-800 text-red-200 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Drag and Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          handleFileUpload(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-brand-500 bg-brand-500/10'
            : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/60'
        }`}
      >
        <div className="w-12 h-12 rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto mb-3">
          <FileUp className="w-6 h-6" />
        </div>
        <div className="text-sm font-semibold text-slate-200">
          Drag & drop files here or click to browse
        </div>
        <div className="text-xs text-slate-400 mt-1">
          Supports <span className="text-brand-300 font-mono">PDF, DOCX, TXT, Markdown, CSV</span> (up to 25MB)
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search indexed documents..."
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-brand-500"
          />
        </div>
        <div className="text-xs text-slate-400">
          Showing <span className="font-semibold text-slate-200">{filteredDocs.length}</span> of {documents.length} documents
        </div>
      </div>

      {/* Documents List */}
      <div className="space-y-3">
        {filteredDocs.length === 0 ? (
          <div className="text-center py-12 rounded-xl bg-slate-900/40 border border-slate-800 text-slate-500 text-xs">
            {searchQuery ? 'No documents match your search.' : 'No documents indexed in this workspace yet.'}
          </div>
        ) : (
          filteredDocs.map((doc) => {
            const isReindexing = reindexingId === doc.id;
            return (
              <div
                key={doc.id}
                className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition group"
              >
                <div className="flex items-center gap-3.5 truncate">
                  <div className="w-10 h-10 rounded-xl bg-slate-800 text-blue-400 flex items-center justify-center shrink-0 border border-slate-700/60">
                    <FileText className="w-5 h-5" />
                  </div>

                  <div className="truncate">
                    <div className="text-sm font-semibold text-slate-100 truncate">
                      {doc.filename}
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                      <span className="uppercase font-mono px-1.5 py-0.2 bg-slate-800 rounded text-slate-300">
                        {doc.file_type}
                      </span>
                      <span>•</span>
                      <span>{Math.round(doc.file_size / 1024)} KB</span>
                      <span>•</span>
                      <span className="flex items-center gap-1 text-emerald-400">
                        <Layers className="w-3 h-3" />
                        {doc.chunk_count} chunks indexed
                      </span>
                      <span>•</span>
                      <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                  <button
                    onClick={() => {
                      if (onSelectDocForChat) onSelectDocForChat(doc.id);
                      onNavigate('assistant');
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-600/20 hover:bg-brand-600/30 text-brand-300 border border-brand-500/30 rounded-lg text-xs font-medium transition"
                    title="Start Grounded Chat with this Document"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Chat with Doc</span>
                  </button>

                  <button
                    onClick={() => handleReindex(doc.id)}
                    disabled={isReindexing}
                    className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
                    title="Re-extract and Re-index"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isReindexing ? 'animate-spin text-brand-400' : ''}`} />
                  </button>

                  <button
                    onClick={() => handleDelete(doc.id, doc.filename)}
                    className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition"
                    title="Delete Document"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
