export type Point = { x: number; y: number };

export type NodeStyle = {
  fill: string;
  stroke: string;
  textColor: string;
};

type BaseNode = {
  id: string;
  name: string;
  position: Point;
  style: NodeStyle;
};

export type ActorNode = BaseNode & {
  kind: 'actor';
  description: string;
};

export type UseCaseNode = BaseNode & {
  kind: 'useCase';
  description: string;
};

export type BoundaryNode = BaseNode & {
  kind: 'boundary';
  size: { width: number; height: number };
};

export type DiagramNode = ActorNode | UseCaseNode | BoundaryNode;
export type RelationType = 'association' | 'include' | 'extend' | 'generalization';

export type DiagramRelation = {
  id: string;
  type: RelationType;
  sourceId: string;
  targetId: string;
};

export type DiagramDocument = {
  schemaVersion: '1.0';
  nodes: DiagramNode[];
  relations: DiagramRelation[];
};

export type EditorTool =
  'select' | 'pan' | 'add-actor' | 'add-use-case' | 'add-boundary' | 'connect';

export type CanvasInteraction =
  | { mode: 'idle' }
  | { mode: 'panning' }
  | { mode: 'placing'; element: 'actor' | 'useCase' | 'boundary' }
  | { mode: 'connecting'; relationType: RelationType; sourceId?: string }
  | { mode: 'marquee'; start: Point }
  | { mode: 'dragging'; elementIds: string[]; initialPositions: Record<string, Point> };
