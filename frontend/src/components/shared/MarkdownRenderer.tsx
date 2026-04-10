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
    <div className={`markdown-preview ${className || ''}`} style={{ padding: '16px', lineHeight: '1.8', color: '#e2e8f0' }}>
      <style>{`
        .markdown-preview {
          color: #e2e8f0;
          word-wrap: break-word;
        }
        .markdown-preview h1, .markdown-preview h2, .markdown-preview h3,
        .markdown-preview h4, .markdown-preview h5, .markdown-preview h6 {
          color: #f1f5f9;
          margin-top: 1.5em;
          margin-bottom: 0.5em;
          font-weight: 600;
        }
        .markdown-preview h1 { font-size: 1.75em; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.3em; }
        .markdown-preview h2 { font-size: 1.5em; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.3em; }
        .markdown-preview h3 { font-size: 1.25em; }
        .markdown-preview p { color: #e2e8f0; margin: 0.8em 0; }
        .markdown-preview ul, .markdown-preview ol { color: #e2e8f0; padding-left: 2em; }
        .markdown-preview li { color: #e2e8f0; margin: 0.3em 0; }
        .markdown-preview strong { color: #f1f5f9; }
        .markdown-preview em { color: #cbd5e1; }
        .markdown-preview a { color: #22d3ee; }
        .markdown-preview a:hover { color: #06b6d4; }
        .markdown-preview blockquote {
          border-left: 3px solid #475569;
          padding-left: 1em;
          margin-left: 0;
          color: #94a3b8;
          background: rgba(255,255,255,0.03);
          padding: 0.5em 1em;
          border-radius: 0 4px 4px 0;
        }
        .markdown-preview hr {
          border: none;
          border-top: 1px solid rgba(255,255,255,0.1);
          margin: 1.5em 0;
        }
        .markdown-preview table {
          border-collapse: collapse;
          width: 100%;
          margin: 1em 0;
        }
        .markdown-preview th, .markdown-preview td {
          border: 1px solid rgba(255,255,255,0.1);
          padding: 0.5em 0.75em;
          text-align: left;
          color: #e2e8f0;
        }
        .markdown-preview th {
          background: rgba(255,255,255,0.05);
          color: #f1f5f9;
          font-weight: 600;
        }
        .markdown-preview tr:nth-child(even) {
          background: rgba(255,255,255,0.02);
        }
        .markdown-preview code {
          color: #7dd3fc;
          background: rgba(255,255,255,0.06);
          padding: 0.15em 0.4em;
          border-radius: 3px;
          font-size: 0.9em;
        }
        .markdown-preview pre {
          background: rgba(0,0,0,0.4) !important;
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 6px;
          padding: 16px;
          overflow: auto;
          margin: 12px 0;
        }
        .markdown-preview pre code {
          color: #e2e8f0;
          background: none;
          padding: 0;
          font-size: 0.875em;
        }
        .markdown-preview img {
          border-radius: 8px;
          margin: 12px 0;
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
      `}</style>
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
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
