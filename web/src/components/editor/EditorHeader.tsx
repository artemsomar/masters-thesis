import { Check, CircleAlert, LoaderCircle } from 'lucide-react';
import type { SaveState } from '../../hooks/useProjectAutosave';
import styles from './EditorHeader.module.scss';

export const EditorHeader = ({
  projectName,
  saveState,
}: {
  projectName: string;
  saveState: SaveState;
}) => {
  const icon =
    saveState === 'saving' ? (
      <LoaderCircle size={13} className={styles.spin} />
    ) : saveState === 'failed' ? (
      <CircleAlert size={13} />
    ) : (
      <Check size={13} />
    );
  const label =
    saveState === 'saving' ? 'Saving' : saveState === 'failed' ? 'Save failed' : 'Saved';
  return (
    <header className={styles.header}>
      <div>
        <strong>{projectName}</strong>
        <span>Use Case Diagram</span>
      </div>
      <div className={`${styles.saveState} ${styles[saveState]}`}>
        {icon}
        {label}
      </div>
    </header>
  );
};
