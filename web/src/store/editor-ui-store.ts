import { create } from 'zustand';
import type { CanvasInteraction, EditorTool, Point } from '../types/diagram';

type EditorUiState = {
  selectedIds: string[];
  activeTool: EditorTool;
  viewport: Point & { scale: number };
  interaction: CanvasInteraction;
  select: (id: string) => void;
  setActiveTool: (tool: EditorTool) => void;
  setViewport: (viewport: Point & { scale: number }) => void;
  setInteraction: (interaction: CanvasInteraction) => void;
};

export const useEditorUiStore = create<EditorUiState>()((set) => ({
  selectedIds: [],
  activeTool: 'select',
  viewport: { x: 0, y: 0, scale: 1 },
  interaction: { mode: 'idle' },
  select: (id) => set({ selectedIds: [id] }),
  setActiveTool: (activeTool) => set({ activeTool }),
  setViewport: (viewport) => set({ viewport }),
  setInteraction: (interaction) => set({ interaction }),
}));
