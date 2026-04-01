import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import 'katex/dist/katex.min.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export default function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={`markdown-preview ${className || ''}`} style={{ padding: '16px', lineHeight: '1.8' }}>
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[
          rehypeRaw,
          [rehypeKatex, { throwOnError: false, strict: false }]
        ]}
        components={{
          img: ({ node, ...props }: any) => (
            <img
              {...props}
              style={{ maxWidth: '100%', height: 'auto' }}
              onError={(e) => { console.error('Image load error:', props.src, e); }}
            />
          ),
          code: ({ node, className, children, ...props }: any) => {
            const isInline = !className || !className.includes('language-');
            if (isInline) {
              return <code className={className} {...props}>{children}</code>;
            }
            return (
              <div style={{ margin: '16px 0' }}>
                <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px', overflow: 'auto' }}>
                  <code className={className} {...props}>{children}</code>
                </pre>
              </div>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
