/**
 * 结果区域占位符组件
 * 当没有结果时显示
 */
import { Empty, Alert } from 'antd';
import { FileImageOutlined, FileTextOutlined, VideoCameraOutlined } from '@ant-design/icons';

type ResultPlaceholderProps = {
  type: 'drawing' | 'document' | 'manim';
  error?: string | null;
};

function ResultPlaceholder({ type, error }: ResultPlaceholderProps) {
  const config = {
    drawing: {
      icon: <FileImageOutlined style={{ fontSize: 48 }} />,
      description: '生成的图表将显示在这里',
    },
    document: {
      icon: <FileTextOutlined style={{ fontSize: 48 }} />,
      description: '生成的文档将显示在这里',
    },
    manim: {
      icon: <VideoCameraOutlined style={{ fontSize: 48 }} />,
      description: '渲染的视频将显示在这里',
    },
  };

  const { icon, description } = config[type];

  return (
    <div>
      {error && (
        <Alert
          message="执行出错"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      <div style={{ padding: '48px 0', textAlign: 'center' }}>
        <Empty
          image={icon}
          styles={{ image: { fontSize: 48, color: '#d9d9d9' } }}
          description={description}
        />
        <div style={{ marginTop: 16, color: '#999', fontSize: 14 }}>
          请在左侧输入需求并点击开始生成
        </div>
      </div>
    </div>
  );
}

export default ResultPlaceholder;
