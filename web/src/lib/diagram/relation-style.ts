import type { RelationType } from '../../types/diagram';

export type RelationStyle = {
  dash?: number[];
  label?: string;
  pointer: 'none' | 'filled' | 'open';
};

export const getRelationStyle = (type: RelationType): RelationStyle => {
  switch (type) {
    case 'association':
      return { pointer: 'none' };
    case 'include':
      return { dash: [7, 5], label: '«include»', pointer: 'filled' };
    case 'extend':
      return { dash: [7, 5], label: '«extend»', pointer: 'filled' };
    case 'generalization':
      return { pointer: 'open' };
  }
};
