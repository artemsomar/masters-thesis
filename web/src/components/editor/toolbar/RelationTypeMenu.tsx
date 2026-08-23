import type { RelationType } from '../../../types/diagram';
import { useEditorUiStore } from '../../../store/editor-ui-store';
import styles from './RelationTypeMenu.module.scss';

const options: Array<{ value: RelationType; label: string }> = [
  { value: 'association', label: 'Association' },
  { value: 'include', label: 'Include' },
  { value: 'extend', label: 'Extend' },
  { value: 'generalization', label: 'Generalization' },
];

export const RelationTypeMenu = () => {
  const relationType = useEditorUiStore((state) => state.relationType);
  const setRelationType = useEditorUiStore((state) => state.setRelationType);
  return (
    <label className={styles.menu}>
      Relation
      <select
        value={relationType}
        onChange={(event) => setRelationType(event.target.value as RelationType)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
};
