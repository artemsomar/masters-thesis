import { useAddDiagramNode } from '../../../hooks/useAddDiagramNode';
import styles from './QuickAddControls.module.scss';

export const QuickAddControls = () => {
  const addNode = useAddDiagramNode();
  return (
    <div className={styles.controls}>
      <button onClick={() => addNode('boundary')}>+ Boundary</button>
      <button onClick={() => addNode('actor')}>+ Actor</button>
      <button onClick={() => addNode('useCase')}>+ Use case</button>
    </div>
  );
};
