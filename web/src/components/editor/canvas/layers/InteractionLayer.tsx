import { Layer } from 'react-konva';
import type { DiagramNode } from '../../../../types/diagram';
import { SelectionTransformer } from '../interactions/SelectionTransformer';

export const InteractionLayer = ({ selectedNodes }: { selectedNodes: DiagramNode[] }) => (
  <Layer listening={false}>
    {selectedNodes.map((node) => (
      <SelectionTransformer key={node.id} node={node} />
    ))}
  </Layer>
);
