import type { ActorNode } from '../../../types/diagram';
import { VisualStyleFields } from './VisualStyleFields';
import styles from './PropertiesPanel.module.scss';

type Props = {
  node: ActorNode;
  onUpdate: (changes: { name?: string; description?: string }) => void;
  onStyleChange: (style: ActorNode['style']) => void;
};

export const ActorProperties = ({ node, onUpdate, onStyleChange }: Props) => (
  <>
    <label className={styles.field}>
      Name
      <input
        defaultValue={node.name}
        onBlur={(event) => onUpdate({ name: event.target.value.trim() || node.name })}
      />
    </label>
    <label className={styles.field}>
      Description
      <textarea
        defaultValue={node.description}
        rows={4}
        onBlur={(event) => onUpdate({ description: event.target.value })}
      />
    </label>
    <VisualStyleFields node={node} onChange={onStyleChange} />
  </>
);
