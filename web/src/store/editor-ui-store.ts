import { create } from 'zustand';
import type { CanvasInteraction, EditorTool, Point, RelationType } from '../types/diagram';

type EditorUiState = {
  selectedIds: string[];
  activeTool: EditorTool;
  viewport: Point & { scale: number };
  interaction: CanvasInteraction;
  relationType: RelationType;
  select: (id: string) => void;
  selectMany: (ids: string[]) => void;
  clearSelection: () => void;
  setActiveTool: (tool: EditorTool) => void;
  setViewport: (viewport: Point & { scale: number }) => void;
  setInteraction: (interaction: CanvasInteraction) => void;
  setRelationType: (relationType: RelationType) => void;
};

export const useEditorUiStore = create<EditorUiState>()((set) => ({
  selectedIds: [],
  activeTool: 'select',
  viewport: { x: 0, y: 0, scale: 1 },
  interaction: { mode: 'idle' },
  relationType: 'association',
  select: (id) => set({ selectedIds: [id] }),
  selectMany: (selectedIds) => set({ selectedIds }),
  clearSelection: () => set({ selectedIds: [] }),
  setActiveTool: (activeTool) => set({ activeTool }),
  setViewport: (viewport) => set({ viewport }),
  setInteraction: (interaction) => set({ interaction }),
  setRelationType: (relationType) => set({ relationType }),
}));
