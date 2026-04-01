import { useWorkflow } from '../contexts/WorkflowContext';
import AppLayout from '../components/layout/AppLayout';
import DrawingPanel from '../components/drawing/DrawingPanel';
import DocumentPanel from '../components/document/DocumentPanel';
import ManimPanel from '../components/manim/ManimPanel';

function HomePage() {
  const { state } = useWorkflow();

  return (
    <AppLayout>
      {state.currentWorkflow === 'drawing' && <DrawingPanel />}
      {state.currentWorkflow === 'document_with_images' && <DocumentPanel />}
      {state.currentWorkflow === 'manim' && <ManimPanel />}
    </AppLayout>
  );
}

export default HomePage;
