import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
  maxHeight?: string | number;
  className?: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'python',
  showLineNumbers = true,
  maxHeight = '100%',
  className = '',
}) => {
  const [copied, setCopied] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const codeRef = useRef<HTMLPreElement>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  const lines = code.split('\n');

  useEffect(() => {
    if (codeRef.current) {
      codeRef.current.scrollTop = codeRef.current.scrollHeight;
    }
  }, [code]);

  return (
    <div 
      className={`code-block ${className} h-full flex flex-col relative group`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex justify-between items-center mb-2 flex-shrink-0 px-1">
        <span className="text-xs text-[#64748b] font-medium">{language}</span>
        
        <AnimatePresence>
          {(isHovered || copied) && (
            <motion.button
              type="button"
              onClick={handleCopy}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.15 }}
              className="flex items-center gap-1.5 text-xs
                px-2.5 py-1.5 rounded-lg
                bg-[rgba(30,41,59,0.8)] backdrop-blur-md
                border border-[rgba(148,163,184,0.15)]
                text-[#94a3b8] hover:text-[#f8fafc]
                hover:border-[rgba(148,163,184,0.25)]
                hover:bg-[rgba(30,41,59,0.95)]
                transition-all duration-200"
            >
              {copied ? (
                <>
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 15 }}
                  >
                    <Check className="w-3.5 h-3.5 text-[#10b981]" />
                  </motion.div>
                  <span className="text-[#10b981]">已复制</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>复制</span>
                </>
              )}
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      <div className="relative flex-1 min-h-0 rounded-xl overflow-hidden
        bg-[rgba(15,23,42,0.9)]
        border border-[rgba(148,163,184,0.1)]">
        <pre
          ref={codeRef}
          className="m-0 p-4 overflow-auto h-full"
          style={{
            maxHeight,
            fontSize: '13px',
            lineHeight: '1.7',
            fontFamily: '"JetBrains Mono", "Fira Code", "SF Mono", Consolas, Monaco, "Courier New", monospace',
          }}
        >
          <code className="text-[#e2e8f0]">
            {showLineNumbers ? (
              lines.map((line, index) => (
                <div key={index} className="table-row">
                  <span className="table-cell text-[#475569] select-none pr-4 text-right min-w-[3ch]">
                    {(index + 1).toString().padStart(2, ' ')}
                  </span>
                  <span className="table-cell text-[#e2e8f0]">{line || ' '}</span>
                </div>
              ))
            ) : (
              code
            )}
          </code>
        </pre>
      </div>
    </div>
  );
};

export default CodeBlock;
