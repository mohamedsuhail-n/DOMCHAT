import React, { useState } from 'react';
import { Citation } from '../types';
import { BookOpen, Globe, FileText, ChevronDown, ChevronUp } from 'lucide-react';

interface CitationBadgeProps {
  citation: Citation;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation }) => {
  const [expanded, setExpanded] = useState(false);

  const isDoc = citation.source_type === 'document';
  const label = citation.title || citation.filename || citation.url || `Source ${citation.source_index}`;
  const pageText = citation.page && String(citation.page) !== '0' && String(citation.page) !== '' ? `p. ${citation.page}` : '';

  return (
    <div className="inline-block my-1 mr-2 text-xs">
      <div
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/90 hover:bg-slate-700/90 text-slate-200 border border-slate-700/70 cursor-pointer transition-all duration-150 select-none shadow-sm"
      >
        {isDoc ? (
          <FileText className="w-3.5 h-3.5 text-blue-400 shrink-0" />
        ) : (
          <Globe className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        )}
        <span className="font-medium text-brand-300">[{citation.source_index}]</span>
        <span className="truncate max-w-[180px] text-slate-300">{label}</span>
        {pageText && (
          <span className="px-1 py-0.2 text-[10px] bg-slate-700 text-slate-300 rounded font-mono">
            {pageText}
          </span>
        )}
        {expanded ? <ChevronUp className="w-3 h-3 text-slate-400" /> : <ChevronDown className="w-3 h-3 text-slate-400" />}
      </div>

      {expanded && (
        <div className="mt-1.5 p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 shadow-xl max-w-md animate-fadeIn">
          <div className="flex items-center justify-between text-[11px] text-slate-400 pb-1.5 mb-1.5 border-b border-slate-800">
            <span className="font-semibold text-slate-200">{isDoc ? 'Document Reference' : 'Website Reference'}</span>
            <span className="font-mono text-emerald-400">Score: {Math.round(citation.score * 100)}%</span>
          </div>
          {citation.url && (
            <a
              href={citation.url}
              target="_blank"
              rel="noreferrer"
              className="block text-brand-400 hover:underline truncate mb-1.5 text-[11px]"
            >
              {citation.url}
            </a>
          )}
          <div className="text-slate-300 text-[11px] leading-relaxed italic bg-slate-950/60 p-2 rounded border border-slate-800/60">
            "{citation.snippet}"
          </div>
        </div>
      )}
    </div>
  );
};
