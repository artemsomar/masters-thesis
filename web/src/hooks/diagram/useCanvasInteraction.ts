import { useEffect, useRef } from 'react';
import type Konva from 'konva';
import {
  createActor,
  createBoundary,
  createRelation,
  createUseCase,
} from '../../lib/diagram/factory';
import { getNodeBounds, isInsideBounds } from '../../lib/diagram/geometry';
import { useDiagramStore } from '../../store/diagram-store';
import { useEditorUiStore } from '../../store/editor-ui-store';
import type { Point } from '../../types/diagram';

const nodeKindForTool = {
  'add-actor': 'actor',
  'add-use-case': 'useCase',
  'add-boundary': 'boundary',
} as const;

const toDocumentPoint = (stage: Konva.Stage): Point => {
  const pointer = stage.getPointerPosition() ?? { x: 0, y: 0 };
  return {
    x: (pointer.x - stage.x()) / stage.scaleX(),
    y: (pointer.y - stage.y()) / stage.scaleY(),
  };
};

export const useCanvasInteraction = () => {
  const dragFrame = useRef<number | undefined>(undefined);
  const pendingDrag = useRef<{ id: string; position: Point } | undefined>(undefined);
  const nodes = useDiagramStore((state) => state.document.nodes);
  const addNode = useDiagramStore((state) => state.addNode);
  const addRelation = useDiagramStore((state) => state.addRelation);
  const beginInteraction = useDiagramStore((state) => state.beginInteraction);
  const moveNodeLive = useDiagramStore((state) => state.moveNodeLive);
  const commitInteraction = useDiagramStore((state) => state.commitInteraction);
  const activeTool = useEditorUiStore((state) => state.activeTool);
  const relationType = useEditorUiStore((state) => state.relationType);
  const interaction = useEditorUiStore((state) => state.interaction);
  const select = useEditorUiStore((state) => state.select);
  const selectMany = useEditorUiStore((state) => state.selectMany);
  const clearSelection = useEditorUiStore((state) => state.clearSelection);
  const setActiveTool = useEditorUiStore((state) => state.setActiveTool);
  const setInteraction = useEditorUiStore((state) => state.setInteraction);

  useEffect(
    () => () => {
      if (dragFrame.current) window.cancelAnimationFrame(dragFrame.current);
    },
    [],
  );

  const flushDragPosition = () => {
    if (dragFrame.current) window.cancelAnimationFrame(dragFrame.current);
    dragFrame.current = undefined;
    const pending = pendingDrag.current;
    pendingDrag.current = undefined;
    if (pending) moveNodeLive(pending.id, pending.position);
  };

  const handleStageMouseDown = (stage: Konva.Stage, targetIsStage: boolean) => {
    if (!targetIsStage) return;
    const point = toDocumentPoint(stage);
    if (activeTool in nodeKindForTool) {
      const kind = nodeKindForTool[activeTool as keyof typeof nodeKindForTool];
      addNode(
        kind === 'actor'
          ? createActor(point)
          : kind === 'useCase'
            ? createUseCase(point)
            : createBoundary(point),
      );
      setActiveTool('select');
      return;
    }
    if (activeTool === 'select') {
      clearSelection();
      setInteraction({ mode: 'marquee', start: point, end: point });
    }
  };

  const handleStageMouseMove = (stage: Konva.Stage) => {
    if (interaction.mode === 'marquee') {
      setInteraction({ ...interaction, end: toDocumentPoint(stage) });
      return;
    }
    if (interaction.mode === 'connecting')
      setInteraction({ ...interaction, point: toDocumentPoint(stage) });
  };

  const handleStageMouseUp = () => {
    if (interaction.mode !== 'marquee') return;
    const selection = {
      x: Math.min(interaction.start.x, interaction.end.x),
      y: Math.min(interaction.start.y, interaction.end.y),
      width: Math.abs(interaction.end.x - interaction.start.x),
      height: Math.abs(interaction.end.y - interaction.start.y),
    };
    if (selection.width > 3 || selection.height > 3)
      selectMany(
        nodes
          .filter((node) => isInsideBounds(getNodeBounds(node), selection))
          .map((node) => node.id),
      );
    setInteraction({ mode: 'idle' });
  };

  const handleNodeSelect = (id: string) => {
    if (activeTool !== 'connect') {
      select(id);
      return;
    }
    if (interaction.mode !== 'connecting' || !interaction.sourceId) {
      select(id);
      setInteraction({ mode: 'connecting', relationType, sourceId: id });
      return;
    }
    if (interaction.sourceId !== id)
      addRelation(createRelation(relationType, interaction.sourceId, id));
    setInteraction({ mode: 'connecting', relationType });
  };

  return {
    activeTool,
    interaction,
    handleStageMouseDown,
    handleStageMouseMove,
    handleStageMouseUp,
    handleNodeSelect,
    handleDragStart: () => {
      pendingDrag.current = undefined;
      beginInteraction();
    },
    handleDragMove: (id: string, position: Point) => {
      pendingDrag.current = { id, position };
      if (dragFrame.current) return;
      dragFrame.current = window.requestAnimationFrame(() => {
        dragFrame.current = undefined;
        const pending = pendingDrag.current;
        pendingDrag.current = undefined;
        if (pending) moveNodeLive(pending.id, pending.position);
      });
    },
    handleDragEnd: (id: string, position: Point) => {
      flushDragPosition();
      moveNodeLive(id, position);
      commitInteraction();
    },
  };
};
