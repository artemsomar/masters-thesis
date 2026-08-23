import { XMLBuilder, XMLParser } from 'fast-xml-parser';
import { createEmptyDocument } from './diagram/factory';
import type { DiagramDocument, DiagramNode, DiagramRelation, NodeStyle } from '../types/diagram';

const defaultStyle: NodeStyle = { fill: '#ffffff', stroke: '#1e293b', textColor: '#1e293b' };

type XmlNode = {
  '@_id': string;
  '@_kind': DiagramNode['kind'];
  '@_name': string;
  '@_x': number;
  '@_y': number;
  '@_width'?: number;
  '@_height'?: number;
  '@_fill'?: string;
  '@_stroke'?: string;
  '@_textColor'?: string;
  description?: string;
};

type XmlRelation = {
  '@_id': string;
  '@_type': DiagramRelation['type'];
  '@_sourceId': string;
  '@_targetId': string;
};

const asArray = <T>(value: T | T[] | undefined): T[] =>
  value === undefined ? [] : Array.isArray(value) ? value : [value];

export const documentToXml = (document: DiagramDocument): string => {
  const builder = new XMLBuilder({ ignoreAttributes: false, format: true });
  return builder.build({
    'diagram-document': {
      '@_version': document.schemaVersion,
      nodes: {
        node: document.nodes.map((node) => ({
          '@_id': node.id,
          '@_kind': node.kind,
          '@_name': node.name,
          '@_x': node.position.x,
          '@_y': node.position.y,
          ...(node.kind === 'boundary'
            ? { '@_width': node.size.width, '@_height': node.size.height }
            : {}),
          '@_fill': node.style.fill,
          '@_stroke': node.style.stroke,
          '@_textColor': node.style.textColor,
          ...(node.kind === 'boundary' ? {} : { description: node.description }),
        })),
      },
      relations: {
        relation: document.relations.map((relation) => ({
          '@_id': relation.id,
          '@_type': relation.type,
          '@_sourceId': relation.sourceId,
          '@_targetId': relation.targetId,
        })),
      },
    },
  });
};

export const xmlToDocument = (xml: string): DiagramDocument => {
  const parsed = new XMLParser({ ignoreAttributes: false, parseAttributeValue: true }).parse(
    xml,
  ) as {
    'diagram-document'?: {
      nodes?: { node?: XmlNode | XmlNode[] };
      relations?: { relation?: XmlRelation | XmlRelation[] };
    };
  };
  const root = parsed['diagram-document'];
  if (!root) throw new Error('The project document is not valid XML.');
  const document = createEmptyDocument();
  document.nodes = asArray(root.nodes?.node).map((node) => {
    const style = {
      fill: node['@_fill'] ?? defaultStyle.fill,
      stroke: node['@_stroke'] ?? defaultStyle.stroke,
      textColor: node['@_textColor'] ?? defaultStyle.textColor,
    };
    const position = { x: Number(node['@_x']) || 0, y: Number(node['@_y']) || 0 };
    if (node['@_kind'] === 'boundary')
      return {
        id: node['@_id'],
        kind: 'boundary',
        name: node['@_name'],
        position,
        size: { width: Number(node['@_width']) || 440, height: Number(node['@_height']) || 300 },
        style,
      };
    if (node['@_kind'] === 'actor' || node['@_kind'] === 'useCase')
      return {
        id: node['@_id'],
        kind: node['@_kind'],
        name: node['@_name'],
        position,
        description: node.description ?? '',
        style,
      };
    throw new Error('The project contains an unsupported diagram element.');
  });
  document.relations = asArray(root.relations?.relation).map((relation) => {
    if (!['association', 'include', 'extend', 'generalization'].includes(relation['@_type']))
      throw new Error('The project contains an unsupported relation type.');
    return {
      id: relation['@_id'],
      type: relation['@_type'],
      sourceId: relation['@_sourceId'],
      targetId: relation['@_targetId'],
    };
  });
  return document;
};
