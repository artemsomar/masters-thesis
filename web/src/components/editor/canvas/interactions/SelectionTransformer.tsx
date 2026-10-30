import { useLayoutEffect, useRef } from 'react';
import type Konva from 'konva';
import { Rect, Transformer } from 'react-konva';
import { getActorLayout } from '../../../../lib/diagram/actor-layout';
import { getUseCaseLayout } from '../../../../lib/diagram/use-case-layout';
import { getNodeBounds } from '../../../../lib/diagram/geometry';
import { useDiagramStore } from '../../../../store/diagram-store';
import type { DiagramNode } from '../../../../types/diagram';

const round = (value: number) => Math.round(value * 100) / 100;

export const SelectionTransformer = ({
  node,
  enabled,
}: {
  node: DiagramNode;
  enabled: boolean;
}) => {
  const rectRef = useRef<Konva.Rect>(null);
  const transformerRef = useRef<Konva.Transformer>(null);
  const bounds = getNodeBounds(node);

  useLayoutEffect(() => {
    const rect = rectRef.current;
    const transformer = transformerRef.current;
    if (!rect || !transformer || transformer.isTransforming()) return;
    rect.setAttrs({ ...bounds, scaleX: 1, scaleY: 1 });
    transformer.nodes([rect]);
    transformer.forceUpdate();
  }, [bounds.x, bounds.y, bounds.width, bounds.height, enabled]);

  const resize = () => {
    const rect = rectRef.current;
    if (!rect) return;
    const width = round(rect.width() * rect.scaleX());
    const height = round(rect.height() * rect.scaleY());
    const position =
      node.kind === 'boundary'
        ? { x: round(rect.x()), y: round(rect.y()) }
        : {
            x: round(rect.x() + width / 2),
            y: round(
              rect.y() +
                (node.kind === 'actor' ? -getActorLayout(node, { width, height }).top : height / 2),
            ),
          };
    useDiagramStore.getState().resizeNodeLive(node.id, position, { width, height });
  };

  return (
    <>
      <Rect ref={rectRef} listening={false} />
      <Transformer
        ref={transformerRef}
        listening={enabled}
        resizeEnabled={enabled}
        rotateEnabled={false}
        flipEnabled={false}
        keepRatio={false}
        ignoreStroke
        borderStroke="#4b41e1"
        borderDash={[4, 3]}
        anchorStroke="#4b41e1"
        anchorFill="#ffffff"
        anchorSize={8}
        anchorCornerRadius={2}
        boundBoxFunc={(previous, next) => {
          const scale = transformerRef.current?.getStage()?.scaleX() ?? 1;
          const minimum =
            node.kind === 'boundary' ? { width: 120, height: 100 } : { width: 52, height: 32 };
          const size = { width: next.width / scale, height: next.height / scale };
          const layout =
            node.kind === 'useCase'
              ? getUseCaseLayout(node.name, size, node.style.fontSize)
              : node.kind === 'actor'
                ? getActorLayout(node, size)
                : minimum;
          return next.width + 0.001 < Math.max(minimum.width, layout.width) * scale ||
            next.height + 0.001 < Math.max(minimum.height, layout.height) * scale
            ? previous
            : next;
        }}
        onTransformStart={() => useDiagramStore.getState().beginInteraction()}
        onTransform={resize}
        onTransformEnd={() => {
          resize();
          useDiagramStore.getState().commitInteraction();
          const current = useDiagramStore
            .getState()
            .document.nodes.find((item) => item.id === node.id);
          if (current)
            rectRef.current?.setAttrs({ ...getNodeBounds(current), scaleX: 1, scaleY: 1 });
          transformerRef.current?.forceUpdate();
        }}
      />
    </>
  );
};
