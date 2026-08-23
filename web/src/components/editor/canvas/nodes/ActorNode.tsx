import { Circle, Group, Line, Text } from 'react-konva';
import type { ActorNode as ActorNodeModel } from '../../../../types/diagram';
import type { DiagramNodeCallbacks } from './node-props';

type Props = DiagramNodeCallbacks & { node: ActorNodeModel };

export const ActorNode = ({
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
    <Circle x={0} y={-26} radius={8} stroke={node.style.stroke} strokeWidth={1.8} />
    <Line
      points={[0, -18, 0, 7, -12, 20, 0, 7, 12, 20]}
      stroke={node.style.stroke}
      strokeWidth={1.8}
      lineCap="round"
      lineJoin="round"
    />
    <Text
      text={node.name}
      y={28}
      x={-48}
      width={96}
      align="center"
      fontSize={12}
      fill={node.style.textColor}
    />
  </Group>
);
