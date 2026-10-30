import { Layer } from 'react-konva';
import type { DiagramNode, DiagramRelation, Point } from '../../../../types/diagram';
import { ActorNode } from '../nodes/ActorNode';
import { SystemBoundaryNode } from '../nodes/SystemBoundaryNode';
import { UseCaseNode } from '../nodes/UseCaseNode';
import { RelationEdge } from '../relations/RelationEdge';

type Props = {
  nodes: DiagramNode[];
  relations: DiagramRelation[];
  selectedIds: string[];
  onSelectNode: (id: string) => void;
  onSelectRelation: (id: string) => void;
  onDragStart: () => void;
  onDragMove: (id: string, position: Point) => void;
  onDragEnd: (id: string, position: Point) => void;
  draggable: boolean;
};

export const DiagramLayer = ({
  nodes,
  relations,
  selectedIds,
  onSelectNode,
  onSelectRelation,
  onDragStart,
  onDragMove,
  onDragEnd,
  draggable,
}: Props) => {
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const renderNode = (node: DiagramNode) => {
    const callbacks = {
      onSelect: () => onSelectNode(node.id),
      onDragStart,
      onDragMove: (position: Point) => onDragMove(node.id, position),
      onDragEnd: (position: Point) => onDragEnd(node.id, position),
      draggable,
    };
    if (node.kind === 'boundary')
      return <SystemBoundaryNode key={node.id} node={node} {...callbacks} />;
    if (node.kind === 'actor') return <ActorNode key={node.id} node={node} {...callbacks} />;
    return <UseCaseNode key={node.id} node={node} {...callbacks} />;
  };
  return (
    <>
      <Layer>
        {nodes.filter((node) => node.kind === 'boundary').map(renderNode)}
        {nodes.filter((node) => node.kind !== 'boundary').map(renderNode)}
      </Layer>
      <Layer name="relations-layer">
        {relations.map((relation) => (
          <RelationEdge
            key={relation.id}
            relation={relation}
            nodesById={nodesById}
            selected={selectedIds.includes(relation.id)}
            selectable={draggable}
            onSelect={() => onSelectRelation(relation.id)}
          />
        ))}
      </Layer>
    </>
  );
};
