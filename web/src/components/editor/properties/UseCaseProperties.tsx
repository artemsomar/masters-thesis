import type { UseCaseNode } from '../../../types/diagram';
import { VisualStyleFields } from './VisualStyleFields';
import styles from './PropertiesPanel.module.scss';

type Props = {
  node: UseCaseNode;
  onUpdate: (changes: { name?: string; description?: string }) => void;
  onStyleChange: (style: UseCaseNode['style']) => void;
};

export const UseCaseProperties = ({ node, onUpdate, onStyleChange }: Props) => (
  <>
    <label className={styles.field}>
      Name
      <input
        key={node.name}
        defaultValue={node.name}
        onBlur={(event) => onUpdate({ name: event.target.value.trim() || node.name })}
      />
    </label>
    <label className={styles.field}>
      Description
      <textarea
        key={node.description}
        defaultValue={node.description}
        rows={4}
        onBlur={(event) => onUpdate({ description: event.target.value })}
      />
    </label>
    <VisualStyleFields node={node} onChange={onStyleChange} />
  </>
);
