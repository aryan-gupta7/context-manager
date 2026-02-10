export type LlmMode = 'local' | 'api';

export interface LlmSettings {
  mode: LlmMode;
  provider: string;
  apiKey: string;
  baseUrl: string;
  mainModel: string;
  graphModel: string;
}

const STORAGE_KEY = 'fractal.llm.settings';

export const defaultLlmSettings: LlmSettings = {
  mode: 'local',
  provider: 'openai',
  apiKey: '',
  baseUrl: '',
  mainModel: '',
  graphModel: '',
};

export function loadLlmSettings(): LlmSettings {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return defaultLlmSettings;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<LlmSettings>;
    return {
      ...defaultLlmSettings,
      ...parsed,
    };
  } catch {
    return defaultLlmSettings;
  }
}

export function saveLlmSettings(settings: LlmSettings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}
