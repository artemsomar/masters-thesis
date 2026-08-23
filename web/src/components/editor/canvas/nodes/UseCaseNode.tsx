import { Ellipse, Group, Text } from 'react-konva';
import type { UseCaseNode as UseCaseNodeModel } from '../../../../types/diagram';
import type { DiagramNodeCallbacks } from './node-props';

type Props = DiagramNodeCallbacks & { node: UseCaseNodeModel };

export const UseCaseNode = ({ node, onSelect, onDragEnd }: Props) => (
  <Group
    x={node.position.x}
    y={node.position.y}
    draggable
    onClick={onSelect}
    onTap={onSelect}
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
