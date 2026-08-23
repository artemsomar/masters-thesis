import { useEffect, useRef, useState } from 'react';
import type Konva from 'konva';
import { Stage } from 'react-konva';
import { useCanvasInteraction } from '../../../hooks/diagram/useCanvasInteraction';
import { useDiagramStore } from '../../../store/diagram-store';
import { useEditorUiStore } from '../../../store/editor-ui-store';
import { DiagramLayer } from './layers/DiagramLayer';
import { GridLayer } from './layers/GridLayer';
import { InteractionLayer } from './layers/InteractionLayer';
import styles from './DiagramCanvas.module.scss';

type Props = { stageRef: React.RefObject<Konva.Stage | null> };

export const DiagramCanvas = ({ stageRef }: Props) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 800, height: 600 });
  const nodes = useDiagramStore((state) => state.document.nodes);
  const relations = useDiagramStore((state) => state.document.relations);
  const selectedIds = useEditorUiStore((state) => state.selectedIds);
  const select = useEditorUiStore((state) => state.select);
  const viewport = useEditorUiStore((state) => state.viewport);
  const setViewport = useEditorUiStore((state) => state.setViewport);
  const canvas = useCanvasInteraction();

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div className={styles.canvas} ref={containerRef}>
      <Stage
        ref={stageRef}
        width={size.width}
        height={size.height}
        x={viewport.x}
        y={viewport.y}
        scaleX={viewport.scale}
        scaleY={viewport.scale}
        draggable={canvas.activeTool === 'pan'}
        onDragStart={() => useEditorUiStore.getState().setInteraction({ mode: 'panning' })}
        onDragEnd={(event) => {
          setViewport({ x: event.target.x(), y: event.target.y(), scale: viewport.scale });
          useEditorUiStore.getState().setInteraction({ mode: 'idle' });
        }}
        onMouseDown={(event) => {
          canvas.handleStageMouseDown(
            event.target.getStage()!,
            event.target === event.target.getStage(),
          );
        }}
        onMouseMove={(event) => canvas.handleStageMouseMove(event.target.getStage()!)}
        onMouseUp={canvas.handleStageMouseUp}
      >
        <GridLayer width={size.width / viewport.scale} height={size.height / viewport.scale} />
        <DiagramLayer
          nodes={nodes}
          relations={relations}
          selectedIds={selectedIds}
          onSelectNode={canvas.handleNodeSelect}
          onSelectRelation={select}
          onDragStart={canvas.handleDragStart}
          onDragMove={canvas.handleDragMove}
          onDragEnd={canvas.handleDragEnd}
          draggable={canvas.activeTool === 'select'}
        />
        <InteractionLayer
          selectedNodes={nodes.filter((node) => selectedIds.includes(node.id))}
          nodes={nodes}
          interaction={canvas.interaction}
        />
      </Stage>
    </div>
  );
};
