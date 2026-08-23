import { useEffect, useRef } from 'react';
import { AlertTriangle, LoaderCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useDiagramSession } from '../../../hooks/generation/useDiagramSession';
import { usePersistGeneratedDiagram } from '../../../hooks/generation/usePersistGeneratedDiagram';
import type { DiagramSessionAccess } from '../../../types/api';
import { GenerationError } from './GenerationError';
import { GenerationProgress } from './GenerationProgress';
import styles from './AiGenerationWorkspace.module.scss';

type Props = { session: DiagramSessionAccess };

export const AiGenerationWorkspace = ({ session }: Props) => {
  const navigate = useNavigate();
  const sessionStatus = useDiagramSession(session);
  const persist = usePersistGeneratedDiagram();
  const hasStartedPersisting = useRef(false);
  const status = sessionStatus.data?.status ?? session.status;

  useEffect(() => {
    if (status !== 'diagram_ready' || hasStartedPersisting.current) return;
    hasStartedPersisting.current = true;
    persist.mutate(session, {
      onSuccess: (project) => navigate(`/editor/${project.projectId}`, { replace: true }),
    });
  }, [navigate, persist, session, status]);

  useEffect(() => {
    if (status === 'awaiting_answers') {
      navigate(`/generating/${session.sessionId}/questions`, { replace: true });
    }
  }, [navigate, session.sessionId, status]);

  if (sessionStatus.isError)
    return (
      <main className={styles.main}>
        <section className={styles.connectionError} role="alert">
          <AlertTriangle size={30} />
          <h1>Could not check generation status</h1>
          <p>The server may be unavailable. Please try again shortly.</p>
          <button type="button" onClick={() => void sessionStatus.refetch()}>
            Try again
          </button>
        </section>
      </main>
    );

  if (status === 'failed' || status === 'cancelled' || status === 'expired')
    return (
      <main className={styles.main}>
        <GenerationError status={status} />
      </main>
    );

  if (status === 'awaiting_answers') return null;

  if (persist.isError)
    return (
      <main className={styles.main}>
        <section className={styles.connectionError} role="alert">
          <AlertTriangle size={30} />
          <h1>Could not save the generated diagram</h1>
          <p>The diagram remains in the AI session until it expires. Please start again.</p>
          <button
            type="button"
            onClick={() => {
              hasStartedPersisting.current = false;
              persist.reset();
            }}
          >
            Try saving again
          </button>
        </section>
      </main>
    );

  return (
    <main className={styles.main}>
      {persist.isPending ? (
        <section className={styles.saving} aria-live="polite">
          <LoaderCircle className={styles.spin} size={36} />
          <h1>Saving your editable diagram…</h1>
        </section>
      ) : (
        <GenerationProgress status={status} streamConnected={sessionStatus.streamConnected} />
      )}
    </main>
  );
};
