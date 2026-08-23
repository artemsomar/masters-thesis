import { Ellipse, Group, Text } from 'react-konva';
import type { UseCaseNode as UseCaseNodeModel } from '../../../../types/diagram';
import type { DiagramNodeCallbacks } from './node-props';

type Props = DiagramNodeCallbacks & { node: UseCaseNodeModel };

export const UseCaseNode = ({
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
    <Ellipse
      radiusX={78}
      radiusY={31}
      fill={node.style.fill}
      stroke={node.style.stroke}
      strokeWidth={1.2}
    />
    <Text
      text={node.name}
      x={-68}
      y={-7}
      width={136}
      align="center"
      fontSize={12}
      fill={node.style.textColor}
    />
  </Group>
);
