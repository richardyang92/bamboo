/**
 * 结果区域占位符组件
 * 当没有结果时显示
 */
import { Image, FileText, Video } from 'lucide-react';

type ResultPlaceholderProps = {
  type: 'drawing' | 'document' | 'manim';
  error?: string | null;
};

function ResultPlaceholder({ type, error }: ResultPlaceholderProps) {
  const config = {
    drawing: {
      icon: <Image className="w-12 h-12 text-gray-400" />,
      description: '生成的图表将显示在这里',
    },
    document: {
      icon: <FileText className="w-12 h-12 text-gray-400" />,
      description: '生成的文档将显示在这里',
    },
    manim: {
      icon: <Video className="w-12 h-12 text-gray-400" />,
      description: '渲染的视频将显示在这里',
    },
  };

  const { icon, description } = config[type];

  return (
    <div>
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="text-red-800 text-sm font-medium">执行出错</div>
          <div className="text-red-600 text-sm mt-1">{error}</div>
        </div>
      )}
      <div className="py-12 text-center">
        <div className="flex justify-center">
          {icon}
        </div>
        <div className="mt-4 text-gray-500 text-sm">
          {description}
        </div>
        <div className="mt-4 text-gray-400 text-xs">
          请在左侧输入需求并点击开始生成
        </div>
      </div>
    </div>
  );
}

export default ResultPlaceholder;
