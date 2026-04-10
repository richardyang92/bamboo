import { motion } from 'framer-motion';
import { Image, FileText, Video, Sparkles, AlertCircle } from 'lucide-react';

type ResultPlaceholderProps = {
  type: 'drawing' | 'document' | 'manim';
  error?: string | null;
};

function ResultPlaceholder({ type, error }: ResultPlaceholderProps) {
  const config = {
    drawing: {
      icon: Image,
      title: '等待生成图表',
      description: '输入绘图需求后，AI 将为您生成精美的数据可视化图表',
      hint: '开始生成',
      gradient: 'from-[#06b6d4]/20 to-[#3b82f6]/20',
    },
    document: {
      icon: FileText,
      title: '等待生成文档',
      description: '输入文档主题后，AI 将为您生成结构化的 Markdown 文档',
      hint: '开始生成',
      gradient: 'from-[#10b981]/20 to-[#06b6d4]/20',
    },
    manim: {
      icon: Video,
      title: '等待生成动画',
      description: '输入动画需求后，AI 将为您生成数学教学动画视频',
      hint: '开始生成',
      gradient: 'from-[#f59e0b]/20 to-[#f43f5e]/20',
    },
  };

  const { icon: Icon, title, description, hint, gradient } = config[type];

  return (
    <div className="relative h-full flex flex-col">
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-4 rounded-xl
            bg-[rgba(244,63,94,0.1)] backdrop-blur-sm
            border border-[rgba(244,63,94,0.2)]"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-[#f43f5e] flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-[#f43f5e] text-sm font-medium">执行出错</div>
              <div className="text-[#94a3b8] text-sm mt-1 leading-relaxed">{error}</div>
            </div>
          </div>
        </motion.div>
      )}

      <div className="flex-1 flex items-center justify-center relative overflow-hidden">
        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(148,163,184,0.3) 1px, transparent 1px),
              linear-gradient(90deg, rgba(148,163,184,0.3) 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
          }}
        />

        <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-50`} />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
          className="relative z-10 text-center px-8"
        >
          <motion.div
            className="relative inline-flex items-center justify-center mb-6"
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${gradient} blur-2xl opacity-60`} />
            
            <div className="relative w-20 h-20 rounded-2xl
              bg-[rgba(30,41,59,0.7)] backdrop-blur-xl
              border border-[rgba(148,163,184,0.1)]
              flex items-center justify-center
              shadow-xl shadow-[rgba(6,182,212,0.1)]">
              <Icon className="w-10 h-10 text-[#06b6d4]" strokeWidth={1.5} />
            </div>
          </motion.div>

          <motion.h3
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="text-xl font-semibold text-[#f8fafc] mb-2"
          >
            {title}
          </motion.h3>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            className="text-[#94a3b8] text-sm max-w-xs mx-auto mb-6 leading-relaxed"
          >
            {description}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full
              bg-[rgba(6,182,212,0.1)] backdrop-blur-sm
              border border-[rgba(6,182,212,0.2)]
              text-[#06b6d4] text-sm"
          >
            <Sparkles className="w-4 h-4" />
            <span>点击「{hint}」开始创作</span>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

export default ResultPlaceholder;
