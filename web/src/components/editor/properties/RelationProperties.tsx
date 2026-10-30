import type { DiagramNode, DiagramRelation, RelationType } from '../../../types/diagram';
import styles from './PropertiesPanel.module.scss';

type Props = {
  relation: DiagramRelation;
  nodes: DiagramNode[];
  onUpdate: (changes: Partial<DiagramRelation>) => void;
};

export const RelationProperties = ({ relation, nodes, onUpdate }: Props) => (
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
    <label className={styles.field}>
      From
      <select
        value={relation.sourceId}
        onChange={(event) => onUpdate({ sourceId: event.target.value, sourceAngle: undefined })}
      >
        {nodes
          .filter((node) => node.id !== relation.targetId)
          .map((node) => (
            <option key={node.id} value={node.id}>
              {node.name}
            </option>
          ))}
      </select>
    </label>
    <label className={styles.field}>
      To
      <select
        value={relation.targetId}
        onChange={(event) => onUpdate({ targetId: event.target.value, targetAngle: undefined })}
      >
        {nodes
          .filter((node) => node.id !== relation.sourceId)
          .map((node) => (
            <option key={node.id} value={node.id}>
              {node.name}
            </option>
          ))}
      </select>
    </label>
    <button
      className={styles.secondaryAction}
      type="button"
      onClick={() =>
        onUpdate({
          sourceId: relation.targetId,
          targetId: relation.sourceId,
          sourceAngle: relation.targetAngle,
          targetAngle: relation.sourceAngle,
        })
      }
    >
      Reverse direction
    </button>
    <p className={styles.empty}>
      Drag the endpoint handles around an object's outline to position the connection.
    </p>
    <button
      className={styles.secondaryAction}
      type="button"
      disabled={relation.sourceAngle === undefined && relation.targetAngle === undefined}
      onClick={() => onUpdate({ sourceAngle: undefined, targetAngle: undefined })}
    >
      Automatic attachment
    </button>
  </>
);
