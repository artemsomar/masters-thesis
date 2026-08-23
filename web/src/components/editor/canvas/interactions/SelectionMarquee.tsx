import { Rect } from 'react-konva';
import type { Point } from '../../../../types/diagram';

export const SelectionMarquee = ({ start, end }: { start: Point; end: Point }) => (
  <Rect
    x={Math.min(start.x, end.x)}
    y={Math.min(start.y, end.y)}
    width={Math.abs(end.x - start.x)}
    height={Math.abs(end.y - start.y)}
    fill="rgba(75, 65, 225, 0.08)"
    stroke="#4b41e1"
    dash={[5, 4]}
    listening={false}
  />
);
