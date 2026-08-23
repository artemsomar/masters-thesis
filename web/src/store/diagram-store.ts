import { create } from 'zustand';
import { createEmptyDocument } from '../lib/diagram/factory';
import type { DiagramDocument, DiagramNode, Point } from '../types/diagram';

type DiagramState = {
  document: DiagramDocument;
  revision: number;
  setDocument: (document: DiagramDocument) => void;
  addNode: (node: DiagramNode) => void;
  moveNode: (id: string, position: Point) => void;
};

export const useDiagramStore = create<DiagramState>()((set) => ({
  document: createEmptyDocument(),
  revision: 0,
  setDocument: (document) => set({ document, revision: 0 }),
  addNode: (node) =>
    set((state) => ({
      document: { ...state.document, nodes: [...state.document.nodes, node] },
      revision: state.revision + 1,
    })),
  moveNode: (id, position) =>
    set((state) => ({
      document: {
        ...state.document,
        nodes: state.document.nodes.map((node) => (node.id === id ? { ...node, position } : node)),
      },
      revision: state.revision + 1,
    })),
}));
