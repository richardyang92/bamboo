/**
 * 历史记录页面
 */
import { Card, List, Tag, Button, Empty, message, Modal } from 'antd';
import { DeleteOutlined, PictureOutlined, FileTextOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { useWorkflowHistory } from '../hooks/useWorkflowHistory';
import { useState } from 'react';
import PreviewModal from '../components/PreviewModal';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';
import type { HistoryItem } from '../types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

function HistoryPage() {
  const { history, loading, error, deleteItem } = useWorkflowHistory();
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewItem, setPreviewItem] = useState<HistoryItem | null>(null);

  const handlePreview = (item: HistoryItem) => {
    setPreviewItem(item);
    setPreviewModalVisible(true);
  };

  const handlePreviewClose = () => {
    setPreviewModalVisible(false);
    setPreviewItem(null);
  };

  const handleDelete = (type: string, filename: string) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除 "${filename}" 吗？`,
      onOk: async () => {
        try {
          await deleteItem(type, filename);
          message.success('删除成功');
        } catch (err) {
          message.error(err instanceof Error ? err.message : '删除失败');
        }
      },
    });
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <PictureOutlined style={{ fontSize: '24px', color: '#1890ff' }} />;
      case 'document':
        return <FileTextOutlined style={{ fontSize: '24px', color: '#52c41a' }} />;
      case 'video':
        return <VideoCameraOutlined style={{ fontSize: '24px', color: '#ff4d4f' }} />;
      default:
        return null;
    }
  };

  const getTypeTag = (type: string) => {
    switch (type) {
      case 'image':
        return <Tag color="blue">图片</Tag>;
      case 'document':
        return <Tag color="green">文档</Tag>;
      case 'video':
        return <Tag color="red">视频</Tag>;
      default:
        return <Tag>未知</Tag>;
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  if (error) {
    return (
      <Card>
        <Empty description={`加载失败: ${error}`} />
      </Card>
    );
  }

  return (
    <>
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Card
          title="历史记录"
          loading={loading}
          styles={{ body: { flex: 1, overflow: 'auto', padding: '24px' } }}
          style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
        >
          {history.length === 0 && !loading ? (
            <Empty description="暂无历史记录" />
          ) : (
            <List
              itemLayout="horizontal"
              dataSource={history}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      danger
                      type="text"
                      icon={<DeleteOutlined />}
                      onClick={() => handleDelete(item.type, item.name)}
                    >
                      删除
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={getTypeIcon(item.type)}
                    title={
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span
                          onClick={() => handlePreview(item)}
                          style={{ cursor: 'pointer', color: '#1890ff', textDecoration: 'underline' }}
                        >
                          {item.name}
                        </span>
                        {getTypeTag(item.type)}
                      </div>
                    }
                    description={
                      <span>
                        {dayjs(item.created * 1000).fromNow()} · {formatSize(item.size)}
                      </span>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Card>
      </div>

      <PreviewModal
        visible={previewModalVisible}
        item={previewItem}
        onClose={handlePreviewClose}
      />
    </>
  );
}

export default HistoryPage;
