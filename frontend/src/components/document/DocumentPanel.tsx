import { useMemo } from 'react';
import { ImageIcon } from 'lucide-react';
import * as Tabs from '@radix-ui/react-tabs';
import * as api from '../../services/api';
import WorkflowPanel from '../shared/WorkflowPanel';
import MarkdownRenderer from '../shared/MarkdownRenderer';
import type { WorkflowResult, GeneratedImage } from '../../types';

function DocumentPanel() {
  const renderDocumentResult = (result: WorkflowResult) => {
    const contentWithPaths = useMemo(() => {
      if (!result.content) return '';
      return result.content.replace(/\.\.\/images\//g, '/api/images/');
    }, [result.content]);

    const outlineWithPaths = useMemo(() => {
      if (!result.outline) return '';
      return result.outline.replace(/\.\.\/images\//g, '/api/images/');
    }, [result.outline]);

    const getImageUrl = (img: GeneratedImage): string => {
      if (img.url) return img.url;
      if (img.relative_path) {
        return img.relative_path.replace(/\.\.\/images\//g, '/api/images/');
      }
      if (img.path) {
        const filename = img.path.split(/[\\/]/).pop();
        if (filename) return `/api/images/${filename}`;
      }
      if (img.filename) return `/api/images/${img.filename}`;
      return '';
    };

    const hasImages = result.images && result.images.length > 0;

    return (
      <Tabs.Root defaultValue="preview" className="h-full flex flex-col">
        <Tabs.List className="flex border-b border-[var(--color-border)] shrink-0">
          <Tabs.Trigger
            value="preview"
            className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] data-[state=active]:text-[var(--color-text-primary)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-accent)] transition-colors"
          >
            预览
          </Tabs.Trigger>
          <Tabs.Trigger
            value="outline"
            className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] data-[state=active]:text-[var(--color-text-primary)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-accent)] transition-colors"
          >
            大纲
          </Tabs.Trigger>
          {hasImages && (
            <Tabs.Trigger
              value="images"
              className="px-3 py-1.5 text-sm text-[var(--color-text-secondary)] data-[state=active]:text-[var(--color-text-primary)] data-[state=active]:border-b-2 data-[state=active]:border-[var(--color-accent)] transition-colors"
            >
              图片 ({result.images!.length})
            </Tabs.Trigger>
          )}
        </Tabs.List>

        <Tabs.Content value="preview" className="flex-1 overflow-auto pt-3">
          <MarkdownRenderer content={contentWithPaths} />
        </Tabs.Content>

        <Tabs.Content value="outline" className="flex-1 overflow-auto pt-3">
          <MarkdownRenderer content={outlineWithPaths} />
        </Tabs.Content>

        {hasImages && (
          <Tabs.Content value="images" className="flex-1 overflow-auto pt-3">
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              {result.images!.map((img, idx) => {
                const imageUrl = getImageUrl(img);
                const hasUrl = !!imageUrl;

                return (
                  <div
                    key={idx}
                    className="rounded-md overflow-hidden border border-[var(--color-border)] bg-[var(--color-bg-card)]"
                  >
                    {hasUrl ? (
                      <img
                        src={imageUrl}
                        alt={img.description || ''}
                        className="w-full h-40 object-cover"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          const placeholder = target.parentElement?.querySelector('.image-placeholder');
                          if (placeholder) {
                            (placeholder as HTMLElement).style.display = 'flex';
                          }
                        }}
                      />
                    ) : null}
                    <div
                      className="image-placeholder hidden w-full h-40 items-center justify-center flex-col bg-[var(--color-secondary)] text-[var(--color-text-muted)]"
                      style={{ display: hasUrl ? 'none' : 'flex' }}
                    >
                      <ImageIcon size={32} className="mb-2 opacity-50" />
                      <span className="text-xs">图片加载失败</span>
                    </div>
                    {img.description && (
                      <p className="p-2 text-xs text-[var(--color-text-secondary)] line-clamp-3">
                        {img.description}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </Tabs.Content>
        )}
      </Tabs.Root>
    );
  };

  return (
    <WorkflowPanel
      workflowType="document_with_images"
      apiStart={api.startDocumentWorkflow}
      apiStop={api.stopDocumentWorkflow}
      apiClear={api.clearDocumentHistory}
      placeholder="请输入文档主题，例如：量子力学基础教程"
      startLabel="开始生成"
      runningLabel="生成中..."
      renderResult={renderDocumentResult}
    />
  );
}

export default DocumentPanel;
