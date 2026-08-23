import { create } from 'zustand';
import { createEmptyDocument } from '../lib/diagram/factory';
import type {
  DiagramDocument,
  DiagramNode,
  DiagramRelation,
  NodeStyle,
  Point,
} from '../types/diagram';

export type NodeChanges = {
  name?: string;
  description?: string;
  position?: Point;
  size?: { width: number; height: number };
  style?: NodeStyle;
};

type DiagramState = {
  document: DiagramDocument;
  revision: number;
  past: DiagramDocument[];
  future: DiagramDocument[];
  interactionSnapshot?: DiagramDocument;
  setDocument: (document: DiagramDocument) => void;
  addNode: (node: DiagramNode) => void;
  updateNode: (id: string, changes: NodeChanges) => void;
  deleteElements: (ids: string[]) => void;
  addRelation: (relation: DiagramRelation) => void;
  updateRelation: (id: string, changes: Partial<Omit<DiagramRelation, 'id'>>) => void;
  beginInteraction: () => void;
  moveNodeLive: (id: string, position: Point) => void;
  commitInteraction: () => void;
  undo: () => void;
  redo: () => void;
};

const commit = (state: DiagramState, document: DiagramDocument) => ({
  document,
  revision: state.revision + 1,
  past: [...state.past, state.document],
  future: [],
  interactionSnapshot: undefined,
});

export const useDiagramStore = create<DiagramState>()((set) => ({
  document: createEmptyDocument(),
  revision: 0,
  past: [],
  future: [],
  interactionSnapshot: undefined,
  setDocument: (document) => set({ document, revision: 0, past: [], future: [] }),
  addNode: (node) =>
    set((state) => commit(state, { ...state.document, nodes: [...state.document.nodes, node] })),
  updateNode: (id, changes) =>
    set((state) =>
      commit(state, {
        ...state.document,
        nodes: state.document.nodes.map((node) =>
          node.id === id ? { ...node, ...changes } : node,
        ),
      }),
    ),
  deleteElements: (ids) =>
    set((state) => {
      const idsToDelete = new Set(ids);
      return commit(state, {
        ...state.document,
        nodes: state.document.nodes.filter((node) => !idsToDelete.has(node.id)),
        relations: state.document.relations.filter(
          (relation) =>
            !idsToDelete.has(relation.id) &&
            !idsToDelete.has(relation.sourceId) &&
            !idsToDelete.has(relation.targetId),
        ),
      });
    }),
  addRelation: (relation) =>
    set((state) =>
      commit(state, { ...state.document, relations: [...state.document.relations, relation] }),
    ),
  updateRelation: (id, changes) =>
    set((state) =>
      commit(state, {
        ...state.document,
        relations: state.document.relations.map((relation) =>
          relation.id === id ? { ...relation, ...changes } : relation,
        ),
      }),
    ),
  beginInteraction: () =>
    set((state) =>
      state.interactionSnapshot ? state : { interactionSnapshot: structuredClone(state.document) },
    ),
  moveNodeLive: (id, position) =>
    set((state) => ({
      document: {
        ...state.document,
        nodes: state.document.nodes.map((node) => (node.id === id ? { ...node, position } : node)),
      },
    })),
  commitInteraction: () =>
    set((state) => {
      if (!state.interactionSnapshot) return state;
      if (JSON.stringify(state.interactionSnapshot) === JSON.stringify(state.document)) {
        return { interactionSnapshot: undefined };
      }
      return {
        revision: state.revision + 1,
        past: [...state.past, state.interactionSnapshot],
        future: [],
        interactionSnapshot: undefined,
      };
    }),
  undo: () =>
    set((state) => {
      const previous = state.past.at(-1);
      if (!previous) return state;
      return {
        document: previous,
        revision: state.revision + 1,
        past: state.past.slice(0, -1),
        future: [state.document, ...state.future],
        interactionSnapshot: undefined,
      };
    }),
  redo: () =>
    set((state) => {
      const next = state.future[0];
      if (!next) return state;
      return {
        document: next,
        revision: state.revision + 1,
        past: [...state.past, state.document],
        future: state.future.slice(1),
        interactionSnapshot: undefined,
      };
    }),
}));
