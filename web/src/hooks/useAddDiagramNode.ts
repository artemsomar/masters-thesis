import { createActor, createBoundary, createUseCase } from '../lib/diagram/factory';
import { useDiagramStore } from '../store/diagram-store';

type NodeKind = 'actor' | 'useCase' | 'boundary';

export const useAddDiagramNode = () => {
  const nodes = useDiagramStore((state) => state.document.nodes);
  const addNode = useDiagramStore((state) => state.addNode);
  return (kind: NodeKind) => {
    const position = { x: 220 + (nodes.length % 3) * 74, y: 150 + (nodes.length % 4) * 62 };
    addNode(
      kind === 'actor'
        ? createActor(position)
        : kind === 'useCase'
          ? createUseCase(position)
          : createBoundary(position),
    );
  };
};
