import { Layer } from 'react-konva';
import type { DiagramNode, Point } from '../../../../types/diagram';
import { ActorNode } from '../nodes/ActorNode';
import { SystemBoundaryNode } from '../nodes/SystemBoundaryNode';
import { UseCaseNode } from '../nodes/UseCaseNode';

type Props = {
  nodes: DiagramNode[];
  onSelect: (id: string) => void;
  onDragEnd: (id: string, position: Point) => void;
};

export const DiagramLayer = ({ nodes, onSelect, onDragEnd }: Props) => {
  const renderNode = (node: DiagramNode) => {
    const callbacks = {
      onSelect: () => onSelect(node.id),
      onDragEnd: (position: Point) => onDragEnd(node.id, position),
    };
    if (node.kind === 'boundary')
      return <SystemBoundaryNode key={node.id} node={node} {...callbacks} />;
    if (node.kind === 'actor') return <ActorNode key={node.id} node={node} {...callbacks} />;
    return <UseCaseNode key={node.id} node={node} {...callbacks} />;
  };
  return (
    <Layer>
      {nodes.filter((node) => node.kind === 'boundary').map(renderNode)}
      {nodes.filter((node) => node.kind !== 'boundary').map(renderNode)}
    </Layer>
  );
};
