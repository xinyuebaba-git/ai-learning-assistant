import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { settingsApi } from '../api'

const ASR_ENGINES = [
  { value: 'faster-whisper', label: 'Faster-Whisper (推荐)' },
  { value: 'whisper', label: 'Whisper (OpenAI)' },
  { value: 'deepgram', label: 'Deepgram (云端 API)' },
]

const ASR_MODELS = {
  'faster-whisper': [
    { value: 'tiny', label: 'Tiny (最快，精度低)' },
    { value: 'base', label: 'Base (快，精度较低)' },
    { value: 'small', label: 'Small (平衡)' },
    { value: 'medium', label: 'Medium (推荐)' },
    { value: 'large-v3', label: 'Large-v3 (最慢，精度最高)' },
    { value: 'turbo', label: 'Turbo (优化版)' },
  ],
  'whisper': [
    { value: 'tiny', label: 'Tiny' },
    { value: 'base', label: 'Base' },
    { value: 'small', label: 'Small' },
    { value: 'medium', label: 'Medium' },
    { value: 'large', label: 'Large' },
    { value: 'turbo', label: 'Turbo' },
  ],
}

const LLM_BACKENDS = [
  { value: 'local', label: '本地 Ollama (免费)' },
  { value: 'deepseek', label: 'DeepSeek (云端)' },
  { value: 'openai', label: 'OpenAI (云端)' },
  { value: 'alibaba', label: '阿里百炼 (云端)' },
]

const ALIBABA_CODING_PLAN_MODELS = [
  { value: 'qwen3.5', label: 'Qwen 3.5 (推荐)' },
  { value: 'qwen3', label: 'Qwen 3' },
  { value: 'qwen2.5-coder', label: 'Qwen 2.5 Coder' },
  { value: 'qwen2.5', label: 'Qwen 2.5' },
]

const LOCAL_MODELS = [
  { value: 'qwen2.5:7b', label: 'Qwen2.5 7B (推荐)' },
  { value: 'qwen2.5:14b', label: 'Qwen2.5 14B' },
  { value: 'dolphin3:8b', label: 'Dolphin3 8B' },
  { value: 'dolphin3:latest', label: 'Dolphin3 Latest' },
  { value: 'huihui_ai/dolphin3-abliterated', label: 'Dolphin3 Abliterated' },
]

export default function SettingsPage() {
  // 配置状态
  const [settings, setSettings] = useState({
    asr_engine: 'faster-whisper',
    asr_model: 'medium',
    deepgram_api_key: '',
    llm_backend: 'local',
    llm_model: 'qwen3.5',
    ollama_base_url: 'http://localhost:11434',
    deepseek_api_key: '',
    openai_api_key: '',
    alibaba_api_key: '',
    alibaba_base_url: 'https://coding.dashscope.aliyuncs.com/v1',
    max_segment_duration: 2.2,
    max_segment_chars: 28,
  })

  const [saved, setSaved] = useState(false)

  // 从后端加载配置
  const { data: loadedSettings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.get().then(res => res.data),
  })

  useEffect(() => {
    if (loadedSettings) {
      setSettings(loadedSettings)
    }
  }, [loadedSettings])

  // 保存配置到后端
  const saveMutation = useMutation({
    mutationFn: async (newSettings: any) => {
      const response = await settingsApi.save(newSettings)
      return response.data
    },
    onSuccess: () => {
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    },
  })

  const handleSave = () => {
    saveMutation.mutate(settings)
  }

  const handleChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">⚙️ 系统设置</h1>

      {/* 保存提示 */}
      {saved && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <p className="text-green-800">✅ 配置已保存！</p>
        </div>
      )}

      {/* ASR 设置 */}
      <div className="mb-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">🎤 ASR 语音识别设置</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ASR 引擎
            </label>
            <select
              value={settings.asr_engine}
              onChange={(e) => handleChange('asr_engine', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {ASR_ENGINES.map(engine => (
                <option key={engine.value} value={engine.value}>
                  {engine.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ASR 模型
            </label>
            <select
              value={settings.asr_model}
              onChange={(e) => handleChange('asr_model', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {settings.asr_engine === 'deepgram' ? (
                <>
                  <option value="nova-3">Nova-3 (最快，推荐)</option>
                  <option value="nova-2">Nova-2 (平衡)</option>
                  <option value="enhanced">Enhanced (增强版)</option>
                  <option value="base">Base (基础版)</option>
                </>
              ) : (
                ASR_MODELS[settings.asr_engine as keyof typeof ASR_MODELS]?.map(model => (
                  <option key={model.value} value={model.value}>
                    {model.label}
                  </option>
                ))
              )}
            </select>
            <p className="mt-1 text-sm text-gray-500">
              {settings.asr_engine === 'deepgram' 
                ? 'Deepgram 云端模型，速度极快，按使用量付费'
                : '模型越大精度越高，但速度越慢'}
            </p>
          </div>

          {settings.asr_engine === 'deepgram' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Deepgram API Key
              </label>
              <input
                type="password"
                value={settings.deepgram_api_key}
                onChange={(e) => handleChange('deepgram_api_key', e.target.value)}
                placeholder="dg-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                在 <a href="https://console.deepgram.com/" target="_blank" className="text-primary-600 hover:underline">Deepgram 控制台</a> 获取 API Key
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              最大分段时长（秒）
            </label>
            <input
              type="number"
              step="0.1"
              value={settings.max_segment_duration}
              onChange={(e) => handleChange('max_segment_duration', parseFloat(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              建议 1.6-2.2 秒，更短的字幕更易读
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              最大分段字符数
            </label>
            <input
              type="number"
              value={settings.max_segment_chars}
              onChange={(e) => handleChange('max_segment_chars', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              建议 24-28 个字符
            </p>
          </div>
        </div>
      </div>

      {/* LLM 设置 */}
      <div className="mb-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">🧠 LLM 大模型设置</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              LLM 后端
            </label>
            <select
              value={settings.llm_backend}
              onChange={(e) => handleChange('llm_backend', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {LLM_BACKENDS.map(backend => (
                <option key={backend.value} value={backend.value}>
                  {backend.label}
                </option>
              ))}
            </select>
          </div>

          {settings.llm_backend === 'local' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                本地模型
              </label>
              <select
                value={settings.llm_model}
                onChange={(e) => handleChange('llm_model', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {LOCAL_MODELS.map(model => (
                  <option key={model.value} value={model.value}>
                    {model.label}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-sm text-gray-500">
                需要先在 Ollama 中拉取模型：`ollama pull {settings.llm_model}`
              </p>
            </div>
          ) : settings.llm_backend === 'alibaba' ? (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  模型名称
                </label>
                <select
                  value={settings.llm_model}
                  onChange={(e) => handleChange('llm_model', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  {ALIBABA_CODING_PLAN_MODELS.map(model => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-sm text-gray-500">
                  Coding Plan 支持的模型，默认 qwen3.5
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  value={settings.alibaba_api_key}
                  onChange={(e) => handleChange('alibaba_api_key', e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  在 <a href="https://bailian.console.aliyun.com/" target="_blank" className="text-primary-600 hover:underline">阿里百炼控制台</a> 获取 API Key
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Base URL
                </label>
                <input
                  type="text"
                  value={settings.alibaba_base_url}
                  onChange={(e) => handleChange('alibaba_base_url', e.target.value)}
                  placeholder="https://coding.dashscope.aliyuncs.com/v1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  <a href="https://help.aliyun.com/zh/model-studio/coding-plan-quickstart" target="_blank" className="text-primary-600 hover:underline">
                    阿里百炼 Coding Plan 专用地址：https://coding.dashscope.aliyuncs.com/v1
                  </a>
                </p>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  模型名称
                </label>
                <input
                  type="text"
                  value={settings.llm_model}
                  onChange={(e) => handleChange('llm_model', e.target.value)}
                  placeholder={settings.llm_backend === 'deepseek' ? 'deepseek-chat' : 'gpt-4.1-mini'}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  value={settings.llm_backend === 'deepseek' ? settings.deepseek_api_key : settings.openai_api_key}
                  onChange={(e) => handleChange(
                    settings.llm_backend === 'deepseek' ? 'deepseek_api_key' : 'openai_api_key',
                    e.target.value
                  )}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </>
          )}

          {settings.llm_backend === 'local' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ollama 服务地址
              </label>
              <input
                type="text"
                value={settings.ollama_base_url}
                onChange={(e) => handleChange('ollama_base_url', e.target.value)}
                placeholder="http://localhost:11434"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="mt-1 text-sm text-gray-500">
                默认：http://localhost:11434
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 保存按钮 */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saveMutation.isPending}
          className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
        >
          {saveMutation.isPending ? '保存中...' : '💾 保存配置'}
        </button>
      </div>

      {/* 使用说明 */}
      <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-md">
        <h3 className="font-semibold text-blue-900 mb-2">📖 使用说明</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• ASR 引擎用于语音识别生成字幕</li>
          <li>• LLM 后端用于生成课程总结和知识点</li>
          <li>• 本地 Ollama 免费但需要下载模型</li>
          <li>• 云端 API 效果更好但需要付费</li>
          <li>• 配置保存后，新处理的视频会使用新设置</li>
        </ul>
      </div>
    </div>
  )
}
