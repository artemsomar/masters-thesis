import { getNodeBounds } from './geometry';
import { getActorLayout } from './actor-layout';
import type { DiagramNode, DiagramRelation, Point } from '../../types/diagram';

const connectionBounds = (node: DiagramNode) => {
  if (node.kind !== 'actor') return getNodeBounds(node);
  // Attach to the actor symbol rather than the whitespace reserved for its label.
  const { scaleX, scaleY } = getActorLayout(node);
  return {
    x: node.position.x - 14 * scaleX,
    y: node.position.y - 34 * scaleY,
    width: 28 * scaleX,
    height: 54 * scaleY,
  };
};

const connectionCenter = (node: DiagramNode): Point => {
  const bounds = connectionBounds(node);
  return { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 };
};

/** Intersection of the ray from a node's centre towards a point with its outline. */
export const getNodeEdgePoint = (node: DiagramNode, towards: Point): Point => {
  const center = connectionCenter(node);
  const bounds = connectionBounds(node);
  const dx = towards.x - center.x;
  const dy = towards.y - center.y;
  if (dx === 0 && dy === 0) return center;
  const rx = bounds.width / 2;
  const ry = bounds.height / 2;
  const distance =
    node.kind === 'useCase'
      ? 1 / Math.hypot(dx / rx, dy / ry)
      : Math.min(dx === 0 ? Infinity : rx / Math.abs(dx), dy === 0 ? Infinity : ry / Math.abs(dy));
  return { x: center.x + dx * distance, y: center.y + dy * distance };
};

/** Ellipse parameter angle; normalized by node size so it survives resizing. */
export const getNodeAnchorAngle = (node: DiagramNode, point: Point): number => {
  const center = connectionCenter(node);
  const bounds = connectionBounds(node);
  return Math.atan2(
    (point.y - center.y) / (bounds.height / 2),
    (point.x - center.x) / (bounds.width / 2),
  );
};

export const getNodeAnchorPoint = (node: DiagramNode, angle: number): Point => {
  const center = connectionCenter(node);
  const bounds = connectionBounds(node);
  const direction = {
    x: center.x + (Math.cos(angle) * bounds.width) / 2,
    y: center.y + (Math.sin(angle) * bounds.height) / 2,
  };
  return node.kind === 'useCase' ? direction : getNodeEdgePoint(node, direction);
};

export const getRelationPoints = (
  relation: DiagramRelation,
  nodesById: Map<string, DiagramNode>,
): [Point, Point] | undefined => {
  const source = nodesById.get(relation.sourceId);
  const target = nodesById.get(relation.targetId);
  if (!source || !target) return undefined;
  const sourceCenter = connectionCenter(source);
  const targetCenter = connectionCenter(target);
  const sourceAnchor =
    relation.sourceAngle === undefined
      ? undefined
      : getNodeAnchorPoint(source, relation.sourceAngle);
  const targetAnchor =
    relation.targetAngle === undefined
      ? undefined
      : getNodeAnchorPoint(target, relation.targetAngle);
  const start = sourceAnchor ?? getNodeEdgePoint(source, targetAnchor ?? targetCenter);
  const end = targetAnchor ?? getNodeEdgePoint(target, sourceAnchor ?? sourceCenter);
  // Overlapping nodes have no visible forward segment between their outlines.
  if (
    relation.sourceAngle === undefined &&
    relation.targetAngle === undefined &&
    (end.x - start.x) * (targetCenter.x - sourceCenter.x) +
      (end.y - start.y) * (targetCenter.y - sourceCenter.y) <=
      0
  )
    return undefined;
  return [start, end];
};
