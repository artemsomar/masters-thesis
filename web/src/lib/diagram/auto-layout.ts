import ELK from 'elkjs/lib/elk.bundled.js';
import type { DiagramDocument, DiagramNode } from '../../types/diagram';

const elk = new ELK();
const actorSize = { width: 110, height: 72 };
const useCaseSize = { width: 164, height: 70 };
const canvasPadding = 120;

const sizeForNode = (node: DiagramNode): { width: number; height: number } =>
  node.kind === 'actor' ? actorSize : useCaseSize;

export const autoLayoutDocument = async (document: DiagramDocument): Promise<DiagramDocument> => {
  const layoutNodes = document.nodes.filter((node) => node.kind !== 'boundary');
  if (!layoutNodes.length) return document;
  const result = await elk.layout({
    id: 'diagram',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'RIGHT',
      'elk.layered.spacing.nodeNodeBetweenLayers': '90',
      'elk.spacing.nodeNode': '54',
      'elk.padding': '[top=80,left=80,bottom=80,right=80]',
    },
    children: layoutNodes.map((node) => ({ id: node.id, ...sizeForNode(node) })),
    edges: document.relations.map((relation) => ({
      id: relation.id,
      sources: [relation.sourceId],
      targets: [relation.targetId],
    })),
  });
  const positions = new Map(
    (result.children ?? []).map((node) => [
      node.id,
      {
        x: (node.x ?? 0) + (node.width ?? 0) / 2 + canvasPadding,
        y: (node.y ?? 0) + (node.height ?? 0) / 2 + canvasPadding,
      },
    ]),
  );
  const laidOutNodes = document.nodes.map((node) => {
    const position = positions.get(node.id);
    return position ? { ...node, position } : node;
  });
  const useCases = laidOutNodes.filter((node) => node.kind === 'useCase');
  if (!useCases.length) return { ...document, nodes: laidOutNodes };
  const left = Math.min(...useCases.map((node) => node.position.x - useCaseSize.width / 2));
  const right = Math.max(...useCases.map((node) => node.position.x + useCaseSize.width / 2));
  const top = Math.min(...useCases.map((node) => node.position.y - useCaseSize.height / 2));
  const bottom = Math.max(...useCases.map((node) => node.position.y + useCaseSize.height / 2));

  return {
    ...document,
    nodes: laidOutNodes.map((node) =>
      node.kind === 'boundary'
        ? {
            ...node,
            position: { x: left - 56, y: top - 72 },
            size: { width: right - left + 112, height: bottom - top + 128 },
          }
        : node,
    ),
  };
};
