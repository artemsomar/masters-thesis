import type { GeneratedDiagram } from '../../types/api';
import type { DiagramDocument, DiagramNode, RelationType } from '../../types/diagram';

const defaultStyle = { fill: '#ffffff', stroke: '#1e293b', textColor: '#1e293b' };

const nodeId = (kind: 'actor' | 'useCase', id: string): string => `${kind}-${id}`;

export const generatedDiagramToDocument = (diagram: GeneratedDiagram): DiagramDocument => {
  const actors: DiagramNode[] = diagram.actors.map((actor) => ({
    id: nodeId('actor', actor.id),
    kind: 'actor',
    name: actor.name,
    description: actor.type === 'primary' ? 'Primary actor' : 'Supporting actor',
    position: { x: 0, y: 0 },
    style: defaultStyle,
  }));
  const useCases: DiagramNode[] = diagram.useCases.map((useCase) => ({
    id: nodeId('useCase', useCase.id),
    kind: 'useCase',
    name: useCase.name,
    description: '',
    position: { x: 0, y: 0 },
    style: defaultStyle,
  }));
  const ids = new Set([...actors, ...useCases].map((node) => node.id));
  const resolveId = (id: string): string => {
    const actorId = nodeId('actor', id);
    return ids.has(actorId) ? actorId : nodeId('useCase', id);
  };

  return {
    schemaVersion: diagram.schemaVersion,
    nodes: [
      {
        id: `boundary-${diagram.system.id}`,
        kind: 'boundary',
        name: diagram.system.name,
        position: { x: 0, y: 0 },
        size: { width: 440, height: 300 },
        style: defaultStyle,
      },
      ...actors,
      ...useCases,
    ],
    relations: diagram.relations.map((relation, index) => ({
      id: `relation-${index + 1}`,
      type: relation.type as RelationType,
      sourceId: resolveId(relation.sourceId),
      targetId: resolveId(relation.targetId),
    })),
  };
};
