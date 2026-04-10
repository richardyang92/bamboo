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
        <Tabs.List className="bg-white/5 rounded-full p-1 inline-flex w-fit">
          <Tabs.Trigger
            value="preview"
            className="px-4 py-1.5 text-sm font-medium transition-all duration-200 rounded-full
                       data-[state=inactive]:text-slate-400 data-[state=inactive]:hover:text-slate-300 data-[state=inactive]:hover:bg-white/5
                       data-[state=active]:bg-[#06b6d4] data-[state=active]:text-white data-[state=active]:shadow-md"
          >
            预览
          </Tabs.Trigger>
          <Tabs.Trigger
            value="outline"
            className="px-4 py-1.5 text-sm font-medium transition-all duration-200 rounded-full
                       data-[state=inactive]:text-slate-400 data-[state=inactive]:hover:text-slate-300 data-[state=inactive]:hover:bg-white/5
                       data-[state=active]:bg-[#06b6d4] data-[state=active]:text-white data-[state=active]:shadow-md"
          >
            大纲
          </Tabs.Trigger>
          {hasImages && (
            <Tabs.Trigger
              value="images"
              className="px-4 py-1.5 text-sm font-medium transition-all duration-200 rounded-full
                         data-[state=inactive]:text-slate-400 data-[state=inactive]:hover:text-slate-300 data-[state=inactive]:hover:bg-white/5
                         data-[state=active]:bg-[#06b6d4] data-[state=active]:text-white data-[state=active]:shadow-md"
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
                    className="rounded-xl overflow-hidden border border-white/10 bg-slate-800/50 backdrop-blur-sm hover:scale-[1.02] hover:shadow-xl transition-all duration-200"
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
                      className="image-placeholder hidden w-full h-40 items-center justify-center flex-col bg-slate-900/50 text-slate-400"
                      style={{ display: hasUrl ? 'none' : 'flex' }}
                    >
                      <ImageIcon size={32} className="mb-2 opacity-50" />
                      <span className="text-xs">图片加载失败</span>
                    </div>
                    {img.description && (
                      <p className="p-2 text-xs text-slate-400 line-clamp-3">
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