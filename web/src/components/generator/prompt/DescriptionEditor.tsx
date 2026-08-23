import type { ChangeEvent } from 'react';
import styles from './DescriptionEditor.module.scss';

type Props = {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
};

export const DescriptionEditor = ({ value, disabled, onChange }: Props) => {
  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => onChange(event.target.value);

  return (
    <label className={styles.field}>
      <span>System architecture prompt</span>
      <textarea
        value={value}
        disabled={disabled}
        onChange={handleChange}
        placeholder="Describe actors, use cases and system boundaries. For example: An e-commerce system where a customer browses items, adds them to a cart and checks out. A payment gateway processes payments."
      />
      <small>Markdown supported</small>
    </label>
  );
};
