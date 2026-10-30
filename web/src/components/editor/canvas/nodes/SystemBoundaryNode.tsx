import { Group, Rect, Text } from 'react-konva';
import type { BoundaryNode as BoundaryNodeModel } from '../../../../types/diagram';
import type { DiagramNodeCallbacks } from './node-props';

type Props = DiagramNodeCallbacks & { node: BoundaryNodeModel };

export const SystemBoundaryNode = ({
  node,
  onSelect,
  onDragStart,
  onDragMove,
  onDragEnd,
  draggable,
}: Props) => (
  <Group
    x={node.position.x}
    y={node.position.y}
    draggable={draggable}
    onClick={(event) => {
      event.cancelBubble = true;
      onSelect();
    }}
    onTap={(event) => {
      event.cancelBubble = true;
      onSelect();
    }}
    onDragStart={onDragStart}
    onDragMove={(event) => onDragMove({ x: event.target.x(), y: event.target.y() })}
    onDragEnd={(event) => onDragEnd({ x: event.target.x(), y: event.target.y() })}
  >
    <Rect
      width={node.size.width}
      height={node.size.height}
      fill="rgba(255,255,255,.42)"
      stroke={node.style.stroke}
      strokeWidth={1.2}
      dash={[7, 5]}
      cornerRadius={3}
    />
    <Text
      text={node.name}
      x={14}
      y={12}
      fontSize={node.style.fontSize ?? 13}
      fontStyle="bold"
      fill={node.style.textColor}
    />
  </Group>
);
