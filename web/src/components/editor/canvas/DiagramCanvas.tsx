import { useEffect, useRef, useState } from 'react';
import type Konva from 'konva';
import { Stage } from 'react-konva';
import { useDiagramStore } from '../../../store/diagram-store';
import { useEditorUiStore } from '../../../store/editor-ui-store';
import { DiagramLayer } from './layers/DiagramLayer';
import { GridLayer } from './layers/GridLayer';
import { InteractionLayer } from './layers/InteractionLayer';
import styles from './DiagramCanvas.module.scss';

export const DiagramCanvas = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const [size, setSize] = useState({ width: 800, height: 600 });
  const nodes = useDiagramStore((state) => state.document.nodes);
  const moveNode = useDiagramStore((state) => state.moveNode);
  const selectedIds = useEditorUiStore((state) => state.selectedIds);
  const select = useEditorUiStore((state) => state.select);
  const activeTool = useEditorUiStore((state) => state.activeTool);
  const viewport = useEditorUiStore((state) => state.viewport);
  const setViewport = useEditorUiStore((state) => state.setViewport);

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
        draggable={activeTool === 'pan'}
        onDragEnd={(event) => {
          setViewport({ x: event.target.x(), y: event.target.y(), scale: viewport.scale });
        }}
        onMouseDown={(event) => {
          if (event.target === event.target.getStage()) select('');
        }}
      >
        <GridLayer width={size.width / viewport.scale} height={size.height / viewport.scale} />
        <DiagramLayer nodes={nodes} onSelect={select} onDragEnd={moveNode} />
        <InteractionLayer selectedNodes={nodes.filter((node) => selectedIds.includes(node.id))} />
      </Stage>
    </div>
  );
};
