import type { DiagramNode } from '../../../types/diagram';
import styles from './PropertiesPanel.module.scss';

export const PropertiesPanel = ({ node }: { node?: DiagramNode }) => (
  <aside className={styles.panel}>
    <span className={styles.eyebrow}>Properties</span>
    {node ? (
      <>
        <div className={styles.field}>
          <label>Name</label>
          <div>{node.name}</div>
        </div>
        <div className={styles.field}>
          <label>Type</label>
          <div>
            {node.kind === 'useCase'
              ? 'Use case'
              : node.kind === 'boundary'
                ? 'System boundary'
                : 'Actor'}
          </div>
        </div>
        <div className={styles.hint}>
          Select an element to inspect it. Full property editing arrives in the next sprint.
        </div>
      </>
    ) : (
      <div className={styles.empty}>Select a diagram element to view its properties.</div>
    )}
  </aside>
);
