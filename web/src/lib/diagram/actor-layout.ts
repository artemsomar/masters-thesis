import type { ActorNode } from '../../types/diagram';
import { getTextLayout } from './use-case-layout';

export const getActorLayout = (node: ActorNode, size = node.size) => {
  const fontSize = node.style.fontSize ?? 12;
  const width = Math.max(size?.width ?? 104, fontSize * 2);
  const textWidth = width - 8;
  const text = getTextLayout(node.name, textWidth, fontSize);
  const height = Math.max(size?.height ?? 84, text.textHeight + 32);
  const scaleY = (height - text.textHeight) / 68;
  return {
    ...text,
    width,
    height,
    textWidth,
    scaleX: width / 104,
    scaleY,
    labelY: 28 * scaleY,
    top: -40 * scaleY,
  };
};
