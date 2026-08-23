import { useRef } from 'react';
import type Konva from 'konva';
import { useProjectAutosave } from '../../hooks/projects/useProjectAutosave';
import { useProjectDocument } from '../../hooks/projects/useProjectDocument';
import { useKeyboardShortcuts } from '../../hooks/diagram/useKeyboardShortcuts';
import { useDiagramStore } from '../../store/diagram-store';
import { useEditorUiStore } from '../../store/editor-ui-store';
import { DiagramCanvas } from './canvas/DiagramCanvas';
import { EditorHeader } from './EditorHeader';
import { PropertiesPanel } from './properties/PropertiesPanel';
import { CanvasControls } from './toolbar/CanvasControls';
import { EditorToolPalette } from './toolbar/EditorToolPalette';
import { EditorExportControls } from './toolbar/EditorExportControls';
import { HistoryControls } from './toolbar/HistoryControls';
import { QuickAddControls } from './toolbar/QuickAddControls';
import styles from './EditorWorkspace.module.scss';

type Props = { projectId: string; projectToken: string; documentXml: string; projectName: string };

export const EditorWorkspace = ({ projectId, projectToken, documentXml, projectName }: Props) => {
  const stageRef = useRef<Konva.Stage>(null);
  useProjectDocument(documentXml);
  useKeyboardShortcuts();
  const document = useDiagramStore((state) => state.document);
  const revision = useDiagramStore((state) => state.revision);
  const selectedIds = useEditorUiStore((state) => state.selectedIds);
  const autosave = useProjectAutosave(projectId, projectToken, document, revision);
  const selectedElement =
    document.nodes.find((node) => node.id === selectedIds[0]) ??
    document.relations.find((relation) => relation.id === selectedIds[0]);

  return (
    <section className={styles.workspace}>
      <EditorHeader projectName={projectName} {...autosave} />
      <div className={styles.editorBody}>
        <div className={styles.canvasArea}>
          <EditorToolPalette />
          <QuickAddControls />
          <HistoryControls />
          <EditorExportControls document={document} stageRef={stageRef} />
          <DiagramCanvas stageRef={stageRef} />
          <CanvasControls />
        </div>
        <PropertiesPanel element={selectedElement} />
      </div>
    </section>
  );
};
