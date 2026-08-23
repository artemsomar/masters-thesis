import { Layer } from 'react-konva';
import type { CanvasInteraction, DiagramNode } from '../../../../types/diagram';
import { ConnectionPreview } from '../interactions/ConnectionPreview';
import { SelectionMarquee } from '../interactions/SelectionMarquee';
import { SelectionTransformer } from '../interactions/SelectionTransformer';

type Props = { selectedNodes: DiagramNode[]; nodes: DiagramNode[]; interaction: CanvasInteraction };

export const InteractionLayer = ({ selectedNodes, nodes, interaction }: Props) => {
  const source =
    interaction.mode === 'connecting'
      ? nodes.find((node) => node.id === interaction.sourceId)
      : undefined;
  return (
    <Layer name="interaction-layer" listening={false}>
      {selectedNodes.map((node) => (
        <SelectionTransformer key={node.id} node={node} />
      ))}
      {interaction.mode === 'marquee' ? (
        <SelectionMarquee start={interaction.start} end={interaction.end} />
      ) : null}
      {interaction.mode === 'connecting' ? (
        <ConnectionPreview source={source} point={interaction.point} />
      ) : null}
    </Layer>
  );
};
