import { Arrow, Line, Text } from 'react-konva';
import { getRelationPoints } from '../../../../lib/diagram/relation-paths';
import { getRelationStyle } from '../../../../lib/diagram/relation-style';
import type { DiagramNode, DiagramRelation } from '../../../../types/diagram';

type Props = {
  relation: DiagramRelation;
  nodesById: Map<string, DiagramNode>;
  selected: boolean;
  onSelect: () => void;
};

export const RelationEdge = ({ relation, nodesById, selected, onSelect }: Props) => {
  const points = getRelationPoints(relation, nodesById);
  if (!points) return null;
  const [source, target] = points;
  const style = getRelationStyle(relation.type);
  const linePoints = [source.x, source.y, target.x, target.y];
  const common = {
    points: linePoints,
    stroke: selected ? '#4b41e1' : '#64748b',
    strokeWidth: selected ? 2.4 : 1.5,
    dash: style.dash,
    onClick: (event: { cancelBubble: boolean }) => {
      event.cancelBubble = true;
      onSelect();
    },
    onTap: (event: { cancelBubble: boolean }) => {
      event.cancelBubble = true;
      onSelect();
    },
  };
  const labelX = (source.x + target.x) / 2;
  const labelY = (source.y + target.y) / 2 - 15;

  return (
    <>
      {style.pointer === 'none' ? (
        <Line {...common} />
      ) : (
        <Arrow
          {...common}
          pointerLength={10}
          pointerWidth={10}
          fill={style.pointer === 'open' ? '#ffffff' : common.stroke}
          pointerAtEnding
        />
      )}
      {style.label ? (
        <Text
          x={labelX - 42}
          y={labelY}
          width={84}
          align="center"
          text={style.label}
          fontSize={11}
          fill={common.stroke}
          listening={false}
        />
      ) : null}
    </>
  );
};
