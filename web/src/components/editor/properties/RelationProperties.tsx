import type { DiagramRelation, RelationType } from '../../../types/diagram';
import styles from './PropertiesPanel.module.scss';

type Props = { relation: DiagramRelation; onUpdate: (changes: Partial<DiagramRelation>) => void };

export const RelationProperties = ({ relation, onUpdate }: Props) => (
  <>
    <label className={styles.field}>
      Type
      <select
        value={relation.type}
        onChange={(event) => onUpdate({ type: event.target.value as RelationType })}
      >
        <option value="association">Association</option>
        <option value="include">Include</option>
        <option value="extend">Extend</option>
        <option value="generalization">Generalization</option>
      </select>
    </label>
    <button
      className={styles.secondaryAction}
      type="button"
      onClick={() => onUpdate({ sourceId: relation.targetId, targetId: relation.sourceId })}
    >
      Reverse direction
    </button>
  </>
);
