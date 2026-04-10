import { motion } from 'framer-motion';
import { Image, FileText, Play, Sparkles, ArrowRight } from 'lucide-react';

interface EmptyViewProps {
  workflowType: 'drawing' | 'document_with_images' | 'manim';
}

const EmptyView: React.FC<EmptyViewProps> = ({ workflowType }) => {
  const config = {
    drawing: {
      icon: Image,
      title: '准备绘制精美图表',
      suggestions: [
        { text: '折线图展示销售趋势', icon: ArrowRight },
        { text: '柱状图对比各品类数据', icon: ArrowRight },
        { text: '散点图分析相关性', icon: ArrowRight },
      ],
      accent: '#06b6d4',
      gradient: 'from-[#06b6d4]/10 via-transparent to-[#3b82f6]/10',
    },
    document_with_images: {
      icon: FileText,
      title: '准备生成结构化文档',
      suggestions: [
        { text: '技术文档与教程', icon: ArrowRight },
        { text: '学术论文与报告', icon: ArrowRight },
        { text: '产品说明与手册', icon: ArrowRight },
      ],
      accent: '#10b981',
      gradient: 'from-[#10b981]/10 via-transparent to-[#06b6d4]/10',
    },
    manim: {
      icon: Play,
      title: '准备制作数学动画',
      suggestions: [
        { text: '函数图像动态绘制', icon: ArrowRight },
        { text: '几何变换动画演示', icon: ArrowRight },
        { text: '数学公式推导过程', icon: ArrowRight },
      ],
      accent: '#f59e0b',
      gradient: 'from-[#f59e0b]/10 via-transparent to-[#f43f5e]/10',
    },
  };

  const { icon: Icon, title, suggestions, accent, gradient } = config[workflowType];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
      className="flex flex-col items-center justify-center h-full px-6 py-8 relative"
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-50`} />

      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
        className="relative mb-6"
      >
        <div 
          className="absolute inset-0 rounded-3xl blur-2xl opacity-40"
          style={{ backgroundColor: accent }}
        />
        <div 
          className="relative w-16 h-16 rounded-2xl flex items-center justify-center
            bg-[rgba(30,41,59,0.8)] backdrop-blur-sm
            border border-[rgba(148,163,184,0.1)]"
        >
          <Icon className="w-8 h-8" style={{ color: accent }} strokeWidth={1.5} />
        </div>
      </motion.div>

      <motion.h3
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        className="text-lg font-semibold text-[#f8fafc] mb-2 relative"
      >
        {title}
      </motion.h3>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25, duration: 0.4 }}
        className="text-[#64748b] text-sm text-center mb-6 relative"
      >
        在上方输入框中描述您的需求，AI 将为您自动生成
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.4 }}
        className="w-full max-w-[280px] space-y-2 relative"
      >
        <div className="flex items-center gap-2 mb-3 px-1">
          <Sparkles className="w-3.5 h-3.5 text-[#64748b]" />
          <span className="text-xs text-[#64748b]">您可以尝试</span>
        </div>

        {suggestions.map((suggestion, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.35 + index * 0.1, duration: 0.3 }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg
              bg-[rgba(30,41,59,0.4)] backdrop-blur-sm
              border border-[rgba(148,163,184,0.08)]
              text-[#94a3b8] text-xs
              hover:bg-[rgba(30,41,59,0.6)]
              hover:border-[rgba(148,163,184,0.15)]
              transition-all duration-200 cursor-default"
          >
            <suggestion.icon className="w-3 h-3 flex-shrink-0" style={{ color: accent }} />
            <span>{suggestion.text}</span>
          </motion.div>
        ))}
      </motion.div>
    </motion.div>
  );
};

export default EmptyView;
