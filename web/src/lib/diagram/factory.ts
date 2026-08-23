import type {
  ActorNode,
  BoundaryNode,
  DiagramDocument,
  DiagramNode,
  DiagramRelation,
  RelationType,
  UseCaseNode,
} from '../../types/diagram';

const baseStyle = { fill: '#ffffff', stroke: '#1e293b', textColor: '#1e293b' };

export const createEmptyDocument = (): DiagramDocument => ({
  schemaVersion: '1.0',
  nodes: [],
  relations: [],
});

const id = (kind: DiagramNode['kind']) => `${kind}-${crypto.randomUUID()}`;

export const createActor = (position: { x: number; y: number }): ActorNode => ({
  id: id('actor'),
  kind: 'actor',
  name: 'New actor',
  description: '',
  position,
  style: baseStyle,
});

export const createUseCase = (position: { x: number; y: number }): UseCaseNode => ({
  id: id('useCase'),
  kind: 'useCase',
  name: 'New use case',
  description: '',
  position,
  style: baseStyle,
});

export const createBoundary = (position: { x: number; y: number }): BoundaryNode => ({
  id: id('boundary'),
  kind: 'boundary',
  name: 'System',
  position,
  size: { width: 440, height: 300 },
  style: baseStyle,
});

export const createRelation = (
  type: RelationType,
  sourceId: string,
  targetId: string,
): DiagramRelation => ({
  id: `relation-${crypto.randomUUID()}`,
  type,
  sourceId,
  targetId,
});
