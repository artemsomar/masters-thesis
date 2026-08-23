import type { DiagramNode } from '../../types/diagram';

export type Bounds = { x: number; y: number; width: number; height: number };

export const getNodeBounds = (node: DiagramNode): Bounds => {
  if (node.kind === 'boundary')
    return {
      x: node.position.x,
      y: node.position.y,
      width: node.size.width,
      height: node.size.height,
    };
  if (node.kind === 'useCase')
    return { x: node.position.x - 82, y: node.position.y - 35, width: 164, height: 70 };
  return { x: node.position.x - 52, y: node.position.y - 40, width: 104, height: 64 };
};
