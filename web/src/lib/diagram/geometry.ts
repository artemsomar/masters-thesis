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

export const getNodeCenter = (node: DiagramNode) => {
  const bounds = getNodeBounds(node);
  return { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 };
};

export const isInsideBounds = (bounds: Bounds, selection: Bounds) =>
  bounds.x >= selection.x &&
  bounds.y >= selection.y &&
  bounds.x + bounds.width <= selection.x + selection.width &&
  bounds.y + bounds.height <= selection.y + selection.height;
