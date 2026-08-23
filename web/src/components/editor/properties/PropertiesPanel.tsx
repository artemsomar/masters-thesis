import { Trash2 } from 'lucide-react';
import { useDiagramStore } from '../../../store/diagram-store';
import type { DiagramNode, DiagramRelation } from '../../../types/diagram';
import { ActorProperties } from './ActorProperties';
import { BoundaryProperties } from './BoundaryProperties';
import { RelationProperties } from './RelationProperties';
import { UseCaseProperties } from './UseCaseProperties';
import styles from './PropertiesPanel.module.scss';

type Props = { element?: DiagramNode | DiagramRelation };

export const PropertiesPanel = ({ element }: Props) => {
  const updateNode = useDiagramStore((state) => state.updateNode);
  const updateRelation = useDiagramStore((state) => state.updateRelation);
  const deleteElements = useDiagramStore((state) => state.deleteElements);
  const isRelation = element && 'sourceId' in element;
  return (
    <aside className={styles.panel}>
      <span className={styles.eyebrow}>Properties</span>
      {element ? (
        <div className={styles.content}>
          <span className={styles.type}>{isRelation ? 'Relation' : element.kind}</span>
          {isRelation ? (
            <RelationProperties
              relation={element}
              onUpdate={(changes) => updateRelation(element.id, changes)}
            />
          ) : element.kind === 'actor' ? (
            <ActorProperties
              node={element}
              onUpdate={(changes) => updateNode(element.id, changes)}
              onStyleChange={(style) => updateNode(element.id, { style })}
            />
          ) : element.kind === 'useCase' ? (
            <UseCaseProperties
              node={element}
              onUpdate={(changes) => updateNode(element.id, changes)}
              onStyleChange={(style) => updateNode(element.id, { style })}
            />
          ) : (
            <BoundaryProperties
              node={element}
              onUpdate={(changes) => updateNode(element.id, changes)}
              onStyleChange={(style) => updateNode(element.id, { style })}
            />
          )}
          <button
            className={styles.deleteAction}
            type="button"
            onClick={() => deleteElements([element.id])}
          >
            <Trash2 size={15} /> Delete
          </button>
        </div>
      ) : (
        <div className={styles.empty}>Select a diagram element to edit its properties.</div>
      )}
    </aside>
  );
};
