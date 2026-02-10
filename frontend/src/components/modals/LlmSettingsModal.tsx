import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { defaultLlmSettings, loadLlmSettings, saveLlmSettings, type LlmMode } from '../../services/llmSettings';

interface Props {
  open: boolean;
  onClose: () => void;
}

const providers = ['openai', 'anthropic', 'gemini', 'deepseek', 'kimi', 'openai_compatible'];

const LlmSettingsModal = ({ open, onClose }: Props) => {
  const [mode, setMode] = useState<LlmMode>(defaultLlmSettings.mode);
  const [provider, setProvider] = useState(defaultLlmSettings.provider);
  const [apiKey, setApiKey] = useState(defaultLlmSettings.apiKey);
  const [baseUrl, setBaseUrl] = useState(defaultLlmSettings.baseUrl);
  const [mainModel, setMainModel] = useState(defaultLlmSettings.mainModel);
  const [graphModel, setGraphModel] = useState(defaultLlmSettings.graphModel);

  useEffect(() => {
    if (!open) return;
    const saved = loadLlmSettings();
    setMode(saved.mode);
    setProvider(saved.provider);
    setApiKey(saved.apiKey);
    setBaseUrl(saved.baseUrl);
    setMainModel(saved.mainModel);
    setGraphModel(saved.graphModel);
  }, [open]);

  if (!open) return null;

  const save = () => {
    saveLlmSettings({ mode, provider, apiKey, baseUrl, mainModel, graphModel });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50 px-4">
      <div className="w-full max-w-xl rounded-xl border border-[#2a303b] bg-[#11161f] text-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-[#2a303b] px-5 py-4">
          <div>
            <h3 className="text-lg font-semibold">LLM Settings</h3>
            <p className="text-xs text-slate-400">Saved in this browser&apos;s localStorage.</p>
          </div>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-white/10"><X size={18} /></button>
        </div>

        <div className="space-y-4 p-5 text-sm">
          <div>
            <label className="mb-1 block text-slate-300">Mode</label>
            <div className="flex gap-2">
              <button onClick={() => setMode('local')} className={`rounded-md px-3 py-2 ${mode === 'local' ? 'bg-primary text-white' : 'bg-[#1b2330] text-slate-300'}`}>Local LLM (Ollama)</button>
              <button onClick={() => setMode('api')} className={`rounded-md px-3 py-2 ${mode === 'api' ? 'bg-primary text-white' : 'bg-[#1b2330] text-slate-300'}`}>API Key Method</button>
            </div>
          </div>

          {mode === 'api' && (
            <>
              <div>
                <label className="mb-1 block text-slate-300">Provider</label>
                <select value={provider} onChange={(e) => setProvider(e.target.value)} className="w-full rounded-md border border-[#2a303b] bg-[#0f141c] px-3 py-2">
                  {providers.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-slate-300">API Key</label>
                <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} type="password" placeholder="Paste API key" className="w-full rounded-md border border-[#2a303b] bg-[#0f141c] px-3 py-2" />
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-slate-300">Main Model</label>
                  <input value={mainModel} onChange={(e) => setMainModel(e.target.value)} placeholder="e.g. gpt-4o-mini" className="w-full rounded-md border border-[#2a303b] bg-[#0f141c] px-3 py-2" />
                </div>
                <div>
                  <label className="mb-1 block text-slate-300">Graph Model</label>
                  <input value={graphModel} onChange={(e) => setGraphModel(e.target.value)} placeholder="e.g. gpt-4o-mini" className="w-full rounded-md border border-[#2a303b] bg-[#0f141c] px-3 py-2" />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-slate-300">Base URL (optional)</label>
                <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="Leave empty for provider default" className="w-full rounded-md border border-[#2a303b] bg-[#0f141c] px-3 py-2" />
              </div>
            </>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t border-[#2a303b] px-5 py-4">
          <button onClick={onClose} className="rounded-md bg-[#1b2330] px-4 py-2 text-slate-300">Cancel</button>
          <button onClick={save} className="rounded-md bg-primary px-4 py-2 text-white">Save</button>
        </div>
      </div>
    </div>
  );
};

export default LlmSettingsModal;
