import React, { useState, useEffect, useRef } from 'react';
import { Project, Conversation, Message, DocumentItem, WebsiteItem } from '../../types';
import { api } from '../../services/api';
import { CitationBadge } from '../../components/CitationBadge';
import {
  Send,
  Plus,
  Trash2,
  RotateCcw,
  Copy,
  Check,
  Download,
  Filter,
  Sparkles,
  Bot,
  User,
  Shield,
  Layers,
  FileText,
  Globe
} from 'lucide-react';

interface AssistantProps {
  project: Project;
  initialConversation: Conversation | null;
  documents: DocumentItem[];
  websites: WebsiteItem[];
  onConversationCreated?: () => void;
}

export const AssistantModule: React.FC<AssistantProps> = ({
  project,
  initialConversation,
  documents,
  websites,
  onConversationCreated,
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConv, setActiveConv] = useState<Conversation | null>(initialConversation);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [useRag, setUseRag] = useState(true);
  const [selectedSourceId, setSelectedSourceId] = useState<string>('all');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load conversations for project
  const loadConversations = async () => {
    try {
      const res = await api.listConversations(project.id);
      setConversations(res.conversations);
      if (!activeConv && res.conversations.length > 0) {
        selectConversation(res.conversations[0]);
      }
    } catch (err) {
      console.error('Failed to load conversations', err);
    }
  };

  useEffect(() => {
    loadConversations();
  }, [project.id]);

  useEffect(() => {
    if (initialConversation) {
      selectConversation(initialConversation);
    }
  }, [initialConversation]);

  // Load messages when active conversation changes
  const selectConversation = async (conv: Conversation) => {
    setActiveConv(conv);
    try {
      const res = await api.getConversation(conv.id);
      setMessages(res.messages);
    } catch (err) {
      console.error('Failed to load messages', err);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleNewChat = async () => {
    try {
      const res = await api.createConversation(project.id, 'New Conversation');
      setConversations([res.conversation, ...conversations]);
      setActiveConv(res.conversation);
      setMessages([]);
      if (onConversationCreated) onConversationCreated();
    } catch (err) {
      console.error('Failed to create new chat', err);
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this conversation?')) return;
    try {
      await api.deleteConversation(id);
      const remaining = conversations.filter((c) => c.id !== id);
      setConversations(remaining);
      if (activeConv?.id === id) {
        if (remaining.length > 0) {
          selectConversation(remaining[0]);
        } else {
          setActiveConv(null);
          setMessages([]);
        }
      }
    } catch (err) {
      console.error('Failed to delete conversation', err);
    }
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');

    // Optimistic user message
    const tempUserMsg: Message = {
      id: 'temp-' + Date.now(),
      conversation_id: activeConv?.id || '',
      role: 'user',
      content: userText,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const sourceIds = selectedSourceId !== 'all' ? [selectedSourceId] : undefined;
      const res = await api.sendMessage({
        conversation_id: activeConv?.id,
        project_id: project.id,
        message: userText,
        use_rag: useRag,
        source_ids: sourceIds
      });

      // Update active conversation if it was newly created
      if (!activeConv || activeConv.id !== res.conversation_id) {
        const updatedConv = await api.getConversation(res.conversation_id);
        setActiveConv(updatedConv.conversation);
        setConversations((prev) => [updatedConv.conversation, ...prev.filter((c) => c.id !== res.conversation_id)]);
      }

      setMessages((prev) => {
        const withoutTemp = prev.filter((m) => m.id !== tempUserMsg.id);
        return [...withoutTemp, res.user_message, res.message];
      });

      loadConversations();
    } catch (err: any) {
      const errMsg: Message = {
        id: 'err-' + Date.now(),
        conversation_id: activeConv?.id || '',
        role: 'assistant',
        content: `Error generating response: ${err.message || 'Server error'}. Please check that Ollama is running with qwen2.5:1.5b.`,
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!activeConv || loading || messages.length === 0) return;
    setLoading(true);
    try {
      const res = await api.regenerateMessage(activeConv.id);
      // Replace last assistant message or append
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.role === 'assistant') {
          return [...prev.slice(0, -1), res.message];
        }
        return [...prev, res.message];
      });
    } catch (err: any) {
      alert(`Regeneration failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (content: string, id: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Conversations Left Panel */}
      <div className="w-64 bg-slate-900/60 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-3 border-b border-slate-800">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-brand-600/20 transition"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500 px-4">
              No chat history yet. Click New Chat above.
            </div>
          ) : (
            conversations.map((c) => {
              const isSelected = activeConv?.id === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => selectConversation(c)}
                  className={`flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer group transition ${
                    isSelected
                      ? 'bg-slate-800 text-slate-100 font-semibold border border-slate-700/60'
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                  }`}
                >
                  <span className="truncate pr-2">{c.title}</span>
                  <button
                    onClick={(e) => handleDeleteConversation(c.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 text-slate-500 rounded transition"
                    title="Delete Conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-slate-950 overflow-hidden">
        {/* Top Chat Bar */}
        <div className="h-14 px-6 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-white truncate max-w-sm">
              {activeConv?.title || 'New Conversation'}
            </h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-brand-500/10 text-brand-300 border border-brand-500/20">
              qwen2.5:1.5b
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Source Filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Filter className="w-3.5 h-3.5" />
              <select
                value={selectedSourceId}
                onChange={(e) => setSelectedSourceId(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-md px-2 py-1 text-xs text-slate-200 outline-none focus:border-brand-500"
              >
                <option value="all">All Sources ({documents.length + websites.length})</option>
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    Doc: {d.filename}
                  </option>
                ))}
                {websites.map((w) => (
                  <option key={w.id} value={w.id}>
                    Site: {w.title || w.url}
                  </option>
                ))}
              </select>
            </div>

            {/* RAG Toggle */}
            <button
              onClick={() => setUseRag(!useRag)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                useRag
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}
              title={useRag ? 'RAG is ON (Grounded Answers)' : 'RAG is OFF (Pure LLM)'}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>RAG {useRag ? 'ON' : 'OFF'}</span>
            </button>

            {/* Export Markdown */}
            {activeConv && messages.length > 0 && (
              <a
                href={api.getExportConversationUrl(activeConv.id, 'markdown')}
                download={`conversation_${activeConv.id.slice(0, 8)}.md`}
                className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
                title="Export as Markdown"
              >
                <Download className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center shadow-lg">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-100">DOMCHAT AI Assistant</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Ask questions, summarize documents, analyze crawled websites, or brainstorm code. All processing is 100% local on CPU.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 w-full pt-2">
                <button
                  onClick={() => {
                    setInput('What documents and websites are currently indexed in this workspace?');
                  }}
                  className="p-2.5 text-left text-xs bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-lg text-slate-300 transition"
                >
                  "What sources are indexed in this workspace?"
                </button>
                <button
                  onClick={() => {
                    setInput('Summarize the key points from our indexed documents.');
                  }}
                  className="p-2.5 text-left text-xs bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-lg text-slate-300 transition"
                >
                  "Summarize key points from indexed files"
                </button>
              </div>
            </div>
          ) : (
            messages.map((m) => {
              const isUser = m.role === 'user';
              return (
                <div
                  key={m.id}
                  className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}
                >
                  {!isUser && (
                    <div className="w-8 h-8 rounded-lg bg-brand-600/20 text-brand-400 border border-brand-500/30 flex items-center justify-center shrink-0 mt-1">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div className={`space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
                    <div
                      className={`text-sm leading-relaxed p-4 rounded-2xl shadow-sm whitespace-pre-wrap ${
                        isUser
                          ? 'bg-brand-600 text-white rounded-tr-sm'
                          : 'bg-slate-900 text-slate-100 border border-slate-800 rounded-tl-sm'
                      }`}
                    >
                      {m.content}
                    </div>

                    {/* Citations block for assistant messages */}
                    {!isUser && m.citations && m.citations.length > 0 && (
                      <div className="pt-1">
                        <div className="text-[11px] font-semibold text-slate-400 mb-1 flex items-center gap-1.5">
                          <Layers className="w-3 h-3 text-brand-400" />
                          <span>Sources Grounding This Answer:</span>
                        </div>
                        <div className="flex flex-wrap">
                          {m.citations.map((c, idx) => (
                            <CitationBadge key={idx} citation={c} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Assistant Message Actions */}
                    {!isUser && (
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => handleCopy(m.content, m.id)}
                          className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-850 transition"
                        >
                          {copiedId === m.id ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                          <span>{copiedId === m.id ? 'Copied' : 'Copy'}</span>
                        </button>

                        <a
                          href={api.getExportMessageUrl(m.id)}
                          download={`response_${m.id.slice(0, 8)}.md`}
                          className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-850 transition"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Export .md</span>
                        </a>
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-8 h-8 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 flex items-center justify-center shrink-0 mt-1">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })
          )}

          {loading && (
            <div className="flex gap-3 max-w-xl mr-auto items-start">
              <div className="w-8 h-8 rounded-lg bg-brand-600/20 text-brand-400 border border-brand-500/30 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-sm p-4 space-y-2">
                <div className="flex items-center gap-2 text-xs text-brand-300">
                  <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
                  <span>Qwen 2.5 1.5B is analyzing context & generating answer...</span>
                </div>
                <div className="space-y-1.5 opacity-60">
                  <div className="h-2 bg-slate-700 rounded-full w-48 animate-pulse" />
                  <div className="h-2 bg-slate-700 rounded-full w-64 animate-pulse" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/40">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto flex gap-2">
            {messages.length > 0 && !loading && (
              <button
                type="button"
                onClick={handleRegenerate}
                className="p-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition border border-slate-700/60"
                title="Regenerate last answer"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}

            <div className="flex-1 relative">
              <textarea
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={
                  useRag
                    ? 'Ask anything (grounded against indexed documents & websites)...'
                    : 'Ask anything (pure local Qwen inference)...'
                }
                className="w-full bg-slate-900 border border-slate-800 focus:border-brand-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none resize-none shadow-inner"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl transition shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="text-center text-[10px] text-slate-500 mt-2">
            DOMCHAT grounds answers on verified sources and will not fabricate evidence.
          </div>
        </div>
      </div>
    </div>
  );
};
