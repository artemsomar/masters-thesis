import { Rect } from 'react-konva';
import { getNodeBounds } from '../../../../lib/diagram/geometry';
import type { DiagramNode } from '../../../../types/diagram';

export const SelectionTransformer = ({ node }: { node: DiagramNode }) => (
  <Rect
    {...getNodeBounds(node)}
    stroke="#4b41e1"
    strokeWidth={1.2}
    dash={[4, 3]}
    listening={false}
  />
);
