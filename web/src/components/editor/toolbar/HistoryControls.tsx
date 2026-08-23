import { Redo2, Undo2 } from 'lucide-react';
import { useDiagramStore } from '../../../store/diagram-store';
import styles from './HistoryControls.module.scss';

export const HistoryControls = () => {
  const canUndo = useDiagramStore((state) => state.past.length > 0);
  const canRedo = useDiagramStore((state) => state.future.length > 0);
  const undo = useDiagramStore((state) => state.undo);
  const redo = useDiagramStore((state) => state.redo);
  return (
    <div className={styles.controls} aria-label="Edit history">
      <button
        type="button"
        aria-label="Undo"
        title="Undo (Ctrl/Cmd + Z)"
        disabled={!canUndo}
        onClick={undo}
      >
        <Undo2 size={16} />
      </button>
      <button
        type="button"
        aria-label="Redo"
        title="Redo (Ctrl/Cmd + Shift + Z)"
        disabled={!canRedo}
        onClick={redo}
      >
        <Redo2 size={16} />
      </button>
    </div>
  );
};
