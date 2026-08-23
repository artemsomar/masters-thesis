import { getNodeCenter } from './geometry';
import type { DiagramNode, DiagramRelation, Point } from '../../types/diagram';

export const getRelationPoints = (
  relation: DiagramRelation,
  nodesById: Map<string, DiagramNode>,
): [Point, Point] | undefined => {
  const source = nodesById.get(relation.sourceId);
  const target = nodesById.get(relation.targetId);
  return source && target ? [getNodeCenter(source), getNodeCenter(target)] : undefined;
};
