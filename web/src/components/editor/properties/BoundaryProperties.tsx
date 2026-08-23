import type { BoundaryNode } from '../../../types/diagram';
import { VisualStyleFields } from './VisualStyleFields';
import styles from './PropertiesPanel.module.scss';

type Props = {
  node: BoundaryNode;
  onUpdate: (changes: { name?: string; size?: BoundaryNode['size'] }) => void;
  onStyleChange: (style: BoundaryNode['style']) => void;
};

export const BoundaryProperties = ({ node, onUpdate, onStyleChange }: Props) => (
  <>
    <label className={styles.field}>
      System name
      <input
        defaultValue={node.name}
        onBlur={(event) => onUpdate({ name: event.target.value.trim() || node.name })}
      />
    </label>
    <div className={styles.sizeFields}>
      <label className={styles.field}>
        Width
        <input
          type="number"
          min="120"
          defaultValue={node.size.width}
          onBlur={(event) =>
            onUpdate({
              size: {
                ...node.size,
                width: Math.max(120, Number(event.target.value) || node.size.width),
              },
            })
          }
        />
      </label>
      <label className={styles.field}>
        Height
        <input
          type="number"
          min="100"
          defaultValue={node.size.height}
          onBlur={(event) =>
            onUpdate({
              size: {
                ...node.size,
                height: Math.max(100, Number(event.target.value) || node.size.height),
              },
            })
          }
        />
      </label>
    </div>
    <VisualStyleFields node={node} onChange={onStyleChange} />
  </>
);
