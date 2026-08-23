import { Hand, MousePointer2, ScanLine, SquareDashed, UserRound } from 'lucide-react';
import { useEditorUiStore } from '../../../store/editor-ui-store';
import type { EditorTool } from '../../../types/diagram';
import styles from './EditorToolPalette.module.scss';

const tools: Array<{ value: EditorTool; label: string; icon: typeof MousePointer2 }> = [
  { value: 'select', label: 'Select', icon: MousePointer2 },
  { value: 'pan', label: 'Pan', icon: Hand },
  { value: 'add-boundary', label: 'System boundary', icon: SquareDashed },
  { value: 'add-actor', label: 'Actor', icon: UserRound },
  { value: 'add-use-case', label: 'Use case', icon: ScanLine },
];

export const EditorToolPalette = () => {
  const activeTool = useEditorUiStore((state) => state.activeTool);
  const setActiveTool = useEditorUiStore((state) => state.setActiveTool);
  return (
    <div className={styles.palette}>
      {tools.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          type="button"
          title={label}
          aria-label={label}
          className={activeTool === value ? styles.selected : ''}
          onClick={() => setActiveTool(value)}
        >
          <Icon size={17} />
        </button>
      ))}
    </div>
  );
};
