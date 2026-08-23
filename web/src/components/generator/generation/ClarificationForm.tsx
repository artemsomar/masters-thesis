import { useState } from 'react';
import type { FormEvent } from 'react';
import type { ClarificationAnswer, ClarificationQuestionsResponse } from '../../../types/api';
import { ClarificationQuestion } from './ClarificationQuestion';
import styles from './ClarificationForm.module.scss';

type Props = {
  questions: ClarificationQuestionsResponse;
  pending: boolean;
  errorMessage?: string;
  onSubmit: (answers: ClarificationAnswer[]) => void;
};

export const ClarificationForm = ({ questions, pending, errorMessage, onSubmit }: Props) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [showValidation, setShowValidation] = useState(false);
  const requiredAnswersPresent = questions.questions.every(
    (question) => !question.required || Boolean(answers[question.id]?.trim()),
  );

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setShowValidation(true);
    if (!requiredAnswersPresent) return;
    onSubmit(
      questions.questions
        .filter((question) => answers[question.id]?.trim())
        .map((question) => ({ questionId: question.id, value: answers[question.id].trim() })),
    );
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <div className={styles.questions}>
        {questions.questions.map((question) => (
          <ClarificationQuestion
            key={question.id}
            question={question}
            value={answers[question.id] ?? ''}
            disabled={pending}
            showValidation={showValidation}
            onChange={(value) => setAnswers((current) => ({ ...current, [question.id]: value }))}
          />
        ))}
      </div>
      {errorMessage ? (
        <p className={styles.error} role="alert">
          {errorMessage}
        </p>
      ) : null}
      <button type="submit" disabled={pending}>
        {pending ? 'Submitting answers…' : 'Continue generation'}
      </button>
    </form>
  );
};
