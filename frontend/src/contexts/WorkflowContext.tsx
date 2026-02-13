/**
 * WorkflowContext
 * 管理应用的全局工作流状态
 */
import { createContext, useContext, useReducer, useCallback, useMemo } from 'react';
import type { WorkflowType, WorkflowStatus, ModelConfig } from '../types';
import type { ReactNode } from 'react';

// 工作流状态接口
interface WorkflowState {
  currentWorkflow: WorkflowType;
  drawing: WorkflowStatus;
  document_with_images: WorkflowStatus;
  manim: WorkflowStatus;
  modelConfig: ModelConfig & { enable_thinking?: boolean };  // 新增：全局模型配置
}

// Context 接口
interface WorkflowContextValue {
  state: WorkflowState;
  setCurrentWorkflow: (type: WorkflowType) => void;
  updateWorkflowStatus: (type: WorkflowType, status: Partial<WorkflowStatus>) => void;
  clearWorkflow: (type: WorkflowType) => void;
  clearAllWorkflows: () => void;
  setModelConfig: (config: ModelConfig & { enable_thinking?: boolean }) => void;  // 新增：设置模型配置
}

// 初始状态
const createInitialWorkflowStatus = (): WorkflowStatus => ({
  status: 'idle',
  current_step: '',
  steps: [],
  result: undefined,
  error: undefined,
});

// 默认模型配置
const defaultModelConfig: ModelConfig & { enable_thinking?: boolean } = {
  provider: 'deepseek',
  model: 'deepseek-chat',
  supports_reasoning: false,
  enable_thinking: false,
};

const initialState: WorkflowState = {
  currentWorkflow: 'drawing',
  drawing: createInitialWorkflowStatus(),
  document_with_images: createInitialWorkflowStatus(),
  manim: createInitialWorkflowStatus(),
  modelConfig: defaultModelConfig,
};

// Action 类型
type WorkflowAction =
  | { type: 'SET_CURRENT_WORKFLOW'; payload: WorkflowType }
  | { type: 'UPDATE_WORKFLOW_STATUS'; workflowType: WorkflowType; payload: Partial<WorkflowStatus> }
  | { type: 'CLEAR_WORKFLOW'; workflowType: WorkflowType }
  | { type: 'CLEAR_ALL_WORKFLOWS' }
  | { type: 'SET_MODEL_CONFIG'; payload: ModelConfig & { enable_thinking?: boolean } };

// Reducer
function workflowReducer(state: WorkflowState, action: WorkflowAction): WorkflowState {
  switch (action.type) {
    case 'SET_CURRENT_WORKFLOW':
      return {
        ...state,
        currentWorkflow: action.payload,
      };

    case 'UPDATE_WORKFLOW_STATUS':
      return {
        ...state,
        [action.workflowType]: {
          ...state[action.workflowType],
          ...action.payload,
        },
      };

    case 'CLEAR_WORKFLOW':
      return {
        ...state,
        [action.workflowType]: createInitialWorkflowStatus(),
      };

    case 'CLEAR_ALL_WORKFLOWS':
      return {
        ...state,
        drawing: createInitialWorkflowStatus(),
        document_with_images: createInitialWorkflowStatus(),
        manim: createInitialWorkflowStatus(),
      };

    case 'SET_MODEL_CONFIG':
      return {
        ...state,
        modelConfig: action.payload,
      };

    default:
      return state;
  }
}

// Context
const WorkflowContext = createContext<WorkflowContextValue | undefined>(undefined);

// Provider Props
interface WorkflowProviderProps {
  children: ReactNode;
}

/**
 * WorkflowProvider 组件
 */
export function WorkflowProvider({ children }: WorkflowProviderProps) {
  const [state, dispatch] = useReducer(workflowReducer, initialState);

  // 设置当前工作流
  const setCurrentWorkflow = useCallback((type: WorkflowType) => {
    dispatch({ type: 'SET_CURRENT_WORKFLOW', payload: type });
  }, []);

  // 更新工作流状态
  const updateWorkflowStatus = useCallback((workflowType: WorkflowType, status: Partial<WorkflowStatus>) => {
    dispatch({ type: 'UPDATE_WORKFLOW_STATUS', workflowType, payload: status });
  }, []);

  // 清除工作流状态
  const clearWorkflow = useCallback((workflowType: WorkflowType) => {
    dispatch({ type: 'CLEAR_WORKFLOW', workflowType });
  }, []);

  // 清除所有工作流状态
  const clearAllWorkflows = useCallback(() => {
    dispatch({ type: 'CLEAR_ALL_WORKFLOWS' });
  }, []);

  // 设置模型配置
  const setModelConfig = useCallback((config: ModelConfig & { enable_thinking?: boolean }) => {
    dispatch({ type: 'SET_MODEL_CONFIG', payload: config });
  }, []);

  // Context 值
  const value = useMemo<WorkflowContextValue>(
    () => ({
      state,
      setCurrentWorkflow,
      updateWorkflowStatus,
      clearWorkflow,
      clearAllWorkflows,
      setModelConfig,
    }),
    [state, setCurrentWorkflow, updateWorkflowStatus, clearWorkflow, clearAllWorkflows, setModelConfig]
  );

  return <WorkflowContext.Provider value={value}>{children}</WorkflowContext.Provider>;
}

/**
 * useWorkflow Hook
 */
export const useWorkflow = (): WorkflowContextValue => {
  const context = useContext(WorkflowContext);
  if (!context) {
    throw new Error('useWorkflow must be used within WorkflowProvider');
  }
  return context;
};

export default WorkflowProvider;
