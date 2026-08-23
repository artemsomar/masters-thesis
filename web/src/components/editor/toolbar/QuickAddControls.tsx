import { useAddDiagramNode } from '../../../hooks/diagram/useAddDiagramNode';
import styles from './QuickAddControls.module.scss';

export const QuickAddControls = () => {
  const addNode = useAddDiagramNode();
  return (
    <div className={styles.controls}>
      <button type="button" onClick={() => addNode('boundary')}>
        + Boundary
      </button>
      <button type="button" onClick={() => addNode('actor')}>
        + Actor
      </button>
      <button type="button" onClick={() => addNode('useCase')}>
        + Use case
      </button>
    </div>
  );
};
