import type { Point } from '../../../../types/diagram';

export type DiagramNodeCallbacks = {
  onSelect: () => void;
  onDragEnd: (position: Point) => void;
};
