import { Arrow } from 'react-konva';
import { getNodeEdgePoint } from '../../../../lib/diagram/relation-paths';
import type { DiagramNode, Point } from '../../../../types/diagram';

export const ConnectionPreview = ({ source, point }: { source?: DiagramNode; point?: Point }) => {
  if (!source || !point) return null;
  const sourcePoint = getNodeEdgePoint(source, point);
  return (
    <Arrow
      points={[sourcePoint.x, sourcePoint.y, point.x, point.y]}
      stroke="#4b41e1"
      fill="#4b41e1"
      dash={[6, 5]}
      strokeWidth={1.5}
      pointerLength={8}
      pointerWidth={8}
      listening={false}
    />
  );
};
