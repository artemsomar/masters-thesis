import { useEffect } from 'react';
import { AlertTriangle, LoaderCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useClarificationQuestions } from '../../../hooks/generation/useClarificationQuestions';
import { useDiagramSession } from '../../../hooks/generation/useDiagramSession';
import { useSubmitClarificationAnswers } from '../../../hooks/generation/useSubmitClarificationAnswers';
import type { DiagramSessionAccess } from '../../../types/api';
import { ApiError } from '../../../api/client';
import { ClarificationForm } from './ClarificationForm';
import styles from './RefinementQuestionsWorkspace.module.scss';

type Props = { session: DiagramSessionAccess };

const errorMessage = (error: unknown, fallback: string): string =>
  error instanceof ApiError ? error.message : fallback;

export const RefinementQuestionsWorkspace = ({ session }: Props) => {
  const navigate = useNavigate();
  const sessionStatus = useDiagramSession(session);
  const status = sessionStatus.data?.status ?? session.status;
  const questions = useClarificationQuestions(session, status === 'awaiting_answers');
  const submitAnswers = useSubmitClarificationAnswers(session);

  useEffect(() => {
    if (sessionStatus.data && status !== 'awaiting_answers') {
      navigate(`/generating/${session.sessionId}`, { replace: true });
    }
  }, [navigate, session.sessionId, sessionStatus.data, status]);

  if (sessionStatus.isError)
    return (
      <main className={styles.main}>
        <section className={styles.state} role="alert">
          <AlertTriangle size={30} />
          <h1>Could not check the generation session</h1>
          <p>Please try again shortly.</p>
          <button type="button" onClick={() => void sessionStatus.refetch()}>
            Try again
          </button>
        </section>
      </main>
    );

  if (sessionStatus.isPending)
    return (
      <main className={styles.main}>
        <section className={styles.state} aria-live="polite">
          <LoaderCircle className={styles.spin} size={32} />
          <p>Checking generation status…</p>
        </section>
      </main>
    );

  if (status !== 'awaiting_answers')
    return (
      <main className={styles.main}>
        <section className={styles.state} aria-live="polite">
          <LoaderCircle className={styles.spin} size={32} />
          <p>Opening generation status…</p>
        </section>
      </main>
    );

  if (questions.isPending)
    return (
      <main className={styles.main}>
        <section className={styles.state} aria-live="polite">
          <LoaderCircle className={styles.spin} size={32} />
          <p>Loading clarification questions…</p>
        </section>
      </main>
    );

  if (questions.isError || !questions.data)
    return (
      <main className={styles.main}>
        <section className={styles.state} role="alert">
          <AlertTriangle size={30} />
          <h1>Could not load clarification questions</h1>
          <p>{errorMessage(questions.error, 'Please try again.')}</p>
          <button type="button" onClick={() => void questions.refetch()}>
            Try again
          </button>
        </section>
      </main>
    );

  if (!questions.data.questions.length)
    return (
      <main className={styles.main}>
        <section className={styles.state} role="alert">
          <AlertTriangle size={30} />
          <h1>No clarification questions are available</h1>
          <p>The server has not provided a question for this round yet.</p>
          <button type="button" onClick={() => void questions.refetch()}>
            Reload questions
          </button>
        </section>
      </main>
    );

  return (
    <main className={styles.main}>
      <section className={styles.content}>
        <header>
          <span>Clarification round {questions.data.round}</span>
          <h1>A few details are needed</h1>
          <p>Answer the required questions so Blueprint UC can generate an accurate diagram.</p>
        </header>
        <ClarificationForm
          key={questions.data.round}
          questions={questions.data}
          pending={submitAnswers.isPending}
          errorMessage={
            submitAnswers.isError
              ? errorMessage(submitAnswers.error, 'Could not submit answers.')
              : undefined
          }
          onSubmit={(answers) =>
            submitAnswers.mutate(
              { round: questions.data.round, answers },
              { onSuccess: () => navigate(`/generating/${session.sessionId}`, { replace: true }) },
            )
          }
        />
      </section>
    </main>
  );
};
