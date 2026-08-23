import type { Point } from '../../../../types/diagram';

export type DiagramNodeCallbacks = {
  onSelect: () => void;
  onDragStart: () => void;
  onDragMove: (position: Point) => void;
  onDragEnd: (position: Point) => void;
  draggable: boolean;
};
