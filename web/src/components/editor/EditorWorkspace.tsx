import { useProjectAutosave } from '../../hooks/useProjectAutosave';
import { useProjectDocument } from '../../hooks/useProjectDocument';
import { useDiagramStore } from '../../store/diagram-store';
import { useEditorUiStore } from '../../store/editor-ui-store';
import { DiagramCanvas } from './canvas/DiagramCanvas';
import { EditorHeader } from './EditorHeader';
import { PropertiesPanel } from './properties/PropertiesPanel';
import { CanvasControls } from './toolbar/CanvasControls';
import { EditorToolPalette } from './toolbar/EditorToolPalette';
import { QuickAddControls } from './toolbar/QuickAddControls';
import styles from './EditorWorkspace.module.scss';

type Props = { projectId: string; projectToken: string; documentXml: string; projectName: string };

export const EditorWorkspace = ({ projectId, projectToken, documentXml, projectName }: Props) => {
  useProjectDocument(documentXml);
  const document = useDiagramStore((state) => state.document);
  const revision = useDiagramStore((state) => state.revision);
  const selectedIds = useEditorUiStore((state) => state.selectedIds);
  const saveState = useProjectAutosave(projectId, projectToken, document, revision);
  const selectedNode = document.nodes.find((node) => node.id === selectedIds[0]);

  return (
    <section className={styles.workspace}>
      <EditorHeader projectName={projectName} saveState={saveState} />
      <div className={styles.editorBody}>
        <div className={styles.canvasArea}>
          <EditorToolPalette />
          <QuickAddControls />
          <DiagramCanvas />
          <CanvasControls />
        </div>
        <PropertiesPanel node={selectedNode} />
      </div>
    </section>
  );
};
