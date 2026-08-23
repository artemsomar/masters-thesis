import { SVG } from '@svgdotjs/svg.js';
import { getNodeBounds } from '../diagram/geometry';
import { getRelationPoints } from '../diagram/relation-paths';
import { getRelationStyle } from '../diagram/relation-style';
import type { DiagramDocument } from '../../types/diagram';

const padding = 32;

const getExportBounds = (document: DiagramDocument) => {
  const bounds = document.nodes.map(getNodeBounds);
  if (!bounds.length) return { x: 0, y: 0, width: 640, height: 400 };
  const left = Math.min(...bounds.map((bound) => bound.x));
  const top = Math.min(...bounds.map((bound) => bound.y));
  const right = Math.max(...bounds.map((bound) => bound.x + bound.width));
  const bottom = Math.max(...bounds.map((bound) => bound.y + bound.height));
  return {
    x: left - padding,
    y: top - padding,
    width: right - left + padding * 2,
    height: bottom - top + padding * 2,
  };
};

export const documentToSvg = (document: DiagramDocument): string => {
  const bounds = getExportBounds(document);
  const draw = SVG()
    .size(bounds.width, bounds.height)
    .viewbox(bounds.x, bounds.y, bounds.width, bounds.height);
  draw.rect(bounds.width, bounds.height).move(bounds.x, bounds.y).fill('#ffffff');
  const nodesById = new Map(document.nodes.map((node) => [node.id, node]));
  for (const relation of document.relations) {
    const points = getRelationPoints(relation, nodesById);
    if (!points) continue;
    const [source, target] = points;
    const style = getRelationStyle(relation.type);
    const line = draw
      .line(source.x, source.y, target.x, target.y)
      .stroke({ color: '#64748b', width: 1.5 });
    if (style.dash) line.attr({ 'stroke-dasharray': style.dash.join(' ') });
    if (style.pointer !== 'none') {
      const angle = Math.atan2(target.y - source.y, target.x - source.x);
      const size = 10;
      const left = {
        x: target.x - size * Math.cos(angle - Math.PI / 6),
        y: target.y - size * Math.sin(angle - Math.PI / 6),
      };
      const right = {
        x: target.x - size * Math.cos(angle + Math.PI / 6),
        y: target.y - size * Math.sin(angle + Math.PI / 6),
      };
      draw
        .polygon(`${target.x},${target.y} ${left.x},${left.y} ${right.x},${right.y}`)
        .fill(style.pointer === 'open' ? '#ffffff' : '#64748b')
        .stroke({ color: '#64748b', width: 1.5 });
    }
    if (style.label)
      draw
        .text(style.label)
        .font({ family: 'Inter, sans-serif', size: 11, anchor: 'middle' })
        .fill('#64748b')
        .center((source.x + target.x) / 2, (source.y + target.y) / 2 - 14);
  }
  for (const node of document.nodes) {
    if (node.kind === 'boundary') {
      draw
        .rect(node.size.width, node.size.height)
        .move(node.position.x, node.position.y)
        .fill({ color: node.style.fill, opacity: 0.42 })
        .stroke({ color: node.style.stroke, width: 1.2, dasharray: '7 5' })
        .radius(3);
      draw
        .text(node.name)
        .move(node.position.x + 14, node.position.y + 8)
        .font({ family: 'Inter, sans-serif', size: 13, weight: 700 })
        .fill(node.style.textColor);
    } else if (node.kind === 'useCase') {
      draw
        .ellipse(156, 62)
        .center(node.position.x, node.position.y)
        .fill(node.style.fill)
        .stroke({ color: node.style.stroke, width: 1.2 });
      draw
        .text(node.name)
        .font({ family: 'Inter, sans-serif', size: 12, anchor: 'middle' })
        .fill(node.style.textColor)
        .center(node.position.x, node.position.y);
    } else {
      const group = draw
        .group()
        .fill('none')
        .stroke({ color: node.style.stroke, width: 1.8, linecap: 'round', linejoin: 'round' });
      group.circle(16).center(node.position.x, node.position.y - 26);
      group.polyline(
        `${node.position.x},${node.position.y - 18} ${node.position.x},${node.position.y + 7} ${node.position.x - 12},${node.position.y + 20} ${node.position.x},${node.position.y + 7} ${node.position.x + 12},${node.position.y + 20}`,
      );
      draw
        .text(node.name)
        .font({ family: 'Inter, sans-serif', size: 12, anchor: 'middle' })
        .fill(node.style.textColor)
        .center(node.position.x, node.position.y + 34);
    }
  }
  return draw.svg();
};
