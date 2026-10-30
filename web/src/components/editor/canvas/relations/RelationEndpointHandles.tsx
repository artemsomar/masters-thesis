import type Konva from 'konva';
import { Circle, Group } from 'react-konva';
import { getNodeAnchorAngle, getNodeAnchorPoint } from '../../../../lib/diagram/relation-paths';
import { useDiagramStore } from '../../../../store/diagram-store';
import type { DiagramNode, DiagramRelation, Point } from '../../../../types/diagram';

type Props = {
  relation: DiagramRelation;
  nodesById: Map<string, DiagramNode>;
  points: [Point, Point];
  scale: number;
};

export const RelationEndpointHandles = ({ relation, nodesById, points, scale }: Props) => (
  <Group name="relation-handles">
    {(['source', 'target'] as const).map((end, index) => {
      const node = nodesById.get(end === 'source' ? relation.sourceId : relation.targetId);
      if (!node) return null;
      const move = (event: Konva.KonvaEventObject<DragEvent>) => {
        event.cancelBubble = true;
        const stage = event.target.getStage();
        const pointer = stage?.getPointerPosition();
        if (!stage || !pointer) return;
        const point = stage.getAbsoluteTransform().copy().invert().point(pointer);
        const angle = getNodeAnchorAngle(node, point);
        // Keep the handle on the outline even when React skips unchanged props.
        event.target.position(getNodeAnchorPoint(node, angle));
        useDiagramStore.getState().moveRelationAnchorLive(relation.id, end, angle);
      };
      return (
        <Circle
          key={end}
          x={points[index].x}
          y={points[index].y}
          radius={6 / scale}
          fill={end === 'source' ? '#ffffff' : '#4b41e1'}
          stroke="#4b41e1"
          strokeWidth={1.5 / scale}
          hitStrokeWidth={12 / scale}
          draggable
          onMouseDown={(event) => {
            event.cancelBubble = true;
          }}
          onTouchStart={(event) => {
            event.cancelBubble = true;
          }}
          onDragStart={(event) => {
            event.cancelBubble = true;
            useDiagramStore.getState().beginInteraction();
          }}
          onDragMove={move}
          onDragEnd={(event) => {
            move(event);
            useDiagramStore.getState().commitInteraction();
          }}
        />
      );
    })}
  </Group>
);
