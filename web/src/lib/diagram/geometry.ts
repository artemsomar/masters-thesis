import type { DiagramNode } from '../../types/diagram';
import { getUseCaseLayout } from './use-case-layout';
import { getActorLayout } from './actor-layout';

export type Bounds = { x: number; y: number; width: number; height: number };

export const getNodeBounds = (node: DiagramNode): Bounds => {
  if (node.kind === 'boundary')
    return {
      x: node.position.x,
      y: node.position.y,
      width: node.size.width,
      height: node.size.height,
    };
  if (node.kind === 'useCase') {
    const { width, height } = getUseCaseLayout(node.name, node.size, node.style.fontSize);
    return { x: node.position.x - width / 2, y: node.position.y - height / 2, width, height };
  }
  const { width, height, top } = getActorLayout(node);
  return { x: node.position.x - width / 2, y: node.position.y + top, width, height };
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
