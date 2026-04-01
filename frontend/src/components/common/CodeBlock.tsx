/**
 * CodeBlock - 代码块展示组件
 * 支持语法高亮、行号显示、复制功能
 */
import React, { useRef, useEffect } from 'react';
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
  const [copied, setCopied] = React.useState(false);
  const codeRef = useRef<HTMLPreElement>(null);

  // 复制到剪贴板
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  // 计算行号
  const lines = code.split('\n');

  // 自动滚动到底部（用于流式内容）
  useEffect(() => {
    if (codeRef.current) {
      codeRef.current.scrollTop = codeRef.current.scrollHeight;
    }
  }, [code]);

  return (
    <div className={`code-block ${className} h-full flex flex-col`}>
      <div className="flex justify-between items-center mb-2 flex-shrink-0">
        <span className="text-xs text-gray-500">{language}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              已复制
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              复制
            </>
          )}
        </button>
      </div>
      <pre
        ref={codeRef}
        className="m-0 p-3 bg-gray-100 rounded-md overflow-auto"
        style={{
          maxHeight,
          fontSize: '13px',
          lineHeight: '1.6',
          fontFamily: 'var(--font-mono), Consolas, Monaco, "Courier New", monospace',
          flex: 1,
          minHeight: 0,
        }}
      >
        <code>
          {showLineNumbers ? (
            lines.map((line, index) => (
              <div key={index}>
                <span className="text-gray-400 select-none mr-3">
                  {(index + 1).toString().padStart(3, ' ')}
                </span>
                <span>{line || ' '}</span>
              </div>
            ))
          ) : (
            code
          )}
        </code>
      </pre>
    </div>
  );
};

export default CodeBlock;
