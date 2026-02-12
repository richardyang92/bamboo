/**
 * CodeBlock - 代码块展示组件
 * 支持语法高亮、行号显示、复制功能
 */
import React, { useRef, useEffect } from 'react';
import { Button } from 'antd';
import { CopyOutlined, CheckOutlined } from '@ant-design/icons';

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
    <div className={`code-block ${className}`} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexShrink: 0 }}>
        <span style={{ fontSize: '12px', color: '#888' }}>{language}</span>
        <Button
          type="text"
          size="small"
          icon={copied ? <CheckOutlined /> : <CopyOutlined />}
          onClick={handleCopy}
          style={{ fontSize: '12px' }}
        >
          {copied ? '已复制' : '复制'}
        </Button>
      </div>
      <pre
        ref={codeRef}
        style={{
          margin: 0,
          padding: '12px',
          background: '#f5f5f5',
          borderRadius: '4px',
          overflow: 'auto',
          maxHeight,
          fontSize: '13px',
          lineHeight: '1.6',
          fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
          flex: 1,
          minHeight: 0,
        }}
      >
        <code>
          {showLineNumbers ? (
            lines.map((line, index) => (
              <div key={index}>
                <span style={{ color: '#999', userSelect: 'none', marginRight: '12px' }}>
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
