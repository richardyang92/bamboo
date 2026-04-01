/**
 * 模型选择器组件 (Tailwind + Radix UI)
 * 支持切换 DeepSeek 和 Ollama 模型
 */
import { useState, useEffect, forwardRef } from 'react';
import * as Select from '@radix-ui/react-select';
import * as Switch from '@radix-ui/react-switch';
import * as Tooltip from '@radix-ui/react-tooltip';
import { Bot, Zap, Lightbulb, ChevronDown, Loader2, Check } from 'lucide-react';
import * as api from '../../services/api';
import { showToast } from '../../services/toast';
import type { LLMProvider, ModelConfig, AvailableModels, ModelInfo } from '../../types';

// 兼容新旧数据格式：将字符串数组或 ModelInfo 数组统一转换为 ModelInfo 数组
const normalizeModels = (models: string[] | ModelInfo[]): ModelInfo[] => {
  if (!models || models.length === 0) return [];

  // 如果第一个元素是字符串，说明是旧格式
  if (typeof models[0] === 'string') {
    return (models as string[]).map(name => ({
      name,
      supports_thinking: false, // 旧格式默认不支持思考
    }));
  }

  // 新格式，直接返回
  return models as ModelInfo[];
};

interface ModelSelectorProps {
  onModelChange?: (config: ModelConfig & { enable_thinking?: boolean }) => void;
  disabled?: boolean;
}

// 默认模型配置（当后端不可用时使用）
// 注意：这是备用配置，实际使用时会从后端 API 获取真实模型列表
const DEFAULT_MODELS: AvailableModels = {
  providers: {
    deepseek: {
      provider: 'deepseek',
      models: [
        { name: 'deepseek-chat', supports_thinking: false },
        { name: 'deepseek-reasoner', supports_thinking: true },
      ],
      supports_reasoning: true,
      current: 'deepseek-chat',
    },
    ollama: {
      provider: 'ollama',
      models: [
        { name: 'deepseek-ocr:latest', supports_thinking: false },
        { name: 'qwen3-vl:8b', supports_thinking: false },
        { name: 'qwen3-coder-next:latest', supports_thinking: false },
        { name: 'gpt-oss:20b', supports_thinking: false },
        { name: 'glm-4.7-flash:latest', supports_thinking: false },
      ],
      supports_reasoning: true,
      current: 'deepseek-ocr:latest',
    },
  },
  current_provider: 'deepseek',
  current_config: {
    provider: 'deepseek',
    model: 'deepseek-chat',
    supports_reasoning: false,
  },
};

// Radix SelectItem needs forwardRef
const SelectItem = forwardRef<
  HTMLDivElement,
  Select.SelectItemProps & { children: React.ReactNode }
>(({ children, ...props }, ref) => (
  <Select.Item
    ref={ref}
    className="relative flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer
               text-[var(--color-text-primary)] rounded-md outline-none
               hover:bg-[var(--color-secondary)] data-[highlighted]:bg-[var(--color-secondary)]
               data-[disabled]:opacity-50 data-[disabled]:pointer-events-none"
    {...props}
  >
    <Select.ItemText>{children}</Select.ItemText>
    <Select.ItemIndicator className="absolute right-2 text-[var(--color-accent)]">
      <Check className="w-3.5 h-3.5" />
    </Select.ItemIndicator>
  </Select.Item>
));
SelectItem.displayName = 'SelectItem';

function ModelSelector({ onModelChange, disabled = false }: ModelSelectorProps) {
  const [models, setModels] = useState<AvailableModels | null>(null);
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [currentProvider, setCurrentProvider] = useState<LLMProvider>('deepseek');
  const [currentModel, setCurrentModel] = useState<string>('deepseek-chat');
  const [loading, setLoading] = useState(false);
  const [enableThinking, setEnableThinking] = useState(false);

  // 根据后端数据判断模型是否支持思考
  const isThinkingModel = (modelName: string): boolean => {
    if (!models) return false;
    const providerConfig = models.providers[currentProvider];
    const modelInfo = providerConfig.models.find(m => m.name === modelName);
    return modelInfo?.supports_thinking ?? false;
  };

  // 加载可用模型
  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const data = await api.getAvailableModels();

      // 验证返回的数据格式
      if (!data || !data.current_provider || !data.current_config || !data.current_config.model) {
        throw new Error('Invalid API response format');
      }

      // 兼容新旧数据格式：如果 models 是字符串数组，转换为 ModelInfo 数组
      const normalizedData: AvailableModels = {
        ...data,
        providers: {
          deepseek: {
            ...data.providers.deepseek,
            models: normalizeModels(data.providers.deepseek.models),
          },
          ollama: {
            ...data.providers.ollama,
            models: normalizeModels(data.providers.ollama.models),
          },
        },
      };

      setModels(normalizedData);
      setCurrentProvider(normalizedData.current_provider);
      setCurrentModel(normalizedData.current_config.model);
      setBackendAvailable(true);
    } catch (err) {
      console.warn('[ModelSelector] 后端不可用，使用默认配置:', err);
      setBackendAvailable(false);
      // 使用默认配置
      setModels(DEFAULT_MODELS);
      setCurrentProvider(DEFAULT_MODELS.current_provider);
      setCurrentModel(DEFAULT_MODELS.current_config.model);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = (provider: string) => {
    const typedProvider = provider as LLMProvider;
    if (!models) return;

    const providerConfig = models.providers[typedProvider];
    setCurrentProvider(typedProvider);
    setCurrentModel(providerConfig.current);

    // 切换提供商时，重置 thinking 模式
    setEnableThinking(false);
  };

  const handleModelChange = async (model: string) => {
    if (!backendAvailable) {
      showToast.warning('后端服务不可用，无法切换模型');
      return;
    }

    if (!currentProvider || !model) {
      showToast.error('模型参数无效');
      return;
    }

    try {
      setLoading(true);
      const result = await api.switchModel(currentProvider, model);

      setCurrentModel(model);

      // 如果新模型不支持 thinking，自动关闭
      if (!isThinkingModel(model)) {
        setEnableThinking(false);
      }

      if (result.success) {
        showToast.success(`已切换到 ${currentProvider} / ${model}`);
        onModelChange?.({
          ...result.current_config,
          enable_thinking: enableThinking && isThinkingModel(model),
        });
      }
    } catch (err) {
      showToast.error('切换模型失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleThinkingChange = (checked: boolean) => {
    setEnableThinking(checked);

    // 通知父组件配置变更
    if (models) {
      const config: ModelConfig & { enable_thinking?: boolean } = {
        provider: currentProvider,
        model: currentModel,
        supports_reasoning: models.providers[currentProvider].supports_reasoning,
        enable_thinking: checked,
      };
      onModelChange?.(config);
    }
  };

  if (!models) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-[var(--color-bg-card)] border border-[var(--color-border)] text-[var(--color-text-muted)] text-sm">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        <span>加载模型中...</span>
      </div>
    );
  }

  const providerConfig = models.providers[currentProvider];
  const availableModels = providerConfig.models;
  const isCurrentModelThinking = isThinkingModel(currentModel);
  const showThinkingToggle = currentProvider === 'ollama' && isCurrentModelThinking;

  return (
    <Tooltip.Provider delayDuration={300}>
      <div className="flex items-center gap-2">
        {/* 标签: 模型 */}
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-500/15 text-blue-400">
          <Bot className="w-3 h-3" />
          模型
        </span>

        {/* 提供商选择 */}
        <Select.Root value={currentProvider} onValueChange={handleProviderChange}>
          <Select.Trigger
            disabled={disabled || loading}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm
                       bg-[var(--color-bg-card)] border border-[var(--color-border)]
                       text-[var(--color-text-primary)]
                       hover:border-[var(--color-text-muted)]
                       focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]
                       disabled:opacity-50 disabled:cursor-not-allowed
                       data-[placeholder]:text-[var(--color-text-muted)]"
            aria-label="选择提供商"
          >
            <Select.Value />
            <Select.Icon>
              <ChevronDown className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
            </Select.Icon>
          </Select.Trigger>

          <Select.Portal>
            <Select.Content
              className="z-50 overflow-hidden rounded-md border border-[var(--color-border)]
                         bg-[var(--color-bg-dark)] shadow-xl"
              position="popper"
              sideOffset={4}
            >
              <Select.Viewport className="p-1">
                <SelectItem value="deepseek">
                  <Zap className="w-3.5 h-3.5 text-[var(--color-text-secondary)]" />
                  <span>DeepSeek</span>
                </SelectItem>
                <SelectItem value="ollama">
                  <Bot className="w-3.5 h-3.5 text-[var(--color-text-secondary)]" />
                  <span>Ollama</span>
                </SelectItem>
              </Select.Viewport>
            </Select.Content>
          </Select.Portal>
        </Select.Root>

        {/* 模型选择 */}
        <Select.Root value={currentModel} onValueChange={handleModelChange}>
          <Select.Trigger
            disabled={disabled || loading}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm
                       bg-[var(--color-bg-card)] border border-[var(--color-border)]
                       text-[var(--color-text-primary)] min-w-[180px]
                       hover:border-[var(--color-text-muted)]
                       focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]
                       disabled:opacity-50 disabled:cursor-not-allowed
                       data-[placeholder]:text-[var(--color-text-muted)]"
            aria-label="选择模型"
          >
            {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <Select.Value />
            <Select.Icon>
              <ChevronDown className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
            </Select.Icon>
          </Select.Trigger>

          <Select.Portal>
            <Select.Content
              className="z-50 overflow-hidden rounded-md border border-[var(--color-border)]
                         bg-[var(--color-bg-dark)] shadow-xl"
              position="popper"
              sideOffset={4}
            >
              <Select.Viewport className="p-1">
                {availableModels
                  .filter(m => m && m.name)
                  .map(modelInfo => (
                    <SelectItem key={modelInfo.name} value={modelInfo.name}>
                      <span>{modelInfo.name}</span>
                      {/* 识别思考模型：根据后端返回的能力信息判断 */}
                      {modelInfo.supports_thinking && (
                        <span className="ml-1 px-1 py-px rounded text-[10px] font-medium bg-purple-500/20 text-purple-400">
                          推理
                        </span>
                      )}
                    </SelectItem>
                  ))}
              </Select.Viewport>
            </Select.Content>
          </Select.Portal>
        </Select.Root>

        {/* Thinking 模式开关 - 仅在 Ollama 推理模型时显示 */}
        {showThinkingToggle && (
          <Tooltip.Root>
            <Tooltip.Trigger asChild>
              <div className="flex items-center gap-1.5">
                <Lightbulb
                  className={`w-3.5 h-3.5 ${enableThinking ? 'text-purple-400' : 'text-[var(--color-text-muted)]'}`}
                />
                <Switch.Root
                  checked={enableThinking}
                  onCheckedChange={handleThinkingChange}
                  disabled={disabled || loading}
                  className="relative h-4 w-8 rounded-full cursor-pointer
                             bg-[var(--color-secondary)] data-[state=checked]:bg-purple-600
                             disabled:opacity-50 disabled:cursor-not-allowed
                             transition-colors"
                >
                  <Switch.Thumb
                    className="block h-3 w-3 rounded-full bg-white shadow-sm
                               translate-x-0.5 data-[state=checked]:translate-x-[18px]
                               transition-transform"
                  />
                </Switch.Root>
                <span className="text-[10px] text-[var(--color-text-muted)]">
                  {enableThinking ? 'Thinking' : 'Normal'}
                </span>
              </div>
            </Tooltip.Trigger>
            <Tooltip.Portal>
              <Tooltip.Content
                className="z-50 px-2.5 py-1 rounded-md text-xs
                           bg-[var(--color-bg-dark)] border border-[var(--color-border)]
                           text-[var(--color-text-secondary)] shadow-lg"
                sideOffset={6}
              >
                启用后显示模型推理过程
                <Tooltip.Arrow className="fill-[var(--color-border)]" />
              </Tooltip.Content>
            </Tooltip.Portal>
          </Tooltip.Root>
        )}

        {/* 功能标识 */}
        {providerConfig.supports_reasoning && isCurrentModelThinking && (
          <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-purple-500/20 text-purple-400">
            思考模式
          </span>
        )}
        {currentProvider === 'ollama' && (
          <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-green-500/20 text-green-400">
            本地
          </span>
        )}
        {!backendAvailable && (
          <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-orange-500/20 text-orange-400">
            离线
          </span>
        )}
      </div>
    </Tooltip.Provider>
  );
}

export default ModelSelector;
