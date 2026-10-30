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
  const nodes = useDiagramStore((state) => state.document.nodes);
  const isRelation = element && 'sourceId' in element;
  return (
    <aside
      className={styles.panel}
      data-properties-panel
      onKeyDown={(event) => {
        if (event.key !== 'Enter' || event.nativeEvent.isComposing) return;
        const field = event.target;
        const singleLine =
          field instanceof HTMLInputElement && ['text', 'number'].includes(field.type);
        const multiline = field instanceof HTMLTextAreaElement && (event.ctrlKey || event.metaKey);
        if (singleLine || multiline) {
          event.preventDefault();
          field.blur();
        }
      }}
    >
      <span className={styles.eyebrow}>Properties</span>
      {element ? (
        <div key={element.id} className={styles.content}>
          <span className={styles.type}>{isRelation ? 'Relation' : element.kind}</span>
          {isRelation ? (
            <RelationProperties
              relation={element}
              nodes={nodes}
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
