import { XMLBuilder, XMLParser, XMLValidator } from 'fast-xml-parser';
import { createEmptyDocument } from '../diagram/factory';
import type { DiagramDocument, DiagramNode, DiagramRelation, NodeStyle } from '../../types/diagram';

const defaultStyle: NodeStyle = { fill: '#ffffff', stroke: '#1e293b', textColor: '#1e293b' };

type XmlNode = {
  '@_id': string;
  '@_kind': DiagramNode['kind'];
  '@_name': string;
  '@_x': string;
  '@_y': string;
  '@_width'?: string;
  '@_height'?: string;
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

const asFiniteNumber = (value: unknown, field: string): number => {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) throw new Error(`The project contains an invalid ${field}.`);
  return numberValue;
};

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
  const syntax = XMLValidator.validate(xml);
  if (syntax !== true)
    throw new Error(`The XML file is not valid (line ${syntax.err.line}: ${syntax.err.msg}).`);
  const parsed = new XMLParser({ ignoreAttributes: false, parseAttributeValue: false }).parse(
    xml,
  ) as {
    'diagram-document'?: {
      '@_version'?: string;
      nodes?: { node?: XmlNode | XmlNode[] };
      relations?: { relation?: XmlRelation | XmlRelation[] };
    };
  };
  const root = parsed['diagram-document'];
  if (!root) throw new Error('The project document is not valid XML.');
  if (root['@_version'] !== '1.0') throw new Error('The project uses an unsupported XML version.');
  const document = createEmptyDocument();
  document.nodes = asArray(root.nodes?.node).map((node) => {
    const style = {
      fill: node['@_fill'] ?? defaultStyle.fill,
      stroke: node['@_stroke'] ?? defaultStyle.stroke,
      textColor: node['@_textColor'] ?? defaultStyle.textColor,
    };
    const position = {
      x: asFiniteNumber(node['@_x'], 'element x coordinate'),
      y: asFiniteNumber(node['@_y'], 'element y coordinate'),
    };
    if (node['@_kind'] === 'boundary')
      return {
        id: node['@_id'],
        kind: 'boundary',
        name: node['@_name'],
        position,
        size: {
          width: asFiniteNumber(node['@_width'], 'boundary width'),
          height: asFiniteNumber(node['@_height'], 'boundary height'),
        },
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
  const nodeIds = new Set<string>();
  for (const node of document.nodes) {
    if (!node.id || !node.name) throw new Error('Each diagram element must have an ID and name.');
    if (nodeIds.has(node.id)) throw new Error('The project contains duplicate element IDs.');
    if (!Number.isFinite(node.position.x) || !Number.isFinite(node.position.y))
      throw new Error('The project contains invalid element coordinates.');
    if (node.kind === 'boundary' && (node.size.width <= 0 || node.size.height <= 0))
      throw new Error('A system boundary must have a positive width and height.');
    nodeIds.add(node.id);
  }
  const relationIds = new Set<string>();
  for (const relation of document.relations) {
    if (!relation.id || relationIds.has(relation.id))
      throw new Error('The project contains invalid or duplicate relation IDs.');
    if (
      relation.sourceId === relation.targetId ||
      !nodeIds.has(relation.sourceId) ||
      !nodeIds.has(relation.targetId)
    )
      throw new Error('A relation must connect two different existing elements.');
    relationIds.add(relation.id);
  }
  return document;
};
