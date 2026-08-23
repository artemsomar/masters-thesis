import { Check, CircleAlert, LoaderCircle } from 'lucide-react';
import type { ProjectAutosave } from '../../hooks/projects/useProjectAutosave';
import styles from './EditorHeader.module.scss';

export const EditorHeader = ({
  projectName,
  saveState,
  retry,
}: {
  projectName: string;
} & ProjectAutosave) => {
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
      <div className={`${styles.saveState} ${styles[saveState]}`} aria-live="polite">
        {icon}
        {label}
        {saveState === 'failed' ? (
          <button type="button" onClick={retry}>
            Retry
          </button>
        ) : null}
      </div>
    </header>
  );
};
