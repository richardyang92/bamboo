/**
 * 工作流预定义步骤配置
 * 用于在工作流开始前就显示所有步骤
 */

import type { WorkflowStep, WorkflowType } from '../types';

/**
 * 获取指定工作流类型的预定义步骤（全部为 pending 状态）
 */
export const getInitialSteps = (workflowType: WorkflowType): WorkflowStep[] => {
  const now = new Date().toISOString();

  switch (workflowType) {
    case 'drawing':
      return [
        {
          step: 'refine_prompt',
          name: '润色提示词',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'generate_code',
          name: '生成绘图代码',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'execute_code',
          name: '执行绘图代码',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'analyze_execution_result',
          name: '分析执行结果',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'fix_code_with_feedback',
          name: '修复代码',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'save_image',
          name: '验证图片保存',
          status: 'pending',
          timestamp: now,
        },
      ];

    case 'document_with_images':
      return [
        {
          step: 'refine_prompt',
          name: '润色写作需求',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'generate_outline',
          name: '生成文档大纲',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'generate_content',
          name: '生成文档内容',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'identify_image_requests',
          name: '识别图片需求',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'generate_images',
          name: '生成图表',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'embed_images',
          name: '整合图片到文档',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'save_document',
          name: '保存文档',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'verify_document',
          name: '验证文档',
          status: 'pending',
          timestamp: now,
        },
      ];

    case 'manim':
      return [
        {
          step: 'refine_prompt',
          name: '润色动画需求',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'generate_code',
          name: '生成动画代码',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'execute_code',
          name: '渲染动画视频',
          status: 'pending',
          timestamp: now,
        },
        {
          step: 'save_video',
          name: '验证视频保存',
          status: 'pending',
          timestamp: now,
        },
      ];

    default:
      return [];
  }
};

/**
 * 将后端返回的步骤状态合并到预定义步骤中
 * 保持步骤顺序，用后端数据更新状态
 */
export const mergeStepStatus = (
  initialSteps: WorkflowStep[],
  backendSteps: WorkflowStep[]
): WorkflowStep[] => {
  // 创建步骤 ID 到后端步骤的映射
  const backendStepMap = new Map<string, WorkflowStep>();
  for (const step of backendSteps) {
    backendStepMap.set(step.step, step);
  }

  // 使用后端状态更新初始步骤
  return initialSteps.map(step => {
    const backendStep = backendStepMap.get(step.step);
    if (backendStep) {
      // 使用后端返回的状态信息
      return {
        ...step,
        status: backendStep.status,
        timestamp: backendStep.timestamp || step.timestamp,
        completed_at: backendStep.completed_at,
        error: backendStep.error,
        retry_info: backendStep.retry_info,  // 保留重试信息
      };
    }
    // 没有后端数据，保持 pending 状态
    return step;
  });
};
