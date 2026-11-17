import React, { useState } from 'react';
import { Project, WebsiteItem } from '../../types';
import { api } from '../../services/api';
import { ActiveTab } from '../../components/Sidebar';
import {
  Globe,
  Plus,
  Trash2,
  RefreshCw,
  MessageSquare,
  ExternalLink,
  Layers,
  AlertCircle,
  Search,
  CheckCircle2,
  Sliders
} from 'lucide-react';

interface DomainModuleProps {
  project: Project;
  websites: WebsiteItem[];
  onRefresh: () => void;
  onNavigate: (tab: ActiveTab) => void;
  onSelectSiteForChat?: (siteId: string) => void;
}

export const DomainModule: React.FC<DomainModuleProps> = ({
  project,
  websites,
  onRefresh,
  onNavigate,
  onSelectSiteForChat,
}) => {
  const [urlInput, setUrlInput] = useState('');
  const [maxPages, setMaxPages] = useState<number>(3);
  const [crawling, setCrawling] = useState(false);
  const [recrawlingId, setRecrawlingId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const handleStartCrawl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    try {
      setCrawling(true);
      setErrorMsg('');
      setSuccessMsg('');
      const res = await api.crawlWebsite(project.id, urlInput.trim(), maxPages);
      setUrlInput('');
      setSuccessMsg(res.message);
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Crawl failed');
    } finally {
      setCrawling(false);
    }
  };

  const handleDelete = async (siteId: string, url: string) => {
    if (!confirm(`Are you sure you want to delete indexed data for ${url}?`)) return;
    try {
      await api.deleteWebsite(siteId);
      onRefresh();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleRecrawl = async (siteId: string) => {
    try {
      setRecrawlingId(siteId);
      await api.recrawlWebsite(siteId, maxPages);
      onRefresh();
    } catch (err: any) {
      alert(`Re-crawl failed: ${err.message}`);
    } finally {
      setRecrawlingId(null);
    }
  };

  const filteredSites = websites.filter(
    (w) =>
      w.url.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (w.title && w.title.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Globe className="w-5 h-5 text-emerald-400" />
          Domain Intelligence & Web Crawling
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Crawl and extract documentation, articles, and websites to ground your local AI conversations with live web content.
        </p>
      </div>

      {/* Crawl Form Card */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg">
        <form onSubmit={handleStartCrawl} className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Globe className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                required
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="Enter URL to crawl (e.g. https://docs.python.org/3/ or https://react.dev)"
                className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 outline-none transition"
              />
            </div>

            {/* Max Pages Selector */}
            <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 shrink-0">
              <Sliders className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs text-slate-400">Limit:</span>
              <select
                value={maxPages}
                onChange={(e) => setMaxPages(Number(e.target.value))}
                className="bg-transparent text-xs text-slate-200 outline-none cursor-pointer"
              >
                <option value={1} className="bg-slate-900">1 Page</option>
                <option value={3} className="bg-slate-900">3 Pages</option>
                <option value={5} className="bg-slate-900">5 Pages</option>
                <option value={10} className="bg-slate-900">10 Pages</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={crawling || !urlInput.trim()}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-emerald-600/20 transition disabled:opacity-50 flex items-center justify-center gap-2 shrink-0"
            >
              {crawling ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Crawling & Indexing...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Crawl Website</span>
                </>
              )}
            </button>
          </div>

          <div className="flex items-center gap-4 text-[11px] text-slate-500">
            <span>• Same-domain crawling only</span>
            <span>• Strips scripts, styles, boilerplate navigation</span>
            <span>• SSRF protection active (localhost blocked)</span>
          </div>
        </form>

        {errorMsg && (
          <div className="mt-3 p-3 bg-red-950/60 border border-red-800 text-red-200 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="mt-3 p-3 bg-emerald-950/60 border border-emerald-800 text-emerald-200 text-xs rounded-xl flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}
      </div>

      {/* Websites Filter & List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search indexed websites..."
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-brand-500"
            />
          </div>
          <div className="text-xs text-slate-400">
            <span className="font-semibold text-slate-200">{filteredSites.length}</span> websites indexed
          </div>
        </div>

        <div className="space-y-3">
          {filteredSites.length === 0 ? (
            <div className="text-center py-12 rounded-xl bg-slate-900/40 border border-slate-800 text-slate-500 text-xs">
              {searchQuery ? 'No websites match your search.' : 'No websites indexed in this workspace yet. Enter a URL above!'}
            </div>
          ) : (
            filteredSites.map((site) => {
              const isRecrawling = recrawlingId === site.id;
              return (
                <div
                  key={site.id}
                  className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition group"
                >
                  <div className="flex items-center gap-3.5 truncate">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 text-emerald-400 flex items-center justify-center shrink-0 border border-slate-700/60">
                      <Globe className="w-5 h-5" />
                    </div>

                    <div className="truncate">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-100 truncate">
                          {site.title || site.url}
                        </span>
                        <a
                          href={site.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-400 hover:text-brand-400"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                        <span className="truncate max-w-xs">{site.url}</span>
                        <span>•</span>
                        <span>{site.page_count} pages crawled</span>
                        <span>•</span>
                        <span className="flex items-center gap-1 text-emerald-400">
                          <Layers className="w-3 h-3" />
                          {site.chunk_count} chunks indexed
                        </span>
                        <span>•</span>
                        <span>{new Date(site.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    <button
                      onClick={() => {
                        if (onSelectSiteForChat) onSelectSiteForChat(site.id);
                        onNavigate('assistant');
                      }}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 rounded-lg text-xs font-medium transition"
                      title="Start Grounded Chat with this Website"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Chat with Website</span>
                    </button>

                    <button
                      onClick={() => handleRecrawl(site.id)}
                      disabled={isRecrawling}
                      className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
                      title="Re-crawl and update chunks"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${isRecrawling ? 'animate-spin text-emerald-400' : ''}`} />
                    </button>

                    <button
                      onClick={() => handleDelete(site.id, site.url)}
                      className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition"
                      title="Delete Website Data"
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
    </div>
  );
};
