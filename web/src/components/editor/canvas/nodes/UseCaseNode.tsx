import { Ellipse, Group, Text } from 'react-konva';
import { getUseCaseLayout } from '../../../../lib/diagram/use-case-layout';
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
}: Props) => {
  const layout = getUseCaseLayout(node.name, node.size, node.style.fontSize);
  return (
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
        radiusX={layout.width / 2}
        radiusY={layout.height / 2}
        fill={node.style.fill}
        stroke={node.style.stroke}
        strokeWidth={1.2}
      />
      <Text
        text={layout.text}
        x={-layout.textWidth / 2}
        y={-layout.textHeight / 2}
        width={layout.textWidth}
        height={layout.textHeight}
        verticalAlign="middle"
        wrap="none"
        fontFamily="Arial"
        lineHeight={layout.lineHeight / layout.fontSize}
        align="center"
        fontSize={layout.fontSize}
        fill={node.style.textColor}
      />
    </Group>
  );
};
