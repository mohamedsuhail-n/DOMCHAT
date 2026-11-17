import React, { useState, useEffect } from 'react';
import { AppSettingsConfig, SystemHealth } from '../../types';
import { api } from '../../services/api';
import {
  Cpu,
  Zap,
  Save,
  CheckCircle2,
  AlertCircle,
  Play,
  Key,
  Shield,
  Activity,
  Sliders,
  Settings,
  RefreshCw
} from 'lucide-react';

interface SettingsModuleProps {
  health: SystemHealth | null;
  onRefreshHealth: () => void;
}

export const SettingsModule: React.FC<SettingsModuleProps> = ({ health, onRefreshHealth }) => {
  const [config, setConfig] = useState<AppSettingsConfig>({
    default_model: 'qwen2.5:1.5b',
    temperature: 0.7,
    top_p: 0.9,
    max_tokens: 2048,
    system_prompt: '',
    chunk_size: 500,
    chunk_overlap: 50,
    top_k: 4,
    hybrid_alpha: 0.6,
    local_only: true,
    embedding_model: 'all-MiniLM-L6-v2',
    has_openai_key: false,
    has_gemini_key: false,
    has_anthropic_key: false,
  });

  const [openaiKey, setOpenaiKey] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');

  const [loading, setLoading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [testPrompt, setTestPrompt] = useState('Verify that DOMCHAT is operating normally.');
  const [testResponse, setTestResponse] = useState('');
  const [testDuration, setTestDuration] = useState<number | null>(null);
  const [testing, setTesting] = useState(false);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const res = await api.getModels();
      if (res.config) {
        setConfig(res.config);
      }
    } catch (err) {
      console.error('Failed to load settings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const payload: any = { ...config };
      if (openaiKey) payload.openai_api_key = openaiKey;
      if (geminiKey) payload.gemini_api_key = geminiKey;
      if (anthropicKey) payload.anthropic_api_key = anthropicKey;

      await api.updateSettings(payload);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
      onRefreshHealth();
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTestInference = async () => {
    if (!testPrompt.trim()) return;
    try {
      setTesting(true);
      setTestResponse('');
      setTestDuration(null);
      const res = await api.testInference(testPrompt, config.default_model);
      setTestResponse(res.response);
      setTestDuration(res.duration_ms);
    } catch (err: any) {
      setTestResponse(`Inference error: ${err.message}`);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-purple-400" />
            Model Studio & Engine Configuration
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure local Ollama inference, RAG chunking parameters, and hybrid retrieval weights.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-brand-600/30 transition disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          <span>{loading ? 'Saving...' : 'Save Configuration'}</span>
        </button>
      </div>

      {savedSuccess && (
        <div className="p-3 bg-emerald-950/60 border border-emerald-800 text-emerald-200 text-xs rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Configuration saved successfully! Changes are active immediately.</span>
        </div>
      )}

      {/* Ollama Status & Model Selection */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <span className="font-semibold text-sm text-slate-100">Local LLM Engine (Ollama)</span>
          </div>
          <span
            className={`flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${
              health?.ai?.connected ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${health?.ai?.connected ? 'bg-emerald-400' : 'bg-red-400'}`} />
            {health?.ai?.connected ? 'Connected to http://127.0.0.1:11434' : 'Ollama Unreachable'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Active LLM Model
            </label>
            <select
              value={config.default_model}
              onChange={(e) => setConfig({ ...config, default_model: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 outline-none focus:border-brand-500 font-mono"
            >
              <option value="qwen2.5:1.5b">qwen2.5:1.5b (Pre-installed & Optimized)</option>
              {health?.ai?.models?.filter((m) => m !== 'qwen2.5:1.5b').map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <div className="text-[11px] text-slate-500 mt-1">
              Qwen 2.5 1.5B fits comfortably in &lt;1GB RAM and operates rapidly on CPU.
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Embedding Model
            </label>
            <input
              type="text"
              disabled
              value="all-MiniLM-L6-v2 (384 dimensions, CPU optimized)"
              className="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-400 font-mono cursor-not-allowed"
            />
            <div className="text-[11px] text-slate-500 mt-1">
              Singleton memory model with hash caching to prevent duplicate embeddings.
            </div>
          </div>
        </div>

        {/* Local Only Mode Toggle */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <div>
            <div className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              Local-Only Execution Mode
            </div>
            <div className="text-[11px] text-slate-400">
              When enabled, all prompt processing and embeddings remain strictly on your local PC.
            </div>
          </div>
          <button
            type="button"
            onClick={() => setConfig({ ...config, local_only: !config.local_only })}
            className={`w-11 h-6 rounded-full transition-colors relative ${
              config.local_only ? 'bg-emerald-600' : 'bg-slate-700'
            }`}
          >
            <span
              className={`block w-4 h-4 rounded-full bg-white transition-transform ${
                config.local_only ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Generation Parameters */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Sliders className="w-4 h-4 text-brand-400" />
          <span className="font-semibold text-sm text-slate-100">Generation Hyperparameters</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1">
              <span>Temperature</span>
              <span className="font-mono text-brand-300">{config.temperature}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={config.temperature}
              onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
              className="w-full accent-brand-500 cursor-pointer"
            />
            <div className="text-[10px] text-slate-500 mt-1">Lower = deterministic, higher = creative</div>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1">
              <span>Top-P</span>
              <span className="font-mono text-brand-300">{config.top_p}</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={config.top_p}
              onChange={(e) => setConfig({ ...config, top_p: parseFloat(e.target.value) })}
              className="w-full accent-brand-500 cursor-pointer"
            />
            <div className="text-[10px] text-slate-500 mt-1">Nucleus sampling cutoff</div>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1">
              <span>Max Tokens</span>
              <span className="font-mono text-brand-300">{config.max_tokens}</span>
            </div>
            <input
              type="range"
              min="256"
              max="4096"
              step="128"
              value={config.max_tokens}
              onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
              className="w-full accent-brand-500 cursor-pointer"
            />
            <div className="text-[10px] text-slate-500 mt-1">Maximum generated tokens per response</div>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            System Prompt
          </label>
          <textarea
            rows={3}
            value={config.system_prompt}
            onChange={(e) => setConfig({ ...config, system_prompt: e.target.value })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 outline-none focus:border-brand-500 resize-none font-sans"
          />
        </div>
      </div>

      {/* RAG Pipeline Settings */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Settings className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-sm text-slate-100">RAG Chunking & Retrieval Parameters</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Chunk Size (chars)
            </label>
            <input
              type="number"
              min={100}
              max={2000}
              step={50}
              value={config.chunk_size}
              onChange={(e) => setConfig({ ...config, chunk_size: parseInt(e.target.value) || 500 })}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Chunk Overlap (chars)
            </label>
            <input
              type="number"
              min={0}
              max={500}
              step={10}
              value={config.chunk_overlap}
              onChange={(e) => setConfig({ ...config, chunk_overlap: parseInt(e.target.value) || 50 })}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Default Top-K
            </label>
            <input
              type="number"
              min={1}
              max={10}
              value={config.top_k}
              onChange={(e) => setConfig({ ...config, top_k: parseInt(e.target.value) || 4 })}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Hybrid Alpha (Dense Weight)
            </label>
            <input
              type="number"
              min={0}
              max={1}
              step={0.05}
              value={config.hybrid_alpha}
              onChange={(e) => setConfig({ ...config, hybrid_alpha: parseFloat(e.target.value) || 0.6 })}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 outline-none focus:border-brand-500"
            />
          </div>
        </div>
      </div>

      {/* Test Inference Live Playground */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Play className="w-4 h-4 text-brand-400" />
            <span className="font-semibold text-sm text-slate-100">Live Model Benchmark Tester</span>
          </div>
          {testDuration && (
            <span className="text-xs font-mono text-emerald-400">
              Response time: {testDuration} ms
            </span>
          )}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={testPrompt}
            onChange={(e) => setTestPrompt(e.target.value)}
            placeholder="Type a test query..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 outline-none focus:border-brand-500"
          />
          <button
            type="button"
            onClick={handleTestInference}
            disabled={testing || !testPrompt.trim()}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition disabled:opacity-50 flex items-center gap-1.5"
          >
            {testing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>{testing ? 'Testing...' : 'Run Test'}</span>
          </button>
        </div>

        {testResponse && (
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-200 font-mono whitespace-pre-wrap">
            {testResponse}
          </div>
        )}
      </div>

      {/* Optional Cloud Providers */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Key className="w-4 h-4 text-amber-400" />
          <span className="font-semibold text-sm text-slate-100">Optional Cloud Providers</span>
        </div>
        <p className="text-xs text-slate-400">
          Optionally store API keys for cloud models. When local-only mode is active, all prompts use local Ollama.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              OpenAI API Key {config.has_openai_key && <span className="text-emerald-400 font-normal">(Configured)</span>}
            </label>
            <input
              type="password"
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Gemini API Key {config.has_gemini_key && <span className="text-emerald-400 font-normal">(Configured)</span>}
            </label>
            <input
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder="AIzaSy..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Anthropic API Key {config.has_anthropic_key && <span className="text-emerald-400 font-normal">(Configured)</span>}
            </label>
            <input
              type="password"
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              placeholder="sk-ant-..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 outline-none focus:border-brand-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
