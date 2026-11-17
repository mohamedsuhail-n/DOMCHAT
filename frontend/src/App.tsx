import React, { useState, useEffect } from 'react';
import { Project, SystemHealth, Conversation, DocumentItem, WebsiteItem } from './types';
import { api } from './services/api';
import { Sidebar, ActiveTab } from './components/Sidebar';
import { ProjectModal } from './components/ProjectModal';
import { DashboardModule } from './modules/dashboard/DashboardModule';
import { AssistantModule } from './modules/assistant/AssistantModule';
import { DocumentModule } from './modules/documents/DocumentModule';
import { DomainModule } from './modules/domain/DomainModule';
import { KnowledgeModule } from './modules/knowledge/KnowledgeModule';
import { SettingsModule } from './modules/settings/SettingsModule';

export function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);

  // Data for active project
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [websites, setWebsites] = useState<WebsiteItem[]>([]);
  const [selectedConvForChat, setSelectedConvForChat] = useState<Conversation | null>(null);

  // Modals & UI State
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);

  // Apply dark class to html
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  // Load health and projects on mount
  const refreshHealth = async () => {
    try {
      const h = await api.getHealth();
      setHealth(h);
    } catch (err) {
      console.warn('Health check failed', err);
    }
  };

  const loadProjects = async () => {
    try {
      const res = await api.listProjects();
      setProjects(res.projects);
      if (!activeProject && res.projects.length > 0) {
        setActiveProject(res.projects[0]);
      }
    } catch (err) {
      console.error('Failed to load projects', err);
    }
  };

  useEffect(() => {
    refreshHealth();
    loadProjects();
    const interval = setInterval(refreshHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Load project-scoped data
  const loadProjectData = async (projId: string) => {
    try {
      const [convsRes, docsRes, sitesRes] = await Promise.all([
        api.listConversations(projId),
        api.listDocuments(projId),
        api.listWebsites(projId)
      ]);
      setConversations(convsRes.conversations);
      setDocuments(docsRes.documents);
      setWebsites(sitesRes.websites);
    } catch (err) {
      console.error('Failed to load project data', err);
    }
  };

  useEffect(() => {
    if (activeProject) {
      loadProjectData(activeProject.id);
    }
  }, [activeProject]);

  const handleCreateProject = async (name: string, description: string) => {
    const res = await api.createProject(name, description);
    setProjects([res.project, ...projects]);
    setActiveProject(res.project);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans antialiased">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          if (activeProject) loadProjectData(activeProject.id);
        }}
        projects={projects}
        activeProject={activeProject}
        onSelectProject={(p) => setActiveProject(p)}
        onOpenNewProject={() => setIsProjectModalOpen(true)}
        health={health}
        isDarkMode={isDarkMode}
        onToggleTheme={() => setIsDarkMode(!isDarkMode)}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {activeProject ? (
          <>
            {activeTab === 'dashboard' && (
              <DashboardModule
                project={activeProject}
                health={health}
                conversations={conversations}
                documents={documents}
                websites={websites}
                onNavigate={(tab) => setActiveTab(tab)}
                onSelectConversation={(c) => {
                  setSelectedConvForChat(c);
                  setActiveTab('assistant');
                }}
              />
            )}

            {activeTab === 'assistant' && (
              <AssistantModule
                project={activeProject}
                initialConversation={selectedConvForChat}
                documents={documents}
                websites={websites}
                onConversationCreated={() => loadProjectData(activeProject.id)}
              />
            )}

            {activeTab === 'documents' && (
              <DocumentModule
                project={activeProject}
                documents={documents}
                onRefresh={() => loadProjectData(activeProject.id)}
                onNavigate={(tab) => setActiveTab(tab)}
              />
            )}

            {activeTab === 'domain' && (
              <DomainModule
                project={activeProject}
                websites={websites}
                onRefresh={() => loadProjectData(activeProject.id)}
                onNavigate={(tab) => setActiveTab(tab)}
              />
            )}

            {activeTab === 'knowledge' && (
              <KnowledgeModule
                project={activeProject}
                onRefresh={() => loadProjectData(activeProject.id)}
              />
            )}

            {activeTab === 'settings' && (
              <SettingsModule
                health={health}
                onRefreshHealth={refreshHealth}
              />
            )}
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
            Loading workspaces...
          </div>
        )}
      </main>

      {/* New Project Modal */}
      <ProjectModal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        onCreate={handleCreateProject}
      />
    </div>
  );
}

export default App;
