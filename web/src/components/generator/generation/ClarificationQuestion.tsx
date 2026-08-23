import type { ClarificationQuestion as ClarificationQuestionData } from '../../../types/api';
import styles from './ClarificationQuestion.module.scss';

type Props = {
  question: ClarificationQuestionData;
  value: string;
  disabled: boolean;
  showValidation: boolean;
  onChange: (value: string) => void;
};

export const ClarificationQuestion = ({
  question,
  value,
  disabled,
  showValidation,
  onChange,
}: Props) => {
  const isInvalid = question.required && showValidation && !value.trim();

  return (
    <label className={styles.question}>
      <span className={styles.prompt}>
        {question.text}
        {question.required ? <em>Required</em> : <em>Optional</em>}
      </span>
      <textarea
        value={value}
        disabled={disabled}
        aria-invalid={isInvalid}
        aria-describedby={isInvalid ? `${question.id}-error` : undefined}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Enter your answer"
        rows={4}
      />
      {isInvalid ? (
        <span id={`${question.id}-error`} className={styles.error}>
          This answer is required.
        </span>
      ) : null}
    </label>
  );
};
