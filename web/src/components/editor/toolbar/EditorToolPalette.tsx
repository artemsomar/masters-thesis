import { Hand, Link2, MousePointer2, ScanLine, SquareDashed, UserRound } from 'lucide-react';
import { useEditorUiStore } from '../../../store/editor-ui-store';
import type { EditorTool } from '../../../types/diagram';
import { RelationTypeMenu } from './RelationTypeMenu';
import styles from './EditorToolPalette.module.scss';

const tools: Array<{ value: EditorTool; label: string; icon: typeof MousePointer2 }> = [
  { value: 'select', label: 'Select', icon: MousePointer2 },
  { value: 'pan', label: 'Pan', icon: Hand },
  { value: 'add-boundary', label: 'System boundary', icon: SquareDashed },
  { value: 'add-actor', label: 'Actor', icon: UserRound },
  { value: 'add-use-case', label: 'Use case', icon: ScanLine },
  { value: 'connect', label: 'Connect', icon: Link2 },
];

export const EditorToolPalette = () => {
  const activeTool = useEditorUiStore((state) => state.activeTool);
  const relationType = useEditorUiStore((state) => state.relationType);
  const setActiveTool = useEditorUiStore((state) => state.setActiveTool);
  const setInteraction = useEditorUiStore((state) => state.setInteraction);
  const handleToolChange = (tool: EditorTool) => {
    setActiveTool(tool);
    setInteraction(tool === 'connect' ? { mode: 'connecting', relationType } : { mode: 'idle' });
  };
  return (
    <>
      <div className={styles.palette}>
        {tools.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            type="button"
            title={label}
            aria-label={label}
            className={activeTool === value ? styles.selected : ''}
            onClick={() => handleToolChange(value)}
          >
            <Icon size={17} />
          </button>
        ))}
      </div>
      {activeTool === 'connect' ? <RelationTypeMenu /> : null}
    </>
  );
};
