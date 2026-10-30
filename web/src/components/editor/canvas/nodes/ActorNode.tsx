import { Circle, Group, Line, Text } from 'react-konva';
import { getActorLayout } from '../../../../lib/diagram/actor-layout';
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
}: Props) => {
  const layout = getActorLayout(node);
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
      <Group scaleX={layout.scaleX} scaleY={layout.scaleY}>
        <Circle x={0} y={-26} radius={8} stroke={node.style.stroke} strokeWidth={1.8} />
        <Line
          points={[0, -18, 0, 7, -12, 20, 0, 7, 12, 20]}
          stroke={node.style.stroke}
          strokeWidth={1.8}
          lineCap="round"
          lineJoin="round"
        />
        <Line
          points={[-14, -9, 14, -9]}
          stroke={node.style.stroke}
          strokeWidth={1.8}
          lineCap="round"
        />
      </Group>
      <Text
        text={layout.text}
        y={layout.labelY}
        x={-layout.textWidth / 2}
        width={layout.textWidth}
        height={layout.textHeight}
        lineHeight={layout.lineHeight / layout.fontSize}
        fontFamily="Arial"
        wrap="none"
        align="center"
        fontSize={layout.fontSize}
        fill={node.style.textColor}
      />
    </Group>
  );
};
