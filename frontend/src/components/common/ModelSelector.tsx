/**
 * 模型选择器组件
 * 支持切换 DeepSeek 和 Ollama 模型
 */
import { useState, useEffect } from 'react';
import { Select, Space, Tag, message, Switch, Tooltip } from 'antd';
import { RobotOutlined, ThunderboltOutlined, BulbOutlined } from '@ant-design/icons';
import * as api from '../../services/api';
import type { LLMProvider, ModelConfig, AvailableModels } from '../../types';

const { Option } = Select;

interface ModelSelectorProps {
  onModelChange?: (config: ModelConfig & { enable_thinking?: boolean }) => void;
  disabled?: boolean;
  size?: 'small' | 'middle' | 'large';
}

// 判断模型是否为思考模型
const isThinkingModel = (model: string): boolean => {
  const modelLower = model.toLowerCase();
  return (
    modelLower.includes('reasoner') ||
    modelLower.includes('deepseek-r1') ||
    modelLower.includes('qwen3') ||
    modelLower.includes('glm4') ||
    modelLower.includes('glm-4') ||
    modelLower.includes('gpt-oss')
  );
};

// 默认模型配置（当后端不可用时使用）
// 注意：这是备用配置，实际使用时会从后端 API 获取真实模型列表
const DEFAULT_MODELS: AvailableModels = {
  providers: {
    deepseek: {
      provider: 'deepseek',
      models: ['deepseek-chat', 'deepseek-reasoner'],
      supports_reasoning: true,
      current: 'deepseek-chat'
    },
    ollama: {
      provider: 'ollama',
      models: [
        'deepseek-ocr:latest',
        'qwen3-vl:8b',
        'qwen3-coder-next:latest',
        'gpt-oss:20b',
        'glm-4.7-flash:latest'
      ],
      supports_reasoning: true,
      current: 'deepseek-ocr:latest'
    }
  },
  current_provider: 'deepseek',
  current_config: {
    provider: 'deepseek',
    model: 'deepseek-chat',
    supports_reasoning: false
  }
};

function ModelSelector({ onModelChange, disabled = false, size = 'middle' }: ModelSelectorProps) {
  const [models, setModels] = useState<AvailableModels | null>(null);
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [currentProvider, setCurrentProvider] = useState<LLMProvider>('deepseek');
  const [currentModel, setCurrentModel] = useState<string>('deepseek-chat');
  const [loading, setLoading] = useState(false);
  const [enableThinking, setEnableThinking] = useState(false);

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

      setModels(data);
      setCurrentProvider(data.current_provider);
      setCurrentModel(data.current_config.model);
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

  const handleProviderChange = (provider: LLMProvider) => {
    if (!models) return;

    const providerConfig = models.providers[provider];
    setCurrentProvider(provider);
    setCurrentModel(providerConfig.current);

    // 切换提供商时，重置 thinking 模式
    setEnableThinking(false);
  };

  const handleModelChange = async (model: string) => {
    if (!backendAvailable) {
      message.warning('后端服务不可用，无法切换模型');
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
        message.success(`已切换到 ${currentProvider} / ${model}`);
        onModelChange?.({
          ...result.current_config,
          enable_thinking: enableThinking && isThinkingModel(model)
        });
      }
    } catch (err) {
      message.error('切换模型失败');
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
        enable_thinking: checked
      };
      onModelChange?.(config);
    }
  };

  if (!models) {
    return <Select loading={loading} disabled placeholder="加载模型中..." size={size} />;
  }

  const providerConfig = models.providers[currentProvider];
  const availableModels = providerConfig.models;
  const isCurrentModelThinking = isThinkingModel(currentModel);
  const showThinkingToggle = currentProvider === 'ollama' && isCurrentModelThinking;

  return (
    <Space size="small">
      <Tag icon={<RobotOutlined />} color="blue">
        模型
      </Tag>

      {/* 提供商选择 */}
      <Select
        value={currentProvider}
        onChange={handleProviderChange}
        disabled={disabled || loading}
        style={{ width: 110 }}
        size={size}
      >
        <Option value="deepseek">
          <Space size="small">
            <ThunderboltOutlined />
            <span>DeepSeek</span>
          </Space>
        </Option>
        <Option value="ollama">
          <Space size="small">
            <RobotOutlined />
            <span>Ollama</span>
          </Space>
        </Option>
      </Select>

      {/* 模型选择 */}
      <Select
        value={currentModel}
        onChange={handleModelChange}
        disabled={disabled || loading}
        loading={loading}
        style={{ width: 160 }}
        size={size}
      >
        {availableModels.map(model => (
          <Option key={model} value={model}>
            <Space size="small">
              <span>{model}</span>
              {/* 识别思考模型：DeepSeek reasoner、Ollama 的思考模型等 */}
              {isThinkingModel(model) && (
                <Tag color="purple" style={{ marginLeft: 4, fontSize: '10px' }}>
                  推理
                </Tag>
              )}
            </Space>
          </Option>
        ))}
      </Select>

      {/* Thinking 模式开关 - 仅在 Ollama 推理模型时显示 */}
      {showThinkingToggle && (
        <Tooltip title="启用后显示模型推理过程">
          <Space size="small" style={{ display: 'inline-flex', alignItems: 'center' }}>
            <BulbOutlined style={{ color: enableThinking ? '#722ed1' : '#999' }} />
            <Switch
              checked={enableThinking}
              onChange={handleThinkingChange}
              disabled={disabled || loading}
              size="small"
              checkedChildren="Thinking"
              unCheckedChildren="Normal"
            />
          </Space>
        </Tooltip>
      )}

      {/* 功能标识 */}
      {providerConfig.supports_reasoning && isThinkingModel(currentModel) && (
        <Tag color="purple" style={{ fontSize: '11px' }}>思考模式</Tag>
      )}
      {currentProvider === 'ollama' && (
        <Tag color="green" style={{ fontSize: '11px' }}>本地</Tag>
      )}
      {!backendAvailable && (
        <Tag color="orange" style={{ fontSize: '11px' }}>离线</Tag>
      )}
    </Space>
  );
}

export default ModelSelector;
