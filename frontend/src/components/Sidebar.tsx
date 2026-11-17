import React from 'react';
import { Project, SystemHealth } from '../types';
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Globe,
  Database,
  Cpu,
  FolderOpen,
  Plus,
  Activity,
  Sun,
  Moon,
  ChevronRight,
  ShieldCheck,
  Zap
} from 'lucide-react';

export type ActiveTab = 'dashboard' | 'assistant' | 'documents' | 'domain' | 'knowledge' | 'settings';

interface SidebarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  projects: Project[];
  activeProject: Project | null;
  onSelectProject: (p: Project) => void;
  onOpenNewProject: () => void;
  health: SystemHealth | null;
  isDarkMode: boolean;
  onToggleTheme: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  projects,
  activeProject,
  onSelectProject,
  onOpenNewProject,
  health,
  isDarkMode,
  onToggleTheme,
}) => {
  const isOllamaConnected = health?.ai?.connected ?? false;
  const cpuPercent = health?.system?.cpu_percent ?? 0;
  const memUsedMb = health?.system?.memory_used_mb ?? 0;

  const navItems = [
    { id: 'dashboard' as ActiveTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'assistant' as ActiveTab, label: 'AI Assistant', icon: MessageSquare },
    { id: 'documents' as ActiveTab, label: 'Documents', icon: FileText, badge: activeProject?.document_count },
    { id: 'domain' as ActiveTab, label: 'Domain Intel', icon: Globe, badge: activeProject?.website_count },
    { id: 'knowledge' as ActiveTab, label: 'Knowledge Base', icon: Database },
    { id: 'settings' as ActiveTab, label: 'Model Studio', icon: Cpu },
  ];

  return (
    <aside className="w-64 bg-slate-900/95 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none z-20 transition-all">
      {/* Brand Header */}
      <div>
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/20 text-white font-black text-sm tracking-tighter">
              DOM
            </div>
            <div>
              <div className="font-bold text-sm tracking-tight text-white flex items-center gap-1.5">
                DOMCHAT
                <span className="text-[10px] px-1.5 py-0.2 bg-brand-500/20 text-brand-300 rounded font-mono font-medium">
                  v1.0
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-medium">Local AI & RAG Engine</div>
            </div>
          </div>

          <button
            onClick={onToggleTheme}
            title={isDarkMode ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
          >
            {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-brand-400" />}
          </button>
        </div>

        {/* Project Switcher */}
        <div className="px-3 pt-3 pb-2 border-b border-slate-800/60">
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400 px-2 mb-1.5 uppercase tracking-wider">
            <span>Workspace</span>
            <button
              onClick={onOpenNewProject}
              title="Create New Workspace"
              className="hover:text-brand-400 transition p-0.5 rounded hover:bg-slate-800"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="relative">
            <select
              value={activeProject?.id || 'default'}
              onChange={(e) => {
                const found = projects.find((p) => p.id === e.target.value);
                if (found) onSelectProject(found);
              }}
              className="w-full bg-slate-950/80 border border-slate-800 hover:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-medium appearance-none cursor-pointer outline-none focus:border-brand-500 transition"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id} className="bg-slate-900 text-slate-100">
                  {p.name}
                </option>
              ))}
            </select>
            <FolderOpen className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>
        </div>

        {/* Navigation List */}
        <nav className="p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30 font-semibold'
                    : 'text-slate-300 hover:bg-slate-800/80 hover:text-slate-100'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 transition-colors ${
                      isActive ? 'text-white' : 'text-slate-400 group-hover:text-brand-400'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge > 0 && (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                      isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Hardware & Ollama Status Footer */}
      <div className="p-3 border-t border-slate-800 space-y-2.5 bg-slate-950/40">
        {/* Model Status Pill */}
        <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800/80">
          <div className="flex items-center justify-between text-[11px] mb-1">
            <span className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Zap className="w-3 h-3 text-amber-400" />
              Local Model
            </span>
            <span
              className={`flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.2 rounded ${
                isOllamaConnected
                  ? 'bg-emerald-500/20 text-emerald-300'
                  : 'bg-red-500/20 text-red-300'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isOllamaConnected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'
                }`}
              />
              {isOllamaConnected ? 'Online' : 'Offline'}
            </span>
          </div>
          <div className="text-[11px] font-mono text-slate-400 truncate">
            {health?.ai?.default_model || 'qwen2.5:1.5b'}
          </div>
        </div>

        {/* System Resource Stats (CPU / 8GB RAM) */}
        <div className="px-1 text-[10px] text-slate-400 space-y-1">
          <div className="flex justify-between items-center">
            <span className="flex items-center gap-1">
              <Activity className="w-3 h-3 text-slate-500" /> CPU Load
            </span>
            <span className="font-mono text-slate-300">{cpuPercent}%</span>
          </div>
          <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                cpuPercent > 80 ? 'bg-red-500' : cpuPercent > 50 ? 'bg-amber-400' : 'bg-brand-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(5, cpuPercent))}%` }}
            />
          </div>

          <div className="flex justify-between items-center pt-1">
            <span>Memory (RAM)</span>
            <span className="font-mono text-slate-300">
              {roundMb(memUsedMb)} / 8.0 GB
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};

function roundMb(mb: number): string {
  if (mb > 1024) {
    return (mb / 1024).toFixed(1) + ' GB';
  }
  return mb + ' MB';
}
